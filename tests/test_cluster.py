import os
import sys
import unittest

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.cluster import (
    MIN_K, MAX_K, FEATURE_COLS,
    compute_cluster_scores, run_clustering,
    compute_cluster_means, compute_author_cluster_counts,
)


def _make_df(n_per_cluster=20, seed=0):
    """4 well-separated clusters in iktus_1..4 space."""
    rng = np.random.default_rng(seed)
    centers = [
        [0.9, 0.9, 0.9, 0.9],
        [0.1, 0.1, 0.1, 0.1],
        [0.9, 0.1, 0.5, 0.5],
        [0.1, 0.9, 0.5, 0.5],
    ]
    rows = []
    for c in centers:
        pts = np.array(c) + rng.normal(0, 0.03, (n_per_cluster, 4))
        rows.append(pts.clip(0, 1))
    arr = np.vstack(rows)
    return pd.DataFrame({
        'id': range(len(arr)),
        'author': 'test',
        'title': 'test',
        'iktus_1': arr[:, 0],
        'iktus_2': arr[:, 1],
        'iktus_3': arr[:, 2],
        'iktus_4': arr[:, 3],
        'analysed_lines': 10,
    })


class TestComputeClusterScores(unittest.TestCase):
    def setUp(self):
        df = _make_df()
        self.features = df[['iktus_1', 'iktus_2', 'iktus_3', 'iktus_4']].to_numpy()

    def test_returns_scores_for_all_k(self):
        scores = compute_cluster_scores(self.features)
        ks = [s['k'] for s in scores]
        self.assertEqual(ks, list(range(MIN_K, MAX_K + 1)))

    def test_scores_are_floats_in_valid_range(self):
        scores = compute_cluster_scores(self.features)
        for s in scores:
            self.assertIsInstance(s['score'], float)
            self.assertGreaterEqual(s['score'], -1.0)
            self.assertLessEqual(s['score'], 1.0)

    def test_raises_on_too_few_rows(self):
        features = np.zeros((MIN_K * 2 - 1, 4))
        with self.assertRaises(ValueError) as ctx:
            compute_cluster_scores(features)
        self.assertIn(str(MIN_K * 2), str(ctx.exception))

    def test_custom_max_k(self):
        scores = compute_cluster_scores(self.features, max_k=6)
        self.assertEqual([s['k'] for s in scores], list(range(MIN_K, 7)))


class TestRunClustering(unittest.TestCase):
    def setUp(self):
        self.df = _make_df()

    def test_adds_cluster_column(self):
        df_result, _, _ = run_clustering(self.df)
        self.assertIn('cluster', df_result.columns)

    def test_cluster_count_matches_chosen_k(self):
        df_result, _, chosen_k = run_clustering(self.df)
        self.assertEqual(df_result['cluster'].nunique(), chosen_k)

    def test_cluster_labels_in_range(self):
        df_result, _, chosen_k = run_clustering(self.df)
        self.assertTrue(df_result['cluster'].between(0, chosen_k - 1).all())

    def test_auto_chosen_k_in_valid_range(self):
        _, _, chosen_k = run_clustering(self.df)
        self.assertGreaterEqual(chosen_k, MIN_K)
        self.assertLessEqual(chosen_k, MAX_K)

    def test_manual_k_is_respected(self):
        _, _, chosen_k = run_clustering(self.df, n_clusters=5)
        self.assertEqual(chosen_k, 5)

    def test_manual_k_outside_max_included_in_scores(self):
        _, scores, chosen_k = run_clustering(self.df, n_clusters=MAX_K + 2)
        ks = [s['k'] for s in scores]
        self.assertIn(MAX_K + 2, ks)
        self.assertEqual(chosen_k, MAX_K + 2)

    def test_scores_cover_min_k_to_max_k(self):
        _, scores, _ = run_clustering(self.df)
        ks = [s['k'] for s in scores]
        self.assertEqual(min(ks), MIN_K)
        self.assertGreaterEqual(max(ks), MAX_K)

    def test_scores_in_ascending_k_order(self):
        _, scores, _ = run_clustering(self.df)
        ks = [s['k'] for s in scores]
        self.assertEqual(ks, sorted(ks))

    def test_original_df_not_modified(self):
        original_cols = list(self.df.columns)
        run_clustering(self.df)
        self.assertEqual(list(self.df.columns), original_cols)

    def test_nan_values_treated_as_zero(self):
        df = self.df.copy()
        df.loc[0, 'iktus_1'] = float('nan')
        df_result, _, _ = run_clustering(df)
        self.assertFalse(df_result['cluster'].isna().any())

    def test_missing_column_raises(self):
        df = self.df.drop(columns=['iktus_3'])
        with self.assertRaises(ValueError) as ctx:
            run_clustering(df)
        self.assertIn('iktus_3', str(ctx.exception))

    def test_too_few_rows_raises(self):
        df = _make_df(n_per_cluster=1)  # 4 rows < MIN_K * 2
        with self.assertRaises(ValueError):
            run_clustering(df)

    def test_manual_k_below_min_raises(self):
        with self.assertRaises(ValueError) as ctx:
            run_clustering(self.df, n_clusters=MIN_K - 1)
        self.assertIn(str(MIN_K), str(ctx.exception))

    def test_row_count_preserved(self):
        df_result, _, _ = run_clustering(self.df)
        self.assertEqual(len(df_result), len(self.df))


