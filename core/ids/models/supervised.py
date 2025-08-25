class SupervisedDetector:
    def __init__(self):
        self.ready = False

    def predict_proba(self, flows):
        return [0.05] * len(flows)  # placeholder
