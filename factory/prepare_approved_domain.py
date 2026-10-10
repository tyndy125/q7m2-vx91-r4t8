#!/usr/bin/env python3
"""Stage independently original, explicitly allowlisted public domains for one batch."""
import hashlib
import json
from pathlib import Path
import shutil

DOMAINS={
 "cooldown_domain":("PUBLIC-COOLDOWN-DOMAIN-00001","cooldowns","cooldown_domain"),
 "resource_pools":("PUBLIC-RESOURCE-POOLS-00001","resource_pools","resource_pools"),
 "status_effects":("PUBLIC-STATUS-EFFECTS-00001","status_effects","status_effects"),
 "loot_tables":("PUBLIC-LOOT-TABLES-00001","loot_tables","loot_tables"),
 "inventory":("PUBLIC-INVENTORY-00001","inventory","inventory"),
 "progression":("PUBLIC-PROGRESSION-00001","progression","progression"),
 "quest_tracker":("PUBLIC-QUEST-TRACKER-00001","quest_tracker","quest_tracker"),
}

def prepare(root=Path("."),out=Path("build/jobs")):
    root=Path(root).resolve();out=Path(out).resolve()
    if out.is_relative_to(root/"jobs"):raise ValueError("refusing to overwrite source jobs")
    if out.exists():raise ValueError("staging output must be fresh")
    shutil.copytree(root/"jobs",out)
    for job,mod,test in DOMAINS.values():
        folder=out/job
        if folder.exists():raise ValueError("duplicate job")
        folder.mkdir()
        files=[]
        for dest,src in [(f"modules/{mod}.py",f"factory/domains/{mod}.py"),
                         (f"tests/test_{test}.py",f"tests/test_{test}.py")]:
            source=root/src
            if source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(root):
                raise ValueError("invalid allowlisted source")
            data=source.read_bytes()
            if dest.startswith("tests/"):
                source_text=data.decode("utf-8")
                if mod=="cooldowns":
                    marker="class CooldownDomainTests"
                    if source_text.count(marker)!=1:raise ValueError("cooldown test layout changed")
                    source_text="import unittest\nimport modules.cooldowns as m\n\n"+marker+source_text.split(marker,1)[1]
                else:
                    old=f"from factory.domains.{mod} import "
                    if source_text.count(old)!=1:raise ValueError("test import layout changed")
                    source_text=source_text.replace(old,f"from modules.{mod} import ")
                data=source_text.encode("utf-8")
            if len(data)>256*1024:raise ValueError("oversized source")
            target=folder/dest;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            files.append({"path":dest,"sha256":hashlib.sha256(data).hexdigest()})
        contract={"schema":1,"job_id":job,"public_release_approved":True,
                  "validation_gate":"UNIT","integration_policy":"WINDOWS_VALIDATE_ONLY",
                  "files":files}
        (folder/"contract.json").write_text(json.dumps(contract,indent=2)+"\n")
    return out

if __name__=="__main__":
    print("STAGED_PUBLIC_DOMAINS",prepare())
