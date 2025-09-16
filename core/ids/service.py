import time
import threading
from .feature_extractor import FeatureExtractor

# Placeholder detectors and enforcement classes (replace with your actual implementations)
class UnsupervisedDetector:
    def __init__(self, contamination=0.01):
        self._is_fitted = False

    def fit_warmup(self, flows):
        self._is_fitted = True

    def score_anomaly(self, flows):
        return [0.0 for _ in flows]

class SupervisedDetector:
    def predict_proba(self, flows):
        return [0.0 for _ in flows]

class Reputation:
    def __init__(self, allowlisted_domains=None):
        self.allowlisted_domains = allowlisted_domains or []

    def score(self, ip, proc):
        return 0.0

class RiskEngine:
    def __init__(self, cfg=None):
        pass

    def fuse(self, flows, a_scores, k_scores, rep_scores):
        return [0 for _ in flows]

class Enforcement:
    def __init__(self, cfg=None):
        pass

    def apply(self, decision, flow):
        # Here you can log or act on flow
        pass

# Minimal config
class IDSConfig:
    poll_interval_ms = 1000
    warmup_minutes = 1
    iforest_contamination = 0.01
    allowlisted_domains = []

class IDSService:
    def __init__(self, cfg=None):
        self.cfg = cfg or IDSConfig()
        self.features = FeatureExtractor()
        self.unsup = UnsupervisedDetector(contamination=self.cfg.iforest_contamination)
        self.sup = SupervisedDetector()
        self.rep = Reputation(self.cfg.allowlisted_domains)
        self.risk = RiskEngine(self.cfg)
        self.enf = Enforcement(self.cfg)
        self._running = False
        self._t = None
        self._warmup_until = time.time() + 60 * self.cfg.warmup_minutes

        # Shared buffer for UI
        self.latest_flows = []

    def start(self):
        if self._running: 
            return
        self._running = True
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()
        print("IDSService started")

    def stop(self):
        self._running = False
        if self._t: self._t.join(timeout=2.0)
        print("IDSService stopped")

    def _loop(self):
        while self._running:
            flows = self.features.sample_flows()
            self.latest_flows = flows  # update shared buffer for UI
            if not flows:
                time.sleep(self.cfg.poll_interval_ms / 1000)
                continue

            if time.time() < self._warmup_until and not self.unsup._is_fitted:
                self.unsup.fit_warmup(flows)
                print("Warmup learning…")
            else:
                a_scores = self.unsup.score_anomaly(flows)
                k_scores = self.sup.predict_proba(flows)
                rep_scores = [self.rep.score(f["r_ip"], f["proc"]) for f in flows]
                decisions = self.risk.fuse(flows, a_scores, k_scores, rep_scores)
                for f, d in zip(flows, decisions):
                    self.enf.apply(d, f)

            time.sleep(self.cfg.poll_interval_ms / 1000)

