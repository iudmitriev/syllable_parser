import math

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

FEATURE_COLS = ['iktus_1', 'iktus_2', 'iktus_3', 'iktus_4']
MIN_K = 4
MAX_K = 10


def compute_cluster_scores(features, min_k=MIN_K, max_k=MAX_K):
    """
    Returns list of {'k': int, 'score': float} for k in [min_k, min(max_k, n-1)].
    Raises ValueError if features has fewer than min_k * 2 rows.
    """
    n = len(features)
    if n < min_k * 2:
        raise ValueError(
            f'Слишком мало строк для кластеризации: нужно ≥ {min_k * 2}, получено {n}.'
        )
    effective_max = min(max_k, n - 1)
    scores = []
    for k in range(min_k, effective_max + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(features)
        score = silhouette_score(features, labels)
        scores.append({'k': k, 'score': score})
    return scores


def run_clustering(df, n_clusters=None):
    """
    Validates df, computes silhouette scores for k in [MIN_K, max(MAX_K, n_clusters)],
    applies k-means with chosen_k. Returns (df_with_cluster, scores, chosen_k).

    Raises ValueError on bad input.
    """
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f'Отсутствуют столбцы: {", ".join(missing)}.')

    if n_clusters is not None and n_clusters < MIN_K:
        raise ValueError(f'Число кластеров должно быть ≥ {MIN_K}.')

    features = df[FEATURE_COLS].fillna(0).to_numpy()

    effective_max = max(MAX_K, n_clusters or 0)
    scores = compute_cluster_scores(features, min_k=MIN_K, max_k=effective_max)

    if n_clusters is not None:
        chosen_k = n_clusters
    else:
        chosen_k = max(scores, key=lambda s: s['score'])['k']

    km = KMeans(n_clusters=chosen_k, random_state=42, n_init=10)
    df = df.copy()
    df['cluster'] = km.fit_predict(features)

    return df, scores, chosen_k


def compute_cluster_means(df, chosen_k):
    """
    Returns list of {'cluster': int, 'iktus_1': float, ...} for each cluster 0..chosen_k-1.
    Missing clusters get 0.0 for all features.
    """
    rows = []
    for k in range(chosen_k):
        subset = df[df['cluster'] == k]
        row = {'cluster': k}
        for col in FEATURE_COLS:
            v = subset[col].mean() if len(subset) > 0 else float('nan')
            row[col] = round(float(v), 4) if not math.isnan(v) else 0.0
        rows.append(row)
    return rows


def compute_author_cluster_counts(df, chosen_k):
    """
    Returns list of {'author': str, 'counts': [int]*chosen_k} sorted by author.
    counts[k] = number of rows for that author assigned to cluster k.
    """
    result = []
    for author, group in df.groupby('author', sort=True):
        counts = [int((group['cluster'] == k).sum()) for k in range(chosen_k)]
        result.append({'author': str(author), 'counts': counts})
    return result
