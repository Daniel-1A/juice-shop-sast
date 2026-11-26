import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

@unittest.skipIf(os.name == 'nt' or not shutil.which('bash'), 'Bash integration runs on Linux/WSL')
class PublishTest(unittest.TestCase):
    def test_failure_keeps_current_artifact_separate_and_cleans_only_own_project(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            (root / 'reports/old').mkdir(parents=True)
            (root / 'reports/old/publication.json').write_text('{"complete":true}')
            docker = bin_dir / 'docker'
            docker.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$DOCKER_TRACE"\nexit 0\n')
            python = bin_dir / 'python3'
            python.write_text('#!/bin/sh\ncase "$*" in *" dtrack "*) exit 1;; *) exit 0;; esac\n')
            docker.chmod(0o755)
            python.chmod(0o755)
            env = {**os.environ, 'PATH': str(bin_dir) + ':' + os.environ['PATH'], 'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_SHA': 'a' * 40, 'GITHUB_WORKSPACE': str(root), 'RUNNER_TEMP': str(root), 'GITHUB_OUTPUT': str(root / 'output'), 'DOCKER_TRACE': str(root / 'docker-trace')}
            result = subprocess.run(['bash', str(Path(__file__).with_name('publish.sh')), str(root / 'bundle')], cwd=root, env=env, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            trace = (root / 'docker-trace').read_text()
            self.assertIn('--project-name juice-aspm-ci-123-1', trace)
            self.assertIn('down --volumes --remove-orphans', trace)
            report = Path((root / 'output').read_text().strip().split('=', 1)[1])
            self.assertNotEqual(report, root / 'reports/old')
            self.assertFalse((report / 'publication.json').exists())
            self.assertTrue((root / 'reports/old/publication.json').exists())

if __name__ == '__main__':
    unittest.main()
