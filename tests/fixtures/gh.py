#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
args = sys.argv[1:]
scenario = os.environ['SCENARIO']
with Path(os.environ['CALL_LOG']).open('a') as log:
    log.write(json.dumps(args) + '\n')
if args[:2] == ['api', '--paginate']:
    if scenario == 'api_failure':
        sys.exit(1)
    if scenario != 'no_prs':
        print('42')
elif args[:2] == ['api', '--method']:
    assert 'sha=tested' in args and 'merge_method=squash' in args
    if scenario == 'merge_rejected':
        sys.exit(1)
    print(json.dumps({'merged': scenario != 'merge_unconfirmed'}))
elif args[0] == 'api':
    pr = {'state': 'open', 'draft': False,
          'user': {'login': 'dependabot[bot]', 'type': 'Bot'},
          'head': {'repo': {'full_name': 'owner/site'}, 'ref': 'dependabot/github_actions/update', 'sha': 'tested'},
          'base': {'repo': {'full_name': 'owner/site'}, 'ref': 'main'}}
    if scenario == 'human': pr['user']['login'] = 'someone'
    if scenario == 'fork': pr['head']['repo']['full_name'] = 'other/site'
    if scenario == 'stale': pr['head']['sha'] = 'newer'
    if scenario == 'draft': pr['draft'] = True
    if scenario == 'closed': pr['state'] = 'closed'
    if scenario == 'wrong_base': pr['base']['ref'] = 'other'
    if scenario == 'changed_while_waiting' and len(Path(os.environ['CALL_LOG']).read_text().splitlines()) > 2:
        pr['head']['sha'] = 'newer'
    if len(Path(os.environ['CALL_LOG']).read_text().splitlines()) > 2:
        if scenario == 'retargeted_while_waiting': pr['base']['ref'] = 'other'
        if scenario == 'drafted_while_waiting': pr['draft'] = True
    print(json.dumps(pr))
elif args[:2] == ['pr', 'checks']:
    if '--watch' in args:
        sys.exit(1 if scenario == 'failed_ci' else 0)
    checks = [{'name': 'Build hakyll site', 'bucket': 'pass', 'workflow': 'build'}]
    if scenario == 'skipped_build': checks[0]['bucket'] = 'skipping'
    if scenario == 'cancelled_ci': checks.append({'name': 'Other CI', 'bucket': 'cancel'})
    if scenario == 'pending_ci': checks.append({'name': 'Other CI', 'bucket': 'pending'})
    if scenario == 'no_checks': checks = []
    if scenario == 'wrong_workflow': checks[0]['workflow'] = 'other'
    print(json.dumps(checks))
elif args == ['workflow', 'run', 'build.yml', '--ref', 'main']:
    if scenario == 'dispatch_failure':
        sys.exit(1)
else:
    raise AssertionError(args)
