import importlib.util
import io
import json
import pathlib
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('artifact_budget',ROOT/'factory/artifact_budget.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class BudgetTests(unittest.TestCase):
    def test_private_repository_is_rejected_before_network_access(self):
        with self.assertRaisesRegex(ValueError,'PUBLIC_REPOSITORY_REQUIRED'):
            m.check([],'private/example','secret',opener=lambda *a,**k:self.fail('network called'))

    def test_small_public_output_uses_only_own_public_artifact_endpoint(self):
        calls=[]
        def opener(request,timeout):
            calls.append(request.full_url)
            return io.BytesIO(json.dumps({'artifacts':[]}).encode())
        result=m.check([],m.REPOSITORY,'temporary-job-token',opener)
        self.assertEqual(result['state'],'PASS')
        self.assertEqual(calls,['https://api.github.com/repos/'+m.REPOSITORY+'/actions/artifacts?per_page=100&page=1'])
        self.assertNotIn('temporary-job-token',json.dumps(result))

    def test_oversized_output_is_refused_without_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            path=pathlib.Path(directory)/'large';path.write_bytes(b'x'*(m.MAX_RUN_BYTES+1))
            with self.assertRaisesRegex(ValueError,'PER_RUN_STORAGE'):
                m.payload_bytes([path])

    def test_existing_storage_cannot_be_ignored(self):
        def opener(*a,**k):
            return io.BytesIO(json.dumps({'artifacts':[{'expired':False,'size_in_bytes':m.MAX_RETAINED_BYTES+1}]}).encode())
        with self.assertRaisesRegex(ValueError,'RETAINED_STORAGE'):
            m.check([],m.REPOSITORY,'temporary-job-token',opener)
