import time
import json
from pathlib import Path

INPUT_FILE = "all_servers.txt"
STATE_FILE = "data/state.json"
OUTPUT_FILE = "recent_servers.txt"

WINDOW_SECONDS = 3 * 1800  # 3 hours


def load_state():
    if Path(STATE_FILE).exists():
        try:
            return json.loads(Path(STATE_FILE).read_text(encoding="utf-8"))
        except:
            return {}
    return {}


def save_state(state):
    Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(STATE_FILE).write_text(
        json.dumps(state, indent=2),
        encoding="utf-8"
    )


def load_configs():
    if not Path(INPUT_FILE).exists():
        return []

    configs = [
        line.strip()
        for line in Path(INPUT_FILE).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    # جلوگیری از پردازش تکراری در هر اجرا
    return list(set(configs))


def main():
    now = time.time()
    cutoff = now - WINDOW_SECONDS

    print("⚙️ Processor started...")

    configs = load_configs()
    state = load_state()

    # 1. فقط برای کانفیگ‌های جدید timestamp ثبت کن
    for c in configs:
        if c not in state:
            state[c] = now
            print(f"🆕 new config added: {c[:40]}...")

    # 2. حذف کانفیگ‌های قدیمی (بیشتر از 6 ساعت)
    filtered_state = {
        c: ts for c, ts in state.items()
        if ts >= cutoff
    }

    removed = len(state) - len(filtered_state)
    if removed > 0:
        print(f"🧹 removed {removed} expired configs")

    state = filtered_state

    # 3. ذخیره خروجی نهایی
    Path(OUTPUT_FILE).write_text(
        "\n".join(state.keys()),
        encoding="utf-8"
    )

    # 4. ذخیره state برای اجرای بعدی
    save_state(state)

    print(f"✅ Done. Active configs: {len(state)}")


if __name__ == "__main__":
    main()
