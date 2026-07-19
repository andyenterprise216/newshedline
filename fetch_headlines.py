#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日米中の新聞見出しまとめページ生成スクリプト
- feeds.json に書かれた RSS/Atom フィードから見出しを取得し、
  site/index.html に1枚のページとして書き出します。
- 依存ライブラリなし（Python 3.9+ の標準ライブラリのみで動作）。
- 一部のフィードが取得失敗しても止まらず、ページ上に失敗を表示します。
"""

import gzip
import html
import io
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "feeds.json")
OUT_DIR = os.path.join(BASE_DIR, "site")
OUT_PATH = os.path.join(OUT_DIR, "index.html")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 HeadlineDigest/1.0"
)
JST = timezone(timedelta(hours=9))


def fetch_bytes(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
            "Accept-Encoding": "gzip, deflate",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    # gzip / deflate を透過的に展開
    if data[:2] == b"\x1f\x8b":
        data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
    else:
        try:
            enc = resp.headers.get("Content-Encoding", "")
            if "deflate" in enc:
                data = zlib.decompress(data)
        except Exception:
            pass
    return data


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def child_text(elem, name: str):
    for c in elem:
        if local_name(c.tag) == name and c.text:
            return c.text.strip()
    return None


def child_link(elem):
    """RSS の <link>テキスト / Atom の <link href="..."> の両方に対応"""
    for c in elem:
        if local_name(c.tag) == "link":
            if c.text and c.text.strip():
                return c.text.strip()
            href = c.get("href")
            rel = c.get("rel", "alternate")
            if href and rel in ("alternate", ""):
                return href
    return None


def parse_feed(data: bytes):
    """RSS 2.0 / RSS 1.0 (RDF) / Atom を解析して [(title, link), ...] を返す"""
    root = ET.fromstring(data)
    entries = []
    for elem in root.iter():
        name = local_name(elem.tag)
        if name in ("item", "entry"):
            title = child_text(elem, "title")
            link = child_link(elem)
            if title:
                entries.append((title, link))
    return entries


def collect(config):
    now = datetime.now(JST)
    max_items = int(config.get("max_items_per_feed", 8))
    timeout = int(config.get("timeout_seconds", 20))
    results = []
    ok_count = fail_count = 0

    for section in config.get("sections", []):
        sec = {"name": section.get("name", ""), "feeds": []}
        for feed in section.get("feeds", []):
            if not feed.get("enabled", True):
                continue
            entry = {
                "name": feed.get("name", feed.get("url", "?")),
                "note": feed.get("note"),
                "url": feed.get("url", ""),
                "items": [],
                "error": None,
            }
            try:
                data = fetch_bytes(entry["url"], timeout)
                items = parse_feed(data)
                seen = set()
                for title, link in items:
                    key = title.strip()
                    if key and key not in seen:
                        seen.add(key)
                        entry["items"].append({"title": key, "link": link})
                    if len(entry["items"]) >= max_items:
                        break
                if not entry["items"]:
                    entry["error"] = "フィードは取得できましたが記事が見つかりませんでした"
            except Exception as e:
                entry["error"] = f"取得失敗: {type(e).__name__}"
            if entry["error"] and not entry["items"]:
                fail_count += 1
                print(f"  [NG] {entry['name']}: {entry['error']} ({entry['url']})")
            else:
                ok_count += 1
                print(f"  [OK] {entry['name']}: {len(entry['items'])}件")
            sec["feeds"].append(entry)
        results.append(sec)

    print(f"\n取得結果: 成功 {ok_count} / 失敗 {fail_count}")
    return now, results


CSS = """
:root { --bg:#f6f5f1; --card:#ffffff; --ink:#1c1c1c; --sub:#6b6b6b;
        --line:#e4e1d8; --accent:#8a1f1f; --link:#1a4a7a; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#171614; --card:#211f1c; --ink:#eceae4; --sub:#9b978d;
          --line:#38352e; --accent:#d98282; --link:#8ab6e0; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
  font-family:"Hiragino Mincho ProN","Yu Mincho","Noto Serif JP",Georgia,serif; }
