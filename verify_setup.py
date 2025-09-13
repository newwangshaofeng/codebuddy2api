#!/usr/bin/env python3
"""
verify_setup.py
- Confirms Python >= 3.8
- Attempts to import core dependencies and reports status
- Exits non-zero if any checks fail
"""
import importlib
import sys

MIN_VERSION = (3, 8)
MODULES = [
    ("fastapi", None),
    ("hypercorn", None),
    ("httpx", None),
    ("pydantic", None),
]

def check_python() -> bool:
    ok = sys.version_info[:2] >= MIN_VERSION
    found = sys.version.split()[0]
    if ok:
        print(f"[OK] Python version: {found}")
    else:
        print(f"[FAIL] Python {MIN_VERSION[0]}.{MIN_VERSION[1]}+ required, found: {found}")
    return ok


def check_modules() -> bool:
    all_ok = True
    for mod, attr in MODULES:
        try:
            m = importlib.import_module(mod)
            if attr:
                getattr(m, attr)
            print(f"[OK] Import: {mod}")
        except Exception as e:
            print(f"[FAIL] Import {mod}: {e}")
            all_ok = False
    return all_ok


def main() -> None:
    ok = True
    ok &= check_python()
    ok &= check_modules()
    if ok:
        print("\nEnvironment looks good.")
        sys.exit(0)
    else:
        print("\nEnvironment verification failed. See messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
