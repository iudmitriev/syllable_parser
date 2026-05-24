from collections import defaultdict
from itertools import product

VOWEL_LETTERS = set('aeiouy')
PHANTOM = '^'
STRESS_MARK = '<'

STRONG_POSITIONS = (2, 4, 6, 8)
SHIFTED_STRONG_POSITIONS = (1, 4, 6, 8)
WEAK_POSITIONS = (1, 3, 5, 7)

IAMB_VARIANTS = (0, 1, 2, 3, 4)


def parse_rhythmic_word(rword):
    """Parse a single rhythmic word string.

    Returns (num_syllables, stress_position_1based) or None if the word has
    no syllables or does not have exactly one stress.
    """
    syllables_stress = []
    i = 0
    n = len(rword)
    while i < n:
        c = rword[i]
        if c == '[':
            end = rword.find(']', i)
            if end == -1:
                i += 1
                continue
            i = end + 1
            stressed = i < n and rword[i] == STRESS_MARK
            if stressed:
                i += 1
            syllables_stress.append(stressed)
        elif c == PHANTOM or c.lower() in VOWEL_LETTERS:
            i += 1
            stressed = i < n and rword[i] == STRESS_MARK
            if stressed:
                i += 1
            syllables_stress.append(stressed)
        else:
            i += 1

    if not syllables_stress:
        return None
    stress_positions = [idx + 1 for idx, s in enumerate(syllables_stress) if s]
    if len(stress_positions) != 1:
        return None
    return (len(syllables_stress), stress_positions[0])


def split_into_rhythmic_words(text):
    """Split marked-up text into rhythmic word strings.

    Both `|` and newlines act as boundaries.
    """
    rwords = []
    for line in text.split('\n'):
        for chunk in line.split('|'):
            chunk = chunk.strip()
            if chunk:
                rwords.append(chunk)
    return rwords


def compute_rhythmic_dictionary(text):
    """Returns counts, proportions, total count, and skipped count."""
    counts = defaultdict(int)
    total_chunks = 0
    skipped = 0
    for chunk in split_into_rhythmic_words(text):
        total_chunks += 1
        parsed = parse_rhythmic_word(chunk)
        if parsed is None:
            skipped += 1
            continue
        counts[parsed] += 1
    total = sum(counts.values())
    proportions = {k: v / total for k, v in counts.items()} if total > 0 else {}
    return counts, proportions, total, skipped


def _pattern_string(stressed_set, total_syllables):
    """Render the stress pattern as a visual string of '-' and '/'."""
    chars = []
    for pos in range(1, total_syllables + 1):
        if pos in stressed_set:
            chars.append('/')
        else:
            chars.append('-')
    return ''.join(chars)


def _enumerate_for_template(proportions, template, total_syllables, weight,
                            allow_preceding_weak, required_positions,
                            pattern_probs, *, is_shifted=False,
                            weak_stress_weight=1.0, shift_weight=1.0):
    template_set = set(template)
    n = len(template)
    for mask in range(1, 1 << n):
        stressed_strong = [template[i] for i in range(n) if mask & (1 << i)]
        if not required_positions.issubset(stressed_strong):
            continue

        if allow_preceding_weak:
            candidate_weaks = [s - 1 for s in stressed_strong
                               if s - 1 >= 1 and (s - 1) not in template_set]
            weak_mask_range = range(1 << len(candidate_weaks))
        else:
            candidate_weaks = []
            weak_mask_range = [0]

        for wmask in weak_mask_range:
            stressed_weak = [candidate_weaks[i]
                             for i in range(len(candidate_weaks))
                             if wmask & (1 << i)]
            all_stressed = sorted(set(stressed_strong) | set(stressed_weak))
            m = len(all_stressed)

            ranges = []
            for i in range(m - 1):
                ranges.append(range(all_stressed[i], all_stressed[i + 1]))

            for inner in product(*ranges):
                bounds = [0] + list(inner) + [total_syllables]
                if bounds[-1] < all_stressed[-1]:
                    continue
                prob = 1.0
                ok = True
                for i in range(m):
                    n_syl = bounds[i + 1] - bounds[i]
                    s_pos = all_stressed[i] - bounds[i]
                    if n_syl <= 0 or s_pos <= 0 or s_pos > n_syl:
                        ok = False
                        break
                    key = (n_syl, s_pos)
                    p = proportions.get(key, 0.0)
                    if p == 0.0:
                        ok = False
                        break
                    prob *= p
                if ok and prob > 0:
                    pattern = _pattern_string(set(all_stressed), total_syllables)
                    effective_weight = weight
                    if is_shifted:
                        effective_weight *= shift_weight
                    if stressed_weak:
                        effective_weight *= weak_stress_weight
                    pattern_probs[pattern] += prob * effective_weight


