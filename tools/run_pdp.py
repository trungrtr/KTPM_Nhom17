"""Isolated PDP entry point: reuse driver, preserve all shared/REG/LOG reports."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument("-k", default="")
    parser.add_argument("-x", action="store_true")
    args = parser.parse_args()
    import pytest
    from utils import pdp_reporting
    options = [str(ROOT / "tests" / "test_chi_tiet_san_pham.py"),
               "--noconftest", "-p", "no:cacheprovider", "-o", "addopts=", "-v", "-ra", "--tb=short"]
    if args.offline:
        options.append("--pdp-offline")
    if args.collect_only:
        options.append("--collect-only")
    if args.k:
        options.extend(["-k", args.k])
    if args.x:
        options.append("-x")
    return pytest.main(options, plugins=[pdp_reporting])


if __name__ == "__main__":
    raise SystemExit(main())
