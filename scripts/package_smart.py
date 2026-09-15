#!/usr/bin/env python3
"""Use the inherited archive safety verifier with the canonical current role set.

The legacy packager duplicates the six-role list. All traversal, completeness,
checksum, marker and runtime validation stays intact; only role membership is
sourced from runtime.layout so simple_executor is a required supported member.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'codex_workflow'))
from runtime.layout import BUILTIN_WORKERS
import package_release
package_release.BUILTIN_WORKERS=BUILTIN_WORKERS
if __name__=='__main__':
    raise SystemExit(package_release.main())
