from typing import List, Dict
import numpy as np
from sklearn.ensemble import IsolationForest

class UnsupervisedDetector:
    def __init__(self, contamination=0.02):
        self.model = IsolationForest(
            n_estimators=200, contamination=contamination, random_state=42
        )
        self._is_fitted = False

    def _featurize(self, flows: List[Dict]) -> np.ndarray:
        X = []
        for f in flows:
            l_port = f.get("l_port", 0)
            r_port = f.get("r_port", 0)
            status = f.get("status", "UNKNOWN")
            is_private_dst = f.get("is_private_dst", 0)
            proc = f.get("proc", "unknown")

            X.append([
                _port_bucket(l_port),
                _port_bucket(r_port),
                1 if status == "ESTABLISHED" else 0,
                1 if is_private_dst else 0,
                hash(proc) % 1000 / 1000.0,
            ])
        return np.array(X, dtype=np.float32) if X else np.zeros((0, 5), dtype=np.float32)

    def fit_warmup(self, flows: List[Dict]):
        X = self._featurize(flows)
        if len(X) >= 20:
            self.model.fit(X)
            self._is_fitted = True

    def score_anomaly(self, flows: List[Dict]) -> List[float]:
        if not self._is_fitted or not flows:
            return [0.0] * len(flows)
        X = self._featurize(flows)
        s = self.model.score_samples(X)
        # Fixed for NumPy 2.0
        s_norm = (s - np.min(s)) / (np.ptp(s) + 1e-6)
        return [1.0 - v for v in s_norm]

def _port_bucket(p: int) -> int:
    if p < 1024:
        return 0
    if p < 49152:
        return 1
    return 2

