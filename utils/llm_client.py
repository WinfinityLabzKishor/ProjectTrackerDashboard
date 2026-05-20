# utils/llm_client.py

import json
import google.generativeai as genai
import streamlit as st

SYSTEM_PROMPT = """
You are a project tracker analyst. You will receive raw data extracted from one sheet of an Excel file containing project tracking information.

Analyse the data and return a structured JSON object. The sheet may have any structure — infer meaning from context, not fixed column names.

Return ONLY valid JSON, no explanation, no markdown, no backticks.

The JSON must follow this structure exactly:
{
  "meta": {
    "programme_name": string or null,
    "programme_window": string or null,
    "total_days": number or null,
    "sponsors": [string] or [],
    "prepared_by": string or null,
    "as_of_date": string (YYYY-MM-DD) or null,
    "programme_status": string or null
  },
  "kpis": {
    "days_elapsed": number or null,
    "days_remaining": number or null,
    "pct_time_elapsed": number or null,
    "pct_work_complete": number or null,
    "phases_total": number or null,
    "phases_complete": number or null,
    "phases_in_flight": number or null,
    "active_risks": number or null
  },
  "phases": [
    {
      "id": string,
      "name": string,
      "start": string (YYYY-MM-DD),
      "end": string (YYYY-MM-DD),
      "owner": string,
      "status": string (DONE | IN FLIGHT | UPCOMING),
      "pct_complete": number
    }
  ],
  "tasks": [
    {
      "phase_id": string,
      "task": string,
      "owner": string,
      "planned_start": string (YYYY-MM-DD),
      "planned_end": string (YYYY-MM-DD),
      "actual_start": string or null,
      "actual_end": string or null,
      "status": string (DONE | IN FLIGHT | UPCOMING),
      "pct_complete": number,
      "is_milestone": boolean,
      "notes": string
    }
  ],
  "risks": [
    {
      "id": string,
      "description": string,
      "impact": string (HIGH | MEDIUM | LOW),
      "mitigation": string,
      "owner": string
    }
  ],
  "critical_actions": [
    {
      "when_label": string,
      "due_date": string (YYYY-MM-DD),
      "action": string,
      "owner": string,
      "status": string (OPEN | DONE),
      "why_it_matters": string
    }
  ]
}

Rules:
- Only extract what is present in this sheet
- If a field is not found in this sheet, use null for strings, 0 for numbers, [] for arrays
- Never hallucinate data
"""

MERGE_PROMPT = """
You will receive a list of JSON objects, each extracted from one sheet of the same Excel file.

Merge them into a single coherent JSON object following the same structure.

Rules:
- For meta and kpis: use the most complete/non-null values across all sheets
- For phases, tasks, risks, critical_actions: combine all items, remove exact duplicates
- Return ONLY valid JSON, no explanation, no markdown, no backticks

Structure to return:
{
  "meta": { "programme_name": string, "programme_window": string, "total_days": number, "sponsors": [string], "prepared_by": string, "as_of_date": string, "programme_status": string },
  "kpis": { "days_elapsed": number, "days_remaining": number, "pct_time_elapsed": number, "pct_work_complete": number, "phases_total": number, "phases_complete": number, "phases_in_flight": number, "active_risks": number },
  "phases": [...],
  "tasks": [...],
  "risks": [...],
  "critical_actions": [...]
}
"""

def get_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT
    )

def parse_json(raw: str) -> dict:
    raw = raw.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def normalise_percentages(data: dict) -> dict:
    # normalize any 0-1 range values to 0-100
    kpis = data.get("kpis", {})
    for key in ["pct_time_elapsed", "pct_work_complete"]:
        val = kpis.get(key)
        if val is not None and 0 < val <= 1:
            kpis[key] = round(val * 100, 1)

    for phase in data.get("phases", []):
        val = phase.get("pct_complete")
        if val is not None and 0 < val <= 1:
            phase["pct_complete"] = round(val * 100, 1)

    for task in data.get("tasks", []):
        val = task.get("pct_complete")
        if val is not None and 0 < val <= 1:
            task["pct_complete"] = round(val * 100, 1)

    return data

def analyse_sheet(model, sheet_name: str, sheet_text: str) -> dict:
    response = model.generate_content(f"Sheet name: {sheet_name}\n\n{sheet_text}")
    return parse_json(response.text)

def merge_results(sheet_results: list) -> dict:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    merge_model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=MERGE_PROMPT
    )
    response = merge_model.generate_content(json.dumps(sheet_results))
    return parse_json(response.text)

def analyse_excel(excel_data: dict) -> dict:
    model = get_model()
    results = []

    for sheet_name, sheet_text in excel_data.items():
        if not sheet_text.strip():
            continue
        try:
            result = analyse_sheet(model, sheet_name, sheet_text)
            results.append(result)
        except Exception as e:
            st.warning(f"Sheet '{sheet_name}' failed: {e}")

    if len(results) == 1:
        final = results[0]
    else:
        final = merge_results(results)

    return normalise_percentages(final)