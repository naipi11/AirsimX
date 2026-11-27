import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from textwrap import dedent
import unittest


RUNNER = Path(__file__).resolve().parents[1] / 'ci' / 'run_offline.py'


class OfflineRunnerTests(unittest.TestCase):
    def test_failed_suite_prints_case_names_and_tracebacks(self):
        failing_tests = dedent('''\
            import unittest

            class ClientTests(unittest.TestCase):
                def test_a_assertion(self):
                    self.fail('fixture assertion failed')

                def test_b_exception(self):
                    raise ValueError('fixture exception raised')
        ''')
        passing_tests = dedent('''\
            import unittest

            class OtherTests(unittest.TestCase):
                def test_passes(self):
                    self.assertTrue(True)
        ''')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner = root / 'tools/airsimx/ci/run_offline.py'
            runner.parent.mkdir(parents=True)
            shutil.copyfile(RUNNER, runner)
            suites = {
                'PythonClient/tests': failing_tests,
                'tools/airsimx/tests': passing_tests,
                'ros2/src/airsim_ros2/test': passing_tests,
                'ros2/src/airsim_nav_bridge/test': passing_tests,
            }
            for directory, contents in suites.items():
                path = root / directory
                path.mkdir(parents=True)
                (path / 'test_fixture.py').write_text(contents, encoding='utf-8')

            output = root / 'report'
            result = subprocess.run(
                [sys.executable, '-I', str(runner), '--output', str(output)],
                cwd=root, capture_output=True, text=True, timeout=30,
            )
            report = json.loads((output / 'result.json').read_text(encoding='utf-8'))

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('FAIL: test_a_assertion', result.stdout)
        self.assertIn('AssertionError: fixture assertion failed', result.stdout)
        self.assertIn('ERROR: test_b_exception', result.stdout)
        self.assertIn('ValueError: fixture exception raised', result.stdout)
        self.assertIn('PASSED airsimx-tools', result.stdout)
        self.assertNotIn('test_passes', result.stdout)
        self.assertEqual(report['failed_suites'], ['python-client'])


if __name__ == '__main__':
    unittest.main()