def _make_df_multi_author(n_per_cluster=20, seed=0):
    """Like _make_df but with 4 distinct authors cycling through rows."""
    df = _make_df(n_per_cluster, seed)
    authors = ['Author A', 'Author B', 'Author C', 'Author D']
    df['author'] = [authors[i % len(authors)] for i in range(len(df))]
    return df


class TestComputeClusterMeans(unittest.TestCase):
    def setUp(self):
        df = _make_df()
        df_result, _, self.chosen_k = run_clustering(df)
        self.df_result = df_result

    def test_length_equals_chosen_k(self):
        result = compute_cluster_means(self.df_result, self.chosen_k)
        self.assertEqual(len(result), self.chosen_k)

    def test_cluster_indices_are_sequential(self):
        result = compute_cluster_means(self.df_result, self.chosen_k)
        self.assertEqual([r['cluster'] for r in result], list(range(self.chosen_k)))

    def test_all_feature_cols_present(self):
        result = compute_cluster_means(self.df_result, self.chosen_k)
        for row in result:
            for col in FEATURE_COLS:
                self.assertIn(col, row)

    def test_means_in_valid_range(self):
        result = compute_cluster_means(self.df_result, self.chosen_k)
        for row in result:
            for col in FEATURE_COLS:
                self.assertGreaterEqual(row[col], 0.0)
                self.assertLessEqual(row[col], 1.0)

    def test_means_are_floats(self):
        result = compute_cluster_means(self.df_result, self.chosen_k)
        for row in result:
            for col in FEATURE_COLS:
                self.assertIsInstance(row[col], float)

    def test_mean_close_to_actual(self):
        result = compute_cluster_means(self.df_result, self.chosen_k)
        for row in result:
            k = row['cluster']
            subset = self.df_result[self.df_result['cluster'] == k]
            for col in FEATURE_COLS:
                expected = float(subset[col].mean())
                self.assertAlmostEqual(row[col], expected, places=3)


class TestComputeAuthorClusterCounts(unittest.TestCase):
    def setUp(self):
        df = _make_df_multi_author()
        df_result, _, self.chosen_k = run_clustering(df)
        self.df_result = df_result
        self.n_authors = df_result['author'].nunique()

    def test_length_equals_author_count(self):
        result = compute_author_cluster_counts(self.df_result, self.chosen_k)
        self.assertEqual(len(result), self.n_authors)

    def test_each_author_appears_once(self):
        result = compute_author_cluster_counts(self.df_result, self.chosen_k)
        authors = [r['author'] for r in result]
        self.assertEqual(len(authors), len(set(authors)))

    def test_counts_length_equals_chosen_k(self):
        result = compute_author_cluster_counts(self.df_result, self.chosen_k)
        for item in result:
            self.assertEqual(len(item['counts']), self.chosen_k)

    def test_counts_sum_matches_author_row_count(self):
        result = compute_author_cluster_counts(self.df_result, self.chosen_k)
        author_totals = self.df_result.groupby('author').size().to_dict()
        for item in result:
            self.assertEqual(sum(item['counts']), author_totals[item['author']])

    def test_counts_are_non_negative_integers(self):
        result = compute_author_cluster_counts(self.df_result, self.chosen_k)
        for item in result:
            for c in item['counts']:
                self.assertIsInstance(c, int)
                self.assertGreaterEqual(c, 0)

    def test_result_is_sorted_by_author(self):
        result = compute_author_cluster_counts(self.df_result, self.chosen_k)
        authors = [r['author'] for r in result]
        self.assertEqual(authors, sorted(authors))


if __name__ == '__main__':
    unittest.main()
