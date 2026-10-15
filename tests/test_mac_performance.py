import json
import re
import subprocess
import unittest

from build_web import patch_page
from serve_local import improve_game_page


PAGE = '''<head></head><body><div id="game-progress"></div><script>
const q = new URLSearchParams(location.search);
setInterval(() => {}, 1);
globalThis.settings = Object.fromEntries(q);
</script></body>'''


class MacPerformanceTests(unittest.TestCase):
    def launch(self, platform='MacIntel', query='', touch=0, static=False):
        page = (patch_page if static else improve_game_page)(PAGE)
        script = next(s for s in re.findall(r'<script>(.*?)</script>', page, re.S)
                      if 'const q = ' in s)
        context = {'navigator': {'platform': platform, 'maxTouchPoints': touch},
                   'location': {'search': query}}
        harness = '''const vm = require('node:vm');
const context = CONTEXT;
const intervals = [];
context.URLSearchParams = URLSearchParams;
context.setInterval = (fn, ms) => intervals.push(ms);
vm.runInNewContext(SCRIPT, context);
console.log(JSON.stringify({settings:context.settings, intervals}));'''
        harness = harness.replace('CONTEXT', json.dumps(context)).replace('SCRIPT', json.dumps(script))
        return json.loads(subprocess.check_output(['node', '-e', harness], text=True))

    def test_mac_defaults_apply_to_local_and_static_launchers(self):
        for static in (False, True):
            with self.subTest(static=static):
                result = self.launch(static=static)
                self.assertEqual(result['settings'], {
                    'low': '1', 'fps': '60', 'res': '1280x720', 'shadows': '0'})
                self.assertEqual(result['intervals'], [])

    def test_explicit_settings_win_on_mac(self):
        for static in (False, True):
            with self.subTest(static=static):
                result = self.launch(query='?low=0&fps=30&res=1600x900&shadows=1&cores=4', static=static)
                self.assertEqual(result['settings'], {
                    'low': '0', 'fps': '30', 'res': '1600x900', 'shadows': '1', 'cores': '4'})

    def test_explicit_scale_is_not_masked_by_default_resolution(self):
        for static in (False, True):
            with self.subTest(static=static):
                settings = self.launch(query='?scale=0.5', static=static)['settings']
                self.assertEqual(settings['scale'], '0.5')
                self.assertNotIn('res', settings)

    def test_windows_timer_is_preserved_without_mac_defaults(self):
        self.assertEqual(self.launch(platform='Win32'), {'settings': {}, 'intervals': [1]})

    def test_linux_and_ipad_do_not_get_mac_defaults_or_windows_timer(self):
        for platform, touch in [('Linux x86_64', 0), ('MacIntel', 5)]:
            with self.subTest(platform=platform, touch=touch):
                self.assertEqual(self.launch(platform=platform, touch=touch),
                                 {'settings': {}, 'intervals': []})


if __name__ == '__main__':
    unittest.main()
