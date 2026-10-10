#!/usr/bin/env python3
"""Materialize explicitly allowlisted public domain as an isolated batch job."""
import hashlib
import json
from pathlib import Path
import shutil

JOB="PUBLIC-COOLDOWN-DOMAIN-00001"
SOURCES={"modules/cooldowns.py":"factory/domains/cooldowns.py",
         "tests/test_cooldown_domain.py":"tests/test_cooldown_domain.py"}

def prepare(root=Path("."),out=Path("build/jobs")):
    root=Path(root).resolve();out=Path(out).resolve()
    if out.is_relative_to(root/"jobs"):
        raise ValueError("refusing to overwrite submitted jobs")
    if out.exists():
        raise ValueError("staging output must be fresh")
    shutil.copytree(root/"jobs",out)
    folder=out/JOB
    folder.mkdir()
    files=[]
    for dest,src in SOURCES.items():
        source=root/src
        if source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(root):
            raise ValueError("invalid approved source")
        target=folder/dest
        target.parent.mkdir(parents=True,exist_ok=True)
        data=source.read_bytes()
        if len(data)>256*1024:raise ValueError("oversized source")
        target.write_bytes(data)
        files.append({"path":dest,"sha256":hashlib.sha256(data).hexdigest()})
    contract={"schema":1,"job_id":JOB,"public_release_approved":True,
              "validation_gate":"UNIT","integration_policy":"WINDOWS_VALIDATE_ONLY",
              "files":files}
    (folder/"contract.json").write_text(json.dumps(contract,indent=2)+"\n")
    return folder

if __name__=="__main__":
    print("STAGED_PUBLIC_DOMAIN",prepare())
