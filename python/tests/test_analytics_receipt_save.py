"""Post-COMMIT local storage failure must report the recoverable durable identity."""

import pytest
from analyst_os_ingestion.snapshot import SnapshotError

from scripts import publish_reported_analytics as cli


def test_receipt_save_failure_reports_commit_and_import_without_raw_error(tmp_path, monkeypatch):
    def disk_failure(*_args):
        raise OSError("TEST ONLY sensitive transport diagnostic")

    monkeypatch.setattr(cli, "write_private", disk_failure)
    result = {"receipt": {"import_id": "00000000-0000-0000-0000-000000000001"}}
    with pytest.raises(SnapshotError, match="database commit confirmed") as error:
        cli.save_committed_receipt(tmp_path, result)
    assert "import_id=00000000-0000-0000-0000-000000000001" in str(error.value)
    assert "sensitive" not in str(error.value)
