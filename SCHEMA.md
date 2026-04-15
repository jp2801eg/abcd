# Asset Data Schema

## Purpose

This schema describes the structure of every asset record produced by this tool. Each record represents one community asset — a person, group, place, tradition, or resource — that was identified in community meeting notes or other text. The goal is to capture not just what the asset *is*, but what it *contributes*, so that communities can see and build on their own strengths.

Assets are classified using the Asset-Based Community Development (ABCD) framework. Because a single asset can play more than one role in a community (for example, a neighborhood celebration is both a gathering group and a cultural tradition), the same real-world asset may appear as separate records under different categories.

---

## Fields

### `name`
**Type:** string

A short, human-readable label for the asset. This is what will appear on maps and in lists.

**Example:** `"Rosa Mendez"`

---

### `category`
**Type:** string — one of six fixed values

Which ABCD category this record represents. The six categories are:

| Category | What it covers |
|---|---|
| `Individuals` | People with skills, knowledge, experience, or passion to contribute |
| `Associations` | Informal groups, clubs, faith communities, neighborhood groups |
| `Institutions` | Formal organizations: schools, hospitals, government agencies, businesses |
| `Built/Natural Environment` | Physical spaces, buildings, parks, land, infrastructure |
| `Economic Assets` | Local businesses, employment, skills that generate income |
| `Cultural Assets` | Traditions, stories, arts, languages, shared history |

**Example:** `"Individuals"`

---

### `description`
**Type:** string

One plain-language sentence explaining why this asset belongs in its category and what makes it worth noting. This is written for a community audience, not a technical one.

**Example:** `"A retired nurse offering free health screenings to the community, demonstrating skilled expertise in healthcare and commitment to resident wellness."`

---

### `contact`
**Type:** string, or `null` if not mentioned

The name or role of a person or group who can be reached about this asset. Left blank when the source text does not name anyone specific.

**Example:** `"Rosa Mendez"`

---

### `location`
**Type:** string, or `null` if not mentioned

Where this asset is physically located, if the source text says so. Left blank when no location is mentioned.

**Example:** `"Elm Street"`

---

### `gifts`
**Type:** array of strings

A list of the specific things this asset contributes or makes available to the community. "Gifts" is the ABCD term for what an asset offers — interpreted broadly:

- For **individuals**: skills and talents
- For **associations**: collective capacity, coordination, or trust they enable
- For **institutions**: space, funding, expertise, or access they provide
- For **built/natural environment**: what the space makes possible
- For **economic assets**: what they contribute beyond commerce
- For **cultural assets**: what they transmit, such as identity, memory, or belonging

Each item in the list is a short phrase, not a sentence.

**Example:** `["healthcare expertise", "health screenings", "nursing knowledge"]`

---

### `source_text`
**Type:** string

The verbatim phrase or sentence from the original input text that identified this asset. This field is preserved exactly as written — no paraphrasing or summarizing.

**Why this matters:** `source_text` supports human-in-the-loop review. Before acting on any asset record, a community organizer or facilitator can read the original words that generated it. This makes it easy to catch misclassifications, check context, and decide whether a record accurately represents what was said. The AI extracts and classifies; humans confirm.

**Example:** `"Rosa Mendez, a retired nurse, has been offering free health screenings out of her garage every Saturday"`

---

## Complete Record Example

```json
{
  "name": "Rosa Mendez",
  "category": "Individuals",
  "description": "A retired nurse offering free health screenings to the community, demonstrating skilled expertise in healthcare and commitment to resident wellness.",
  "contact": "Rosa Mendez",
  "location": "Her garage",
  "gifts": [
    "healthcare expertise",
    "health screenings",
    "nursing knowledge"
  ],
  "source_text": "Rosa Mendez, a retired nurse, has been offering free health screenings out of her garage every Saturday"
}
```

---

## Future Migration

This schema is intentionally platform-agnostic. The fields were chosen to map cleanly onto the data structures used by common community mapping and network visualization tools, so that assets.json can be imported or converted without restructuring.

**Kumu** (kumu.io) is a relationship mapping platform well suited to ABCD work. Each asset record can become a Kumu *element*, with `name` as the label, `category` as the element type, and `gifts` as tags. `description`, `contact`, `location`, and `source_text` can be imported as custom attributes. Connections between assets (for example, a person and the institution they work with) can be added as *connections* once the elements are loaded.

**Miro** (miro.com) is a visual collaboration whiteboard that community groups sometimes use for facilitated mapping sessions. Assets can be imported as sticky notes or cards, grouped by category, with fields surfaced as card metadata. The `gifts` list is well suited to keyword tags that participants can sort and cluster visually.

When the time comes to migrate, no fields need to be renamed or restructured — the current schema is the migration-ready format.
