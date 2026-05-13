import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIXTURES = os.path.join(HERE, 'fixtures')
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.iamb_analyzer import (
    analyze_iamb,
    compute_rhythmic_dictionary,
    compute_stress_profile,
    enumerate_iamb_patterns,
    find_accidental_iambs,
    parse_rhythmic_word,
    split_into_rhythmic_words,
)


class ParseRhythmicWordTests(unittest.TestCase):
    def test_monosyllable_stressed(self):
        self.assertEqual(parse_rhythmic_word("wa<s"), (1, 1))

    def test_monosyllable_with_trailing_mute(self):
        self.assertEqual(parse_rhythmic_word("ha<v-"), (1, 1))

    def test_two_syllables_stress_on_second(self):
        self.assertEqual(parse_rhythmic_word("the Wo<rd,"), (2, 2))

    def test_three_syllables_stress_on_second(self):
        self.assertEqual(parse_rhythmic_word("begi<nning"), (3, 2))

    def test_five_syllables_compound(self):
        self.assertEqual(parse_rhythmic_word("In the begi<nning"), (5, 4))

    def test_bracket_vowel_group_counts_as_one(self):
        self.assertEqual(parse_rhythmic_word("th[ee]<"), (1, 1))

    def test_bracket_vowel_group_unstressed_then_stressed(self):
        self.assertEqual(parse_rhythmic_word("rec[ei]<v-d"), (2, 2))

    def test_phantom_vowel_counts(self):
        self.assertEqual(parse_rhythmic_word("d^<"), (1, 1))

    def test_y_is_a_vowel(self):
        self.assertEqual(parse_rhythmic_word("a<ny"), (2, 1))

    def test_uppercase_vowels(self):
        self.assertEqual(parse_rhythmic_word("A<ll"), (1, 1))

    def test_no_stress_returns_none(self):
        self.assertIsNone(parse_rhythmic_word("the"))

    def test_no_vowels_returns_none(self):
        self.assertIsNone(parse_rhythmic_word(",.;"))

    def test_multiple_stresses_returns_none(self):
        self.assertIsNone(parse_rhythmic_word("a< e<"))

    def test_section_header_returns_none(self):
        self.assertIsNone(parse_rhythmic_word("(I)"))
        self.assertIsNone(parse_rhythmic_word("(II)"))

    def test_unclosed_bracket_does_not_crash(self):
        # We don't assert exact output for malformed input, just that the
        # parser produces a well-formed result (tuple or None) without raising.
        result = parse_rhythmic_word("a<[oo")
        self.assertTrue(result is None or isinstance(result, tuple))


class SplitIntoRhythmicWordsTests(unittest.TestCase):
    def test_splits_on_pipe(self):
        chunks = split_into_rhythmic_words("a<| b<| c<|")
        self.assertEqual(chunks, ["a<", "b<", "c<"])

    def test_splits_on_newline(self):
        chunks = split_into_rhythmic_words("a<\nb<\nc<")
        self.assertEqual(chunks, ["a<", "b<", "c<"])

    def test_strips_whitespace(self):
        chunks = split_into_rhythmic_words("  a<  |   b<  ")
        self.assertEqual(chunks, ["a<", "b<"])

    def test_skips_empty(self):
        chunks = split_into_rhythmic_words("||a<|||\n\nb<|\n")
        self.assertEqual(chunks, ["a<", "b<"])

    def test_section_header_kept_as_separate_chunk(self):
        chunks = split_into_rhythmic_words("(I)\nIn the begi<nning| wa<s|")
        self.assertEqual(chunks, ["(I)", "In the begi<nning", "wa<s"])


