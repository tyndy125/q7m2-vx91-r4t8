import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec=importlib.util.spec_from_file_location("package_batch",Path(__file__).resolve().parents[1]/"factory/package_batch.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
JOB="PUBLIC-MODULE-00001"

def setup(root,job=JOB):
    folder=root/"jobs"/job
    (folder/"modules").mkdir(parents=True)
    (folder/"tests").mkdir()
    files=[]
    for name,data in (("modules/demo.py",b"VALUE = 1\n"),("tests/test_demo.py",b"def test_demo(): assert True\n")):
        (folder/name).write_bytes(data)
        files.append({"path":name,"sha256":hashlib.sha256(data).hexdigest()})
    contract={"schema":1,"job_id":job,"validation_gate":"UNIT",
              "public_release_approved":True,"integration_policy":"WINDOWS_VALIDATE_ONLY","files":files}
    (folder/"contract.json").write_text(json.dumps(contract))
    return folder,contract

class BatchTests(unittest.TestCase):
    def test_package_and_hash(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);setup(root)
            index=m.build(root/"jobs",root/"dist")
            self.assertEqual(index["count"],1)
            item=index["jobs"][0]; archive=root/"dist"/item["artifact"]
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),item["sha256"])
            with zipfile.ZipFile(archive) as z:self.assertEqual(len(z.namelist()),3)
    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);setup(root)
            first=m.build(root/"jobs",root/"a")
            second=m.build(root/"jobs",root/"b")
            self.assertEqual(first,second)
    def test_multiple_jobs(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);setup(root,"PUBLIC-MODULE-00002");setup(root)
            self.assertEqual(m.build(root/"jobs",root/"dist")["count"],2)
    def test_approval_required(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);folder,contract=setup(root)
            contract["public_release_approved"]=False
            (folder/"contract.json").write_text(json.dumps(contract))
            with self.assertRaises(m.Rejected):m.build(root/"jobs",root/"dist")
    def test_checksum_mismatch(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);folder,_=setup(root)
            (folder/"modules/demo.py").write_text("tampered")
            with self.assertRaises(m.Rejected):m.build(root/"jobs",root/"dist")
    def test_traversal(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);folder,contract=setup(root)
            contract["files"][0]["path"]="../private.py"
            (folder/"contract.json").write_text(json.dumps(contract))
            with self.assertRaises(m.Rejected):m.build(root/"jobs",root/"dist")
    def test_capacity(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);setup(root);setup(root,"PUBLIC-MODULE-00002")
            with self.assertRaises(m.Rejected):m.build(root/"jobs",root/"dist",1)
    def test_no_jobs(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/"jobs").mkdir()
            with self.assertRaises(m.Rejected):m.build(root/"jobs",root/"dist")
    def test_output_inside_source(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);setup(root)
            with self.assertRaises(m.Rejected):m.build(root/"jobs",root/"jobs"/"dist")
    def test_bad_gate(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);folder,contract=setup(root)
            contract["validation_gate"]="LIVE_RUNTIME"
            (folder/"contract.json").write_text(json.dumps(contract))
            with self.assertRaises(m.Rejected):m.build(root/"jobs",root/"dist")
if __name__=="__main__":unittest.main()
