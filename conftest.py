import sys
from pathlib import Path

# The MEPS example lives under examples/meps (package `meps`); put examples/ on the
# path so its tests can import it. The library itself never depends on this.
sys.path.insert(0, str(Path(__file__).parent / "examples"))
