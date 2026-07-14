# geosite-cn for sing-box

A [sing-box](https://sing-box.sagernet.org/) `geosite-cn` rule-set built from the
mainland-China ICP 备案 domain list, rebuilt daily via GitHub Actions against the
**latest sing-box alpha**. Every entry is a `domain_suffix`; route it to **direct**.

The JSON schema `version` is auto-detected from the installed sing-box, so it always
tracks the newest rule-set format the alpha supports.

## Files

- `rules/geosite-cn.json` — rule-set source (JSON)
- `rules/geosite-cn.srs` — rule-set binary (SRS)

## Usage

```jsonc
{
  "type": "remote",
  "tag": "geosite-cn",
  "format": "binary",
  "url": "https://raw.githubusercontent.com/<user>/<repo>/main/rules/geosite-cn.srs",
  "download_detour": "proxy",
  "update_interval": "1d"
}
```

Then add a route rule: `{ "rule_set": "geosite-cn", "outbound": "direct" }`.

## Build

```bash
python3 build.py
sing-box rule-set compile --output rules/geosite-cn.srs rules/geosite-cn.json
```

Rebuilt daily at 20:30 UTC (04:30 Asia/Shanghai); both files are committed to the repo.
