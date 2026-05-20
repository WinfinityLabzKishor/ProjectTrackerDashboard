# utils/supabase_client.py

import json
from datetime import datetime, timezone, timedelta
from supabase import create_client
import streamlit as st

def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

def save_snapshot(data: dict):
    client = get_client()
    from datetime import timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    client.table("snapshots").insert({
        "uploaded_at": now_ist,
        "data": json.dumps(data)
    }).execute()

def get_latest() -> dict | None:
    client = get_client()
    result = client.table("snapshots") \
        .select("*") \
        .order("uploaded_at", desc=True) \
        .limit(1) \
        .execute()

    if result.data:
        return {
            "uploaded_at": result.data[0]["uploaded_at"],
            "data": json.loads(result.data[0]["data"])
        }
    return None

def get_all_snapshots() -> list:
    client = get_client()
    result = client.table("snapshots") \
        .select("*") \
        .order("uploaded_at", desc=True) \
        .execute()

    return [
        {
            "uploaded_at": row["uploaded_at"],
            "data": json.loads(row["data"])
        }
        for row in result.data
    ]