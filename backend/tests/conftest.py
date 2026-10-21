import sys
from pathlib import Path

# Add src to path so imports work
backend_root = Path(__file__).parent.parent
src_path = backend_root / 'src'
sys.path.insert(0, str(src_path))

pytest_plugins = ('pytest_asyncio',)
