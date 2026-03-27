from __future__ import annotations

import subprocess
import sys
from pathlib import Path


_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "validate_k8s_env_sources.py"


def test_validator_reports_env_index_and_name_for_dual_source_item(tmp_path: Path) -> None:
    manifest = tmp_path / "bad-deployment.yaml"
    manifest.write_text(
        "\n".join(
            [
                "apiVersion: apps/v1",
                "kind: Deployment",
                "metadata:",
                "  name: bad",
                "spec:",
                "  template:",
                "    spec:",
                "      containers:",
                "        - name: api",
                "          env:",
                "            - name: TEST_ENV",
                "              value: explicit",
                "              valueFrom:",
                "                secretKeyRef:",
                "                  name: app-secret",
                "                  key: TEST_ENV",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_SCRIPT_PATH), str(manifest)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "env[0] 'TEST_ENV' defines both value and valueFrom" in result.stderr
    assert str(manifest) in result.stderr


def test_validator_accepts_single_source_env_items(tmp_path: Path) -> None:
    manifest = tmp_path / "good-deployment.yaml"
    manifest.write_text(
        "\n".join(
            [
                "apiVersion: apps/v1",
                "kind: Deployment",
                "metadata:",
                "  name: good",
                "spec:",
                "  template:",
                "    spec:",
                "      containers:",
                "        - name: api",
                "          env:",
                "            - name: VALUE_ENV",
                "              value: explicit",
                "            - name: SECRET_ENV",
                "              valueFrom:",
                "                secretKeyRef:",
                "                  name: app-secret",
                "                  key: SECRET_ENV",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_SCRIPT_PATH), str(manifest)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "[OK] validated 1 manifest file(s): env items use a single source." in result.stdout
