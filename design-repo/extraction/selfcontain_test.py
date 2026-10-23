#!/usr/bin/env python3
"""Self-containment proof: copy this design-repo ALONE into a fresh directory under
the OS temp dir (no sibling source tree), then run every script there.

Run:  python3 extraction/selfcontain_test.py
Passes only if verify_all.py, semantic_validate.py and adversarial_test.py all exit 0
in the isolated copy, i.e. there is no hidden dependency on the clone project or on
a hardcoded path.
"""
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    tmp = tempfile.mkdtemp(prefix="refire-selfcontain-")
    try:
        dest = os.path.join(tmp, "design-repo")
        shutil.copytree(REPO, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        siblings = sorted(os.listdir(tmp))
        print("isolated copy: <OS temp>/%s/design-repo   siblings in its parent: %s" % (os.path.basename(tmp), siblings))
        if siblings != ["design-repo"]:
            print("FAIL: parent directory is not empty")
            return 1
        ok = True
        for rel in ("extraction/verify_all.py", "schema/semantic_validate.py", "schema/tests/adversarial_test.py"):
            p = subprocess.run([sys.executable, "-B", os.path.join(dest, rel)], cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            print("\n===== %s  (exit %d) =====" % (rel, p.returncode))
            print(p.stdout.replace(tmp, "<OS temp>/" + os.path.basename(tmp)).rstrip())
            ok &= p.returncode == 0
        print("\nselfcontain: %s" % ("PASS - every script passes with no sibling source tree" if ok else "FAIL"))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