def _is_valid_variant_4_stress_set(stressed):
    """Variant 4 rule: every stressed weak position must have at least one
    stressed adjacent position, with one exception — position 1 is always
    allowed to carry a stress (its missing left neighbour does not count
    against it). Positions outside the line at the right end are treated
    as unstressed. Empty stress sets are rejected.
    """
    if not stressed:
        return False
    weak = set(WEAK_POSITIONS)
    for w in stressed:
        if w in weak and w != 1:
            if (w - 1) not in stressed and (w + 1) not in stressed:
                return False
    return True


def _enumerate_variant_4(proportions, total_syllables, weight, pattern_probs,
                         *, weak_stress_weight=1.0):
    """Enumerate every stress set on positions 1..8 satisfying the variant-4
    rule and accumulate decomposition probabilities for each."""
    candidate_positions = tuple(range(1, 9))
    n = len(candidate_positions)
    weak = set(WEAK_POSITIONS)
    for mask in range(1, 1 << n):
        stressed = {candidate_positions[i] for i in range(n) if mask & (1 << i)}
        if not _is_valid_variant_4_stress_set(stressed):
            continue
        all_stressed = sorted(stressed)
        m = len(all_stressed)
        ranges = []
        for i in range(m - 1):
            ranges.append(range(all_stressed[i], all_stressed[i + 1]))
        has_weak = any(p in weak for p in stressed)
        for inner in product(*ranges):
            bounds = [0] + list(inner) + [total_syllables]
            if bounds[-1] < all_stressed[-1]:
                continue
            prob = 1.0
            ok = True
            for i in range(m):
                n_syl = bounds[i + 1] - bounds[i]
                s_pos = all_stressed[i] - bounds[i]
                if n_syl <= 0 or s_pos <= 0 or s_pos > n_syl:
                    ok = False
                    break
                key = (n_syl, s_pos)
                p = proportions.get(key, 0.0)
                if p == 0.0:
                    ok = False
                    break
                prob *= p
            if ok and prob > 0:
                pattern = _pattern_string(stressed, total_syllables)
                effective_weight = weight
                if has_weak:
                    effective_weight *= weak_stress_weight
                pattern_probs[pattern] += prob * effective_weight


def _enumerate_for_length(proportions, variant, total_syllables, pattern_probs,
                          *, weak_stress_weight=1.0, shift_weight=1.0):
    """Populate `pattern_probs` for a single line length, with unit weight
    (no feminine_weight applied)."""
    if variant == 4:
        _enumerate_variant_4(
            proportions, total_syllables, 1.0, pattern_probs,
            weak_stress_weight=weak_stress_weight,
        )
        return

    if variant == 0:
        templates = [(STRONG_POSITIONS, False, {8}, False)]
    else:
        templates = [(STRONG_POSITIONS, variant >= 2, set(), False)]
        if variant >= 3:
            templates.append((SHIFTED_STRONG_POSITIONS, True, {1}, True))

    for template, allow_weak, required, is_shifted in templates:
        _enumerate_for_template(
            proportions, template, total_syllables, 1.0,
            allow_preceding_weak=allow_weak,
            required_positions=required,
            pattern_probs=pattern_probs,
            is_shifted=is_shifted,
            weak_stress_weight=weak_stress_weight,
            shift_weight=shift_weight,
        )


