"""Bound optional public artifacts; never queries private repositories."""
import argparse
import json
import os
from pathlib import Path
import urllib.request

REPOSITORY='tyndy125/q7m2-vx91-r4t8'
MAX_RUN_BYTES=1024*1024
MAX_RETAINED_BYTES=8*1024*1024


def payload_bytes(paths):
    total=0
    for root in map(Path,paths):
        if not root.exists():continue
        if root.is_symlink():raise ValueError('SYMLINK_ARTIFACT_FORBIDDEN')
        for path in root.rglob('*') if root.is_dir() else [root]:
            if path.is_symlink():raise ValueError('SYMLINK_ARTIFACT_FORBIDDEN')
            if path.is_file():total+=path.stat().st_size
    if total>MAX_RUN_BYTES:raise ValueError('PER_RUN_STORAGE_BUDGET_EXCEEDED')
    return total


def check(paths,repository,token,opener=urllib.request.urlopen):
    if repository!=REPOSITORY:raise ValueError('PUBLIC_REPOSITORY_REQUIRED')
    size=payload_bytes(paths);retained=0
    for page in range(1,11):
        request=urllib.request.Request(f'https://api.github.com/repos/{REPOSITORY}/actions/artifacts?per_page=100&page={page}',
            headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
        with opener(request,timeout=15) as response:body=json.load(response)
        artifacts=body['artifacts']
        retained+=sum(a['size_in_bytes'] for a in artifacts if not a['expired'])
        if len(artifacts)<100:break
    else:raise ValueError('ARTIFACT_INVENTORY_INCOMPLETE')
    if retained+size*2>MAX_RETAINED_BYTES:raise ValueError('RETAINED_STORAGE_BUDGET_EXCEEDED')
    return dict(state='PASS',payload_bytes=size,retained_bytes=retained,maximum_bytes=MAX_RETAINED_BYTES)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('paths',nargs='+');args=parser.parse_args()
    print(json.dumps(check(args.paths,os.environ['GITHUB_REPOSITORY'],os.environ['GH_TOKEN'])))
