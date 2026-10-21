import os
from pathlib import Path

os.environ["STATIC_DIR"] = str(Path(__file__).parent / "static")
