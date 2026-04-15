# ABCD Community Asset Map

> **This is a working prototype.** Running it currently requires technical setup (Python, a terminal, and an API key). A facilitator-friendly version that requires no installation or technical knowledge is planned for the future. If you are not comfortable with the setup steps below, hold on for that version — or ask a technically inclined colleague to run it on your behalf.

---

A simple tool that reads community meeting notes and automatically identifies and maps the assets in them — the people, groups, places, traditions, and resources that a neighborhood already has.

It is built on the Asset-Based Community Development (ABCD) framework, which starts from what a community *has* rather than what it *lacks*. This tool does the time-consuming work of reading through notes and sorting assets into the six ABCD categories, so facilitators can spend their energy on the community conversation instead.

---

## Who this is for

Community organizers, neighborhood facilitators, and ABCD practitioners who want a faster way to turn meeting notes into a visual asset map — without needing any technical background to run it.

You do not need to know how to code. You just need to be able to open a terminal and type a few commands, which are explained step by step below.

---

## What it produces

For every set of notes you feed in, the tool produces two files:

- **`outputs/assets.json`** — a structured list of every asset found, including its name, category, description, gifts (what it contributes), a contact if one was mentioned, a location if one was mentioned, and the exact sentence from your notes that it came from.
- **`outputs/map.html`** — a visual map you can open in any web browser, with no internet connection required. Assets are grouped by category, searchable, and filterable.

Both files stay on your computer. Nothing is sent to a server or stored anywhere else.

---

## Before you begin: what you need

1. **Python 3** — the programming language this tool runs on. Check whether you already have it by opening a terminal and typing `python --version`. If you see a version number starting with 3, you're set. If not, download it free from [python.org](https://python.org).

