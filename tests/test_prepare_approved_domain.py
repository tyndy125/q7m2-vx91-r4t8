import importlib.util
import pathlib
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("prepare_domain",ROOT/"factory/prepare_approved_domain.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class DomainPackageTests(unittest.TestCase):
    def test_materialized_domain_is_approved_and_testable(self):
        with tempfile.TemporaryDirectory() as d:
            dest=pathlib.Path(d)/"jobs"
            m.prepare(ROOT,dest)
            import sys
            package=importlib.util.spec_from_file_location("package_batch",ROOT/"factory/package_batch.py")
            pkg=importlib.util.module_from_spec(package)
            sys.modules[package.name]=pkg
            package.loader.exec_module(pkg)
            result=pkg.build(dest,pathlib.Path(d)/"dist")
            self.assertEqual(set(m.DOMAINS.values()) and {v[0] for v in m.DOMAINS.values()}, {j["job_id"] for j in result["jobs"] if j["job_id"] in {v[0] for v in m.DOMAINS.values()}})
    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            dest=pathlib.Path(d)/"jobs"
            m.prepare(ROOT,dest)
            with self.assertRaises(ValueError):m.prepare(ROOT,dest)
if __name__=="__main__":unittest.main()
