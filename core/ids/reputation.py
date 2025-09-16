import time

class Reputation:
    def __init__(self, allowlisted_domains=None):
        self.allow = allowlisted_domains or set()
        self.first_seen = {}

    def score(self, ip: str, proc: str) -> float:
        key = f"{proc}:{ip}"
        now = time.time()
        if key not in self.first_seen:
            self.first_seen[key] = now
            return 0.6
        age = now - self.first_seen[key]
        return max(0.1, 0.6 - 0.0001 * age)