class RhythmicDictionaryTests(unittest.TestCase):
    def test_counts_and_proportions(self):
        # Three pipe-separated chunks: two parseable (1,1) words and one
        # chunk with no vowels (so it is skipped).
        text = "a<| e<| b<c<|"
        counts, proportions, total, skipped = compute_rhythmic_dictionary(text)
        self.assertEqual(total, 2)
        self.assertEqual(skipped, 1)
        self.assertEqual(counts[(1, 1)], 2)
        self.assertAlmostEqual(proportions[(1, 1)], 1.0)

    def test_mixed_types(self):
        text = "a<|the Wo<rd|begi<nning|"
        counts, proportions, total, skipped = compute_rhythmic_dictionary(text)
        self.assertEqual(total, 3)
        self.assertEqual(skipped, 0)
        self.assertEqual(counts[(1, 1)], 1)
        self.assertEqual(counts[(2, 2)], 1)
        self.assertEqual(counts[(3, 2)], 1)
        for k in counts:
            self.assertAlmostEqual(proportions[k], 1 / 3)

    def test_proportions_sum_to_one(self):
        text = "a<| a<| b<c<| d<|the Wo<rd| begi<nning|"
        _, proportions, total, _ = compute_rhythmic_dictionary(text)
        self.assertGreater(total, 0)
        self.assertAlmostEqual(sum(proportions.values()), 1.0)


class EnumerateIambPatternsTests(unittest.TestCase):
    def test_unbuildable_dictionary_yields_no_patterns(self):
        # With only (1,1) words, every word's stress lands on its own
        # 1-syllable span, so consecutive (1,1) words would stress positions
        # 1,2,3,... which violates the weak-position rule. No iamb is
        # buildable.
        patterns = enumerate_iamb_patterns({(1, 1): 1.0}, feminine_weight=1.0)
        self.assertEqual(patterns, {})

    def test_masculine_and_feminine_patterns_both_present(self):
        # (2,2) makes pure iambic feet (8 syllables) and (3,2) lets the
        # last foot run into a 9th unstressed syllable -> feminine ending.
        proportions = {(2, 2): 1.0, (3, 2): 1.0}
        patterns = enumerate_iamb_patterns(proportions, feminine_weight=1.0)
        lengths = {len(p) for p in patterns}
        self.assertIn(8, lengths)
        self.assertIn(9, lengths)

    def test_feminine_weight_zero_drops_nine_syllable_patterns(self):
        proportions = {(2, 2): 1.0, (3, 2): 1.0}
        patterns = enumerate_iamb_patterns(proportions, feminine_weight=0.0)
        self.assertTrue(patterns)
        for pattern in patterns:
            self.assertEqual(len(pattern), 8)

    def test_feminine_weight_scales_nine_syllable_patterns(self):
        proportions = {(2, 2): 0.5, (3, 2): 0.3, (1, 1): 0.2}
        full = enumerate_iamb_patterns(proportions, feminine_weight=1.0)
        half = enumerate_iamb_patterns(proportions, feminine_weight=0.5)
        # All masculine patterns from `full` are unchanged in `half`,
        # all feminine patterns are exactly halved.
        for pattern, prob in full.items():
            self.assertIn(pattern, half)
            if len(pattern) == 9:
                self.assertAlmostEqual(half[pattern], prob * 0.5)
            else:
                self.assertAlmostEqual(half[pattern], prob)

    def test_pattern_strong_positions_only_stressed(self):
        proportions = {(2, 2): 1.0, (1, 1): 1.0, (3, 2): 1.0}
        patterns = enumerate_iamb_patterns(proportions, feminine_weight=1.0)
        self.assertTrue(patterns)
        for pattern in patterns:
            for idx, ch in enumerate(pattern):
                position = idx + 1
                if ch == '/':
                    self.assertIn(position, (2, 4, 6, 8))

    def test_simple_pure_iamb_probability(self):
        # All weight on the (2,2) iambic foot: only -/-/-/-/ is reachable
        # (4 feet of (2,2)) with probability 1**4 = 1.
        proportions = {(2, 2): 1.0}
        patterns = enumerate_iamb_patterns(proportions, feminine_weight=1.0)
        self.assertEqual(set(patterns.keys()), {"-/-/-/-/"})
        self.assertAlmostEqual(patterns["-/-/-/-/"], 1.0)


