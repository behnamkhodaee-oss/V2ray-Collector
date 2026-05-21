import time
import json
from pathlib import Path

INPUT_FILE = "all_servers.txt"
STATE_FILE = "data/state.json"
OUTPUT_FILE = "recent_servers.txt"

WINDOW_SECONDS = 2 * 3600  # 2 hours


def load_state():
    if Path(STATE_FILE).exists():
        try:
            return json.loads(
                Path(STATE_FILE).read_text(encoding="utf-8")
            )
        except:
            return {}

    return {}


def save_state(state):
    Path(STATE_FILE).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    Path(STATE_FILE).write_text(
        json.dumps(state, ensure_ascii=False),
        encoding="utf-8"
    )


def load_configs():
    if not Path(INPUT_FILE).exists():
        return []

    configs = []

    for line in Path(INPUT_FILE).read_text(
        encoding="utf-8"
    ).splitlines():

        line = line.strip()

        if line:
            configs.append(line)

    # حذف duplicate
    return list(dict.fromkeys(configs))


def main():

    now = int(time.time())
    cutoff = now - WINDOW_SECONDS

    print("⚙️ Processor started...")

    configs = load_configs()
    state = load_state()

    # هر config که الان داخل فایل هست
    # timestamp جدید بگیرد
    for config in configs:
        state[config] = now

    # فقط configهای 3 ساعت اخیر نگه داشته شوند
    filtered_state = {
        config: ts
        for config, ts in state.items()
        if ts >= cutoff
    }

    removed = len(state) - len(filtered_state)

    if removed:
        print(f"🧹 Removed {removed} expired configs")

    # ذخیره خروجی
    Path(OUTPUT_FILE).write_text(
        "\n".join(filtered_state.keys()),
        encoding="utf-8"
    )

    # ذخیره state
    save_state(filtered_state)

    print(f"✅ Active configs: {len(filtered_state)}")


if __name__ == "__main__":
    main()
