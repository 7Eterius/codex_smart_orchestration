"""Installer safety retained across the Smart 3 architecture change."""
from __future__ import annotations
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

PACKAGE=Path(__file__).resolve().parents[1]/'codex_workflow'
sys.path.insert(0,str(PACKAGE))
from runtime import smart_install as install, transaction
from runtime.errors import ValidationError, TransactionError
from runtime.layout import PackageLayout
from runtime.plan import resolve_owned_runtime_path
from runtime.smart_restore import prepare_restore

def snapshot(root):
    return {p.relative_to(root).as_posix():(p.read_bytes(),p.stat().st_mode&0o777)
            for p in root.rglob('*') if p.is_file() and '.smart-orchestration-backups' not in p.relative_to(root).parts}

class InstallerIntegrityTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.home=self.root/'home';self.home.mkdir()
        self.package=self.root/'package';shutil.copytree(PACKAGE,self.package,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        (self.home/'config.toml').write_text('model="owner"\n[agents]\nmax_threads=2\n')
        (self.home/'AGENTS.md').write_text('Owner instruction\n')

    def apply(self):
        plan,prior=install.prepare(self.package,self.home)
        return install.apply_plan(plan,prior,self.home)

    def state(self):return json.loads((self.home/'codex_workflow/install_state.json').read_text())
    def save(self,state):(self.home/'codex_workflow/install_state.json').write_text(json.dumps(state))

    def test_preview_is_readonly_and_disk_check_is_not_runtime_claim(self):
        before=snapshot(self.home)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(install.main(['--package-root',str(self.package),'--codex-home',str(self.home)]),0)
        self.assertEqual(snapshot(self.home),before)
        self.apply();before=snapshot(self.home);result=install.status(self.home)
        self.assertTrue(result['disk_ok']);self.assertEqual(result['runtime_observation'],'not_inspected')
        self.assertEqual(result['package_fingerprint'],PackageLayout.resolve(self.package).fingerprint)
        self.assertEqual(snapshot(self.home),before)

    def test_corrupt_runtime_and_managed_block_are_detected(self):
        self.apply();p=self.home/'codex_workflow/allocation-not-real.txt';p.write_text('unmanaged')
        f=self.home/'codex_workflow/runtime/allocation.py';f.write_text(f.read_text()+'\n# changed\n')
        self.assertFalse(install.status(self.home)['disk_ok'])
        before=snapshot(self.home)
        with self.assertRaises(ValidationError):install.prepare(self.package,self.home)
        self.assertEqual(snapshot(self.home),before)

    def test_manifest_inventory_cannot_be_missing(self):
        self.apply();s=self.state();s['owned_runtime_hashes'].pop('browser.md');self.save(s)
        self.assertFalse(install.status(self.home)['disk_ok'])

    def test_custom_templates_do_not_authorize_replacement(self):
        self.apply()
        for rel in ('agents/default_executor.toml','codex_workflow/templates/agents/default_executor.toml'):
            p=self.home/rel;p.write_text(p.read_text()+'\n# owner\n')
        with self.assertRaises(ValidationError):install.prepare(self.package,self.home)

    def test_state_identity_and_schema_conflicts_stop(self):
        self.apply();original=self.state()
        for key,value in (('workflow','other'),('schema_version',True),('version','0.0.0')):
            state=dict(original);state[key]=value;self.save(state)
            with self.assertRaises(ValidationError):install.prepare(self.package,self.home)
        self.save(original)

    def test_local_modified_retired_file_preserved(self):
        self.apply();p=self.home/'codex_workflow/obsolete.md';p.write_text('owner')
        state=self.state();state['owned_runtime_files'].append('obsolete.md')
        state['owned_runtime_hashes']['obsolete.md']='0'*64;self.save(state)
        self.apply();self.assertEqual(p.read_text(),'owner')

    def test_source_backup_is_not_retired(self):
        self.apply();p=self.home/'codex_workflow/.source_backup/old/owner';p.parent.mkdir(parents=True);p.write_text('keep')
        self.apply();self.assertEqual(p.read_text(),'keep')
        for rel in ('../config.toml','/etc/passwd','.source_backup/old/x','.backups/x','.git/config','.'):
            with self.assertRaises(ValidationError):resolve_owned_runtime_path(self.home/'codex_workflow',rel)

    def test_missing_files_invalid_roles_and_symlinks_fail_package_validation(self):
        p=self.package/'verification.md';content=p.read_bytes();p.unlink()
        with self.assertRaises(ValidationError):PackageLayout.resolve(self.package)
        p.write_bytes(content)
        role=self.package/'agents/simple_executor.toml';content=role.read_text();role.write_text(content.replace('enabled = false','enabled = true'))
        with self.assertRaises(ValidationError):PackageLayout.resolve(self.package)
        role.write_text(content)
        alias=self.package/'alias';alias.symlink_to(role)
        with self.assertRaises(ValidationError):PackageLayout.resolve(self.package)

    def test_unowned_collision_and_config_symlink_are_protected(self):
        target=self.home/'codex_workflow/execution.md';target.parent.mkdir();target.write_text('owner')
        with self.assertRaises(ValidationError):self.apply()
        self.assertEqual(target.read_text(),'owner');target.unlink();target.parent.rmdir()
        outside=self.root/'outside';outside.write_text('model="owner"\n')
        config=self.home/'config.toml';config.unlink();config.symlink_to(outside)
        with self.assertRaises(ValidationError):self.apply()
        self.assertEqual(outside.read_text(),'model="owner"\n')

    def test_transaction_failure_restores_original_bytes(self):
        before=snapshot(self.home);original=transaction._atomic_write;count=0
        def broken(*args,**kwargs):
            nonlocal count
            count+=1
            if count==6:raise OSError('Injected failure')
            return original(*args,**kwargs)
        with mock.patch.object(transaction,'_atomic_write',side_effect=broken):
            with self.assertRaises(TransactionError):self.apply()
        self.assertEqual(snapshot(self.home),before)
        self.assertFalse((self.home/'.smart-orchestration-install.lock').exists())

    def test_stale_lock_and_changed_backup_require_review(self):
        lock=self.home/'.smart-orchestration-install.lock';lock.mkdir()
        with self.assertRaises(ValidationError):self.apply()
        self.assertTrue(lock.exists());lock.rmdir()
        backup=self.apply();(backup/'files/config.toml').write_text('corrupt')
        with self.assertRaises(ValidationError):prepare_restore(self.home,backup)

    def test_scratch_not_installed_and_same_version_update_supported(self):
        (self.package/'private.txt').write_text('not distributed');self.apply()
        self.assertFalse((self.home/'codex_workflow/private.txt').exists())
        p=self.package/'browser.md';p.write_text(p.read_text()+'\nReviewed update.\n');self.apply()
        self.assertEqual(p.read_bytes(),(self.home/'codex_workflow/browser.md').read_bytes())
        self.assertTrue(install.status(self.home)['disk_ok'])

    def test_failed_disk_check_returns_nonzero(self):
        self.apply();(self.home/'codex_workflow/browser.md').unlink()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(install.main(['--codex-home',str(self.home),'--check']),1)

if __name__=='__main__':unittest.main()
