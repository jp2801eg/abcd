import json
import os
import time
import streamlit as st

from classify import classify_assets, split_into_chunks

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
uploaded_file = st.file_uploader(
    "Upload your meeting notes (.txt or .md)",
    type=["txt", "md"],
)

st.divider()

pasted_text = st.text_area(
    "Or paste your notes here",
    placeholder="Paste your meeting notes directly…",
    height=200,
)

# Determine input: file takes priority over pasted text
if uploaded_file is not None:
    input_text = uploaded_file.read().decode("utf-8")
    st.success(f"File loaded: **{uploaded_file.name}**")
elif pasted_text.strip():
    input_text = pasted_text.strip()
else:
    input_text = None

if input_text is not None:
    if st.button("Generate Map", type="primary"):
        text = input_text
        chunks = split_into_chunks(text)

        progress_bar = st.progress(0, text="Starting…")
        status = st.empty()

        all_assets = []
        try:
            for i, chunk in enumerate(chunks):
                label = (
                    f"Analyzing chunk {i + 1} of {len(chunks)}…"
                    if len(chunks) > 1
                    else "Analyzing your notes…"
                )
                status.write(label)
                progress_bar.progress(i / len(chunks), text=label)

                all_assets.extend(classify_with_retries(chunk, label, status))
        except RuntimeError as e:
            progress_bar.empty()
            status.empty()
            st.error(str(e))
            st.stop()

        progress_bar.progress(1.0, text="Building map…")
        status.write("Building map…")

        # Build the HTML map in memory (avoid touching outputs/ on disk)
        template_path = os.path.join(os.path.dirname(__file__), "map_template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        assets_json = json.dumps(all_assets, ensure_ascii=False)
        html_output = template.replace("__ASSETS_DATA__", assets_json)

        progress_bar.empty()
        status.empty()

        st.success(
            f"Done! Found **{len(all_assets)} assets** in your community notes."
        )
        st.download_button(
            label="Download Asset Map (HTML)",
            data=html_output.encode("utf-8"),
            file_name="community-asset-map.html",
            mime="text/html",
        )
        st.caption("Open the downloaded file in any web browser to explore the map.")
