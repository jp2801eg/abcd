import json
import os
import anthropic

SYSTEM_PROMPT = """You are an expert in Asset-Based Community Development (ABCD).
Your job is to read community meeting notes or text and identify community assets.

Classify every asset you find into one of these 6 ABCD categories:

1. Individuals — People with skills, knowledge, experience, or passion to contribute
2. Associations — Informal groups, clubs, faith communities, neighborhood groups
3. Institutions — Formal organizations: schools, hospitals, government agencies, businesses
4. Built/Natural Environment — Physical spaces, buildings, parks, land, infrastructure
5. Economic Assets — Local businesses, employment, skills that generate income
6. Cultural Assets — Traditions, stories, arts, languages, shared history

An asset may appear in more than one category if it represents different dimensions of the same thing. For example, a Día de los Muertos celebration organized by a neighborhood family is both an Association (an informal group that gathers) and a Cultural Asset (the tradition and heritage it carries). When this applies, create a separate entry for each category.

For every asset entry, populate these fields:
- name: short identifying name for the asset
- category: one of the 6 category names above
- description: one sentence on why this asset qualifies in this category
- contact: name or role of a person or group to reach (null if not mentioned)
- location: physical location if mentioned (null if not mentioned)
- gifts: a JSON array of strings, each naming one thing this asset contributes or makes available to the community — e.g. ["food production", "gathering space"]. Never a comma-separated string. Interpreted broadly: for individuals this is skills and talents; for institutions it is space, funding, expertise, or access they provide; for associations it is collective capacity, coordination, or trust; for built/natural environment it is what the space enables; for economic assets it is what they contribute beyond commerce; for cultural assets it is what they transmit such as identity, knowledge, or belonging
- source_text: the exact phrase or sentence from the input that identified this asset

Return ONLY a valid JSON array of asset objects. No explanation, no markdown, no code fences — just the raw JSON array."""

MODEL = "claude-haiku-4-5-20251001"


def load_input_file(filename: str) -> str:
    path = os.path.join("inputs", filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"No file found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


CHUNK_SIZE = 4000


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    remaining = text
    while len(remaining) > chunk_size:
        split_at = remaining.rfind("\n\n", 0, chunk_size)
        if split_at == -1:
            split_at = remaining.rfind("\n", 0, chunk_size)
        if split_at == -1:
            split_at = chunk_size
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def classify_assets(text: str) -> list:
    client = anthropic.Anthropic()

    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Please identify and classify the community assets in the following text:\n\n{text}",
            }
        ],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("\nError: The response from Claude could not be parsed as valid JSON.")
        if response.stop_reason == "max_tokens":
            print("The output was cut off because the input file produced too many assets to fit in one response.")
            print("Try splitting the file into smaller sections and running each one separately.")
        else:
            print("The response may be malformed. The raw output has been saved to outputs/raw_response.txt for inspection.")
            os.makedirs("outputs", exist_ok=True)
            with open(os.path.join("outputs", "raw_response.txt"), "w", encoding="utf-8") as f:
                f.write(text)
        raise SystemExit(1)


def generate_map(assets: list) -> None:
    template_path = "map_template.html"
    if not os.path.exists(template_path):
        print(f"Warning: {template_path} not found — skipping map generation.")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    assets_json = json.dumps(assets, ensure_ascii=False)
    html = template.replace("__ASSETS_DATA__", assets_json)

    os.makedirs("outputs", exist_ok=True)
    with open(os.path.join("outputs", "map.html"), "w", encoding="utf-8") as f:
        f.write(html)


def main():
    filename = input("Enter the filename from the inputs/ folder: ").strip()

    print(f"\nReading '{filename}'...")
    text = load_input_file(filename)
    print(f"Loaded {len(text)} characters.\n")

    chunks = split_into_chunks(text)
    if len(chunks) > 1:
        print(f"Input is large — splitting into {len(chunks)} chunks...\n")
    assets = []
    for i, chunk in enumerate(chunks, 1):
        if len(chunks) > 1:
            print(f"  Classifying chunk {i}/{len(chunks)} ({len(chunk)} chars)...")
        assets.extend(classify_assets(chunk))

    os.makedirs("outputs", exist_ok=True)
    output_path = os.path.join("outputs", "assets.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(assets, f, indent=2, ensure_ascii=False)

    generate_map(assets)

    print(f"Found {len(assets)} asset entries.")
    print(f"  JSON saved to {output_path}")
    print(f"  Map saved to outputs/map.html (open directly in any browser)")


if __name__ == "__main__":
    main()
