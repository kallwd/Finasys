from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def package_status() -> dict[str, dict[str, str | bool]]:
    result: dict[str, dict[str, str | bool]] = {}
    for key, distribution in {
        "scikit_learn": "scikit-learn",
        "lightgbm": "lightgbm",
        "hmmlearn": "hmmlearn",
    }.items():
        try:
            result[key] = {"installed": True, "version": version(distribution)}
        except PackageNotFoundError:
            result[key] = {"installed": False, "version": ""}
    return result


def run_demo_model() -> dict[str, float | int | str]:
    """Exercise the three ML libraries on deterministic synthetic data only."""
    import numpy as np
    from hmmlearn.hmm import GaussianHMM
    from lightgbm import LGBMClassifier
    from sklearn.metrics import accuracy_score

    rng = np.random.default_rng(42)
    rows = 420
    momentum = rng.normal(0, 1, rows)
    value = rng.normal(0, 1, rows)
    volatility = np.abs(rng.normal(0.02, 0.008, rows))
    noise = rng.normal(0, 0.7, rows)
    score = 0.7 * momentum + 0.35 * value - 8 * volatility + noise
    labels = (score > np.median(score)).astype(int)
    features = np.column_stack((momentum, value, volatility))

    split = 320
    classifier = LGBMClassifier(
        n_estimators=60,
        learning_rate=0.05,
        max_depth=3,
        num_leaves=7,
        verbosity=-1,
        random_state=42,
    )
    classifier.fit(features[:split], labels[:split])
    predicted = classifier.predict(features[split:])

    hidden_regimes = np.repeat(np.array([0, 1, 2, 1, 0, 2, 1]), 60)[:rows]
    regime_means = np.array([-0.012, 0.0, 0.012])
    returns = (regime_means[hidden_regimes] + rng.normal(0, 0.004, rows)).reshape(-1, 1)
    hmm = GaussianHMM(
        n_components=3,
        covariance_type="diag",
        n_iter=120,
        random_state=42,
    )
    hmm.fit(returns)
    states = hmm.predict(returns)
    observed_states = np.unique(states)
    state_means = {
        int(state): float(returns[states == state].mean()) for state in observed_states
    }
    latest_state = int(states[-1])
    ordered = sorted(state_means, key=state_means.get)
    if len(ordered) == 3:
        regime_name = {
            ordered[0]: "偏空",
            ordered[1]: "盤整",
            ordered[2]: "偏多",
        }[latest_state]
    else:
        latest_mean = state_means[latest_state]
        regime_name = "偏多" if latest_mean > 0.002 else "偏空" if latest_mean < -0.002 else "盤整"

    return {
        "data": "synthetic_self_test_only",
        "rows": rows,
        "test_rows": rows - split,
        "classifier_accuracy": round(float(accuracy_score(labels[split:], predicted)), 4),
        "latest_hmm_regime": regime_name,
    }
