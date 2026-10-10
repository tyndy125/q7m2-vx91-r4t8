"""Deterministic resource pools for health, mana, stamina or other resources."""
from dataclasses import dataclass, field

@dataclass
class Pool:
    maximum: int
    current: int
    regen: int = 0
    def __post_init__(self):
        for v in (self.maximum,self.current,self.regen):
            if type(v) is not int or v<0: raise ValueError("invalid resource value")
        if self.current>self.maximum: raise ValueError("current exceeds maximum")
    def spend(self,amount):
        if type(amount) is not int or amount<0: raise ValueError("invalid amount")
        if amount>self.current: return False
        self.current-=amount
        return True
    def restore(self,amount):
        if type(amount) is not int or amount<0: raise ValueError("invalid amount")
        gained=min(amount,self.maximum-self.current)
        self.current+=gained
        return gained
    def tick(self,steps=1):
        if type(steps) is not int or steps<0: raise ValueError("invalid steps")
        return self.restore(self.regen*steps)
    def damage(self,amount): return self.spend(amount)
    def set_maximum(self,maximum,keep_ratio=False):
        if type(maximum) is not int or maximum<0: raise ValueError("invalid maximum")
        old=self.maximum
        self.maximum=maximum
        self.current=min(maximum, (self.current*maximum//old if old and keep_ratio else self.current))
    def snapshot(self):
        return {"maximum":self.maximum,"current":self.current,"regen":self.regen}
    @classmethod
    def restore_snapshot(cls,data):
        if not isinstance(data,dict) or set(data)!={"maximum","current","regen"}:raise ValueError("invalid snapshot")
        return cls(**data)

@dataclass
class Resources:
    pools: dict[str,Pool]=field(default_factory=dict)
    def add(self,key,maximum,current=None,regen=0):
        if not isinstance(key,str) or not key or key in self.pools:raise ValueError("invalid or duplicate key")
        self.pools[key]=Pool(maximum,maximum if current is None else current,regen)
    def tick(self,steps=1):
        if type(steps) is not int or steps<0:raise ValueError("invalid steps")
        return {k:p.tick(steps) for k,p in self.pools.items()}
    def snapshot(self):return {k:v.snapshot() for k,v in sorted(self.pools.items())}
    @classmethod
    def restore_snapshot(cls,data):
        if not isinstance(data,dict):raise ValueError("invalid snapshot")
        result=cls()
        for key,values in data.items():
            pool=Pool.restore_snapshot(values)
            result.add(key,pool.maximum,pool.current,pool.regen)
        return result