2. **An Anthropic API key** — this is what allows the tool to use Claude (the AI) to read your notes. You can get one at [console.anthropic.com](https://console.anthropic.com). There is a small cost per use, but processing a typical set of meeting notes costs a fraction of a cent.

3. **This project folder** — the folder you're reading this in.

---

## Installation

Open a terminal, navigate to this folder, and run these two commands in order.

**Step 1 — Install dependencies:**
```
pip install anthropic
```

**Step 2 — Set your API key:**

On Mac or Linux:
```
export ANTHROPIC_API_KEY=your-key-here
```

On Windows:
```
set ANTHROPIC_API_KEY=your-key-here
```

Replace `your-key-here` with the actual key from your Anthropic account. You will need to do this each time you open a new terminal window, unless you add it to your system's environment variables permanently.

---

## How to use it: uploading notes after a meeting

This is the most common workflow. After a meeting, you paste or type your notes into a text file and run the tool.

**Step 1 — Put your notes in the `inputs/` folder.**

Create a plain text file (for example, `april-meeting.txt`) and paste your meeting notes into it. The notes can be rough — sentence fragments, names without context, shorthand — as long as a person could read them and understand what was said. Save the file in the `inputs/` folder.

If you want to see what the expected format looks like, there is a sample file at `inputs/sample.txt`.

**Step 2 — Run the tool.**

In your terminal, from this folder, run:
```
python classify.py
```

When prompted, type the filename you saved:
```
Enter the filename from the inputs/ folder: april-meeting.txt
```

**Step 3 — Review the output.**

The tool will print how many assets it found and confirm that two files were saved:

- `outputs/assets.json` — the full structured data
- `outputs/map.html` — the visual map

Open `outputs/map.html` by double-clicking it. It will open in your browser. From there you can search, filter by category, and review each asset.

**Step 4 — Check the source text.**

Every asset card on the map includes the exact sentence from your notes that it was drawn from. Before sharing the map or acting on it, read through these and make sure the AI read the notes the way you intended. If something was misclassified or missed, you can edit `outputs/assets.json` directly (it is a plain text file) and re-run the map generation, or adjust your notes and run again.

---

## Alternative workflow: live capture during a meeting

If you are facilitating a meeting and want to map assets in real time, you can do it through any AI chat interface — no installation or API key required. This works with Claude, ChatGPT, Gemini, Microsoft Copilot, or any similar tool you already have access to.

**How it works:**

1. Open your preferred AI chat tool in a browser tab during your meeting.
2. As participants name assets, jot down what they say. You can paste notes in gradually as the meeting goes, or all at once at the end.
3. Send the AI this prompt, with your notes pasted in at the bottom:

---

**Copy and paste this prompt — replace everything in brackets with your actual notes:**

> Please identify and classify the community assets in the notes below using the Asset-Based Community Development (ABCD) framework.
>
> Return ONLY a valid JSON array — no explanation, no formatting, just the raw JSON. Each item in the array should have exactly these fields:
>
> - **name** — a short label for the asset
> - **category** — one of: Individuals, Associations, Institutions, Built/Natural Environment, Economic Assets, Cultural Assets
> - **description** — one sentence on why this qualifies as an asset in that category
> - **contact** — name of a person or group to reach, or null if not mentioned
> - **location** — physical location, or null if not mentioned
> - **gifts** — a JSON array of short phrases describing what this asset contributes (e.g. ["food production", "gathering space"])
> - **source_text** — the exact phrase or sentence from the notes that identified this asset
>
> An asset may appear in more than one category if it represents different things (e.g. a cultural celebration is both an Association and a Cultural Asset). Create a separate entry for each category when that applies.
>
> Here are the notes:
>
> [PASTE YOUR MEETING NOTES HERE]

---

4. Copy the JSON the AI returns and save it as a new file called `assets.json` inside the `outputs/` folder in this project.
5. Run just the map generation step:
   ```
   python -c "import json, classify; classify.generate_map(json.load(open('outputs/assets.json')))"
   ```
   This skips the classification step (which you already did in chat) and goes straight to building the visual map.

This approach is especially useful for large-group sessions where capturing things in real time matters, or when you want to avoid the API key setup entirely. The JSON format produced by the prompt above is compatible with this tool regardless of which AI you used to generate it.

---

## The six ABCD asset categories

The tool sorts every asset it finds into one of these six categories:

| Category | What it includes |
|---|---|
| **Individuals** | People with skills, knowledge, experience, or passion to share |
| **Associations** | Informal groups — neighborhood clubs, faith communities, mutual aid networks |
| **Institutions** | Formal organizations — schools, hospitals, government agencies, local businesses |
| **Built/Natural Environment** | Physical places — parks, gardens, buildings, land, infrastructure |
| **Economic Assets** | Things that generate or sustain economic activity — local businesses, skilled trades |
| **Cultural Assets** | Traditions, stories, art, language, and shared history |

One asset can belong to more than one category. A family-run cultural celebration, for example, is both an Association (a group that organizes) and a Cultural Asset (the tradition it carries). When that happens, the tool creates a separate record for each category so nothing is lost.

---

## File overview

```
abcd-asset-map/
├── classify.py          The main script — runs classification and map generation
├── map_template.html    The visual map template
├── inputs/
│   └── sample.txt       An example set of meeting notes to try first
├── outputs/
│   ├── assets.json      The structured asset data (created after you run the tool)
│   └── map.html         The generated map (created after you run the tool)
├── SCHEMA.md            Full documentation of every field in assets.json
└── README.md            This file
```

---

## Questions and troubleshooting

**"I get an error about a missing API key."**
Make sure you ran the `export` (Mac/Linux) or `set` (Windows) command in the same terminal window where you are running the tool.

**"The tool ran but I don't see map.html."**
Check that `map_template.html` is still in the project folder. The map is built from that template.

**"An asset is wrong or missing."**
Open `outputs/assets.json` in any text editor and correct it by hand. Then re-run the map generation using the command in the live capture section above. You can also just adjust your notes and run `classify.py` again.

**"Can I run this on notes from multiple meetings?"**
Yes — save each meeting's notes as a separate file in `inputs/` and run the tool once per file. Each run overwrites `outputs/assets.json` and `map.html`, so rename the outputs you want to keep before running again.
