#!/usr/bin/env python3
"""Execute only approved batch tests in a disposable GitHub runner.
The workflow must invoke this only for trusted main-branch code, not PR code.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

JOB=re.compile(r"^[A-Z0-9][A-Z0-9_-]{4,100}$")
PATH=re.compile(r"^(modules|tests)/[a-z][a-z0-9_]*\.py$")
MAX_FILE=256*1024

def run(source,output):
    source=Path(source);output=Path(output)
    if source.is_symlink() or not source.is_dir(): raise ValueError("invalid jobs root")
    contracts=sorted(source.glob("*/contract.json"))
    if not 1<=len(contracts)<=16: raise ValueError("invalid batch size")
    output.mkdir(parents=True,exist_ok=True)
    results=[]
    for path in contracts:
        folder=path.parent
        if folder.is_symlink() or path.is_symlink(): raise ValueError("symlink job")
        obj=json.loads(path.read_text(encoding="utf-8"))
        job=obj.get("job_id")
        if not isinstance(job,str) or not JOB.fullmatch(job) or job!=folder.name or obj.get("public_release_approved") is not True or obj.get("validation_gate")!="UNIT" or obj.get("integration_policy")!="WINDOWS_VALIDATE_ONLY":
            raise ValueError("invalid public job contract")
        files=obj.get("files")
        if not isinstance(files,list) or not 2<=len(files)<=8: raise ValueError("invalid file manifest")
        seen=set()
        for item in files:
            if not isinstance(item,dict) or set(item)!={"path","sha256"}: raise ValueError("invalid file entry")
            name,digest=item["path"],item["sha256"]
            if not isinstance(name,str) or not PATH.fullmatch(name) or name in seen or not isinstance(digest,str) or not re.fullmatch("[a-f0-9]{64}",digest):
                raise ValueError("invalid path or hash")
            seen.add(name)
            f=folder/name
            if f.is_symlink() or not f.is_file() or not f.resolve().is_relative_to(folder.resolve()) or f.stat().st_size>MAX_FILE or hashlib.sha256(f.read_bytes()).hexdigest()!=digest:
                raise ValueError("file not approved")
        if not any(n.startswith("modules/") for n in seen) or not any(n.startswith("tests/test_") for n in seen):
            raise ValueError("missing module or test")
        start=time.monotonic()
        env={"PATH":os.environ.get("PATH",""),"PYTHONPATH":str(folder.resolve()),"PYTHONDONTWRITEBYTECODE":"1"}
        # Run simple zero-argument test_* functions and unittest suites; reject zero tests.
        runner = """import pathlib,types,unittest,sys
count=0
for f in sorted(pathlib.Path('tests').glob('test_*.py')):
 mod=types.ModuleType('isolated_'+f.stem)
 mod.__file__=str(f)
 sys.modules[mod.__name__]=mod
 exec(compile(f.read_bytes(),str(f),'exec'),mod.__dict__)
 for name,fn in sorted(vars(mod).items()):
  if name.startswith('test_') and callable(fn):
   fn();count+=1
 suite=unittest.defaultTestLoader.loadTestsFromModule(mod)
 count+=suite.countTestCases()
 if suite.countTestCases():
  result=unittest.TextTestRunner(verbosity=2).run(suite)
  if not result.wasSuccessful():sys.exit(1)
print('EXECUTED_TESTS='+str(count))
if count==0: raise RuntimeError('No executable tests found')
"""
        command=[sys.executable,"-B","-c",runner]
        try:
            p=subprocess.run(command,cwd=folder,capture_output=True,text=True,timeout=30,env=env)
            status="PASS" if p.returncode==0 else "FAIL"
            log=(p.stdout+"\n"+p.stderr)[-200000:]
        except subprocess.TimeoutExpired:
            status="TIMEOUT";log="Test execution exceeded 30 seconds"
        duration=round(time.monotonic()-start,3)
        logpath=output/(job+".log")
        logpath.write_text(log,encoding="utf-8")
        results.append({"job_id":job,"status":status,"duration_seconds":duration,
                        "log":logpath.name,"log_sha256":hashlib.sha256(logpath.read_bytes()).hexdigest()})
    summary={"schema":1,"count":len(results),"passed":sum(x["status"]=="PASS" for x in results),"jobs":results}
    (output/"test-results.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",default="jobs")
    parser.add_argument("--output",default="dist/test-reports")
    args=parser.parse_args()
    try:
        result=run(args.source,args.output)
        print(json.dumps({"count":result["count"],"passed":result["passed"],"report":"dist/test-reports/test-results.json"}))
        sys.exit(0 if result["passed"]==result["count"] else 1)
    except Exception as exc:
        print("BATCH_TESTS_REJECTED: "+str(exc),file=sys.stderr)
        sys.exit(1)
