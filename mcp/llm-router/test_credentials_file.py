"""Only new private-file credential behavior; does not rerun the 41-test suite."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from router import Engine, Fault

class PrivateCredentialTests(unittest.TestCase):
    def test_private_file_precedes_environment_without_export(self):
        with tempfile.TemporaryDirectory() as root:
            key = Path(root)/'key'
            key.write_text('synthetic-file-only\n')
            key.chmod(0o600)
            engine = Engine({'identity':'isolated-test','state_dir':root+'/state','key_file':str(key)})
            with patch.dict(os.environ,{'LLM_ROUTER_LITELLM_KEY':'synthetic-other-identity'}):
                self.assertEqual(engine.key(),'synthetic-file-only')
                self.assertEqual(os.environ['LLM_ROUTER_LITELLM_KEY'],'synthetic-other-identity')
            engine.db.close()
    def test_public_or_symlink_credential_refused(self):
        with tempfile.TemporaryDirectory() as root:
            key = Path(root)/'key'
            key.write_text('synthetic-only')
            key.chmod(0o644)
            engine = Engine({'identity':'isolated-test','state_dir':root+'/state','key_file':str(key)})
            with self.assertRaisesRegex(Fault,'not_private'):
                engine.key()
            key.chmod(0o600)
            link = Path(root)/'link'
            link.symlink_to(key)
            engine.c['key_file'] = str(link)
            with self.assertRaisesRegex(Fault,'unavailable'):
                engine.key()
            engine.db.close()

if __name__ == '__main__':
    unittest.main()
