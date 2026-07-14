import json
import os
import shutil
import subprocess
import tempfile
import urllib.request

SOURCE_URL = os.environ.get(
    "SOURCE_URL",
    "https://static-file-global.353355.xyz/rules/cn-additional-list.txt",
)
OUT_JSON = os.environ.get("OUT_JSON", "rules/geosite-cn.json")
MIN_ENTRIES = int(os.environ.get("MIN_ENTRIES", "1000"))
VERSION_CEILING = int(os.environ.get("VERSION_CEILING", "15"))
FALLBACK_VERSION = int(os.environ.get("FALLBACK_VERSION", "3"))


def fetch(url, retries=3):
    last = None
    for _ in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "geosite-cn-singbox/1.0"}
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as exc:
            last = exc
    raise SystemExit(f"failed to fetch {url}: {last}")


def detect_version():
    env = os.environ.get("RULESET_VERSION")
    if env:
        return int(env)
    sb = shutil.which("sing-box")
    if not sb:
        return FALLBACK_VERSION
    for v in range(VERSION_CEILING, 1, -1):
        src = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        src.write(json.dumps({"version": v, "rules": [{"domain_suffix": ["a.com"]}]}))
        src.close()
        out = src.name + ".srs"
        code = subprocess.run(
            [sb, "rule-set", "compile", "--output", out, src.name],
            capture_output=True,
        ).returncode
        os.unlink(src.name)
        if os.path.exists(out):
            os.unlink(out)
        if code == 0:
            return v
    return FALLBACK_VERSION


def parse(text):
    seen = set()
    out = []
    for line in text.splitlines():
        s = line.strip().lower()
        if not s or s.startswith("#"):
            continue
        s = s.lstrip("+").lstrip(".")
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    out.sort()
    return out


def main():
    domains = parse(fetch(SOURCE_URL))
    if len(domains) < MIN_ENTRIES:
        raise SystemExit(f"only {len(domains)} domains parsed (< {MIN_ENTRIES})")
    version = detect_version()
    ruleset = {"version": version, "rules": [{"domain_suffix": domains}]}
    os.makedirs(os.path.dirname(OUT_JSON) or ".", exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(ruleset, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    print(f"wrote {OUT_JSON}: {len(domains)} domain_suffix entries (version {version})")


if __name__ == "__main__":
    main()
