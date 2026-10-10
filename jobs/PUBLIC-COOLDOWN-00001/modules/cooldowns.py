"""Deterministic tick-based cooldown engine, independent of any game-specific data."""
from dataclasses import dataclass, field


@dataclass
class Cooldowns:
    deadlines: dict[str, int] = field(default_factory=dict)

    def remaining(self, key: str, now: int) -> int:
        return max(0, self.deadlines.get(key, now) - now)

    def ready(self, key: str, now: int) -> bool:
        return self.remaining(key, now) == 0

    def activate(self, key: str, now: int, duration: int) -> bool:
        if not key or now < 0 or duration < 0:
            raise ValueError("invalid cooldown arguments")
        if not self.ready(key, now):
            return False
        self.deadlines[key] = now + duration
        return True

    def purge(self, now: int) -> int:
        expired = [key for key, deadline in self.deadlines.items() if deadline <= now]
        for key in expired:
            del self.deadlines[key]
        return len(expired)
