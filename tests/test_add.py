# tests/test_add.py
from typer.testing import CliRunner
from idflow.app import app
from pathlib import Path

runner = CliRunner()

def test_add_creates_file(tmp_path: Path):
    result = runner.invoke(app, ["doc","add","--set","title=Test","--base-dir",str(tmp_path)])
    assert result.exit_code == 0
    # assert auf erzeugte Datei…