.wrap { max-width: 860px; margin: 0 auto; padding: 24px 16px 64px; }
header { border-bottom: 3px double var(--ink); padding-bottom: 14px; margin-bottom: 8px; }
h1 { font-size: 1.7rem; margin: 0; letter-spacing: .06em; }
.updated { color: var(--sub); font-size: .85rem; margin-top: 6px;
  font-family:-apple-system,"Hiragino Sans","Yu Gothic",sans-serif; }
h2.section { font-size: 1.15rem; letter-spacing: .2em; color: var(--accent);
  border-left: 5px solid var(--accent); padding-left: 10px; margin: 34px 0 12px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  padding: 14px 18px; margin-bottom: 14px; }
h3.paper { font-size: 1.0rem; margin: 0 0 8px; padding-bottom: 6px;
  border-bottom: 1px solid var(--line); }
.note { font-size: .72rem; color: var(--sub); font-weight: normal; margin-left: 8px;
  font-family:-apple-system,"Hiragino Sans","Yu Gothic",sans-serif; }
ul.headlines { list-style: none; margin: 0; padding: 0; }
ul.headlines li { padding: 5px 0 5px 1em; text-indent: -1em; line-height: 1.55;
  font-size: .95rem; }
ul.headlines li::before { content: "・"; color: var(--accent); }
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }
.error { color: #a05252; font-size: .85rem;
  font-family:-apple-system,"Hiragino Sans","Yu Gothic",sans-serif; }
footer { margin-top: 40px; color: var(--sub); font-size: .78rem; text-align: center;
  border-top: 1px solid var(--line); padding-top: 14px;
  font-family:-apple-system,"Hiragino Sans","Yu Gothic",sans-serif; }
"""


def render_html(now, sections) -> str:
    e = html.escape
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="ja"><head><meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    parts.append("<title>今日の見出し ─ 日・米・中</title>")
    parts.append(f"<style>{CSS}</style></head><body>")
    parts.append('<div class="wrap">')
    parts.append("<header><h1>今日の見出し ─ 日・米・中</h1>")
    parts.append(
        f'<div class="updated">最終更新: {now.strftime("%Y年%m月%d日 %H:%M")} (日本時間)</div>'
    )
    parts.append("</header>")

    for sec in sections:
        parts.append(f'<h2 class="section">{e(sec["name"])}</h2>')
        for feed in sec["feeds"]:
            parts.append('<div class="card">')
            note = f'<span class="note">{e(feed["note"])}</span>' if feed.get("note") else ""
            parts.append(f'<h3 class="paper">{e(feed["name"])}{note}</h3>')
            if feed["items"]:
                parts.append('<ul class="headlines">')
                for it in feed["items"]:
                    t = e(it["title"])
                    if it.get("link"):
                        parts.append(
                            f'<li><a href="{e(it["link"])}" target="_blank" rel="noopener">{t}</a></li>'
                        )
                    else:
                        parts.append(f"<li>{t}</li>")
                parts.append("</ul>")
            else:
                parts.append(f'<div class="error">⚠ {e(feed["error"] or "不明なエラー")}</div>')
            parts.append("</div>")

    parts.append(
        "<footer>各新聞社のRSSフィードから自動生成 / 見出しの著作権は各社に帰属します<br>"
        "このページは GitHub Actions により毎朝自動更新されます</footer>"
    )
    parts.append("</div></body></html>")
    return "\n".join(parts)


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else CONFIG_PATH
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    print("フィード取得を開始します…\n")
    now, sections = collect(config)
    os.makedirs(OUT_DIR, exist_ok=True)
    html_text = render_html(now, sections)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_text)
    print(f"\n生成完了: {OUT_PATH}")
    # 全フィード失敗時のみ異常終了(通知に気づけるように)
    total = sum(len(s["feeds"]) for s in sections)
    failed = sum(1 for s in sections for fd in s["feeds"] if not fd["items"])
    if total > 0 and failed == total:
        print("すべてのフィードが取得失敗でした", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
