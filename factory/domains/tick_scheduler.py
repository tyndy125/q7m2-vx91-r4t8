"""Deterministic tick scheduler for independent, serializable game events."""
from dataclasses import dataclass,field
import heapq

@dataclass(order=True,frozen=True)
class Event:
    tick:int
    sequence:int
    kind:str
    payload:str=""
    def __post_init__(self):
        if type(self.tick) is not int or self.tick<0 or type(self.sequence) is not int or self.sequence<0:raise ValueError("invalid tick or sequence")
        if not isinstance(self.kind,str) or not self.kind or not isinstance(self.payload,str):raise ValueError("invalid event")

@dataclass
class TickScheduler:
    pending:list[Event]=field(default_factory=list)
    sequence:int=0
    def schedule(self,tick,kind,payload=""):
        if type(tick) is not int or tick<0:raise ValueError("invalid tick")
        event=Event(tick,self.sequence,kind,payload)
        self.sequence+=1
        heapq.heappush(self.pending,event)
        return event.sequence
    def due(self,now,limit=1000):
        if type(now) is not int or now<0 or type(limit) is not int or limit<0:raise ValueError("invalid time or limit")
        result=[]
        while self.pending and len(result)<limit and self.pending[0].tick<=now:
            result.append(heapq.heappop(self.pending))
        return result
    def cancel(self,sequence):
        if type(sequence) is not int or sequence<0:raise ValueError("invalid sequence")
        old=len(self.pending)
        self.pending=[e for e in self.pending if e.sequence!=sequence]
        heapq.heapify(self.pending)
        return len(self.pending)!=old
    def snapshot(self):
        return {"sequence":self.sequence,"pending":[{"tick":e.tick,"sequence":e.sequence,"kind":e.kind,"payload":e.payload} for e in sorted(self.pending)]}
    @classmethod
    def restore(cls,data):
        if not isinstance(data,dict) or set(data)!={"sequence","pending"} or type(data["sequence"]) is not int or data["sequence"]<0 or not isinstance(data["pending"],list):raise ValueError("invalid snapshot")
        events=[Event(**entry) for entry in data["pending"]]
        ids=[e.sequence for e in events]
        if len(ids)!=len(set(ids)) or any(x>=data["sequence"] for x in ids):raise ValueError("invalid sequence")
        heapq.heapify(events)
        return cls(events,data["sequence"])
