"""Deterministic stack-based inventory with atomic operations."""
from dataclasses import dataclass,field

def positive(n):
 if type(n) is not int or n<1:raise ValueError("positive integer required")

@dataclass
class Inventory:
 slots:int
 stacks:dict[str,int]=field(default_factory=dict)
 def __post_init__(self):
  positive(self.slots)
  if len(self.stacks)>self.slots:raise ValueError("capacity exceeded")
  for key,amount in self.stacks.items():
   self._key(key);positive(amount)
 @staticmethod
 def _key(key):
  if not isinstance(key,str) or not key or len(key)>128:raise ValueError("invalid item")
 def count(self,key):self._key(key);return self.stacks.get(key,0)
 def add(self,key,amount):
  self._key(key);positive(amount)
  if key not in self.stacks and len(self.stacks)>=self.slots:return False
  self.stacks[key]=self.count(key)+amount
  return True
 def remove(self,key,amount):
  self._key(key);positive(amount)
  if self.count(key)<amount:return False
  left=self.stacks[key]-amount
  if left:self.stacks[key]=left
  else:del self.stacks[key]
  return True
 def transfer(self,other,key,amount):
  if not isinstance(other,Inventory) or other is self:raise ValueError("invalid destination")
  self._key(key);positive(amount)
  if self.count(key)<amount:return False
  if not other.add(key,amount):return False
  assert self.remove(key,amount)
  return True
 def snapshot(self):return {"slots":self.slots,"stacks":dict(sorted(self.stacks.items()))}
 @classmethod
 def restore(cls,data):
  if not isinstance(data,dict) or set(data)!={"slots","stacks"} or not isinstance(data["stacks"],dict):raise ValueError("invalid snapshot")
  return cls(data["slots"],data["stacks"].copy())