def enumerate_iamb_patterns_split(proportions, variant=1,
                                  weak_stress_weight=1.0, shift_weight=1.0):
    """Return (male_pattern_probs, female_pattern_probs) — pattern probability
    masses for 8- and 9-syllable iambs respectively, without any feminine
    weighting applied. Each dict maps a pattern string (length 8 or 9) to a
    mass; the relative sizes within each dict reflect the model probabilities
    of those patterns, while the sum across each dict reflects the model's
    likelihood of producing an iambic line of that length at all.
    """
    if variant not in IAMB_VARIANTS:
        variant = 1
    male = defaultdict(float)
    female = defaultdict(float)
    _enumerate_for_length(
        proportions, variant, 8, male,
        weak_stress_weight=weak_stress_weight, shift_weight=shift_weight,
    )
    _enumerate_for_length(
        proportions, variant, 9, female,
        weak_stress_weight=weak_stress_weight, shift_weight=shift_weight,
    )
    return dict(male), dict(female)


def enumerate_iamb_patterns(proportions, feminine_weight=1.0, variant=1,
                            weak_stress_weight=1.0, shift_weight=1.0):
    """For each iamb stress pattern, sum the products of word proportions
    over all word-sequence combinations that realize that pattern.

    Patterns include both masculine (8 syllables) and feminine (9 syllables)
    endings. Feminine-ending pattern probabilities are multiplied by
    `feminine_weight` (a value in [0, 1]).

    The `variant` parameter controls what counts as an iamb:
      0: like variant 1, but the 8th syllable must be stressed.
      1: only stresses on strong positions (2, 4, 6, 8).
      2: variant 1, plus stresses on a weak position immediately preceding
         a stressed strong position.
      3: variant 2, plus lines with a shifted first foot
         (strong positions 1, 4, 6, 8 — pattern /--/-/-/...).
      4: any stress set is allowed as long as no stressed weak position
         (other than position 1) has both neighbours unstressed. Position 1
         may always be stressed regardless of position 2.

    `weak_stress_weight` (variant 2+): multiplier for patterns that have at
    least one stress on a weak position. Applied in addition to
    feminine_weight where both are relevant.

    `shift_weight` (variant 3): multiplier for patterns generated from the
    shifted-first-foot template (strong positions 1, 4, 6, 8). Applied in
    addition to other weights where relevant. Has no effect on variant 4.
    """
    male, female = enumerate_iamb_patterns_split(
        proportions, variant=variant,
        weak_stress_weight=weak_stress_weight, shift_weight=shift_weight,
    )
    combined = defaultdict(float)
    for pattern, mass in male.items():
        combined[pattern] += mass
    if feminine_weight > 0:
        for pattern, mass in female.items():
            combined[pattern] += mass * feminine_weight
    return dict(combined)


def _stresses_match_template(stresses, template, allow_preceding_weak, required):
    template_set = set(template)
    if not required.issubset(stresses):
        return False
    strong = stresses & template_set
    weak = stresses - template_set
    if not strong:
        return False
    if weak and not allow_preceding_weak:
        return False
    for w in weak:
        if (w + 1) not in template_set:
            return False
        if (w + 1) not in strong:
            return False
    return True


def _is_valid_iamb_pattern(stresses, total_syllables, variant):
    if total_syllables not in (8, 9):
        return False
    if not stresses:
        return False
    if total_syllables == 9 and 9 in stresses:
        return False

    if variant == 0:
        return _stresses_match_template(
            stresses, STRONG_POSITIONS,
            allow_preceding_weak=False, required={8},
        )
    if variant == 4:
        return _is_valid_variant_4_stress_set(stresses)
    if _stresses_match_template(
        stresses, STRONG_POSITIONS,
        allow_preceding_weak=variant >= 2, required=set(),
    ):
        return True
    if variant >= 3 and _stresses_match_template(
        stresses, SHIFTED_STRONG_POSITIONS,
        allow_preceding_weak=True, required={1},
    ):
        return True
    return False


