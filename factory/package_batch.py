#!/usr/bin/env python3
"""Public isolated factory: validate approved files, package deterministic artifacts.
No network, git, private repository access, execution of submitted code or main writes.
"""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

JOB = re.compile(r"^[A-Z0-9][A-Z0-9_-]{4,100}$")
PATH = re.compile(r"^(?:modules|tests)/[a-z][a-z0-9_]*\.py$")
SHA = re.compile(r"^[0-9a-f]{64}$")
MAX_FILE = 256 * 1024
MAX_BATCH = 16
class Rejected(ValueError): pass

def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()

def load_contract(path):
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict): raise Rejected("contract object required")
    job=obj.get("job_id")
    if not isinstance(job,str) or not JOB.fullmatch(job): raise Rejected("invalid job_id")
    if obj.get("schema")!=1 or obj.get("validation_gate")!="UNIT": raise Rejected("unsupported contract")
    if obj.get("public_release_approved") is not True: raise Rejected("public release approval required")
    if obj.get("integration_policy")!="WINDOWS_VALIDATE_ONLY": raise Rejected("invalid integration policy")
    files=obj.get("files")
    if not isinstance(files,list) or not 2<=len(files)<=8: raise Rejected("invalid files")
    seen=set()
    for entry in files:
        if not isinstance(entry,dict) or set(entry)!={"path","sha256"}: raise Rejected("invalid file entry")
        name,digest=entry["path"],entry["sha256"]
        if not isinstance(name,str) or not PATH.fullmatch(name) or name in seen:
            raise Rejected("duplicate or disallowed path")
        if not isinstance(digest,str) or not SHA.fullmatch(digest): raise Rejected("invalid sha256")
        seen.add(name)
    if not any(x.startswith("modules/") for x in seen) or not any(x.startswith("tests/test_") for x in seen):
        raise Rejected("module and test required")
    return obj

def inside(root,relative):
    path=root.joinpath(*PurePosixPath(relative).parts)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise Rejected("missing, symlinked or escaping source file")
    return path

def build(source,out,limit=MAX_BATCH):
    if not source.is_dir() or source.is_symlink() or out.resolve().is_relative_to(source.resolve()):
        raise Rejected("invalid source/output roots")
    contracts=sorted(source.glob("*/contract.json"))
    if not 1<=limit<=MAX_BATCH or len(contracts)>limit: raise Rejected("invalid batch capacity")
    if not contracts: raise Rejected("no contracts")
    seen=set(); records=[]
    out.mkdir(parents=True,exist_ok=True)
    for contract_path in contracts:
        if contract_path.is_symlink() or contract_path.parent.is_symlink():
            raise Rejected("symlink contract")
        contract=load_contract(contract_path)
        job=contract["job_id"]
        if contract_path.parent.name!=job or job in seen: raise Rejected("job mismatch or duplicate")
        seen.add(job)
        contents={}
        for entry in contract["files"]:
            name=entry["path"]
            path=inside(contract_path.parent,name)
            if path.stat().st_size>MAX_FILE: raise Rejected("file too large")
            data=path.read_bytes()
            if hashlib.sha256(data).hexdigest()!=entry["sha256"]: raise Rejected("checksum mismatch")
            contents[name]=data
        payload={"schema":1,"job_id":job,"validation_gate":"UNIT",
                 "integration_policy":"WINDOWS_VALIDATE_ONLY",
                 "files":sorted(contract["files"],key=lambda x:x["path"])}
        target=out/(job+".zip")
        with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
            for name,data in sorted({**contents,"contract.json":canonical(payload)}.items()):
                info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o100644<<16
                archive.writestr(info,data)
        records.append({"job_id":job,"artifact":target.name,
                        "sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
    index={"schema":1,"mode":"PUBLIC_ISOLATED_BATCH","count":len(records),"jobs":records}
    (out/"index.json").write_bytes(canonical(index)+b"\n")
    return index

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("jobs"))
    p.add_argument("--output",type=Path,default=Path("dist"))
    p.add_argument("--limit",type=int,default=MAX_BATCH)
    a=p.parse_args()
    try:
        print(json.dumps(build(a.source,a.output,a.limit),indent=2))
    except (Rejected,ValueError,OSError) as e:
        print("REJECTED: "+str(e),file=sys.stderr)
        return 1
    return 0
if __name__=="__main__":sys.exit(main())
