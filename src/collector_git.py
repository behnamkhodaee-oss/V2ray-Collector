#!/usr/bin/env python3
import os
import asyncio
import aiohttp
import aiosqlite
import re
import json
import time
import base64
from datetime import datetime, timezone
from dotenv import load_dotenv

# ============================
# ⚙️ تنظیمات
# ============================

CONFIG_DEFAULTS = {
    "GENERAL_CONCURRENT_REQUESTS": 50,
    "AIOHTTP_CONNECTION_LIMIT": 50,
    "MAX_FILE_BYTES": 10 * 1024 * 1024,
    "OUTPUT_FILE": "all_servers.txt",
    "DB_FILE": "collector.db",
    "ENV_FILE": ".env",
    "CACHE_FILE": "cache.json",
}

# ============================
# ✋ فقط داده‌های دستی
# ============================

MANUAL_REPOS_TO_SCAN = [
    ("MrAbolfazlNorouzi", "iran-configs"),
    ("MustafaBaqer", "VestraNet-Nodes"),
]

COMMON_BRANCH_NAMES = [
    "main",
    "master",
    "freeiran",
    "worker",
]

# ============================
# 🔧 Regex کانفیگ‌ها
# ============================

V2RAY_PATTERN = re.compile(
    r'(vless|vmess|trojan|ss|ssr|hysteria|hysteria2|tuic)://[^\s`\'"]+',
    re.IGNORECASE
)

SUB_LINK_PATTERN = re.compile(
    r'https?://[^\s`\'"]+\.(txt|yaml|yml|json|conf)[^\s`\'"]*',
    re.IGNORECASE
)

# ============================
# 💾 DB ساده
# ============================

_db = None

async def get_db():
    global _db
    if _db is None:
        _db = await aiosqlite.connect(CONFIG_DEFAULTS["DB_FILE"])
        await _db.execute("CREATE TABLE IF NOT EXISTS configs (config TEXT PRIMARY KEY)")
        await _db.commit()
    return _db


async def save_config(cfgs):
    db = await get_db()
    for c in cfgs:
        await db.execute("INSERT OR IGNORE INTO configs VALUES (?)", (c,))
    await db.commit()


async def get_all_configs():
    db = await get_db()
    cur = await db.execute("SELECT config FROM configs")
    rows = await cur.fetchall()
    return [r[0] for r in rows]

# ============================
# 🌐 fetch
# ============================

async def fetch(session, url):
    try:
        async with session.get(url, timeout=20) as r:
            if r.status == 200:
                return await r.text()
    except:
        return None

# ============================
# 📁 گرفتن فایل‌های repo
# ============================

async def get_files(session, owner, repo, branch):
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}"
    # ساده‌ترین حالت: لیست فایل‌ها از API tree
    api = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"

    tree_text = await fetch(session, api)
    if not tree_text:
        return set()

    try:
        data = json.loads(tree_text)
    except:
        return set()

    files = set()

    for item in data.get("tree", []):
        if item.get("type") == "blob":
            path = item.get("path")
            if path.endswith((".txt", ".yml", ".yaml", ".json", ".conf")):
                files.add(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}")

    return files

# ============================
# 🔍 پردازش فایل
# ============================

async def process_file(session, url):
    text = await fetch(session, url)
    if not text:
        return set()

    results = set()

    results.update(V2RAY_PATTERN.findall(text))

    # base64 decode fallback
    try:
        stripped = text.strip()
        if len(stripped) < 200000:
            decoded = base64.b64decode(stripped + "==").decode("utf-8", errors="ignore")
            results.update(V2RAY_PATTERN.findall(decoded))
    except:
        pass

    return results

# ============================
# 🚀 main
# ============================

async def main():
    load_dotenv()

    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "User-Agent": "manual-scanner"
    }

    connector = aiohttp.TCPConnector(limit=CONFIG_DEFAULTS["AIOHTTP_CONNECTION_LIMIT"])

    all_results = set()

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:

        for owner, repo in MANUAL_REPOS_TO_SCAN:

            for branch in COMMON_BRANCH_NAMES:

                tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"

                tree_text = await fetch(session, tree_url)
                if not tree_text:
                    continue

                try:
                    data = json.loads(tree_text)
                except:
                    continue

                file_urls = set()

                for item in data.get("tree", []):
                    if item.get("type") != "blob":
                        continue
                    path = item.get("path", "")
                    if path.endswith((".txt", ".yaml", ".yml", ".json", ".conf")):
                        file_urls.add(
                            f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
                        )

                for url in file_urls:
                    results = await process_file(session, url)
                    if results:
                        all_results.update(results)

        # ذخیره
        db = await get_db()
        for c in all_results:
            await db.execute("INSERT OR IGNORE INTO configs VALUES (?)", (c,))
        await db.commit()

        # خروجی
        all_cfgs = await get_all_configs()

        with open(CONFIG_DEFAULTS["OUTPUT_FILE"], "w") as f:
            f.write("\n".join(all_cfgs))

        print(f"Done. Total configs: {len(all_cfgs)}")


if __name__ == "__main__":
    asyncio.run(main())
