import json
import os
import time
import streamlit as st

from classify import classify_assets, consolidate_assets, split_into_chunks

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


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

# ── Main UI (shown only after authentication) ─────────────────────────────────
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
        all_chunks = [(label, chunk) for label, text in inputs for chunk in split_into_chunks(text)]
        total_chunks = len(all_chunks)

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

        status.write("Building map…")

        # Build the HTML map in memory (avoid touching outputs/ on disk)
        template_path = os.path.join(os.path.dirname(__file__), "map_template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        assets_json = json.dumps(all_assets, ensure_ascii=False)
        html_output = template.replace("__ASSETS_DATA__", assets_json)

        progress_bar.empty()
        status.empty()

        files_processed = len(inputs)
        file_word = "file" if files_processed == 1 else "files"
        st.success(
            f"Done! Processed **{files_processed} {file_word}** and found "
            f"**{len(all_assets)} assets** across your community notes."
        )
        st.download_button(
            label="Download Asset Map (HTML)",
            data=html_output.encode("utf-8"),
            file_name="community-asset-map.html",
            mime="text/html",
        )
        st.caption("Open the downloaded file in any web browser to explore the map.")
