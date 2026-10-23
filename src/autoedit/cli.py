from __future__ import annotations

import sys

from .runtime import configure_runtime_storage


def main() -> None:
    configure_runtime_storage()
    from .gui import launch

    sys.exit(launch())


if __name__ == "__main__":
    main()
