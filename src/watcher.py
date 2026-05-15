
import time
import os
import processor

FILE = "all_servers.txt"
CHECK_INTERVAL = 15 * 60  # 15 minutes

last_mtime = 0

def get_mtime(path):
    try:
        return os.path.getmtime(path)
    except FileNotFoundError:
        return 0

print("👀 Watcher started... (checking every 15 minutes)")

while True:
    try:
        mtime = get_mtime(FILE)

        print(f"⏳ Checking file... {time.ctime()}")

        if mtime > last_mtime:
            print("📦 Change detected → running processor...")

            last_mtime = mtime

            processor.main()

            print("✅ Processing finished")

        else:
            print("— No change detected")

    except Exception as e:
        print(f"❌ Error: {e}")

    time.sleep(CHECK_INTERVAL)
