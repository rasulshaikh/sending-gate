"""sending-gate: pre-send PASS/FLAG/FAIL core for Clay outbound exports."""

from .gate import evaluate_batch, evaluate_row

__all__ = ["evaluate_row", "evaluate_batch"]
__version__ = "0.1.0"
