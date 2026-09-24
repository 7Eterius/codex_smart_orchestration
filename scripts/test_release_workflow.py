"""Execute the actual release shell with local Git and a non-network fake gh."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/validate.yml'

FAKE_GH = r'''
import hashlib,json,os,sys,zipfile
from pathlib import Path
p=Path(os.environ['FAKE_GH_STATE']); s=json.loads(p.read_text()); args=sys.argv[1:]
s.setdefault('calls',[]).append(args)
def finish(code=0, value=None):
 p.write_text(json.dumps(s))
 if value is not None: print(json.dumps(value))
 sys.exit(code)
if args[:3]==['api','--method','POST']:
 if s.get('offline'): finish(1)
 if s.get('tag') is not None: finish(1)
 s['tag']={'type':'commit','sha':os.environ['GITHUB_SHA']}
 finish(value={'object':s['tag']})
if args[0]=='api':
 if s.get('offline') or s.get('tag') is None: finish(1)
 finish(value={'object':s['tag']})
if args[:2]==['release','view']:
 if s.get('release') is None: finish(1)
 finish(value=s['release'])
if args[:2]==['release','create']:
 if s.get('create_failure'): finish(1)
 assert '--verify-tag' in args and '--latest' in args
 tag=args[2]; archive=Path(args[3]); sums=Path(args[4])
 expected=hashlib.sha256(archive.read_bytes()).hexdigest()
 assert sums.read_text().split()[0]==expected
 with zipfile.ZipFile(archive) as z:
  version=z.read('smart-orchestration-'+tag[1:]+'/codex_workflow/operate/VERSION').decode().strip()
 assert tag=='v'+version
 notes=Path(args[args.index('--notes-file')+1]).read_text()
 assert os.environ['GITHUB_SHA'] in notes and 'not native Codex qualification' in notes
 s['published_version']=version
 s['release']={'isDraft':False,'isPrerelease':False,'tagName':tag}
 finish(value={'url':'https://example.invalid/release/'+tag})
finish(3)
'''


class ReleaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.state = self.root / 'state.json'
        self.state.write_text('{}')
        binary = self.root / 'bin'
        binary.mkdir()
        gh = binary / 'gh'
        gh.write_text('#!' + sys.executable + '\n' + FAKE_GH)
        gh.chmod(0o755)
        self.env = {**os.environ, 'PATH': str(binary) + os.pathsep + os.environ['PATH'],
                    'FAKE_GH_STATE': str(self.state), 'GITHUB_REPOSITORY': 'fixture/repo',
                    'GITHUB_RUN_ID': '123', 'RUNNER_TEMP': str(self.root),
                    'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}
        self.git('init', '-q')
        self.git('config', 'user.name', 'Release Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.version = self.repo / 'codex_workflow/operate/VERSION'
        self.version.parent.mkdir(parents=True)
        self.version.write_text('2.2.0\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'baseline')
        self.notes = self.repo / 'docs/v2.3.md'
        self.notes.parent.mkdir()
        self.notes.write_text('# Fixture source release\n')
        self.commit_version('2.3.0')
        text = WORKFLOW.read_text()
        release = text.split('      - name: Publish immutable tested source\n', 1)[1]
        self.script = textwrap.dedent(release.split('        run: |\n', 1)[1])

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.repo, env=self.env, check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit_version(self, value):
        self.version.write_text(value + '\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'version change')
        self.env['GITHUB_SHA'] = self.git('rev-parse', 'HEAD')

    def run_release(self, state=None):
        if state is not None:
            self.state.write_text(json.dumps(state))
        result = subprocess.run(['bash', '-c', self.script], cwd=self.repo, env=self.env,
                                capture_output=True, text=True, timeout=30)
        return result, json.loads(self.state.read_text())

    def tag(self, sha=None, kind='commit'):
        return {'type': kind, 'sha': sha or self.env['GITHUB_SHA']}

    def test_version_change_publishes_pinned_archive_and_checksum(self):
        result, state = self.run_release()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(state['published_version'], '2.3.0')
        self.assertEqual(state['tag'], self.tag())
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_unchanged_version_does_not_call_github(self):
        self.notes.write_text('# Another documentation change\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'docs only')
        self.env['GITHUB_SHA'] = self.git('rev-parse', 'HEAD')
        result, state = self.run_release()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(state.get('calls', []), [])

    def test_invalid_version_stops_before_github(self):
        self.commit_version('2.3.0;bad')
        result, state = self.run_release()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(state.get('calls', []), [])

    def test_missing_notes_stops_before_github(self):
        self.notes.unlink()
        result, state = self.run_release()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(state.get('calls', []), [])

    def test_wrong_existing_tag_is_never_moved(self):
        result, state = self.run_release({'tag': self.tag('0' * 40)})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(state['tag']['sha'], '0' * 40)
        self.assertFalse(any(c[:2] == ['release', 'create'] for c in state['calls']))

    def test_annotated_existing_tag_requires_inspection(self):
        result, state = self.run_release({'tag': self.tag(kind='tag')})
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(c[:2] == ['release', 'create'] for c in state['calls']))

    def test_existing_exact_published_release_is_not_overwritten(self):
        release = {'isDraft': False, 'isPrerelease': False, 'tagName': 'v2.3.0'}
        result, state = self.run_release({'tag': self.tag(), 'release': release})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(c[:2] == ['release', 'create'] for c in state['calls']))

    def test_existing_draft_or_prerelease_is_not_silently_published(self):
        for key in ('isDraft', 'isPrerelease'):
            release = {'isDraft': False, 'isPrerelease': False, 'tagName': 'v2.3.0', key: True}
            result, state = self.run_release({'tag': self.tag(), 'release': release})
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(any(c[:2] == ['release', 'create'] for c in state['calls']))

    def test_offline_tag_failure_is_not_treated_as_missing(self):
        result, state = self.run_release({'offline': True})
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(c[:2] == ['release', 'create'] for c in state['calls']))

    def test_failed_creation_can_retry_exact_tag_without_moving_it(self):
        result, state = self.run_release({'create_failure': True})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(state['tag'], self.tag())
        state['create_failure'] = False
        result, state = self.run_release(state)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state['tag'], self.tag())
        self.assertEqual(state['published_version'], '2.3.0')

    def test_workflow_limits_release_to_successful_main_push(self):
        text = WORKFLOW.read_text()
        self.assertIn('    needs: validate\n', text)
        self.assertIn("github.event_name == 'push' && github.ref == 'refs/heads/main'", text)
        self.assertIn("github.repository == '7Eterius/codex_smart_orchestration'", text)
        self.assertIn('permissions:\n  contents: read\n', text)
        self.assertIn('    permissions:\n      contents: write\n', text)
        self.assertIn('git diff --check HEAD^ HEAD', text)
