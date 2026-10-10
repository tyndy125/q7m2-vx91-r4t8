import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location("run_batch_tests",Path(__file__).resolve().parents[1]/"factory/run_batch_tests.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ExecutionTests(unittest.TestCase):
    def make_job(self,root,body):
        folder=root/"jobs"/"PUBLIC-TEST-00001"
        (folder/"modules").mkdir(parents=True)
        (folder/"tests").mkdir()
        (folder/"modules"/"sample.py").write_text("VALUE=4\n")
        (folder/"tests"/"test_sample.py").write_text(body)
        entries=[]
        for name in ["modules/sample.py","tests/test_sample.py"]:
            entries.append({"path":name,"sha256":hashlib.sha256((folder/name).read_bytes()).hexdigest()})
        (folder/"contract.json").write_text(json.dumps({"schema":1,"job_id":folder.name,"public_release_approved":True,"validation_gate":"UNIT","integration_policy":"WINDOWS_VALIDATE_ONLY","files":entries}))
    def test_real_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.make_job(root,"def test_sample():\n from modules.sample import VALUE\n assert VALUE==4\n")
            result=m.run(root/"jobs",root/"reports")
            self.assertEqual(result["passed"],1)
            self.assertIn("EXECUTED_TESTS=1",(root/"reports"/"PUBLIC-TEST-00001.log").read_text())
    def test_real_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.make_job(root,"def test_sample():\n assert False\n")
            self.assertEqual(m.run(root/"jobs",root/"reports")["passed"],0)
    def test_zero_tests_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.make_job(root,"VALUE=4\n")
            self.assertEqual(m.run(root/"jobs",root/"reports")["passed"],0)
    def test_tampered_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.make_job(root,"def test_sample():\n assert True\n")
            (root/"jobs"/"PUBLIC-TEST-00001"/"modules"/"sample.py").write_text("VALUE=5\n")
            with self.assertRaises(ValueError):m.run(root/"jobs",root/"reports")
if __name__=="__main__":unittest.main()
