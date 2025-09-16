from dataclasses import dataclass, field

@dataclass
class IDSConfig:
    poll_interval_ms: int = 800            # how often we sample connections
    warmup_minutes: int = 1                # learn "normal" for X minutes
    iforest_contamination: float = 0.02    # anomaly prior
    risk_threshold_observe: float = 0.45
    risk_threshold_soft: float = 0.65
    risk_threshold_block: float = 0.82
    auto_block_minutes: int = 30
    platform: str = "auto"                 # "auto" | "win" | "linux"
    dry_run: bool = True                   # True = log only, don’t enforce
    allowlisted_domains: set = field(default_factory=lambda: {"microsoft.com","google.com","openai.com"})
    suspicious_ports: set = field(default_factory=lambda: {4444,1337,23,31337})

