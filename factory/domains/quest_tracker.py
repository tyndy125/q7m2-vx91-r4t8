"""Independent quest objective tracker; no game-specific quest names."""
from dataclasses import dataclass,field

@dataclass(frozen=True)
class Objective:
 key:str
 target:int
 def __post_init__(self):
  if not isinstance(self.key,str) or not self.key or len(self.key)>128:raise ValueError("invalid objective")
  if type(self.target) is not int or self.target<1:raise ValueError("invalid target")

@dataclass
class Quest:
 objectives:tuple[Objective,...]
 counts:dict[str,int]=field(default_factory=dict)
 claimed:bool=False
 def __post_init__(self):
  keys=[x.key for x in self.objectives]
  if not keys or len(set(keys))!=len(keys):raise ValueError("invalid objective set")
  if type(self.claimed) is not bool:raise ValueError("invalid claim state")
  if not set(self.counts).issubset(keys):raise ValueError("unknown objective")
  for k,v in self.counts.items():
   if type(v) is not int or not 0<=v<=next(x.target for x in self.objectives if x.key==k):raise ValueError("invalid progress")
  if self.claimed and not self.complete:raise ValueError("claimed incomplete quest")
 @property
 def complete(self):return all(self.counts.get(o.key,0)>=o.target for o in self.objectives)
 def advance(self,key,amount=1):
  if self.claimed:raise ValueError("quest already claimed")
  if type(amount) is not int or amount<1:raise ValueError("invalid amount")
  target=next((o.target for o in self.objectives if o.key==key),None)
  if target is None:raise ValueError("unknown objective")
  previous=self.counts.get(key,0)
  self.counts[key]=min(target,previous+amount)
  return self.counts[key]-previous
 def claim(self):
  if not self.complete or self.claimed:return False
  self.claimed=True;return True
 def snapshot(self):
  return {"objectives":[{"key":o.key,"target":o.target} for o in self.objectives],"counts":dict(sorted(self.counts.items())),"claimed":self.claimed}
 @classmethod
 def restore(cls,data):
  if not isinstance(data,dict) or set(data)!={"objectives","counts","claimed"} or not isinstance(data["objectives"],list) or not isinstance(data["counts"],dict):raise ValueError("invalid snapshot")
  return cls(tuple(Objective(**x) for x in data["objectives"]),data["counts"],data["claimed"])
