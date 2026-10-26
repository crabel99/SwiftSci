"""Regenerate independent finite-step logistic expectations with NumPy/SciPy."""
from pathlib import Path
import json
import numpy as np
from scipy.special import expit

x = np.array([[-2., -1.], [0., 1.], [1., 2.], [3., 0.]])
y = np.array([0., 0., 1., 1.])
output = {"features": x.tolist(), "targets": y.tolist(), "learning_rate": .25, "cases": [], "numpy": np.__version__}
for epochs in (0, 1, 32):
    weights = np.zeros(x.shape[1])
    bias = 0.
    for _ in range(epochs):
        error = expit(x @ weights + bias) - y
        weights -= .25 * (x.T @ error / len(y))
        bias -= .25 * error.mean()
    output["cases"].append({"epochs": epochs, "weights": weights.tolist(), "bias": float(bias), "positive_probabilities": expit(x @ weights + bias).tolist()})
Path(__file__).with_name("logistic-independent-reference.json").write_text(json.dumps(output, indent=2) + "\n")