class StressProfileTests(unittest.TestCase):
    def test_profile_picks_up_strong_positions(self):
        patterns = {
            "-/-/-/-/":  0.4,  # stresses at 2,4,6,8
            "---/-/-/":  0.3,  # stresses at 4,6,8
            "-/-/-/-/-": 0.2,  # stresses at 2,4,6,8 (feminine)
            "-/---/--":  0.1,  # stresses at 2,6
        }
        raw, normalized, total = compute_stress_profile(patterns)
        self.assertAlmostEqual(total, 1.0)
        self.assertAlmostEqual(raw[2], 0.4 + 0.2 + 0.1)
        self.assertAlmostEqual(raw[4], 0.4 + 0.3 + 0.2)
        self.assertAlmostEqual(raw[6], 0.4 + 0.3 + 0.2 + 0.1)
        self.assertAlmostEqual(raw[8], 0.4 + 0.3 + 0.2)
        for pos in (2, 4, 6, 8):
            self.assertAlmostEqual(normalized[pos], raw[pos] / total)

    def test_empty_patterns_yields_zero_profile(self):
        raw, normalized, total = compute_stress_profile({})
        self.assertEqual(total, 0)
        self.assertEqual(raw, {2: 0.0, 4: 0.0, 6: 0.0, 8: 0.0})
        self.assertEqual(normalized, {2: 0.0, 4: 0.0, 6: 0.0, 8: 0.0})


class EnumerateIambVariantsTests(unittest.TestCase):
    def test_default_variant_matches_variant_1(self):
        proportions = {(2, 2): 0.5, (1, 1): 0.3, (3, 2): 0.2}
        default = enumerate_iamb_patterns(proportions, feminine_weight=1.0)
        explicit = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=1)
        self.assertEqual(default, explicit)

    def test_invalid_variant_falls_back_to_one(self):
        proportions = {(2, 2): 1.0}
        ref = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=1)
        out = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=99)
        self.assertEqual(ref, out)

    def test_variant_1_only_stresses_strong_positions(self):
        # With only (1,1) and (2,2) words, variant 1 still produces -/-/-/-/
        # but never any pattern with a stressed weak position.
        proportions = {(1, 1): 0.5, (2, 2): 0.5}
        v1 = enumerate_iamb_patterns(proportions, feminine_weight=0.0, variant=1)
        self.assertTrue(v1)
        for pattern in v1:
            for idx, ch in enumerate(pattern):
                if ch == '/':
                    self.assertIn(idx + 1, (2, 4, 6, 8))

    def test_variant_0_requires_stress_at_position_8(self):
        proportions = {(2, 2): 0.4, (3, 2): 0.3, (1, 1): 0.3}
        v0 = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=0)
        self.assertTrue(v0)
        for pattern in v0:
            self.assertEqual(pattern[7], '/')

    def test_variant_0_is_subset_of_variant_1(self):
        proportions = {(2, 2): 0.4, (3, 2): 0.3, (1, 1): 0.3}
        v0 = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=0)
        v1 = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=1)
        self.assertTrue(v0)
        for pattern, prob in v0.items():
            self.assertIn(pattern, v1)
            self.assertAlmostEqual(v1[pattern], prob)

    def test_variant_0_drops_patterns_without_stress_at_8(self):
        # (4,2) lets the last foot end at position 6, producing -/-/-/--;
        # variant 0 must drop that pattern.
        proportions = {(2, 2): 0.3, (3, 2): 0.3, (1, 1): 0.2, (4, 2): 0.2}
        v0 = enumerate_iamb_patterns(proportions, feminine_weight=0.0, variant=0)
        v1 = enumerate_iamb_patterns(proportions, feminine_weight=0.0, variant=1)
        self.assertIn('-/-/-/--', v1)
        self.assertNotIn('-/-/-/--', v0)
        for pattern in v0:
            self.assertEqual(pattern[7], '/')

    def test_variant_2_includes_variant_1_patterns(self):
        proportions = {(2, 2): 0.5, (1, 1): 0.3, (3, 2): 0.2}
        v1 = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=1)
        v2 = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=2)
        self.assertTrue(v1)
        for pattern, prob in v1.items():
            self.assertIn(pattern, v2)
            self.assertAlmostEqual(v2[pattern], prob)

    def test_variant_2_allows_weak_stress_before_strong(self):
        # (1,1)(1,1)(2,2)(2,2)(2,2)(2,2) realises //-/-/-/ — only variant 2+
        # permits the stress on position 1 (weak before stressed 2).
        proportions = {(1, 1): 0.5, (2, 2): 0.5}
        v1 = enumerate_iamb_patterns(proportions, feminine_weight=0.0, variant=1)
        v2 = enumerate_iamb_patterns(proportions, feminine_weight=0.0, variant=2)
        self.assertNotIn('//-/-/-/', v1)
        self.assertIn('//-/-/-/', v2)

    def test_variant_2_does_not_allow_isolated_weak_stress(self):
        # A weak position can only be stressed when the following strong
        # position is also stressed. Position 3 stress without stress at 4
        # must never appear.
        proportions = {(1, 1): 0.3, (2, 2): 0.4, (3, 2): 0.3, (3, 3): 0.3}
        v2 = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=2)
        self.assertTrue(v2)
        for pattern in v2:
            for idx, ch in enumerate(pattern):
                pos = idx + 1
                if ch == '/' and pos not in (2, 4, 6, 8):
                    # weak position is stressed -> the next strong must be too
                    self.assertLess(pos, len(pattern))
                    self.assertEqual(pattern[pos], '/')

    def test_variant_3_includes_variant_2_patterns(self):
        proportions = {(1, 1): 0.3, (2, 2): 0.3, (3, 2): 0.2, (3, 3): 0.2}
        v2 = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=2)
        v3 = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=3)
        self.assertTrue(v2)
        for pattern, prob in v2.items():
            self.assertIn(pattern, v3)
            self.assertAlmostEqual(v3[pattern], prob)

    def test_variant_3_adds_shifted_first_foot(self):
        # /--/-/-/ requires stress at 1 and 4 without stress at 2 — only the
        # shifted first foot of variant 3 can produce it.
        proportions = {(1, 1): 0.4, (3, 3): 0.3, (2, 2): 0.3}
        v2 = enumerate_iamb_patterns(proportions, feminine_weight=0.0, variant=2)
        v3 = enumerate_iamb_patterns(proportions, feminine_weight=0.0, variant=3)
        self.assertNotIn('/--/-/-/', v2)
        self.assertIn('/--/-/-/', v3)
        # Probability matches the only decomposition (1,1)(3,3)(2,2)(2,2).
        self.assertAlmostEqual(v3['/--/-/-/'], 0.4 * 0.3 * 0.3 * 0.3)

    def test_variant_3_shifted_template_never_stresses_position_2(self):
        # The shifted first foot keeps position 2 unstressed by construction,
        # and weak position 2 is not adjacent to any shifted strong position.
        proportions = {(1, 1): 0.4, (3, 3): 0.3, (2, 2): 0.3}
        v2 = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=2)
        v3 = enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=3)
        shifted_only = set(v3) - set(v2)
        self.assertTrue(shifted_only)
        for pattern in shifted_only:
            self.assertEqual(pattern[0], '/')
            self.assertEqual(pattern[1], '-')

    def test_total_probability_nondecreasing_across_variants(self):
        proportions = {(1, 1): 0.3, (2, 2): 0.3, (3, 2): 0.2, (3, 3): 0.2}
        p1 = sum(enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=1).values())
        p2 = sum(enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=2).values())
        p3 = sum(enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=3).values())
        self.assertLessEqual(p1, p2 + 1e-12)
        self.assertLessEqual(p2, p3 + 1e-12)


