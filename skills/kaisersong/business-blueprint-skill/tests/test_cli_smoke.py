import subprocess
import sys
from pathlib import Path

import pytest

from business_blueprint.export_integrity import ExportIntegrityError, ExportIntegrityFailure


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "business_blueprint.cli", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_cli_help_lists_supported_commands() -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    assert "--plan" in result.stdout
    assert "--project" in result.stdout
    assert "--generate" in result.stdout
    assert "--validate" in result.stdout


def test_cli_export_returns_structured_diagnostics_on_integrity_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from business_blueprint import cli as cli_module

    blueprint = tmp_path / "solution.blueprint.json"
    blueprint.write_text(
        '{"meta":{"title":"Broken"},"library":{"capabilities":[],"actors":[],"flowSteps":[],"systems":[]},"relations":[]}',
        encoding="utf-8",
    )

    def fake_export_svg_auto(*args, **kwargs):
        del args, kwargs
        raise ExportIntegrityError(
            ExportIntegrityFailure(
                requested_route="poster",
                attempted_route="freeflow",
                fallback_route="freeflow",
                terminal_reason="integrity_failed_after_fallback",
                errors=[{"kind": "canvas_clipping", "axis": "y", "actual": 110.0, "limit": 100.0}],
            )
        )

    monkeypatch.setattr(cli_module, "export_svg_auto", fake_export_svg_auto)
    monkeypatch.setattr(cli_module.sys, "argv", ["business-blueprint", "--export", str(blueprint)])

    exit_code = cli_module.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert '"kind": "export_integrity_failure"' in captured.err
    assert '"terminalReason": "integrity_failed_after_fallback"' in captured.err
