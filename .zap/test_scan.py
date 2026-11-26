import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.name != 'nt' and shutil.which('bash'), 'Requires Linux Bash')
class OutputIsolationTests(unittest.TestCase):
    def test_failed_new_runs_do_not_publish_an_older_successful_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / '.zap').mkdir()
            shutil.copy(Path(__file__).with_name('scan.sh'), root / '.zap/scan.sh')
            (root / '.zap/image.txt').write_text('unused-image\n')
            old = root / 'reports/dast/full/summary.json'
            old.parent.mkdir(parents=True)
            old.write_text('{"passed":true}')
            binary = root / 'bin'
            binary.mkdir()
            docker = binary / 'docker'
            docker.write_text('#!/bin/sh\nexit 9\n')
            docker.chmod(0o755)
            outputs = []
            for attempt in ('1', '2'):
                output = root / ('output-' + attempt)
                env = dict(os.environ, PATH=str(binary) + ':' + os.environ['PATH'],
                           GITHUB_OUTPUT=str(output), GITHUB_RUN_ID='123', GITHUB_RUN_ATTEMPT=attempt)
                result = subprocess.run(['bash', '.zap/scan.sh', 'juice-shop:test', 'false'], cwd=root,
                                        env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 9)
                published = output.read_text().strip().split('=', 1)[1]
                self.assertNotEqual(published, 'reports/dast')
                self.assertTrue((root / published).is_dir())
                self.assertEqual((root / published).stat().st_mode & 0o005, 0o005,
                                 'Artifact uploader may have a different UID from ZAP')
                self.assertFalse((root / published / 'full/summary.json').exists())
                outputs.append(published)
            self.assertNotEqual(outputs[0], outputs[1])
            self.assertEqual(old.read_text(), '{"passed":true}')


if __name__ == '__main__':
    unittest.main()
