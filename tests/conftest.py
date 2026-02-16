import sys
from pathlib import Path

# Add src/ to the Python path so tests can import MCP server modules.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