def find_accidental_iambs(text, feminine_weight=1.0, variant=1):
    """Find every contiguous run of rhythmic words in `text` whose total
    syllable count is 8 or 9 and whose stress positions form a valid iamb
    under the chosen variant.

    Chunks that fail to parse (section headers like "(I)", multi-stress
    chunks, punctuation-only chunks) break the run — an accidental iamb
    cannot span them.
    """
    feminine_weight = max(0.0, min(1.0, float(feminine_weight)))
    try:
        variant = int(variant)
    except (TypeError, ValueError):
        variant = 1
    if variant not in IAMB_VARIANTS:
        variant = 1

    chunks = []
    for chunk in split_into_rhythmic_words(text):
        chunks.append((parse_rhythmic_word(chunk), chunk))

    allowed_lengths = (8, 9) if feminine_weight > 0 else (8,)
    max_len = max(allowed_lengths)

    iambs = []
    n = len(chunks)
    for start in range(n):
        if chunks[start][0] is None:
            continue
        total = 0
        stresses = set()
        for end in range(start, n):
            parsed, _ = chunks[end]
            if parsed is None:
                break
            n_syl, s_pos = parsed
            total += n_syl
            stresses.add(total - n_syl + s_pos)
            if total > max_len:
                break
            if total in allowed_lengths and _is_valid_iamb_pattern(
                stresses, total, variant,
            ):
                snippet = ' | '.join(c for _, c in chunks[start:end + 1])
                iambs.append({
                    'text': snippet,
                    'pattern': _pattern_string(stresses, total),
                    'syllables': total,
                })

    return iambs


def _iamb_form_order():
    """Return the 16 form signatures (s2, s4, s6, s8) in canonical order:
    first by stress on position 8 (stressed first), then by total number of
    stresses on strong positions (descending), then by the unstressed strong
    positions among {2, 4, 6} in ascending lexicographic order.
    """
    forms = []
    for stress_8 in (True, False):
        candidates = []
        for s2, s4, s6 in product((True, False), repeat=3):
            sig = (s2, s4, s6, stress_8)
            unstressed_246 = tuple(
                p for p, s in zip((2, 4, 6), (s2, s4, s6)) if not s
            )
            candidates.append((sig, unstressed_246))
        candidates.sort(key=lambda item: (-sum(item[0]), item[1]))
        forms.extend(sig for sig, _ in candidates)
    return forms


