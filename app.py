import glob
import os
import re

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Trail Echo", layout="wide")

st.title("Trail Echo: Offline Bird Log")
st.markdown("Powered by open-weight local inference.")

RESULTS_DIR = "results"
TS_PATTERN = re.compile(r"chunk_(\d{8}_\d{6})")

# Sidebar controls
min_conf = st.sidebar.slider("Minimum confidence", 0.25, 0.95, 0.70, 0.05)
if st.sidebar.button("Refresh"):
    st.rerun()

all_files = glob.glob(os.path.join(RESULTS_DIR, "*.csv"))

if not all_files:
    st.warning("No data found. Go outside and run the logger!")
    st.stop()

df_list, skipped = [], []
for file in all_files:
    name = os.path.basename(file)
    match = TS_PATTERN.search(name)
    if not match:
        skipped.append(f"{name}: filename has no timestamp")
        continue
    try:
        df = pd.read_csv(file)
        if df.empty:
            continue  # header-only CSV = no detections in that chunk
        chunk_start = pd.to_datetime(match.group(1), format="%Y%m%d_%H%M%S")
        df["Chunk Start"] = chunk_start
        # Actual time of each detection = chunk start + offset within chunk
        df["Detected At"] = chunk_start + pd.to_timedelta(df["Start (s)"], unit="s")
        df_list.append(df)
    except Exception as e:
        skipped.append(f"{name}: {e}")

if skipped:
    with st.expander(f"{len(skipped)} file(s) skipped"):
        for s in skipped:
            st.write(s)

if not df_list:
    st.info("No detections yet.")
    st.stop()

final_df = pd.concat(df_list, ignore_index=True)
final_df = final_df[final_df["Confidence"] >= min_conf]

if final_df.empty:
    st.info("No detections above this confidence yet. Try lowering the slider.")
    st.stop()

# Summary
c1, c2, c3 = st.columns(3)
c1.metric("Detections", len(final_df))
c2.metric("Species", final_df["Common name"].nunique())
c3.metric("Chunks analyzed", len(all_files))

species_counts = (
    final_df.groupby("Common name")
    .agg(Detections=("Confidence", "size"), Avg_Confidence=("Confidence", "mean"))
    .sort_values("Detections", ascending=False)
    .reset_index()
    .rename(columns={"Common name": "Species"})
)

st.subheader("Species Detected on Walk")
left, right = st.columns([1, 1])
left.dataframe(species_counts, use_container_width=True, hide_index=True)
right.bar_chart(species_counts.set_index("Species")["Detections"])

st.subheader("Detections Over Time")
timeline = final_df.set_index("Detected At").resample("1min").size()
st.line_chart(timeline)

st.subheader("Raw Detection Log")
st.dataframe(
    final_df.sort_values("Detected At", ascending=False)[
        ["Detected At", "Common name", "Scientific name", "Confidence"]
    ],
    use_container_width=True,
    hide_index=True,
)