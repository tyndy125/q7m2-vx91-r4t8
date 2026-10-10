"""Self-contained deterministic cooldown domain. Tick units are caller-defined.

No wall clock, network, global state, persistence I/O, or game-specific names.
"""
from dataclasses import dataclass, field
import json


def _integer(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


@dataclass
class CooldownState:
    ready_at: dict[str, int] = field(default_factory=dict)
    groups: dict[str, int] = field(default_factory=dict)
    charges: dict[str, list[int]] = field(default_factory=dict)
    capacities: dict[str, int] = field(default_factory=dict)

    def remaining(self, key: str, now: int, group: str | None = None) -> int:
        _integer(now, "now")
        self._key(key)
        if group is not None:
            self._key(group)
        return max(0, self.ready_at.get(key, 0) - now,
                   self.groups.get(group, 0) - now if group else 0)

    def ready(self, key: str, now: int, group: str | None = None) -> bool:
        return self.remaining(key, now, group) == 0

    def activate(self, key: str, now: int, duration: int, *,
                 group: str | None = None, group_duration: int = 0) -> bool:
        self._key(key)
        _integer(now, "now")
        _integer(duration, "duration")
        _integer(group_duration, "group_duration")
        if group is not None:
            self._key(group)
        elif group_duration:
            raise ValueError("group_duration requires group")
        if not self.ready(key, now, group):
            return False
        self.ready_at[key] = now + duration
        if group is not None:
            self.groups[group] = now + group_duration
        return True

    def configure_charges(self, key: str, capacity: int) -> None:
        self._key(key)
        if type(capacity) is not int or capacity < 1 or capacity > 100:
            raise ValueError("capacity must be 1..100")
        if key in self.charges and len(self.charges[key]) > capacity:
            raise ValueError("cannot reduce capacity below pending charges")
        self.capacities[key] = capacity
        self.charges.setdefault(key, [])

    def available_charges(self, key: str, now: int) -> int:
        self._key(key)
        _integer(now, "now")
        if key not in self.capacities:
            raise ValueError("charges not configured")
        return self.capacities[key] - sum(t > now for t in self.charges[key])

    def spend_charge(self, key: str, now: int, recharge: int, *,
                     group: str | None = None, group_duration: int = 0) -> bool:
        self._key(key)
        _integer(now, "now")
        _integer(recharge, "recharge")
        _integer(group_duration, "group_duration")
        if group is not None:
            self._key(group)
        elif group_duration:
            raise ValueError("group_duration requires group")
        if self.available_charges(key, now) == 0:
            return False
        if group and self.groups.get(group, 0) > now:
            return False
        self.charges[key] = [t for t in self.charges[key] if t > now]
        if recharge:
            self.charges[key].append(now + recharge)
        if group:
            self.groups[group] = now + group_duration
        return True

    def reduce(self, key: str, ticks: int, now: int) -> None:
        self._key(key)
        _integer(ticks, "ticks")
        _integer(now, "now")
        if key in self.ready_at:
            self.ready_at[key] = max(now, self.ready_at[key] - ticks)
        if key in self.charges:
            self.charges[key] = [max(now, t - ticks) for t in self.charges[key]]

    def purge(self, now: int) -> int:
        _integer(now, "now")
        removed = 0
        for mapping in (self.ready_at, self.groups):
            expired = [k for k, t in mapping.items() if t <= now]
            for key in expired:
                del mapping[key]
            removed += len(expired)
        for key, deadlines in self.charges.items():
            future = [t for t in deadlines if t > now]
            removed += len(deadlines) - len(future)
            self.charges[key] = future
        return removed

    def snapshot(self) -> str:
        return json.dumps({"schema": 1, "ready_at": self.ready_at,
                           "groups": self.groups, "charges": self.charges,
                           "capacities": self.capacities}, sort_keys=True, separators=(",", ":"))

    @classmethod
    def restore(cls, snapshot: str) -> "CooldownState":
        data = json.loads(snapshot)
        if not isinstance(data, dict) or set(data) != {"schema", "ready_at", "groups", "charges", "capacities"} or data["schema"] != 1:
            raise ValueError("invalid snapshot")
        for name in ("ready_at", "groups", "charges", "capacities"):
            if not isinstance(data[name], dict):
                raise ValueError("invalid snapshot mapping")
        for name in ("ready_at", "groups"):
            for k, v in data[name].items():
                cls._key(k)
                _integer(v, name)
        for k, cap in data["capacities"].items():
            cls._key(k)
            if type(cap) is not int or not 1 <= cap <= 100:
                raise ValueError("invalid capacity")
        if set(data["charges"]) != set(data["capacities"]):
            raise ValueError("inconsistent charge keys")
        for k, values in data["charges"].items():
            if not isinstance(values, list) or len(values) > data["capacities"][k]:
                raise ValueError("invalid charge queue")
            for t in values:
                _integer(t, "recharge deadline")
        return cls(data["ready_at"], data["groups"], data["charges"], data["capacities"])

    @staticmethod
    def _key(key: str) -> None:
        if not isinstance(key, str) or not key or len(key) > 128:
            raise ValueError("invalid key")
