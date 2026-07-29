# CN rule-sets for sing-box (+ dae)

| Rule-set | Content | Source | Use for |
| --- | --- | --- | --- |
| `geosite-cn` | 备案 CN domains (`domain_suffix`) | [cn-additional-list](https://static-file-global.353355.xyz/rules/cn-additional-list.txt) | DNS + routing → direct |
| `geosite-cndns` | accelerated-china domains (`domain_suffix`) | [felixonmars/dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) | DNS only |
| `geoip-cn` | CN IPv4 + IPv6 (`ip_cidr`) | [gaoyifan/china-operator-ip](https://github.com/gaoyifan/china-operator-ip) | routing → direct |

Each ships as `.json` + `.srs` (sing-box) and `.dat` (dae, tags `cn` / `cndns` / `CN`) under
[`rules/`](rules).
