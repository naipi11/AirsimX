import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location('stage_build', Path(__file__).resolve().parents[1] / 'build_windows.py')
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / 'checkout'
        self.project = self.base / 'separate-project/Custom.uproject'
        files = {
            'AirSim.props': 'props', 'LICENSE': 'license',
            'Unreal/Plugins/AirSim/AirSim.uplugin': 'new descriptor',
            'Unreal/Plugins/AirSim/Source/AirSim.Build.cs': 'new rules',
            'Unreal/Plugins/AirSim/Content/sample.uasset': 'new asset',
            'AirLib/include/body.hpp': 'header',
            'AirLib/deps/eigen3/Eigen/Core': 'eigen',
            'AirLib/deps/eigen3/COPYING.MPL2': 'license',
            'AirLib/deps/rpclib/include/rpc.hpp': 'rpc header',
            'AirLib/deps/MavLinkCom/include/mav.hpp': 'mav header',
        }
        for config in ('Release', 'Debug'):
            files['AirLib/lib/x64/' + config + '/AirLib.lib'] = 'airlib ' + config
            for dependency, name in (('rpclib', 'rpc'), ('MavLinkCom', 'MavLinkCom')):
                files['AirLib/deps/' + dependency + '/lib/x64/' + config + '/' + name + '.lib'] = dependency + config
        for relative, content in files.items():
            self.put(self.root / relative, content)
        self.put(self.project, '{}')
        self.plugin = self.project.parent / 'Plugins/AirSim'
        self.put(self.plugin / 'AirSim.uplugin', 'old descriptor')
        self.put(self.plugin / 'Source/AirSim.Build.cs', 'old rules')
        self.put(self.plugin / 'Source/AirLib/include/body.hpp', 'old header')
        self.put(self.plugin / 'Content/sample.uasset', 'old asset')
        self.put(self.plugin / 'Content/custom.uasset', 'user asset')
        self.put(self.plugin / 'Binaries/Win64/existing.dll', 'existing output')
        self.put(self.plugin / 'Intermediate/existing.obj', 'existing object')
        self.args = argparse.Namespace(root=self.root, project=self.project, cache_dir=None,
            command='stage', output=self.root / 'record', configuration='Both',
            engine_root=None, archive_dir=None, jobs=4, game_target=None, editor_target=None)
        self.builder = build.Builder(self.args)

    @staticmethod
    def put(path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def snapshot(self):
        return {p.relative_to(self.plugin).as_posix(): p.read_bytes() for p in self.plugin.rglob('*') if p.is_file()}

    def test_missing_library_preserves_entire_installed_plugin(self):
        before = self.snapshot()
        (self.root / 'AirLib/lib/x64/Debug/AirLib.lib').unlink()
        with self.assertRaises(FileNotFoundError):
            self.builder.stage()
        self.assertEqual(self.snapshot(), before)

    def test_rejected_compilation_unit_preserves_entire_plugin(self):
        before = self.snapshot()
        self.put(self.root / 'AirLib/deps/eigen3/Eigen/example.cpp', 'bad')
        with self.assertRaises(ValueError):
            self.builder.stage()
        self.assertEqual(self.snapshot(), before)

    def test_swap_failure_rolls_back_sources_assets_and_dependencies(self):
        before = self.snapshot()
        replace = Path.replace
        def fail_swap(source, target):
            if source.name.startswith('plugin-') and Path(target) == self.plugin:
                raise PermissionError('injected replacement failure')
            return replace(source, target)
        with mock.patch.object(Path, 'replace', fail_swap):
            with self.assertRaises(PermissionError):
                self.builder.stage()
        self.assertEqual(self.snapshot(), before)

    def test_staging_and_backup_use_project_volume(self):
        moves = []
        replace = Path.replace
        def capture(source, target):
            if source == self.plugin or Path(target) == self.plugin:
                moves.append((source, Path(target)))
            return replace(source, target)
        with mock.patch.object(Path, 'replace', capture):
            self.builder.stage()
        self.assertEqual(len(moves), 2)
        self.assertTrue(all(source.is_relative_to(self.project.parent) and target.is_relative_to(self.project.parent)
                            for source, target in moves))
        backup = Path(self.builder.record['previous_plugin_backup'])
        self.assertEqual((backup / 'AirSim.uplugin').read_text(), 'old descriptor')
        self.assertEqual((self.plugin / 'AirSim.uplugin').read_text(), 'new descriptor')
        self.assertEqual((self.plugin / 'Binaries/Win64/existing.dll').read_text(), 'existing output')
        self.assertEqual((self.plugin / 'Content/custom.uasset').read_text(), 'user asset')

    def test_unchanged_staging_does_not_swap_or_touch_timestamps(self):
        self.builder.stage()
        timestamp = (self.plugin / 'Source/AirSim.Build.cs').stat().st_mtime_ns
        moves = []
        replace = Path.replace
        def capture(source, target):
            if source == self.plugin or Path(target) == self.plugin:
                moves.append((source, target))
            return replace(source, target)
        with mock.patch.object(Path, 'replace', capture):
            self.builder.stage()
        self.assertEqual(moves, [])
        self.assertTrue(self.builder.record['stage_unchanged'])
        self.assertEqual((self.plugin / 'Source/AirSim.Build.cs').stat().st_mtime_ns, timestamp)

    def test_native_changes_do_not_reuse_copied_intermediate_objects(self):
        self.builder.stage()
        obj = self.plugin / 'Intermediate/old.obj'
        self.put(obj, 'compiled previous source')
        self.put(self.root / 'Unreal/Plugins/AirSim/Source/AirSim.Build.cs', 'changed native rules')
        self.args.output = self.root / 'record-native-update'
        updated = build.Builder(self.args)
        updated.stage()
        self.assertTrue(updated.record['native_inputs_changed'])
        self.assertFalse(updated.record['plugin_intermediate_reused'])
        self.assertFalse(obj.exists())
        self.assertEqual((Path(updated.record['previous_plugin_backup']) / 'Intermediate/old.obj').read_text(),
                         'compiled previous source')

    def test_asset_only_changes_can_reuse_native_intermediate(self):
        self.builder.stage()
        self.put(self.plugin / 'Intermediate/current.obj', 'compiled current source')
        self.put(self.root / 'Unreal/Plugins/AirSim/Content/sample.uasset', 'changed asset')
        self.args.output = self.root / 'record-asset-update'
        updated = build.Builder(self.args)
        updated.stage()
        self.assertFalse(updated.record['native_inputs_changed'])
        self.assertTrue(updated.record['plugin_intermediate_reused'])
        self.assertEqual((self.plugin / 'Intermediate/current.obj').read_text(), 'compiled current source')

    def test_release_only_does_not_require_debug_artifacts(self):
        self.args.configuration = 'Release'
        for path in self.root.glob('AirLib/**/Debug/*.lib'):
            path.unlink()
        self.builder.stage()
        self.assertEqual(self.builder.record['staged_configurations'], ['Release'])
        self.assertFalse((self.plugin / 'Source/AirLib/lib/x64/Debug').exists())

    def test_debug_only_all_is_rejected_before_any_work(self):
        with mock.patch.object(build, 'Builder') as constructor, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                build.main(['all', '--configuration', 'Debug'])
        self.assertEqual(result.exception.code, 2)
        constructor.assert_not_called()

    def test_explicit_target_may_differ_from_project_name(self):
        self.args.game_target = 'FlightGame'
        self.args.editor_target = 'FlightEditor'
        self.put(self.project.parent / 'Source/FlightGame.Target.cs', 'target')
        self.put(self.project.parent / 'Source/FlightEditor.Target.cs', 'target')
        self.assertEqual(self.builder.target('game'), 'FlightGame')
        self.assertEqual(self.builder.target('editor'), 'FlightEditor')
        self.args.game_target = None
        with self.assertRaises(ValueError):
            self.builder.target('game')

    def test_package_checks_selected_target_and_receipt_executable(self):
        self.args.game_target = 'FlightGame'
        self.args.engine_root = self.base / 'engine'
        self.args.archive_dir = self.base / 'package'
        self.put(self.project.parent / 'Source/FlightGame.Target.cs', 'target')
        self.put(self.args.engine_root / 'Engine/Build/Build.version', json.dumps({'MajorVersion': 5, 'MinorVersion': 8}))
        self.put(self.project.parent / 'Binaries/Win64/FlightGame.target', json.dumps({
            'TargetName': 'FlightGame', 'Configuration': 'Development',
            'BuildProducts': [{'Type': 'Executable', 'Path': '$(ProjectDir)/Binaries/Win64/ActualBinary.exe'}]}))
        def execute(label, command, timeout=1800):
            if label == 'ue-package':
                self.put(self.args.archive_dir / 'Windows/ActualBinary.exe', 'binary')
        with mock.patch.object(self.builder, 'run', side_effect=execute):
            self.builder.package()
        self.assertIn('Windows\\ActualBinary.exe' if build.os.name == 'nt' else 'Windows/ActualBinary.exe',
                      self.builder.record['package_executables'])
        self.assertEqual(self.builder.record['game_target'], 'FlightGame')


if __name__ == '__main__':
    unittest.main()
