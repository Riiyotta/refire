#!/usr/bin/env python3
"""Build ../design-repo.zip (next to this design-repo folder) with the CLI `zip` tool.

Run LAST, after verify_all.py and the adversarial suite pass, and again after every
change: a zip older than any file in the folder is stale. The archive is staged in the
OS temp dir and excludes OS/tool junk (__MACOSX, .DS_Store, Thumbs.db, desktop.ini,
__pycache__, *.pyc). Never commit the zip next to the live folder.
"""
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT = os.path.dirname(REPO)
NAME = os.path.basename(REPO)
EXCLUDE = ["*/__MACOSX/*", "*.DS_Store", "*/Thumbs.db", "*/desktop.ini", "*/__pycache__/*", "*.pyc"]
JUNK = ("__MACOSX", ".DS_Store", "Thumbs.db", "desktop.ini", "__pycache__", ".pyc")


def main():
    if not shutil.which("zip") or not shutil.which("unzip"):
        print("the CLI `zip`/`unzip` tools are required (never use a GUI archiver: it injects OS metadata)")
        return 2
    stage = tempfile.mkdtemp(prefix="refire-zip-")
    try:
        tmpzip = os.path.join(stage, NAME + ".zip")
        subprocess.check_call(["zip", "-r", "-X", "-q", tmpzip, NAME, "-x"] + EXCLUDE, cwd=PARENT)
        listing = subprocess.check_output(["unzip", "-l", tmpzip], universal_newlines=True)
        bad = [l for l in listing.splitlines() if any(j in l for j in JUNK)]
        if bad:
            print("junk in archive:\n" + "\n".join(bad))
            return 1
        out = os.path.join(PARENT, NAME + ".zip")
        if os.path.exists(out):
            os.remove(out)
        shutil.move(tmpzip, out)
        entries = listing.strip().splitlines()[-1]
        print("wrote %s.zip next to the design-repo folder (%s)" % (NAME, entries.strip()))
        return 0
    finally:
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
