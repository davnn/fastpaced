"""Run the workflow's actual shell with a fake GitHub CLI; no network or writes to GitHub."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/dependabot-automerge.yml'
FIXTURE = ROOT / 'tests/fixtures/gh.py'


def merge_script():
    """Extract the named step's block without depending on its position or indent."""
    lines = WORKFLOW.read_text().splitlines(keepends=True)
    target = '- name: Squash merge passing Dependabot PRs'
    matches = [index for index, line in enumerate(lines) if line.strip() == target]
    if len(matches) != 1:
        raise ValueError('Expected one named Dependabot merge step')
    start = matches[0]
    step_indent = len(lines[start]) - len(lines[start].lstrip())
    for index in range(start + 1, len(lines)):
        line = lines[index]
        indent = len(line) - len(line.lstrip())
        if line.strip() and indent <= step_indent:
            break
        if line.strip() == 'run: |':
            body = []
            for candidate in lines[index + 1:]:
                candidate_indent = len(candidate) - len(candidate.lstrip())
                if candidate.strip() and candidate_indent <= indent:
                    break
                body.append(candidate)
            script = textwrap.dedent(''.join(body))
            if script.strip():
                return script
    raise ValueError('The Dependabot merge step must have a nonempty run block')


class Automerge(unittest.TestCase):
    def run_scenario(self, scenario):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cli = root / 'gh'
            cli.write_text(FIXTURE.read_text())
            cli.chmod(0o755)
            log = root / 'calls.jsonl'
            env = dict(os.environ, PATH=directory + os.pathsep + os.environ['PATH'],
                       GH_REPO='owner/site', TESTED_SHA='tested', GH_TOKEN='test-only',
                       SCENARIO=scenario, CALL_LOG=str(log))
            result = subprocess.run(['bash', '-c', merge_script()], env=env, text=True, capture_output=True, timeout=10)
            self.assertTrue(log.is_file(), result.stderr or "Mock CLI was never called")
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            return result, calls

    def test_success_merges_then_dispatches(self):
        result, calls = self.run_scenario('success')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls[-2][:2], ['api', '--method'])
        self.assertEqual(calls[-1], ['workflow', 'run', 'build.yml', '--ref', 'main'])

    def test_ineligible_prs_are_ignored(self):
        for scenario in ('human', 'fork', 'stale', 'draft', 'closed', 'wrong_base'):
            with self.subTest(scenario=scenario):
                result, calls = self.run_scenario(scenario)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(len(calls), 2)

    def test_unsuccessful_checks_never_merge(self):
        for scenario in ('failed_ci', 'cancelled_ci', 'pending_ci', 'skipped_build', 'no_checks', 'wrong_workflow', 'changed_while_waiting', 'retargeted_while_waiting', 'drafted_while_waiting'):
            with self.subTest(scenario=scenario):
                result, calls = self.run_scenario(scenario)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(any(call[:2] == ['api', '--method'] for call in calls))
                self.assertFalse(any(call[0] == 'workflow' for call in calls))

    def test_rejected_merge_does_not_dispatch(self):
        result, calls = self.run_scenario('merge_rejected')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(call[0] == 'workflow' for call in calls))

    def test_no_associated_pr_does_nothing(self):
        result, calls = self.run_scenario('no_prs')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 1)

    def test_api_failure_does_not_attempt_merge(self):
        result, calls = self.run_scenario('api_failure')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(calls), 1)

    def test_unconfirmed_merge_does_not_dispatch(self):
        result, calls = self.run_scenario('merge_unconfirmed')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(call[0] == 'workflow' for call in calls))

    def test_dispatch_failure_is_reported_after_merge(self):
        result, calls = self.run_scenario('dispatch_failure')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls[-2][:2], ['api', '--method'])
        self.assertEqual(calls[-1][0], 'workflow')


if __name__ == '__main__':
    unittest.main()
