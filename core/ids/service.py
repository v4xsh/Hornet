import time, threading
from ..config_ids import IDSConfig
from ..logging_ids import get_ids_logger
from .feature_extractor import FeatureExtractor
from .models.unsupervised import UnsupervisedDetector
from .models.supervised import SupervisedDetector
from .reputation import Reputation
from .risk_engine import RiskEngine
from .enforcement import Enforcement

log = get_ids_logger("hornet.ids.service")

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

    def start(self):
        if self._running: return
        self._running = True
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()
        log.info("IDSService started")

    def stop(self):
        self._running = False
        if self._t: self._t.join(timeout=2.0)
        log.info("IDSService stopped")

    def _loop(self):
        while self._running:
            flows = self.features.sample_flows()
            if not flows:
                time.sleep(self.cfg.poll_interval_ms/1000); continue

            if time.time() < self._warmup_until and not self.unsup._is_fitted:
                self.unsup.fit_warmup(flows)
                log.info("Warmup learning…")
            else:
                a_scores = self.unsup.score_anomaly(flows)
                k_scores = self.sup.predict_proba(flows)
                rep_scores = [self.rep.score(f["r_ip"], f["proc"]) for f in flows]
                decisions = self.risk.fuse(flows, a_scores, k_scores, rep_scores)
                for f, d in zip(flows, decisions):
                    self.enf.apply(d, f)

            time.sleep(self.cfg.poll_interval_ms/1000)

if __name__ == "__main__":
    ids = IDSService()
    ids.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        ids.stop()
