"""
Dynamic call test for Rabt (runtime vs static).

This file is designed so that static analysis CANNOT see the call to
`secret_function`, but the runtime tracer can. It demonstrates that
Rabt's hybrid static+runtime graph finds edges that a pure AST parser
misses.
"""

import sys
from pathlib import Path

# Add project root so `runtime.tracer` can be imported when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runtime.tracer import track_runtime


@track_runtime
def secret_function() -> None:
    print("I was called dynamically!")


def main() -> None:
    # Static analysis sees "globals()[func_name]" but does NOT see a direct call
    # to `secret_function`. The actual target is decided at runtime.
    func_name = "secret_" + "function"
    method = globals()[func_name]
    method()  # The call happens here dynamically.


if __name__ == "__main__":
    main()

