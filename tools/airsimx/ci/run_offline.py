"""Run the offline test suites and record a CI-shaped result.

This is the entry point both for local use and for the GitHub workflow in
``.github/workflows/airsimx-offline.yml``. It runs every suite that needs
neither Unreal nor a flight controller, and writes a JSON report carrying
the source commit, the Python and dependency versions, and each suite's
exit code and output, so a pass or failure can be reproduced later from the
artifact alone.

Suites that need an installed ``airsim`` package get ``PythonClient`` on
``PYTHONPATH`` instead, so a clean checkout works without installing
anything. A suite whose optional dependency is missing reports ``skipped``
(the tests themselves raise ``unittest.SkipTest``) and does not fail the run.

Exit code is 0 only when every suite passes.
"""

import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
PYTHON_CLIENT = ROOT / 'PythonClient'
ROS2_PACKAGE = ROOT / 'ros2' / 'src' / 'airsim_ros2'
NAV_PACKAGE = ROOT / 'ros2' / 'src' / 'airsim_nav_bridge'

SUITES = (
    ('python-client', PYTHON_CLIENT / 'tests', (PYTHON_CLIENT,)),
    ('airsimx-tools', ROOT / 'tools' / 'airsimx' / 'tests', ()),
    ('ros2-conversions', ROS2_PACKAGE / 'test', (PYTHON_CLIENT, ROS2_PACKAGE)),
    # test/ros has no __init__.py: its explicit Jazzy/DDS tests are separate.
    ('px4-odometry-conversions', NAV_PACKAGE / 'test', (NAV_PACKAGE,)),
)


def command_output(*args):
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as error:
        return 'unavailable: %r' % (error,)
    return (result.stdout or result.stderr).strip()


def installed_version(module):
    try:
        from importlib import metadata
        return metadata.version(module)
    except Exception:
        return None


def environment():
    packages = {}
    for name in ('msgpack', 'numpy', 'opencv-contrib-python', 'gymnasium',
                 'stable-baselines3', 'torch'):
        version = installed_version(name)
        if version is not None:
            packages[name] = version
    return {
        'python': sys.version.split()[0],
        'executable': sys.executable,
        'platform': platform.platform(),
        'commit': command_output('git', 'rev-parse', 'HEAD'),
        'branch': command_output('git', 'rev-parse', '--abbrev-ref', 'HEAD'),
        'dirty': bool(command_output('git', 'status', '--porcelain')),
        'packages': packages,
    }


def run_suite(name, start_dir, extra_path):
    env = os.environ.copy()
    entries = [str(path) for path in extra_path]
    if env.get('PYTHONPATH'):
        entries.append(env['PYTHONPATH'])
    if entries:
        env['PYTHONPATH'] = os.pathsep.join(entries)
    started = time.monotonic()
    result = subprocess.run(
        [sys.executable, '-m', 'unittest', 'discover', '-s', str(start_dir), '-v'],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=1800)
    output = (result.stdout or '') + (result.stderr or '')
    if result.returncode != 0:
        print(f'{name} test output:\n{output.rstrip()}', flush=True)
    skipped = 'skipped' in output and result.returncode == 0
    return {
        'name': name,
        'directory': str(start_dir.relative_to(ROOT)),
        'returncode': result.returncode,
        'status': 'passed' if result.returncode == 0 else 'failed',
        'skipped_some': skipped,
        'elapsed_s': round(time.monotonic() - started, 1),
        'tail': output.strip().splitlines()[-12:],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='directory for result.json; created if missing')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'status': 'running', 'scope': 'offline suites only; no simulator, no flight controller',
              'environment': environment(), 'suites': []}

    def save():
        (args.output / 'result.json').write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    save()
    try:
        for name, directory, extra_path in SUITES:
            suite = run_suite(name, directory, extra_path)
            report['suites'].append(suite)
            save()
            print('%s %s in %.1fs' % (suite['status'].upper(), name, suite['elapsed_s']), flush=True)
        failed = [suite['name'] for suite in report['suites'] if suite['status'] != 'passed']
        report['status'] = 'passed' if not failed else 'failed'
        if failed:
            report['failed_suites'] = failed
    except KeyboardInterrupt:
        report['status'] = 'interrupted'
    except Exception as error:
        report['status'] = 'failed'
        report['error'] = repr(error)
        print(repr(error), flush=True)
    finally:
        report['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
        save()
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
