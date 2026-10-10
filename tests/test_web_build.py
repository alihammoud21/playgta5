import unittest
import json
import subprocess
from build_web import patch_page, patch_worker


class WebBuildTests(unittest.TestCase):
    def test_static_prefetch_removes_backend_dependency(self):
        code = 'try { if (wanted.size) await batchFetch(full, true, wanted); } catch (e) {}'
        result = patch_worker(code)
        script = "const full=[{id:1,a:0,b:2},{id:2,a:3,b:4}]; const wanted=new Set([2]); const calls=[]; async function ensureBlocks(...args){calls.push(args);} async function batchFetch(){throw Error('Backend must not be used');} (async()=>{" + result + ";console.log(JSON.stringify(calls));})();"
        completed = subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(completed.stdout), [[2, 3, 4, True]])

    def test_hosted_defaults_preserve_explicit_user_settings(self):
        result = patch_page('const q = new URLSearchParams(location.search);')
        for query, expected in [('', {'low': '1', 'fps': '30', 'res': '1280x720'}), ('?low=0&fps=60&res=1920x1080', {'low':'0','fps':'60','res':'1920x1080'})]:
            script = 'const location={search:' + json.dumps(query) + '};' + result + ';console.log(JSON.stringify(Object.fromEntries(q)));'
            completed = subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(completed.stdout), expected)

    def test_unknown_or_already_patched_snapshots_fail_closed(self):
        for fn, text in [(patch_page, 'changed snapshot'), (patch_worker, 'changed worker')]:
            with self.assertRaises(ValueError):
                fn(text)


if __name__ == '__main__':
    unittest.main()
