"""Deterministic loot table engine; caller supplies seeded random.Random instance."""
from dataclasses import dataclass
from random import Random

@dataclass(frozen=True)
class Drop:
    item:str
    weight:int
    minimum:int=1
    maximum:int=1
    unique:bool=False
    def __post_init__(self):
        if not isinstance(self.item,str) or not self.item:raise ValueError("invalid item")
        if any(type(v) is not int for v in (self.weight,self.minimum,self.maximum)) or self.weight<1 or self.minimum<0 or self.maximum<self.minimum:raise ValueError("invalid weight or quantity")
        if type(self.unique) is not bool:raise ValueError("invalid unique flag")

class LootTable:
    def __init__(self,drops):
        self.drops=tuple(drops)
        if not self.drops or not all(isinstance(x,Drop) for x in self.drops):raise ValueError("nonempty drop list required")
        if len({x.item for x in self.drops})!=len(self.drops):raise ValueError("duplicate item")
    def roll(self,rng,draws=1,excluded=()):
        if not isinstance(rng,Random) or type(draws) is not int or not 0<=draws<=1000:raise ValueError("invalid roll arguments")
        if not isinstance(excluded,(tuple,list,set,frozenset)):raise ValueError("invalid exclusions")
        blocked=set(excluded)
        if not all(isinstance(x,str) for x in blocked):raise ValueError("invalid exclusions")
        result={}
        for _ in range(draws):
            eligible=[x for x in self.drops if x.item not in blocked]
            if not eligible:break
            total=sum(x.weight for x in eligible)
            ticket=rng.randrange(total)
            chosen=eligible[-1]
            for x in eligible:
                ticket-=x.weight
                if ticket<0:
                    chosen=x
                    break
            qty=rng.randint(chosen.minimum,chosen.maximum)
            result[chosen.item]=result.get(chosen.item,0)+qty
            if chosen.unique:blocked.add(chosen.item)
        return result
    def snapshot(self):
        return [{"item":x.item,"weight":x.weight,"minimum":x.minimum,"maximum":x.maximum,"unique":x.unique} for x in self.drops]
    @classmethod
    def restore_snapshot(cls,records):
        if not isinstance(records,list):raise ValueError("invalid snapshot")
        if any(not isinstance(r,dict) or set(r)!={"item","weight","minimum","maximum","unique"} for r in records):raise ValueError("invalid drop record")
        return cls([Drop(**r) for r in records])
