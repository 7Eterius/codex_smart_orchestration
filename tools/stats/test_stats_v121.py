"""Collector 1.2.1 malformed-input and version-cohort regressions."""
from datetime import datetime,timedelta,timezone
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import smart_weekly_stats as s

BASE='e96ad3bd5cbd368141f58d1940466b80fd27f578'
ROOT=Path(__file__).resolve().parents[2]

class Collector121(unittest.TestCase):
    def association(self,markers,parent_markers=()):
        start=datetime(2026,10,1,tzinfo=timezone.utc)
        c=s.Collector(Path('/no-read'),start,start+timedelta(days=7),timezone.utc,progress=False)
        c.session('root').version_markers=set(parent_markers)
        child=c.session('child');child.parent='root';child.version_markers=set(markers)
        c.parents_with_smart_roles=set()
        return c.association('child')

    def test_malformed_durations_are_unavailable_not_exceptions(self):
        for value in ('.s','1.2.3s','..ms','NaNs','-1s','1e100s','9'*100+'s'):
            with self.subTest(value=value):self.assertIsNone(s.parse_duration(value))

    def test_supported_duration_formats_still_work(self):
        for value,expected in (('123ms',.123),('1.5s',1.5),('.5seconds',.5),(2,2)):
            self.assertEqual(s.parse_duration(value),expected)

    def test_exact_current_marker_is_not_collapsed_to_series(self):
        self.assertEqual(self.association({'4.2.1'}),'instruction_marker_4.2.1')
        self.assertEqual(self.association({'4.2.0'}),'instruction_marker_4.2.0')

    def test_series_marker_does_not_prove_patch(self):
        self.assertEqual(self.association({'4.2'}),'instruction_marker_4.2_series_patch_unproven')

    def test_consistent_series_and_patch_remain_one_exact_association(self):
        self.assertEqual(self.association({'4.2.1'},{'4.2'}),'instruction_marker_4.2.1')

    def test_copied_old_and_new_markers_are_mixed_not_latest_activation(self):
        self.assertEqual(self.association({'4.2.1'},{'4.0.1'}),'mixed_smart_instruction_versions')
        self.assertEqual(self.association({'4.2.0','4.2.1'}),'mixed_smart_instruction_versions')

    def test_older_cohort_compatibility_is_preserved(self):
        self.assertEqual(self.association({'4.0.1'}),'instruction_marker_4.0.1')
        self.assertEqual(self.association({'4.0'}),'instruction_marker_4.0_series_patch_unproven')

    def test_original_duration_counterexample(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'collector120.py'
            path.write_bytes(subprocess.check_output(['git','show',BASE+':tools/stats/smart_weekly_stats.py'],cwd=ROOT))
            key='_stats_original_120';spec=importlib.util.spec_from_file_location(key,path)
            old=importlib.util.module_from_spec(spec);sys.modules[key]=old;spec.loader.exec_module(old)
            with self.assertRaises(ValueError):old.parse_duration('1.2.3s')
            self.assertIsNone(s.parse_duration('1.2.3s'))

if __name__=='__main__':unittest.main()
