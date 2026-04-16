import json
import os
import time
import streamlit as st

from classify import classify_assets, consolidate_assets, split_into_chunks

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

CATEGORIES = [
    "Individuals",
    "Associations",
    "Institutions",
    "Built/Natural Environment",
    "Economic Assets",
    "Cultural Assets",
]


def _build_kumu_json(assets: list) -> bytes:
    """Return a UTF-8 encoded Kumu blueprint JSON string."""
    elements = []
    for a in assets:
        elements.append({
            "label":       a.get("name") or "",
            "type":        a.get("category") or "",
            "description": a.get("description") or "",
            "tags":        list(a.get("gifts") or []),
            "Contact":     a.get("contact") or "",
            "Location":    a.get("location") or "",
            "Source":      a.get("source_text") or "",
        })

    connections = []
    seen: set = set()

    def _add_connection(label_a, label_b, conn_type):
        key = (min(label_a, label_b), max(label_a, label_b))
        if key not in seen:
            seen.add(key)
            connections.append({"from": label_a, "to": label_b, "type": conn_type})

    by_location: dict[str, list] = {}
    by_contact: dict[str, list] = {}

    for a in assets:
        loc = (a.get("location") or "").strip()
        if loc:
            by_location.setdefault(loc.lower(), []).append(a.get("name") or "")
        con = (a.get("contact") or "").strip()
        if con:
            by_contact.setdefault(con.lower(), []).append(a.get("name") or "")

    for labels in by_location.values():
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                _add_connection(labels[i], labels[j], "shared location")

    for labels in by_contact.values():
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                _add_connection(labels[i], labels[j], "shared contact")

    blueprint = {"elements": elements, "connections": connections}
    return json.dumps(blueprint, ensure_ascii=False, indent=2).encode("utf-8")


def classify_with_retries(chunk: str, chunk_label: str, status) -> list:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return classify_assets(chunk)
        except Exception as e:
            if attempt < MAX_RETRIES:
                status.write(
                    f"{chunk_label} — attempt {attempt} failed, retrying in {RETRY_DELAY}s…"
                )
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(
                    f"Failed to process {chunk_label} after {MAX_RETRIES} attempts. "
                    f"The API may be overloaded. Please try again in a moment."
                ) from e


ACCESS_CODE = "abcd2025"

st.set_page_config(page_title="AI Asset Mapping Tool", layout="centered")

st.title("AI Asset Mapping Tool")
st.write(
    "Built on the Asset-Based Community Development (ABCD) framework, this tool reads "
    "your community meeting notes and automatically identifies and sorts assets into the "
    "six ABCD categories — so facilitators can spend their energy on the community "
    "conversation instead of organizing notes afterward. Upload your notes, get back a "
    "visual map. Nothing is stored. Everything stays with you."
)

st.info(
    "AI classification is a starting point, not a final product. "
    "Always review assets with your community before sharing or acting on them."
)

st.divider()

# ── Access code gate ──────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    code = st.text_input("Enter access code", type="password")
    if st.button("Continue"):
        if code == ACCESS_CODE:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect access code. Please try again.")
    st.stop()

