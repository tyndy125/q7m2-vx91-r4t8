"""Tick-based status effect collection with explicit stacking policies."""
from dataclasses import dataclass,field

@dataclass(frozen=True)
class Effect:
    name:str
    expires:int
    magnitude:int=0
    stacks:int=1
    def __post_init__(self):
        if not isinstance(self.name,str) or not self.name or len(self.name)>128:raise ValueError("invalid name")
        if type(self.expires) is not int or self.expires<0:raise ValueError("invalid expiry")
        if type(self.magnitude) is not int:raise ValueError("invalid magnitude")
        if type(self.stacks) is not int or self.stacks<1 or self.stacks>100:raise ValueError("invalid stacks")

@dataclass
class Effects:
    active:dict[str,Effect]=field(default_factory=dict)
    def apply(self,name,now,duration,magnitude=0,policy="refresh",max_stacks=1):
        if any(type(v) is not int for v in (now,duration,magnitude,max_stacks)) or now<0 or duration<0 or not 1<=max_stacks<=100:raise ValueError("invalid timing or stacks")
        if policy not in ("refresh","replace","stack","ignore"):raise ValueError("invalid policy")
        old=self.active.get(name)
        if old and old.expires<=now:old=None
        if old and policy=="ignore":return old
        if old and policy=="stack":
            effect=Effect(name,max(old.expires,now+duration),magnitude,min(max_stacks,old.stacks+1))
        elif old and policy=="refresh":
            effect=Effect(name,max(old.expires,now+duration),old.magnitude,old.stacks)
        else:effect=Effect(name,now+duration,magnitude)
        self.active[name]=effect
        return effect
    def get(self,name,now):
        if type(now) is not int or now<0:raise ValueError("invalid time")
        e=self.active.get(name)
        return e if e and e.expires>now else None
    def total_modifier(self,now):
        if type(now) is not int or now<0:raise ValueError("invalid time")
        return sum(e.magnitude*e.stacks for e in self.active.values() if e.expires>now)
    def dispel(self,name):return self.active.pop(name,None) is not None
    def purge(self,now):
        if type(now) is not int or now<0:raise ValueError("invalid time")
        expired=[k for k,v in self.active.items() if v.expires<=now]
        for k in expired:del self.active[k]
        return len(expired)
    def snapshot(self):
        return [{"name":e.name,"expires":e.expires,"magnitude":e.magnitude,"stacks":e.stacks} for e in sorted(self.active.values(),key=lambda x:x.name)]
    @classmethod
    def restore_snapshot(cls,records):
        if not isinstance(records,list):raise ValueError("invalid snapshot")
        result=cls()
        for item in records:
            if not isinstance(item,dict) or set(item)!={"name","expires","magnitude","stacks"}:raise ValueError("invalid effect record")
            effect=Effect(**item)
            if effect.name in result.active:raise ValueError("duplicate effect")
            result.active[effect.name]=effect
        return result
