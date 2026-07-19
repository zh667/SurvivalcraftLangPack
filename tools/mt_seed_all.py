#!/usr/bin/env python3
"""Machine-translate the base-game English source into many languages (draft)."""
import json, re, time, os, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "source", "en-US.json")
LANGDIR = os.path.join(ROOT, "Assets", "Lang")

# (filename code, google MT code, endonym for Language.Name)
LANGS = [
    ("id-ID", "id", "Bahasa Indonesia"),
    ("tr-TR", "tr", "Türkçe"),
    ("ja-JP", "ja", "日本語"),
    ("ko-KR", "ko", "한국어"),
    ("fr-FR", "fr", "Français"),
    ("de-DE", "de", "Deutsch"),
    ("it-IT", "it", "Italiano"),
    ("pl-PL", "pl", "Polski"),
    ("hi-IN", "hi", "हिन्दी"),
    ("th-TH", "th", "ไทย"),
    ("uk-UA", "uk", "Українська"),
    ("ar-SA", "ar", "العربية"),
]

PLACEHOLDER = re.compile(r"\{[^}]*\}")
TRIVIAL = re.compile(r"^[\s\d\W]*$")

def should_translate(s):
    return isinstance(s, str) and s.strip() and not TRIVIAL.match(s)

base = json.load(open(SRC, encoding="utf-8"))

# collect unique translatable strings once
uniq = []
seen = set()
def walk_collect(o):
    if isinstance(o, dict):
        for v in o.values(): walk_collect(v)
    elif isinstance(o, list):
        for v in o: walk_collect(v)
    elif isinstance(o, str) and should_translate(o) and o not in seen:
        seen.add(o); uniq.append(o)
walk_collect(base)
print(f"unique translatable strings: {len(uniq)}", flush=True)

def mt_batch(lines, tl):
    q = "\n".join(x.replace("\n", " ").replace("\r", " ") for x in lines)
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={tl}&dt=t"
    body = urllib.parse.urlencode({"q": q}).encode()
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.loads(r.read().decode("utf-8"))
            out = "".join(seg[0] for seg in d[0] if seg and seg[0] is not None)
            parts = out.split("\n")
            if len(parts) == len(lines):
                return parts
            return None
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None

def ph_ok(src, tgt):
    return PLACEHOLDER.findall(src) == PLACEHOLDER.findall(tgt)

def build_lang(file_code, tl, endonym):
    out_path = os.path.join(LANGDIR, f"{file_code}.json")
    if os.path.exists(out_path):
        try:
            existing = json.load(open(out_path, encoding="utf-8"))
            n = sum(1 for _ in re.finditer(r'"', json.dumps(existing)))  # cheap non-empty check
            print(f"[{file_code}] already exists, skipping", flush=True)
            return
        except Exception:
            pass
    print(f"[{file_code}] translating via tl={tl} ...", flush=True)
    tmap = {}
    BATCH = 40
    for i in range(0, len(uniq), BATCH):
        chunk = uniq[i:i+BATCH]
        res = mt_batch(chunk, tl)
        if res is None:
            res = []
            for s in chunk:
                r = mt_batch([s], tl)
                res.append(r[0] if r else s)
        for s, t in zip(chunk, res):
            t = (t or "").strip()
            if not t or not ph_ok(s, t):
                t = s  # keep English if translation empty or broke a placeholder
            tmap[s] = t
        if (i // BATCH) % 10 == 0:
            print(f"  [{file_code}] {min(i+BATCH,len(uniq))}/{len(uniq)}", flush=True)
        time.sleep(0.15)
    # rebuild structure
    data = json.loads(json.dumps(base))  # deep copy
    def apply(o):
        if isinstance(o, dict):
            for k, v in list(o.items()):
                if isinstance(v, (dict, list)): apply(v)
                elif isinstance(v, str) and should_translate(v): o[k] = tmap.get(v, v)
        elif isinstance(o, list):
            for idx, v in enumerate(o):
                if isinstance(v, (dict, list)): apply(v)
                elif isinstance(v, str) and should_translate(v): o[idx] = tmap.get(v, v)
    apply(data)
    if isinstance(data.get("Language"), dict):
        data["Language"]["Name"] = endonym
    json.dump(data, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[{file_code}] DONE -> {out_path}", flush=True)

for file_code, tl, endonym in LANGS:
    try:
        build_lang(file_code, tl, endonym)
    except Exception as e:
        print(f"[{file_code}] FAILED: {e}", flush=True)

print("ALL DONE", flush=True)
