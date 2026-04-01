import subprocess
import sys
from pathlib import Path


def test_evaluation_script_runs():
    script = Path(__file__).resolve().parents[2] / "scripts" / "evaluate_accuracy.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, check=True)
    assert "CareerPilot 评估结果" in result.stdout

