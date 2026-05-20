# pages/admin.py

import streamlit as st
from utils.excel_parser import parse_excel
from utils.llm_client import analyse_excel
from utils.supabase_client import save_snapshot, get_latest

st.set_page_config(page_title="Admin — Upload", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.title("Admin — Upload Tracker")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    with st.spinner("Parsing Excel..."):
        excel_text = parse_excel(uploaded_file)

    with st.spinner("Analysing ..."):
        try:
            data = analyse_excel(excel_text)
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

    with st.spinner("Saving to Supabase..."):
        try:
            save_snapshot(data)
        except Exception as e:
            st.error(f"Failed to save snapshot: {e}")
            st.stop()

    st.success("Analysis complete. Dashboard has been updated with the latest data.")
    # st.json(data)