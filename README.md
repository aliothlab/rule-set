# CN rule-sets for sing-box

[sing-box](https://sing-box.sagernet.org/) rule-sets for mainland China, rebuilt daily
via GitHub Actions against the **latest sing-box prerelease** (alpha/beta). The JSON
schema `version` is auto-detected from the installed sing-box, so it always tracks the
newest rule-set format that prerelease supports.

| Rule-set | Type | Source |
| --- | --- | --- |
| `geosite-cn` | `domain_suffix` | mainland-China ICP 备案 domain list |
| `geoip-cn` | `ip_cidr` (IPv4 **+** IPv6) | [gaoyifan/china-operator-ip](https://github.com/gaoyifan/china-operator-ip) (BGP, by-operator) |

Both are meant to be routed to **direct**.

## Files

- `rules/geosite-cn.json` / `rules/geosite-cn.srs` — CN domains
- `rules/geoip-cn.json` / `rules/geoip-cn.srs` — CN IPs, v4 and v6 combined in one rule-set

## Usage

Example for a current sing-box (≥ 1.14, matching the prerelease this repo builds against).
`http_client.detour` replaces the deprecated `download_detour`, and the route rule uses the
explicit `action: "route"`:

```jsonc
{
  "route": {
    "rule_set": [
      {
        "type": "remote",
        "tag": "geosite-cn",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/aliothlab/rule-set/main/rules/geosite-cn.srs",
        "http_client": { "detour": "proxy" },
        "update_interval": "1d"
      },
      {
        "type": "remote",
        "tag": "geoip-cn",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/aliothlab/rule-set/main/rules/geoip-cn.srs",
        "http_client": { "detour": "proxy" },
        "update_interval": "1d"
      }
    ],
    "rules": [
      { "rule_set": ["geosite-cn", "geoip-cn"], "action": "route", "outbound": "direct" }
    ]
  }
}
```

> On older sing-box (< 1.14) use `"download_detour": "proxy"` instead of `http_client`.

## Build

```bash
python3 build.py    # writes rules/geosite-cn.json and rules/geoip-cn.json
sing-box rule-set compile --output rules/geosite-cn.srs rules/geosite-cn.json
sing-box rule-set compile --output rules/geoip-cn.srs   rules/geoip-cn.json
```

Rebuilt daily at 20:30 UTC (04:30 Asia/Shanghai); all four files are committed to the repo.
