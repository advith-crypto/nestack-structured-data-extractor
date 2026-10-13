"""Call the local API for each assessment sample and write results.json."""
import json
import os
from pathlib import Path

import requests

BASE_URL = os.getenv("EXTRACTOR_BASE_URL", "http://127.0.0.1:8000")
ROOT = Path(__file__).resolve().parent


def main():
    samples = json.loads((ROOT / "sample_inputs.json").read_text(encoding="utf-8"))
    results = []
    for sample in samples:
        response = requests.post(
            f"{BASE_URL}/extract", json={"text": sample["text"]}, timeout=90
        )
        response.raise_for_status()
        results.append({"label": sample["label"], "input": sample["text"], "response": response.json()})
    (ROOT / "results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(results)} API responses to {ROOT / 'results.json'}")


if __name__ == "__main__":
    main()
