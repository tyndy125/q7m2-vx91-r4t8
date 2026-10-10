"""Table-driven level progression, with deterministic reward unlocks."""
from dataclasses import dataclass

@dataclass(frozen=True)
class LevelTable:
 thresholds:tuple[int,...]
 def __post_init__(self):
  if not self.thresholds or self.thresholds[0]!=0 or any(type(x) is not int or x<0 for x in self.thresholds):raise ValueError("invalid thresholds")
  if any(b<=a for a,b in zip(self.thresholds,self.thresholds[1:])):raise ValueError("thresholds must increase")
 def level(self,xp):
  if type(xp) is not int or xp<0:raise ValueError("invalid xp")
  from bisect import bisect_right
  return bisect_right(self.thresholds,xp)
 def next_required(self,xp):
  level=self.level(xp)
  return None if level==len(self.thresholds) else self.thresholds[level]-xp

@dataclass
class Progress:
 table:LevelTable
 xp:int=0
 def __post_init__(self):self.table.level(self.xp)
 @property
 def level(self):return self.table.level(self.xp)
 def grant(self,amount):
  if type(amount) is not int or amount<0:raise ValueError("invalid xp gain")
  before=self.level;self.xp+=amount
  return tuple(range(before+1,self.level+1))
 def snapshot(self):return {"xp":self.xp,"thresholds":list(self.table.thresholds)}
 @classmethod
 def restore(cls,data):
  if not isinstance(data,dict) or set(data)!={"xp","thresholds"} or not isinstance(data["thresholds"],list):raise ValueError("invalid snapshot")
  return cls(LevelTable(tuple(data["thresholds"])),data["xp"])
