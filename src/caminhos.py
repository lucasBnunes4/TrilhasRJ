"""Localização dos dados no código-fonte e no aplicativo empacotado."""
from pathlib import Path
import sys

PASTA = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
