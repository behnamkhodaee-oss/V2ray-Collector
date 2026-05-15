import time
import os
import processor  # فایل processor.py باید کنار این باشه

FILE = "all_servers.txt"   # چون در ریشه پروژه است
CHECK_INTERVAL = 15 * 60    # 15 دقیقه

last_mtime = 0


def get_mtime(path):
    try:
        return os.path.getmtime(path)
    except FileNotFoundError:
        return 0


print("👀 Watcher started... monitoring all_servers.txt")

while True:
    mtime = get_mtime(FILE)

    if mtime > last_mtime:
        print("📦 Change detected → running processor...")

        last_mtime = mtime

        try:
            processor.main()
            print("✅ Processing done")
        except Exception as e:
            print(f"❌ Processor error: {e}")

    else:
        print("⏳ No change detected")

    time.sleep(CHECK_INTERVAL)
