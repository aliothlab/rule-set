import ipaddress
import json
import os
import urllib.request

GEOSITE_CN_URL = "https://static-file-global.353355.xyz/rules/cn-additional-list.txt"
GEOSITE_CNDNS_URL = ("https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/"
                     "master/accelerated-domains.china.conf")
GEOIP_V4_URL = "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/ip-lists/china.txt"
GEOIP_V6_URL = "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/ip-lists/china6.txt"

GEOSITE_CN = ("rules/geosite-cn.json", "rules/geosite-cn.dat", "cn")
GEOSITE_CNDNS = ("rules/geosite-cndns.json", "rules/geosite-cndns.dat", "cndns")
GEOIP_JSON, GEOIP_DAT, GEOIP_TAG = "rules/geoip-cn.json", "rules/geoip-cn.dat", "CN"
GEOIP_TXT = "rules/cn-v{}.txt"

MIN_DOMAINS, MIN_V4, MIN_V6 = 1000, 1000, 100
RULESET_VERSION = 2
ROOT_DOMAIN = 2


def fetch(url, retries=3):
    last = None
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rule-set-build/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as exc:
            last = exc
    raise SystemExit(f"failed to fetch {url}: {last}")


def _varint(value):
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if not value:
            out.append(byte)
            return bytes(out)
        out.append(byte | 0x80)


def _pb_varint(field, value):
    return _varint(field << 3) + _varint(value)


def _pb_bytes(field, data):
    return _varint((field << 3) | 2) + _varint(len(data)) + data


def _pb_string(field, text):
    return _pb_bytes(field, text.encode("utf-8"))


def encode_geosite_dat(tag, domains):
    parts = [_pb_string(1, tag)]
    for domain in domains:
        parts.append(_pb_bytes(2, _pb_varint(1, ROOT_DOMAIN) + _pb_string(2, domain)))
    return _pb_bytes(1, b"".join(parts))


def encode_geoip_dat(tag, cidrs):
    parts = [_pb_string(1, tag)]
    for packed, prefix in cidrs:
        parts.append(_pb_bytes(2, _pb_bytes(1, packed) + _pb_varint(2, prefix)))
    return _pb_bytes(1, b"".join(parts))


def write(path, data, binary=False):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb" if binary else "w", encoding=None if binary else "utf-8") as f:
        f.write(data)


def write_ruleset(path, rule):
    write(path, json.dumps({"version": RULESET_VERSION, "rules": [rule]},
                           ensure_ascii=False, indent=2) + "\n")


def normalize(domain):
    return domain.strip().lower().lstrip("*+").strip(".")


def parse_plain(text):
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            yield line


def parse_dnsmasq(text):
    for line in text.splitlines():
        parts = line.strip().split("/")
        if len(parts) >= 3 and parts[0] in ("server=", "address=") and parts[1]:
            yield parts[1]


def collect(text, parser):
    return {d for d in (normalize(t) for t in parser(text)) if d}


def dedup(domains):
    def covered(domain):
        labels = domain.split(".")
        return any(".".join(labels[i:]) in domains for i in range(1, len(labels)))

    minimal = sorted(d for d in domains if not covered(d))
    return minimal, len(domains) - len(minimal)


def parse_cidrs(text):
    seen, nets = set(), []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            net = ipaddress.ip_network(line.split()[0], strict=False)
        except ValueError:
            continue
        if str(net) not in seen:
            seen.add(str(net))
            nets.append(net)
    return nets

def write_cidr_txt(nets, version):
    lines = sorted(n for n in nets if n.version == version)
    write(GEOIP_TXT.format(version), "".join(f"{n}\n" for n in lines))
    return len(lines)

def build_geosite(url, parser, json_path, dat_path, tag):
    domains = collect(fetch(url), parser)
    if len(domains) < MIN_DOMAINS:
        raise SystemExit(f"only {len(domains)} domains parsed from {url} (< {MIN_DOMAINS})")
    domains, redundant = dedup(domains)
    write_ruleset(json_path, {"domain_suffix": domains})
    write(dat_path, encode_geosite_dat(tag, domains), binary=True)
    print(f"wrote {json_path} + {dat_path}: {len(domains)} domain_suffix "
          f"({redundant} redundant subdomains removed)")


def build_geoip():
    v4, v6 = parse_cidrs(fetch(GEOIP_V4_URL)), parse_cidrs(fetch(GEOIP_V6_URL))
    if len(v4) < MIN_V4:
        raise SystemExit(f"only {len(v4)} IPv4 CIDRs parsed (< {MIN_V4})")
    if len(v6) < MIN_V6:
        raise SystemExit(f"only {len(v6)} IPv6 CIDRs parsed (< {MIN_V6})")
    txt4, txt6 = write_cidr_txt(v4, 4), write_cidr_txt(v6, 6)
    print(f"wrote {GEOIP_TXT.format(4)} + {GEOIP_TXT.format(6)}: {txt4} v4 + {txt6} v6 CIDRs")
    nets = sorted(v4 + v6, key=lambda n: (n.version, int(n.network_address), n.prefixlen))
    write_ruleset(GEOIP_JSON, {"ip_cidr": [str(n) for n in nets]})
    write(GEOIP_DAT,
          encode_geoip_dat(GEOIP_TAG, [(n.network_address.packed, n.prefixlen) for n in nets]),
          binary=True)
    print(f"wrote {GEOIP_JSON} + {GEOIP_DAT}: {len(v4)} v4 + {len(v6)} v6 ip_cidr")


def main():
    build_geoip()
    build_geosite(GEOSITE_CN_URL, parse_plain, *GEOSITE_CN)
    build_geosite(GEOSITE_CNDNS_URL, parse_dnsmasq, *GEOSITE_CNDNS)


if __name__ == "__main__":
    main()
