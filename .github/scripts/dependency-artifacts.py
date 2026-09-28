import json
import os
import re
import subprocess


def latest_builds(artifacts, keys):
    """The newest attempt's unexpired build of each key; a missing one means its job failed."""
    builds = {}
    for artifact in artifacts:
        match = re.fullmatch(r'package-([a-f0-9]{64})-([1-9][0-9]*)', artifact['name'])
        if not match or artifact['expired'] or match[1] not in keys:
            continue
        attempt = int(match[2])
        if attempt > builds.get(match[1], (0, None))[0]:
            builds[match[1]] = (attempt, artifact['id'])
    missing = [key for key in keys if key not in builds]
    if missing:
        raise ValueError(f'No build in this run for dependency inputs {", ".join(missing)}: their job failed, '
                         'or found a result published after planning; re-run all jobs to plan against it')
    return [builds[key][1] for key in keys]


def main():
    keys = os.environ['DEPENDENCIES'].split()
    listing = subprocess.check_output(
        ['gh', 'api', '--paginate', '--jq', '.artifacts[] | {id, name, expired}',
         f"repos/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}/artifacts"],
        text=True)
    artifacts = [json.loads(line) for line in listing.splitlines() if line]
    ids = latest_builds(artifacts, keys)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write(f'ids={",".join(map(str, ids))}\n')


if __name__ == '__main__':
    main()
