import time
import json
from pathlib import Path

INPUT_FILE = "all_servers.txt"
STATE_FILE = "data/state.json"
OUTPUT_FILE = "recent_servers.txt"

WINDOW_SECONDS = 6 * 3600  # 6 hours


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
    return [
        line.strip()
        for line in Path(INPUT_FILE).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main():
    now = time.time()
    cutoff = now - WINDOW_SECONDS

    print("⚙️ Processor started...")

    configs = load_configs()
    state = load_state()

    # 1. assign timestamp to new configs
    for c in configs:
        if c not in state:
            state[c] = now
            print(f"🆕 new config added: {c[:40]}...")

    # 2. remove expired configs (older than 6 hours)
    filtered_state = {
        c: ts for c, ts in state.items()
        if ts >= cutoff
    }

    removed = len(state) - len(filtered_state)
    if removed > 0:
        print(f"🧹 removed {removed} expired configs")

    state = filtered_state

    # 3. write output file (only active configs)
    Path(OUTPUT_FILE).write_text(
        "\n".join(state.keys()),
        encoding="utf-8"
    )

    # 4. save state for next run
    save_state(state)

    print(f"✅ Done. Active configs: {len(state)}")


if __name__ == "__main__":
    main()
