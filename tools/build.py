#!/usr/bin/env python3
"""Package the language pack into a .netmod (plain zip) with all lang files."""
import os, glob, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "artifacts", "SurvivalcraftLangPack.netmod")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
langs = sorted(glob.glob(os.path.join(ROOT, "Assets", "Lang", "*.json")))
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(ROOT, "modinfo.json"), "modinfo.json")
    for f in langs:
        z.write(f, os.path.relpath(f, ROOT))
print("built", OUT, os.path.getsize(OUT), "bytes;", len(langs), "languages")
