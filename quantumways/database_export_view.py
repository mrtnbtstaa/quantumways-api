import logging
import os
import shutil
import subprocess
import tempfile
from contextlib import suppress
from datetime import datetime

from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from quantumways.permissions import IsAdmin
from quantumways.utils import response_message_utils

logger = logging.getLogger(__name__)

POSTGRES_ENGINES = (
    "django.db.backends.postgresql",
    "django.db.backends.postgresql_psycopg2",
)


def _remove(path):
    with suppress(FileNotFoundError):
        os.remove(path)


class DatabaseExportDownloadView(APIView):

    # permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, *args, **kwargs):
        db = settings.DATABASES["default"]

        if db.get("ENGINE") not in POSTGRES_ENGINES:
            return response_message_utils(
                message="Database export is only available for PostgreSQL databases.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not db.get("NAME"):
            return response_message_utils(
                message="Invalid database configuration.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        pg_dump = os.environ.get("PG_DUMP_PATH") or shutil.which("pg_dump")
        if not pg_dump:
            return response_message_utils(
                message="Database export is unavailable: pg_dump was not found. Install PostgreSQL client tools or set PG_DUMP_PATH.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        fd, backup_path = tempfile.mkstemp(prefix="quantumways_db_", suffix=".sql")
        os.close(fd)

        # Neon requires pg_dump to connect to the direct host, not the pooler.
        host = str(db.get("HOST") or "")
        if host.endswith(".neon.tech"):
            host = host.replace("-pooler.", ".")

        env = os.environ.copy()
        env["PGHOST"] = host
        env["PGPORT"] = str(db.get("PORT") or "")
        env["PGUSER"] = str(db.get("USER") or "")
        env["PGDATABASE"] = str(db["NAME"])
        if db.get("PASSWORD"):
            env["PGPASSWORD"] = str(db["PASSWORD"])

        options = db.get("OPTIONS") or {}
        if options.get("sslmode"):
            env["PGSSLMODE"] = str(options["sslmode"])
        if options.get("channel_binding"):
            env["PGCHANNELBINDING"] = str(options["channel_binding"])

        try:
            result = subprocess.run(
                [
                    pg_dump,
                    "--format=plain",
                    "--no-owner",
                    "--no-privileges",
                    "--no-password",
                    "--file",
                    backup_path,
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            _remove(backup_path)
            logger.error("Database export timed out")
            return response_message_utils(
                message="Database export timed out.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            _remove(backup_path)
            logger.exception("Database export failed")
            return response_message_utils(
                message="Database export failed.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if result.returncode != 0:
            _remove(backup_path)
            logger.error("pg_dump failed: %s", result.stderr)
            return response_message_utils(
                message="Database export failed.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        def file_chunks():
            try:
                with open(backup_path, "rb") as backup:
                    while chunk := backup.read(64 * 1024):
                        yield chunk
            finally:
                _remove(backup_path)

        filename = f"quantumways_db_{datetime.now():%Y%m%d_%H%M%S}.sql"
        response = StreamingHttpResponse(file_chunks(), content_type="application/sql")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "no-store"
        return response
