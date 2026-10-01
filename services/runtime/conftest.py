"""Garante que a raiz do repositorio esteja no sys.path para `import nexum`."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
