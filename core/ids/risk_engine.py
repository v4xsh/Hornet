from typing import List, Dict
from ..config_ids import IDSConfig

class RiskEngine:
    def __init__(self, cfg: IDSConfig):
        self.cfg = cfg

    def fuse(
        self,
        flows: List[Dict],
        anomaly: List[float],
        known: List[float],
        rep_scores: List[float]
    ):
        out = []
        for f, a, k, r in zip(flows, anomaly, known, rep_scores):

            # --- Weighted fusion ---
            # anomaly dominates if very high (>0.8)
            anomaly_weight = 0.55 + (0.15 if a > 0.8 else 0.0)
            risk = anomaly_weight * a + 0.30 * r + 0.15 * k

            # suspicious ports = extra risk
            reasons = []
            if f["r_port"] in self.cfg.suspicious_ports:
                risk += 0.1
                reasons.append(f"suspicious port {f['r_port']}")

            # normalize (0–1)
            risk = min(max(risk, 0.0), 1.0)

            # --- Determine level ---
            if risk >= self.cfg.risk_threshold_block:
                level = "block"
                reasons.append("risk exceeds block threshold")
            elif risk >= self.cfg.risk_threshold_soft:
                level = "soft"
                reasons.append("risk exceeds soft threshold")
            else:
                level = "observe"

            out.append({
                "risk": round(risk, 2),
                "level": level,
                "reasons": reasons or ["baseline risk"]
            })

        return out

