"""Tests of the export boundary, not of production services."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('collector',Path(__file__).with_name('collect_remote.py'))
c=importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class RedactionTests(unittest.TestCase):
    def test_nested_credentials(self):
        data={'password':'DUMMY-PASSWORD','options':'rw,password=DUMMY-CIFS,vers=3',
              'url':'https://user:DUMMY-URL@host/path?token=DUMMY-TOKEN',
              'traefik.http.middlewares.test.basicauth.users':'DUMMY-HTPASSWD'}
        output=str(c.clean(data))
        for marker in ['DUMMY-PASSWORD','DUMMY-CIFS','DUMMY-URL','DUMMY-TOKEN','DUMMY-HTPASSWD']:
            self.assertNotIn(marker,output)

    def test_compose_never_exports_environment_or_command(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'compose.yml'
            path.write_text('''services:
  app:
    image: example:1
    environment:
      PASSWORD: DUMMY-ENV
      TZ: DUMMY-NONSECRET-ENV
    command: [echo, DUMMY-CMD]
    entrypoint: DUMMY-ENTRY
    healthcheck:
      test: [CMD, DUMMY-HEALTH]
    labels:
      arbitrary: DUMMY-LABEL
      traefik.http.routers.app.rule: Host(`example.org`)
''')
            out=c.config_file(path,'compose')
            for marker in ['DUMMY-ENV','DUMMY-NONSECRET-ENV','DUMMY-CMD','DUMMY-ENTRY','DUMMY-HEALTH','DUMMY-LABEL']:
                self.assertNotIn(marker,str(out))
            self.assertEqual(out['configuration']['services']['app']['environment_keys_only'],['PASSWORD','TZ'])

    def test_traefik_header_values_not_exported(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'routes.yml'
            path.write_text('''http:
  middlewares:
    app:
      headers:
        customRequestHeaders:
          X-Custom: DUMMY-HEADER
''')
            self.assertNotIn('DUMMY-HEADER',str(c.config_file(path,'traefik')))


if __name__=='__main__':unittest.main()
