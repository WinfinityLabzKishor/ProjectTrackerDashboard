# NeoNiche Programme Tracker Dashboard

[View Dashboard](https://winfinitylabzprojecttrackerdashboard.streamlit.app/)

A web-based dashboard for tracking the NeoNiche 90-Day Programme — built to replace manual reporting with an automated, always-live view of project status.

## What it does

- Admin uploads an Excel tracker file
- The file is analysed automatically and a structured dashboard is generated
- The dashboard is publicly accessible to all stakeholders without login
- Historical uploads are stored, enabling comparison between any two versions

## Features

- Current dashboard — KPIs, phases, tasks, Gantt chart, risks, critical actions
- History and comparison — track changes over time, colour-coded by nature of change
- Schema-flexible — handles changes in Excel structure, new/removed sheets, columns, phases, and tasks
- Two separate views — admin (upload) and public (view only)

## Tech Stack

- [Streamlit](https://streamlit.io) — frontend and hosting
- [Google Gemini API](https://aistudio.google.com) — AI-powered Excel analysis
- [Supabase](https://supabase.com) — data storage
- Python — backend logic

## Project Structure

```
neoniche-tracker/
├── .streamlit/
│   └── secrets.toml        # API keys and credentials (not committed)
├── pages/
│   └── admin.py            # Admin upload page
├── utils/
│   ├── excel_parser.py     # Excel to text extraction
│   ├── llm_client.py       # Gemini API integration
│   └── supabase_client.py  # Supabase read/write
├── app.py                  # Public dashboard
├── requirements.txt
└── .gitignore
```

## Setup

1. Clone the repo
2. Install dependencies — `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml` with the following:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
SUPABASE_URL = "your_supabase_project_url"
SUPABASE_ANON_KEY = "your_supabase_anon_key"
```

4. Run locally — `streamlit run app.py`

## Usage

- Public dashboard — open the app URL
- History — switch to the History tab on the public dashboard

## Notes

- All times are stored and displayed in IST
- The dashboard persists the last uploaded report until a new file is uploaded