class AnalyzeIambTests(unittest.TestCase):
    def test_analyze_returns_expected_keys(self):
        result = analyze_iamb("a<| the Wo<rd| begi<nning|", feminine_weight=1.0)
        expected_keys = {
            'total_words', 'skipped_chunks', 'rhythmic_dictionary',
            'patterns', 'profile', 'total_pattern_probability',
            'feminine_weight', 'variant',
            'accidental_iambs', 'accidental_iamb_stats',
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_feminine_weight_clamped_to_unit_interval(self):
        below = analyze_iamb("a<| b<|", feminine_weight=-1.0)
        above = analyze_iamb("a<| b<|", feminine_weight=5.0)
        self.assertEqual(below['feminine_weight'], 0.0)
        self.assertEqual(above['feminine_weight'], 1.0)

    def test_feminine_weight_zero_means_only_masculine_patterns(self):
        with open(os.path.join(FIXTURES, 'sample_input.txt')) as f:
            text = f.read()
        result = analyze_iamb(text, feminine_weight=0.0)
        for row in result['patterns']:
            self.assertEqual(len(row['pattern']), 8)

    def test_feminine_weight_changes_total_probability_linearly(self):
        with open(os.path.join(FIXTURES, 'sample_input.txt')) as f:
            text = f.read()
        zero = analyze_iamb(text, feminine_weight=0.0)['total_pattern_probability']
        half = analyze_iamb(text, feminine_weight=0.5)['total_pattern_probability']
        full = analyze_iamb(text, feminine_weight=1.0)['total_pattern_probability']
        self.assertAlmostEqual(half, zero + 0.5 * (full - zero))

    def test_sample_input_counts(self):
        with open(os.path.join(FIXTURES, 'sample_input.txt')) as f:
            text = f.read()
        result = analyze_iamb(text, feminine_weight=1.0)
        self.assertEqual(result['total_words'], 2675)
        self.assertEqual(result['skipped_chunks'], 8)

    def test_variant_default_is_one(self):
        result = analyze_iamb("a<| the Wo<rd| begi<nning|", feminine_weight=1.0)
        self.assertEqual(result['variant'], 1)

    def test_variant_passed_through(self):
        result = analyze_iamb("a<| the Wo<rd| begi<nning|",
                              feminine_weight=1.0, variant=2)
        self.assertEqual(result['variant'], 2)

    def test_invalid_variant_clamped_to_one(self):
        result = analyze_iamb("a<| the Wo<rd|", feminine_weight=1.0, variant=99)
        self.assertEqual(result['variant'], 1)
        result_str = analyze_iamb("a<| the Wo<rd|", feminine_weight=1.0,
                                  variant="nonsense")
        self.assertEqual(result_str['variant'], 1)

    def test_variant_total_probability_nondecreasing_on_sample(self):
        with open(os.path.join(FIXTURES, 'sample_input.txt')) as f:
            text = f.read()
        p1 = analyze_iamb(text, feminine_weight=1.0, variant=1)['total_pattern_probability']
        p2 = analyze_iamb(text, feminine_weight=1.0, variant=2)['total_pattern_probability']
        p3 = analyze_iamb(text, feminine_weight=1.0, variant=3)['total_pattern_probability']
        self.assertLessEqual(p1, p2 + 1e-12)
        self.assertLessEqual(p2, p3 + 1e-12)

    def test_accidental_iamb_stats_match_list(self):
        text = ("the Wo<rd| the Wo<rd| the Wo<rd| the Wo<rd|"
                "\n(I)\n"
                "the Wo<rd| the Wo<rd| the Wo<rd| begi<nning|")
        result = analyze_iamb(text, feminine_weight=1.0, variant=1)
        stats = result['accidental_iamb_stats']
        self.assertEqual(stats['total'], len(result['accidental_iambs']))
        # Two iambs: one masculine -/-/-/-/, one feminine -/-/-/-/-.
        self.assertEqual(stats['total'], 2)
        pattern_counts = {row['pattern']: row['count']
                          for row in stats['by_pattern']}
        self.assertEqual(pattern_counts.get('-/-/-/-/'), 1)
        self.assertEqual(pattern_counts.get('-/-/-/-/-'), 1)
        syl_counts = {row['syllables']: row['count']
                      for row in stats['by_syllables']}
        self.assertEqual(syl_counts, {8: 1, 9: 1})

    def test_accidental_iamb_stats_by_pattern_sorted_by_count(self):
        # Three masculine iambs of -/-/-/-/ separated by section headers.
        text = ("the Wo<rd| the Wo<rd| the Wo<rd| the Wo<rd|"
                "\n(I)\n"
                "the Wo<rd| the Wo<rd| the Wo<rd| the Wo<rd|"
                "\n(II)\n"
                "the Wo<rd| the Wo<rd| the Wo<rd| the Wo<rd|")
        result = analyze_iamb(text, feminine_weight=0.0, variant=1)
        stats = result['accidental_iamb_stats']
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['by_pattern'][0]['pattern'], '-/-/-/-/')
        self.assertEqual(stats['by_pattern'][0]['count'], 3)

    def test_rhythmic_dictionary_sorted_by_type(self):
        with open(os.path.join(FIXTURES, 'sample_input.txt')) as f:
            text = f.read()
        result = analyze_iamb(text, feminine_weight=1.0)
        keys = [(row['syllables'], row['stress'])
                for row in result['rhythmic_dictionary']]
        self.assertEqual(keys, sorted(keys))