def _iamb_form_pattern(sig):
    """Render an 8-character pattern for a form signature."""
    chars = []
    for pos in range(1, 9):
        if pos in STRONG_POSITIONS:
            idx = (pos // 2) - 1
            chars.append('/' if sig[idx] else '-')
        else:
            chars.append('-')
    return ''.join(chars)


def _form_signature_from_pattern(pattern):
    return tuple(
        (pos - 1) < len(pattern) and pattern[pos - 1] == '/'
        for pos in STRONG_POSITIONS
    )


def compute_iamb_forms(male_probs, female_probs, feminine_weight):
    """Aggregate pattern masses into the 16 iamb forms defined by the stress
    pattern at strong positions (2, 4, 6, 8). For each form, return three
    probabilities:

    - male:   normalized share of the form among 8-syllable iambs (∑ = 1).
    - female: normalized share of the form among 9-syllable iambs (∑ = 1).
    - total:  (1 - feminine_weight) * male + feminine_weight * female.
    """
    male_by_form = defaultdict(float)
    female_by_form = defaultdict(float)
    for pattern, mass in male_probs.items():
        male_by_form[_form_signature_from_pattern(pattern)] += mass
    for pattern, mass in female_probs.items():
        female_by_form[_form_signature_from_pattern(pattern)] += mass

    male_total = sum(male_by_form.values())
    female_total = sum(female_by_form.values())

    rows = []
    for i, sig in enumerate(_iamb_form_order(), 1):
        m_mass = male_by_form.get(sig, 0.0)
        f_mass = female_by_form.get(sig, 0.0)
        m_norm = m_mass / male_total if male_total > 0 else 0.0
        f_norm = f_mass / female_total if female_total > 0 else 0.0
        total = (1.0 - feminine_weight) * m_norm + feminine_weight * f_norm
        rows.append({
            'form_number': i,
            'pattern': _iamb_form_pattern(sig),
            'male': m_norm,
            'female': f_norm,
            'total': total,
        })
    return rows


def compute_stress_profile(pattern_probs):
    """For each strong position, compute the total probability mass of
    patterns that have a stress at that position. Also returns the
    normalized probability (conditional on producing an iambic line).
    """
    raw = {p: 0.0 for p in STRONG_POSITIONS}
    total = sum(pattern_probs.values())
    for pattern, prob in pattern_probs.items():
        for pos in STRONG_POSITIONS:
            if pos - 1 < len(pattern) and pattern[pos - 1] == '/':
                raw[pos] += prob
    if total > 0:
        normalized = {p: raw[p] / total for p in STRONG_POSITIONS}
    else:
        normalized = {p: 0.0 for p in STRONG_POSITIONS}
    return raw, normalized, total


def analyze_iamb(text, feminine_weight=1.0, variant=1,
                 weak_stress_weight=1.0, shift_weight=1.0):
    feminine_weight = max(0.0, min(1.0, float(feminine_weight)))
    weak_stress_weight = max(0.0, float(weak_stress_weight))
    shift_weight = max(0.0, float(shift_weight))
    try:
        variant = int(variant)
    except (TypeError, ValueError):
        variant = 1
    if variant not in IAMB_VARIANTS:
        variant = 1
    counts, proportions, total, skipped = compute_rhythmic_dictionary(text)
    male_probs, female_probs = enumerate_iamb_patterns_split(
        proportions, variant=variant,
        weak_stress_weight=weak_stress_weight, shift_weight=shift_weight,
    )
    pattern_probs = defaultdict(float)
    for pattern, mass in male_probs.items():
        pattern_probs[pattern] += mass
    if feminine_weight > 0:
        for pattern, mass in female_probs.items():
            pattern_probs[pattern] += mass * feminine_weight
    pattern_probs = dict(pattern_probs)
    raw_profile, normalized_profile, total_pattern_prob = compute_stress_profile(pattern_probs)
    iamb_forms = compute_iamb_forms(male_probs, female_probs, feminine_weight)
    accidental_iambs = find_accidental_iambs(
        text, feminine_weight=feminine_weight, variant=variant,
    )
    pattern_counts = defaultdict(int)
    syllable_counts = defaultdict(int)
    for iamb in accidental_iambs:
        pattern_counts[iamb['pattern']] += 1
        syllable_counts[iamb['syllables']] += 1
    accidental_iamb_stats = {
        'total': len(accidental_iambs),
        'by_syllables': [
            {'syllables': s, 'count': syllable_counts[s]}
            for s in sorted(syllable_counts)
        ],
        'by_pattern': [
            {'pattern': p, 'count': c}
            for p, c in sorted(pattern_counts.items(),
                               key=lambda kv: (-kv[1], kv[0]))
        ],
    }

    rhythmic_dict_rows = []
    for key in sorted(counts.keys()):
        n_syl, s_pos = key
        c = counts[key]
        p = proportions[key]
        rhythmic_dict_rows.append({
            'syllables': n_syl,
            'stress': s_pos,
            'count': c,
            'proportion': p,
        })

    pattern_rows = []
    for pattern in sorted(pattern_probs.keys(),
                          key=lambda x: (-pattern_probs[x], x)):
        pattern_rows.append({
            'pattern': pattern,
            'probability': pattern_probs[pattern],
            'normalized': (pattern_probs[pattern] / total_pattern_prob)
                          if total_pattern_prob > 0 else 0.0,
        })

    profile_rows = []
    for pos in STRONG_POSITIONS:
        profile_rows.append({
            'position': pos,
            'raw': raw_profile[pos],
            'normalized': normalized_profile[pos],
        })

    return {
        'total_words': total,
        'skipped_chunks': skipped,
        'rhythmic_dictionary': rhythmic_dict_rows,
        'patterns': pattern_rows,
        'profile': profile_rows,
        'total_pattern_probability': total_pattern_prob,
        'feminine_weight': feminine_weight,
        'variant': variant,
        'accidental_iambs': accidental_iambs,
        'accidental_iamb_stats': accidental_iamb_stats,
        'iamb_forms': iamb_forms,
    }
