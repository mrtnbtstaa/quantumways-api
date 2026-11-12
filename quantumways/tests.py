import os
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from quantumways.database_export_view import DatabaseExportDownloadView

POSTGRES_DB = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "quantumways_db",
    "USER": "quantumways_db_owner",
    "PASSWORD": "secret",
    "HOST": "ep-test-pooler.ap-southeast-1.aws.neon.tech",
    "PORT": "5432",
    "OPTIONS": {"sslmode": "require", "channel_binding": "require"},
}


class DatabaseExportDownloadTests(SimpleTestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(
            is_authenticated=True,
            user_role=SimpleNamespace(role="admin"),
        )

    def download(self):
        request = self.factory.get("/api/database/export/download")
        force_authenticate(request, user=self.user)
        return DatabaseExportDownloadView.as_view()(request)

    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
    def test_rejects_non_postgres_database(self):
        self.assertEqual(self.download().status_code, 400)

    @override_settings(DATABASES={"default": POSTGRES_DB})
    @patch.dict(os.environ, {"PG_DUMP_PATH": ""})
    @patch("quantumways.database_export_view.shutil.which", return_value=None)
    def test_missing_pg_dump(self, _which):
        self.assertEqual(self.download().status_code, 500)

    @override_settings(DATABASES={"default": POSTGRES_DB})
    @patch.dict(os.environ, {"PG_DUMP_PATH": ""})
    @patch("quantumways.database_export_view.shutil.which", return_value="pg_dump")
    @patch("quantumways.database_export_view.subprocess.run")
    def test_download_streams_dump_and_removes_temp_file(self, run, _which):
        paths, commands, envs = [], [], []

        def fake_run(command, **kwargs):
            path = command[command.index("--file") + 1]
            with open(path, "wb") as dump:
                dump.write(b"-- dump\n")
            paths.append(path)
            commands.append(command)
            envs.append(kwargs["env"])
            return SimpleNamespace(returncode=0, stderr="")

        run.side_effect = fake_run
        response = self.download()
        body = b"".join(response.streaming_content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body, b"-- dump\n")
        self.assertIn('attachment; filename="quantumways_db_', response["Content-Disposition"])
        self.assertNotIn("secret", " ".join(commands[0]))
        self.assertEqual(envs[0]["PGPASSWORD"], "secret")
        self.assertEqual(envs[0]["PGSSLMODE"], "require")
        self.assertEqual(envs[0]["PGHOST"], "ep-test.ap-southeast-1.aws.neon.tech")
        self.assertFalse(os.path.exists(paths[0]))