# ── Review / editing interface ────────────────────────────────────────────────
if st.session_state.get("review_mode"):
    assets = st.session_state.assets
    files_processed = st.session_state.get("files_processed", 1)
    file_word = "file" if files_processed == 1 else "files"

    col_title, col_action = st.columns([3, 1])
    with col_title:
        st.subheader(f"Review Your Assets ({len(assets)} found)")
        st.caption(
            "Edit any details that need correcting, and delete assets that don't belong. "
            "When you're satisfied, click Generate Final Map."
        )
    with col_action:
        if st.button("← Start Over", help="Clear results and upload new notes"):
            # Remove widget keys for all current assets to avoid stale values on next run
            for asset in assets:
                aid = asset["_id"]
                for prefix in ("name_", "category_", "description_", "contact_", "location_"):
                    st.session_state.pop(f"{prefix}{aid}", None)
            st.session_state.pop("review_mode", None)
            st.session_state.pop("assets", None)
            st.session_state.pop("files_processed", None)
            st.rerun()

    st.divider()

    # Sort by canonical category order then alphabetically by live name within each group.
    # Use live session state values so the order reflects any edits made this session.
    def sort_key(a):
        aid = a["_id"]
        live_cat = st.session_state.get(f"category_{aid}", a.get("category", ""))
        live_name = st.session_state.get(f"name_{aid}", a.get("name", ""))
        cat_order = CATEGORIES.index(live_cat) if live_cat in CATEGORIES else len(CATEGORIES)
        return (cat_order, live_name.lower())

    sorted_assets = sorted(assets, key=sort_key)

    to_delete = None  # Collect deletion outside the loop to avoid mutating mid-iteration
    any_category_changed = False
    current_group = None

    for asset in sorted_assets:
        aid = asset["_id"]
        live_name = st.session_state.get(f"name_{aid}", asset.get("name", "Unnamed asset"))
        live_category = st.session_state.get(f"category_{aid}", asset.get("category", ""))

        if live_category != asset.get("category"):
            any_category_changed = True

        # Emit a category subheader whenever the group changes
        if live_category != current_group:
            if current_group is not None:
                st.write("")  # breathing room between groups
            st.subheader(live_category)
            current_group = live_category

        with st.expander(live_name, expanded=False):
            col_left, col_right = st.columns(2)

            with col_left:
                st.text_input(
                    "Name",
                    value=asset.get("name", ""),
                    key=f"name_{aid}",
                )
                current_category = asset.get("category", CATEGORIES[0])
                cat_index = CATEGORIES.index(current_category) if current_category in CATEGORIES else 0
                st.selectbox(
                    "Category",
                    CATEGORIES,
                    index=cat_index,
                    key=f"category_{aid}",
                )
                st.text_input(
                    "Contact",
                    value=asset.get("contact") or "",
                    key=f"contact_{aid}",
                    help="Name or role of a person to reach about this asset",
                )

            with col_right:
                st.text_area(
                    "Description",
                    value=asset.get("description", ""),
                    key=f"description_{aid}",
                    height=108,
                )
                st.text_input(
                    "Location",
                    value=asset.get("location") or "",
                    key=f"location_{aid}",
                    help="Physical location, if known",
                )

            gifts = asset.get("gifts") or []
            if gifts:
                st.markdown("**What this asset contributes**")
                for gift in gifts:
                    st.markdown(f"- {gift}")

            source = asset.get("source_text", "")
            if source:
                st.caption(f"From the notes: _{source}_")

            if st.button("Delete this asset", key=f"delete_{aid}", type="secondary"):
                to_delete = asset

    if to_delete is not None:
        st.session_state.assets = [a for a in assets if a["_id"] != to_delete["_id"]]
        st.rerun()

    st.divider()

    if st.button("Generate Final Map", type="primary"):
        final_assets = []
        for asset in assets:
            aid = asset["_id"]
            contact_val = st.session_state.get(f"contact_{aid}", asset.get("contact") or "").strip()
            location_val = st.session_state.get(f"location_{aid}", asset.get("location") or "").strip()
            final_assets.append({
                "name": st.session_state.get(f"name_{aid}", asset.get("name", "")),
                "category": st.session_state.get(f"category_{aid}", asset.get("category", "")),
                "description": st.session_state.get(f"description_{aid}", asset.get("description", "")),
                "contact": contact_val or None,
                "location": location_val or None,
                "gifts": asset.get("gifts"),
                "source_text": asset.get("source_text"),
            })

        template_path = os.path.join(os.path.dirname(__file__), "map_template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        assets_json = json.dumps(final_assets, ensure_ascii=False)
        html_output = template.replace("__ASSETS_DATA__", assets_json)

        st.success(
            f"Map ready! Processed **{files_processed} {file_word}** and mapped "
            f"**{len(final_assets)} assets** after your review."
        )
        st.download_button(
            label="Download Asset Map (HTML)",
            data=html_output.encode("utf-8"),
            file_name="community-asset-map.html",
            mime="text/html",
        )
        st.caption(
            "Opens in any browser. Visual and interactive right away — but changes won't save."
        )

        st.download_button(
            label="Download for Kumu (.json)",
            data=_build_kumu_json(final_assets),
            file_name="community-asset-map-kumu.json",
            mime="application/json",
        )
        st.caption(
            "For a persistent, collaborative map. Requires a free Kumu account at kumu.io"
            " — import the file to keep your map editable over time."
        )

    if any_category_changed:
        st.caption(
            "Note: if you changed any asset categories, click Generate Final Map "
            "to see the updated groupings."
        )

    st.stop()

# ── Upload interface (shown when not in review mode) ──────────────────────────
uploaded_files = st.file_uploader(
    "Upload your meeting notes (.txt or .md)",
    type=["txt", "md"],
    accept_multiple_files=True,
)

st.divider()

pasted_text = st.text_area(
    "Or paste your notes here",
    placeholder="Paste your meeting notes directly…",
    height=200,
)

# Determine input: files take priority over pasted text
# Each entry in `inputs` is a (label, text) tuple.
if uploaded_files:
    inputs = [(f.name, f.read().decode("utf-8")) for f in uploaded_files]
    file_names = ", ".join(f"**{name}**" for name, _ in inputs)
    st.success(
        f"{'File' if len(inputs) == 1 else f'{len(inputs)} files'} loaded: {file_names}"
    )
elif pasted_text.strip():
    inputs = [("pasted text", pasted_text.strip())]
else:
    inputs = []

if inputs:
    if st.button("Generate Map", type="primary"):
        # Count total chunks across all inputs for the overall progress bar.
        total_chunks = sum(len(split_into_chunks(text)) for _, text in inputs)

        progress_bar = st.progress(0, text="Starting…")
        status = st.empty()

        all_assets = []
        chunks_done = 0
        try:
            for label, text in inputs:
                file_chunks = split_into_chunks(text)
                for i, chunk in enumerate(file_chunks):
                    if len(inputs) > 1 and len(file_chunks) > 1:
                        progress_label = f"**{label}** — chunk {i + 1} of {len(file_chunks)}…"
                    elif len(inputs) > 1:
                        progress_label = f"Analyzing **{label}**…"
                    elif len(file_chunks) > 1:
                        progress_label = f"Analyzing chunk {i + 1} of {len(file_chunks)}…"
                    else:
                        progress_label = "Analyzing your notes…"

                    status.write(progress_label)
                    progress_bar.progress(chunks_done / total_chunks, text=progress_label)

                    all_assets.extend(classify_with_retries(chunk, progress_label, status))
                    chunks_done += 1
        except RuntimeError as e:
            progress_bar.empty()
            status.empty()
            st.error(str(e))
            st.stop()

        progress_bar.progress(1.0, text="Consolidating and deduplicating assets…")
        status.write("Consolidating and deduplicating assets…")
        all_assets = consolidate_assets(all_assets)

        progress_bar.empty()
        status.empty()

        # Assign stable IDs so widget keys don't collide across editing sessions
        id_base = st.session_state.get("asset_id_counter", 0)
        for i, asset in enumerate(all_assets):
            asset["_id"] = id_base + i
        st.session_state.asset_id_counter = id_base + len(all_assets)

        st.session_state.assets = all_assets
        st.session_state.files_processed = len(inputs)
        st.session_state.review_mode = True
        st.rerun()