class FindAccidentalIambsTests(unittest.TestCase):
    def test_text_shorter_than_iamb_returns_empty(self):
        text = "the Wo<rd| the Wo<rd|"
        self.assertEqual(find_accidental_iambs(text, feminine_weight=1.0, variant=1), [])

    def test_finds_single_masculine_iamb(self):
        text = "the Wo<rd| the Wo<rd| the Wo<rd| the Wo<rd|"
        iambs = find_accidental_iambs(text, feminine_weight=1.0, variant=1)
        self.assertEqual(len(iambs), 1)
        self.assertEqual(iambs[0]['pattern'], '-/-/-/-/')
        self.assertEqual(iambs[0]['syllables'], 8)
        self.assertIn('Wo<rd', iambs[0]['text'])

    def test_finds_feminine_iamb(self):
        # (2,2)(2,2)(2,2)(3,2) — 9 syllables, stresses at 2,4,6,8.
        text = "the Wo<rd| the Wo<rd| the Wo<rd| begi<nning|"
        iambs = find_accidental_iambs(text, feminine_weight=1.0, variant=1)
        patterns = [i['pattern'] for i in iambs]
        self.assertIn('-/-/-/-/-', patterns)

    def test_feminine_weight_zero_drops_feminine_iambs(self):
        text = "the Wo<rd| the Wo<rd| the Wo<rd| begi<nning|"
        iambs = find_accidental_iambs(text, feminine_weight=0.0, variant=1)
        for iamb in iambs:
            self.assertEqual(iamb['syllables'], 8)

    def test_section_header_breaks_run(self):
        text = "the Wo<rd| the Wo<rd|\n(I)\nthe Wo<rd| the Wo<rd|"
        iambs = find_accidental_iambs(text, feminine_weight=1.0, variant=1)
        self.assertEqual(iambs, [])

    def test_finds_multiple_disjoint_iambs(self):
        # 4 x (2,2) iamb, then break via (I), then 4 x (2,2) iamb again.
        text = ("the Wo<rd| the Wo<rd| the Wo<rd| the Wo<rd|"
                "\n(I)\n"
                "the Wo<rd| the Wo<rd| the Wo<rd| the Wo<rd|")
        iambs = find_accidental_iambs(text, feminine_weight=1.0, variant=1)
        self.assertEqual(len(iambs), 2)
        for iamb in iambs:
            self.assertEqual(iamb['pattern'], '-/-/-/-/')

    def test_variant_0_requires_stress_at_position_8(self):
        # -/-/-/-/ has stress at 8 → valid for v0.
        text = "the Wo<rd| the Wo<rd| the Wo<rd| the Wo<rd|"
        v0 = find_accidental_iambs(text, feminine_weight=1.0, variant=0)
        self.assertEqual(len(v0), 1)

    def test_variant_3_picks_up_shifted_first_foot(self):
        # (1,1)(3,3)(2,2)(2,2) -> stresses {1,4,6,8} -> /--/-/-/,
        # only valid under variant 3 (shifted first foot).
        # `aoo<` is a synthetic 3-vowel chunk with stress on the third vowel.
        text = "wa<s| aoo<| the Wo<rd| the Wo<rd|"
        v2 = find_accidental_iambs(text, feminine_weight=0.0, variant=2)
        v3 = find_accidental_iambs(text, feminine_weight=0.0, variant=3)
        v2_patterns = {i['pattern'] for i in v2}
        v3_patterns = {i['pattern'] for i in v3}
        self.assertNotIn('/--/-/-/', v2_patterns)
        self.assertIn('/--/-/-/', v3_patterns)

    def test_multi_stress_chunk_breaks_run(self):
        # "a< e<" has two stresses -> parse_rhythmic_word returns None,
        # so it should break the iamb-search run just like a section header.
        text = ("the Wo<rd| the Wo<rd|"
                " a< e<|"
                " the Wo<rd| the Wo<rd|")
        iambs = find_accidental_iambs(text, feminine_weight=1.0, variant=1)
        self.assertEqual(iambs, [])


if __name__ == '__main__':
    unittest.main()
