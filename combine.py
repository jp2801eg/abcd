import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from classify import generate_map

OUTPUTS_DIR = "outputs"


def load_asset_files() -> list[tuple[str, list]]:
    files = [
        f for f in os.listdir(OUTPUTS_DIR)
        if f.endswith("-assets.json")
    ]
    if not files:
        print(f"No files matching *-assets.json found in {OUTPUTS_DIR}/")
        raise SystemExit(1)

    results = []
    for filename in sorted(files):
        path = os.path.join(OUTPUTS_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            assets = json.load(f)
        print(f"  Loaded {len(assets):>3} assets from {filename}")
        results.append((filename, assets))
    return results


def combine_and_deduplicate(file_assets: list[tuple[str, list]]) -> list:
    seen = set()
    combined = []
    duplicates = 0

    for filename, assets in file_assets:
        for asset in assets:
            key = (asset.get("name", "").strip().lower(), asset.get("category", "").strip().lower())
            if key in seen:
                duplicates += 1
            else:
                seen.add(key)
                combined.append(asset)

    print(f"\n  {sum(len(a) for _, a in file_assets)} total assets across all files")
    print(f"  {duplicates} duplicate(s) removed")
    print(f"  {len(combined)} unique assets remaining")
    return combined


def main():
    print(f"Reading *-assets.json files from {OUTPUTS_DIR}/...\n")
    file_assets = load_asset_files()

    combined = combine_and_deduplicate(file_assets)

    output_path = os.path.join(OUTPUTS_DIR, "assets.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    print(f"\n  Combined data saved to {output_path}")

    generate_map(combined)
    print(f"  Map saved to outputs/map.html")


if __name__ == "__main__":
    main()
