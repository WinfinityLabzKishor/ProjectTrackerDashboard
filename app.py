# app.py

import streamlit as st
from utils.supabase_client import get_latest, get_all_snapshots
from datetime import datetime,timezone,timedelta

st.set_page_config(page_title="NeoNiche Programme Tracker", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* rectangular progress bars */
.stProgress > div > div > div > div {
    border-radius: 2px;
}
.stProgress > div > div {
    border-radius: 2px;
}
</style>
""", unsafe_allow_html=True)

def format_date(d):
    try:
        return datetime.fromisoformat(d).strftime("%d %b %Y")
    except:
        return d or "—"

def status_badge(status):
    colours = {
        "DONE": "🟢",
        "IN FLIGHT": "🟡",
        "UPCOMING": "⚪",
        "ON TRACK": "🟢",
        "AT RISK": "🔴",
        "DELAYED": "🔴"
    }
    return f"{colours.get(status.upper(), '⚪')} {status}"

def render_gantt(phases, tasks, kpis, meta):
    st.markdown("### Gantt Chart")

    total_days = meta.get('total_days', 91)
    days_elapsed = kpis.get('days_elapsed', 0)

    try:
        all_starts = [p.get('start') for p in phases if p.get('start')]
        base_date = datetime.fromisoformat(min(all_starts)) if all_starts else datetime.today()
    except:
        base_date = datetime.today()

    def day_offset(date_str):
        try:
            return (datetime.fromisoformat(date_str) - base_date).days
        except:
            return 0

    status_colours = {
        "DONE": "#4CAF50",
        "IN FLIGHT": "#2196F3",
        "UPCOMING": "#9E9E9E",
        "ACTIVE": "#2196F3",
        "PENDING": "#FF9800"
    }

    today_pct = (days_elapsed / total_days) * 100

    gantt_html = f"""
<style>
.gantt-wrap {{ overflow-x: auto; font-family: sans-serif; font-size: 12px; }}
.gantt-inner {{ min-width: 600px; }}
.gantt-row {{ display: flex; align-items: center; margin-bottom: 3px; }}
.gantt-label {{ width: 160px; flex-shrink: 0; position: sticky; left: 0; z-index: 2; padding-right: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.gantt-bar-wrap {{ flex: 1; position: relative; height: 18px; background: #f0f0f0; border-radius: 2px; }}
.gantt-bar {{ position: absolute; height: 100%; border-radius: 2px; opacity: 0.85; }}
.gantt-today {{ position: absolute; top: 0; bottom: 0; width: 2px; background: red; z-index: 10; left: {today_pct:.1f}%; }}

/* checkbox hack for collapsible */
.gantt-toggle {{ display: none; }}
.gantt-tasks {{ display: none; }}
.gantt-toggle:checked ~ .gantt-tasks {{ display: block; }}
.gantt-toggle:checked ~ .phase-row-wrap .toggle-icon::before {{ content: '▼'; }}
.toggle-icon::before {{ content: '▶'; font-size: 10px; margin-right: 4px; }}
.phase-label-wrap {{ cursor: pointer; display: flex; align-items: center; width: 160px; flex-shrink: 0; position: sticky; left: 0; background: #f9f9f9; z-index: 2; padding-right: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: bold; }}
</style>
<div class="gantt-wrap">
  <div class="gantt-inner">
    <div class="gantt-row" style="border-bottom:1px solid #ccc; margin-bottom:6px; padding-bottom:4px;">
      <div style="width:160px; flex-shrink:0; font-weight:bold; background:white; position:sticky; left:0; z-index:2;">Phase / Task</div>
      <div style="flex:1; display:flex; justify-content:space-between; font-size:10px; color:#888;">
        <span>Day 0</span><span>Day {total_days//4}</span><span>Day {total_days//2}</span><span>Day {3*total_days//4}</span><span>Day {total_days}</span>
      </div>
    </div>
"""

    for i, phase in enumerate(phases):
        phase_tasks = [t for t in tasks if t.get('phase_id') == phase.get('id')]
        start_day = day_offset(phase.get('start'))
        end_day = day_offset(phase.get('end'))
        duration = max(end_day - start_day, 1)
        left_pct = (start_day / total_days) * 100
        width_pct = (duration / total_days) * 100
        colour = status_colours.get(phase.get('status', '').upper(), '#9E9E9E')
        has_tasks = len(phase_tasks) > 0
        chk_id = f"chk_{i}"

        if has_tasks:
            gantt_html += f'<input type="checkbox" class="gantt-toggle" id="{chk_id}">'

        gantt_html += f"""
    <div class="phase-row-wrap">
      <div class="gantt-row" style="background:#f9f9f9;">
        {'<label for="' + chk_id + '" class="phase-label-wrap"><span class="toggle-icon"></span>' + phase.get('id','') + ' · ' + phase.get('name','') + '</label>' if has_tasks else '<div class="phase-label-wrap" style="cursor:default;"><span style="margin-right:14px;"></span>' + phase.get('id','') + ' · ' + phase.get('name','') + '</div>'}
        <div class="gantt-bar-wrap">
          <div class="gantt-bar" style="left:{left_pct:.1f}%; width:{width_pct:.1f}%; background:{colour};"></div>
          <div class="gantt-today"></div>
        </div>
      </div>
    </div>
"""

        if has_tasks:
            gantt_html += f'<div class="gantt-tasks" id="tasks_{i}">'
            for task in phase_tasks:
                t_start = day_offset(task.get('planned_start'))
                t_end = day_offset(task.get('planned_end'))
                t_duration = max(t_end - t_start, 1)
                t_left = (t_start / total_days) * 100
                t_width = (t_duration / total_days) * 100
                t_colour = status_colours.get(task.get('status', '').upper(), '#9E9E9E')
                milestone = " 🏁" if task.get('is_milestone') else ""
                gantt_html += f"""
      <div class="gantt-row">
        <div style="width:160px; flex-shrink:0; position:sticky; left:0; background:white; z-index:2; padding-left:16px; padding-right:8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-size:11px;">{task.get('task','')}{milestone}</div>
        <div class="gantt-bar-wrap">
          <div class="gantt-bar" style="left:{t_left:.1f}%; width:{t_width:.1f}%; background:{t_colour};"></div>
          <div class="gantt-today"></div>
        </div>
      </div>
"""
            gantt_html += '</div>'

    gantt_html += f"""
    <div style="font-size:11px; margin-top:10px; color:#666; display:flex; gap:12px; flex-wrap:wrap;">
      <span><span style="display:inline-block;width:12px;height:12px;background:#4CAF50;border-radius:2px;margin-right:4px;"></span>Done</span>
      <span><span style="display:inline-block;width:12px;height:12px;background:#2196F3;border-radius:2px;margin-right:4px;"></span>In Flight / Active</span>
      <span><span style="display:inline-block;width:12px;height:12px;background:#FF9800;border-radius:2px;margin-right:4px;"></span>Pending</span>
      <span><span style="display:inline-block;width:12px;height:12px;background:#9E9E9E;border-radius:2px;margin-right:4px;"></span>Upcoming</span>
      <span><span style="display:inline-block;width:12px;height:12px;background:red;border-radius:2px;margin-right:4px;"></span>Today</span>
    </div>
  </div>
</div>
"""
    st.html(gantt_html)

def programme_status_display(status: str):
    if not status:
        return "—", "#888"
    s = status.upper()
    if any(x in s for x in ["ON TRACK", "ADVANCE", "AHEAD"]):
        return "ON TRACK", "#4CAF50"
    elif any(x in s for x in ["AT RISK", "DELAYED", "DELAY", "AMBER"]):
        return "AT RISK", "#FF9800"
    elif any(x in s for x in ["CRITICAL", "RED", "BEHIND"]):
        return "CRITICAL", "#f44336"
    else:
        return status.split(".")[0].split("·")[0].strip(), "#888"

def render_dashboard(data):

    IST = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(IST)
    st.markdown(f"""
    <div style="text-align:center; font-size:14px; color:#444; margin-bottom:8px; font-weight:500;">
        {now_ist.strftime("%A, %d %b %Y")}
    </div>
    """, unsafe_allow_html=True)
    
    meta = data.get("meta", {})
    kpis = data.get("kpis", {})
    phases = data.get("phases", [])
    tasks = data.get("tasks", [])
    risks = data.get("risks", [])
    actions = data.get("critical_actions", [])

    # HEADER
    st.markdown(f"## {meta.get('programme_name', 'Programme Dashboard')}")
    st.caption(f"{meta.get('programme_window', '')} · Prepared by {meta.get('prepared_by', '')} · As of {format_date(meta.get('as_of_date', ''))}")
    st.caption(f"Sponsors: {', '.join(meta.get('sponsors', []))}")

    st.divider()

    # KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    p_status, p_colour = programme_status_display(meta.get('programme_status', ''))
    c1.markdown(f"""
<div style="background:{p_colour}18; border-left:4px solid {p_colour}; border-radius:4px; padding:8px 12px;">
  <div style="font-size:12px; color:#666; margin-bottom:2px;">Programme Status</div>
  <div style="font-size:20px; font-weight:bold; color:{p_colour};">{p_status}</div>
</div>
""", unsafe_allow_html=True)
    
    c2.metric("Phases Done", f"{kpis.get('phases_complete', 0)} / {kpis.get('phases_total', 0)}")
    c3.metric("Work Complete", f"{kpis.get('pct_work_complete', 0)}%", f"vs {kpis.get('pct_time_elapsed', 0)}% time")
    c4.metric("Day", f"{kpis.get('days_elapsed', 0)} / {meta.get('total_days', 0)}", f"{kpis.get('pct_time_elapsed', 0)}% elapsed")
    c5.metric("Days Remaining", kpis.get('days_remaining', 0))
    
    programme_status = meta.get('programme_status', '—')
    active_risks = kpis.get('active_risks', 0)


    st.divider()

    # PROGRESS BAR
    pct_work = kpis.get('pct_work_complete', 0)
    pct_time = kpis.get('pct_time_elapsed', 0)
    ahead = pct_work - pct_time

    st.markdown("**Programme Progress vs Time Elapsed**")
    st.markdown(f"""
<div style="margin-bottom: 6px; font-size: 13px; color: #666;">
    Work done vs time spent — {'🟢 Ahead by' if ahead >= 0 else '🔴 Behind by'} <strong>{abs(ahead):.0f} percentage points</strong>
</div>
<div style="margin-bottom: 4px; display: flex; align-items: center; gap: 10px;">
    <div style="width: 120px; font-size: 13px;">Work Complete</div>
    <div style="flex: 1; background: #e0e0e0; border-radius: 2px; height: 20px; position: relative;">
        <div style="width: {pct_work}%; background: #2196F3; height: 100%; border-radius: 2px;"></div>
        <div style="position: absolute; top: 0; left: {pct_work}%; transform: translateX(-50%); font-size: 11px; color: #333; line-height: 20px; padding: 0 4px; background: white; border-radius: 2px;">{pct_work}%</div>
    </div>
</div>
<div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 120px; font-size: 13px;">Time Elapsed</div>
    <div style="flex: 1; background: #e0e0e0; border-radius: 2px; height: 20px; position: relative;">
        <div style="width: {pct_time}%; background: #FF9800; height: 100%; border-radius: 2px;"></div>
        <div style="position: absolute; top: 0; left: {pct_time}%; transform: translateX(-50%); font-size: 11px; color: #333; line-height: 20px; padding: 0 4px; background: white; border-radius: 2px;">{pct_time}%</div>
    </div>
</div>
""", unsafe_allow_html=True)
    st.divider()

    st.divider()

    # PHASES
    st.markdown("### Phases")
    for phase in phases:
        with st.expander(f"{phase.get('id', '')} · {phase.get('name', '')} · {status_badge(phase.get('status', ''))}"):
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"**Dates:** {format_date(phase.get('start'))} → {format_date(phase.get('end'))}")
            col2.markdown(f"**Owner:** {phase.get('owner', '—')}")
            col3.markdown(f"**Complete:** {phase.get('pct_complete', 0)}%")
            st.progress(phase.get('pct_complete', 0) / 100)

            phase_tasks = [t for t in tasks if t.get('phase_id') == phase.get('id')]
            if phase_tasks:
                st.markdown("**Tasks:**")
                for task in phase_tasks:
                    milestone = " 🏁" if task.get('is_milestone') else ""

                    start = task.get('planned_start')
                    end = task.get('planned_end')
                    date_str = f"· {format_date(start)} → {format_date(end)} " if start and end else ""

                    pct = task.get('pct_complete', 0)
                    pct_str = f"· {pct}%" if pct and pct > 0 else ""

                    notes_str = f"· *{task['notes']}*" if task.get('is_milestone') and task.get('notes') else ""

                    st.markdown(
                        f"- {status_badge(task.get('status', ''))} **{task.get('task', '')}**{milestone} "
                        f"· {task.get('owner', '—')} "
                        f"{date_str}{pct_str} {notes_str}"
                    )

    st.divider()

    render_gantt(phases, tasks, kpis, meta)

    # CRITICAL ACTIONS
    if actions:
        st.markdown("### Critical Actions")
        for action in actions:
            status = action.get('status', 'OPEN')
            border = "🔴" if status == "OPEN" else "✅"
            with st.expander(f"{border} {action.get('action', '')} · Due {format_date(action.get('due_date'))}"):
                st.markdown(f"**When:** {action.get('when_label', '—')}")
                st.markdown(f"**Owner:** {action.get('owner', '—')}")
                if action.get('why_it_matters'):
                    st.markdown(f"**Why it matters:** {action.get('why_it_matters')}")

    st.divider()

    # RISKS
    if risks:
        st.markdown("### Risks")
        for risk in risks:
            impact = risk.get('impact', 'MEDIUM')
            icon = "🔴" if impact == "HIGH" else "🟡" if impact == "MEDIUM" else "🟢"
            with st.expander(f"{icon} {risk.get('id', '')} · {risk.get('description', '')}"):
                st.markdown(f"**Impact:** {impact}")
                st.markdown(f"**Owner:** {risk.get('owner', '—')}")
                if risk.get('mitigation'):
                    st.markdown(f"**Mitigation:** {risk.get('mitigation')}")


def render_history(snapshots):
    st.markdown("### Historical Snapshots")

    if len(snapshots) < 2:
        st.info("At least 2 uploads needed for comparison.")
        return

    def format_upload_time(ts):
        try:
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S IST")
            return dt.strftime("%d-%b-%Y %I:%M %p IST")
        except:
            return ts

    labels = [format_upload_time(s['uploaded_at']) for s in snapshots]

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        idx_a = st.selectbox("Compare (older)", range(len(snapshots)), format_func=lambda i: labels[i], index=1)
    with col2:
        idx_b = st.selectbox("Compare (newer)", range(len(snapshots)), format_func=lambda i: labels[i], index=0)

    snap_a = snapshots[idx_a]
    snap_b = snapshots[idx_b]

    st.divider()

    # LEGEND
    st.markdown("""
<div style="font-size:12px; display:flex; gap:16px; flex-wrap:wrap; margin-bottom:8px;">
  <span style="color:#1a7f37;">● Completed / Improved / Risk Closed</span>
  <span style="color:#b08800;">● Progressed but not done</span>
  <span style="color:#cf222e;">● No progress / Regressed / New Risk</span>
  <span style="color:#0969da;">● Newly Added</span>
  <span style="color:#6e7781;">● Removed</span>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # KPI COMPARISON
    st.markdown("#### KPI Comparison")
    kpis_a = snap_a['data'].get('kpis', {})
    kpis_b = snap_b['data'].get('kpis', {})
    meta_b = snap_b['data'].get('meta', {})

    total_days = meta_b.get('total_days', 0)
    days_elapsed = kpis_b.get('days_elapsed', 0)
    days_remaining = kpis_b.get('days_remaining', 0)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Timeline",
        f"Day {days_elapsed} of {total_days}",
        f"{days_remaining} days left"
    )

    pct_work_a = kpis_a.get('pct_work_complete', 0)
    pct_work_b = kpis_b.get('pct_work_complete', 0)
    delta_work = pct_work_b - pct_work_a
    col2.metric("Work Complete", f"{pct_work_b}%", f"{delta_work:+}%" if delta_work != 0 else "no change")

    phases_done_a = kpis_a.get('phases_complete', 0)
    phases_done_b = kpis_b.get('phases_complete', 0)
    delta_phases = phases_done_b - phases_done_a
    col3.metric("Phases Done", f"{phases_done_b} / {kpis_b.get('phases_total', 0)}", f"{delta_phases:+}" if delta_phases != 0 else "no change")

    risks_a = kpis_a.get('active_risks', 0)
    risks_b = kpis_b.get('active_risks', 0)
    delta_risks = risks_b - risks_a
    # inverse delta — fewer risks is good
    col4.metric(
        "Active Risks",
        risks_b,
        delta=f"{delta_risks:+}" if delta_risks != 0 else "no change",
        delta_color="inverse"
    )

    st.divider()

    # PHASE CHANGES
    st.markdown("#### Phase Changes")
    phases_a_by_id = {p['id']: p for p in snap_a['data'].get('phases', [])}
    phases_b_by_id = {p['id']: p for p in snap_b['data'].get('phases', [])}
    phases_a_by_name = {p['name']: p for p in snap_a['data'].get('phases', [])}
    phases_b_by_name = {p['name']: p for p in snap_b['data'].get('phases', [])}

    added_phases, removed_phases, changed_phases = [], [], []

    for pid, p in phases_b_by_id.items():
        if pid in phases_a_by_id:
            pa = phases_a_by_id[pid]
            diffs = []
            if pa.get('status') != p.get('status'):
                diffs.append(f"status: {pa.get('status')} → {p.get('status')}")
            if pa.get('pct_complete') != p.get('pct_complete'):
                diffs.append(f"progress: {pa.get('pct_complete')}% → {p.get('pct_complete')}%")
            if pa.get('owner') != p.get('owner'):
                diffs.append(f"owner: {pa.get('owner')} → {p.get('owner')}")
            if diffs:
                changed_phases.append({"phase": p, "prev": pa, "diffs": diffs})
        elif p['name'] in phases_a_by_name:
            pa = phases_a_by_name[p['name']]
            diffs = ["id changed: possibly renumbered"]
            if pa.get('status') != p.get('status'):
                diffs.append(f"status: {pa.get('status')} → {p.get('status')}")
            if pa.get('pct_complete') != p.get('pct_complete'):
                diffs.append(f"progress: {pa.get('pct_complete')}% → {p.get('pct_complete')}%")
            changed_phases.append({"phase": p, "prev": pa, "diffs": diffs})
        else:
            added_phases.append(p)

    for pid, p in phases_a_by_id.items():
        if pid not in phases_b_by_id and p['name'] not in phases_b_by_name:
            removed_phases.append(p)

    def phase_change_colour(p_new, p_old):
        status_new = p_new.get('status', '').upper()
        status_old = p_old.get('status', '').upper()
        pct_new = p_new.get('pct_complete', 0)
        pct_old = p_old.get('pct_complete', 0)

        status_order = {'UPCOMING': 1, 'PENDING': 2, 'ACTIVE': 2, 'IN FLIGHT': 3, 'DONE': 4, 'COMPLETED': 4}

        if status_new in ('DONE', 'COMPLETED'):
            return st.success
        elif status_order.get(status_new, 0) > status_order.get(status_old, 0):
            return st.warning
        elif pct_new > pct_old:
            return st.warning
        elif pct_new < pct_old:
            return st.error
        else:
            return st.warning

    if added_phases:
        st.markdown("**Added phases:**")
        for p in added_phases:
            st.info(f"+ {p.get('id')} · {p.get('name')} · {p.get('status')} · {p.get('pct_complete')}%")
    if removed_phases:
        st.markdown("**Removed phases:**")
        for p in removed_phases:
            st.markdown(f"<div style='color:#6e7781; padding:4px 0;'>— {p.get('id')} · {p.get('name')}</div>", unsafe_allow_html=True)

    if changed_phases or phases_b_by_id:
        st.markdown("**Phase Progress:**")
        bar_rows = []
        for pid, p in phases_b_by_id.items():
            prev = phases_a_by_id.get(pid) or phases_a_by_name.get(p.get('name', ''))
            prev_pct = prev.get('pct_complete', 0) if prev else 0
            curr_pct = p.get('pct_complete', 0)
            gained = max(curr_pct - prev_pct, 0)
            remaining = max(100 - curr_pct, 0)
            bar_rows.append({
                "label": f"{p.get('id')} · {p.get('name')}",
                "prev": prev_pct,
                "gained": gained,
                "remaining": remaining
            })

        bar_html = """
<style>
.gained-bar {
  background-image: repeating-linear-gradient(
    -45deg,
    transparent,
    transparent 4px,
    rgba(33,150,243,0.6) 4px,
    rgba(33,150,243,0.6) 6px
  );
  background-color: #e8f4fd;
}
</style>
<div style="overflow-x:auto;">
<div style="min-width:600px;">
<div style="font-size:12px; margin-bottom:8px; display:flex; gap:16px; flex-wrap:wrap;">
  <span><span style="display:inline-block;width:12px;height:12px;background:#2196F3;margin-right:4px;border-radius:2px;"></span>Previous progress</span>
  <span><span style="display:inline-block;width:12px;height:12px;background-image:repeating-linear-gradient(-45deg,transparent,transparent 4px,rgba(33,150,243,0.6) 4px,rgba(33,150,243,0.6) 6px);background-color:#e8f4fd;margin-right:4px;border-radius:2px;"></span>New progress</span>
  <span><span style="display:inline-block;width:12px;height:12px;background:#f0f0f0;border:1px solid #ccc;margin-right:4px;border-radius:2px;"></span>Remaining</span>
</div>
<div style="font-family:sans-serif; font-size:13px;">
"""
        for row in bar_rows:
            bar_html += f"""
<div style="display:flex; align-items:center; margin-bottom:8px;">
  <div style="width:200px; flex-shrink:0; padding-right:10px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-size:12px; position:sticky; left:0; background:white; z-index:1;">{row['label']}</div>
  <div style="flex:1; display:flex; height:22px; border-radius:2px; overflow:hidden; border:1px solid #ddd;">
    <div style="width:{row['prev']}%; background:#2196F3; display:flex; align-items:center; justify-content:center; overflow:hidden;">
      {'<span style="color:white; font-size:10px; white-space:nowrap; padding:0 4px;">Existing Work</span>' if row['prev'] > 8 else ''}
    </div>
    <div class="gained-bar" style="width:{row['gained']}%; display:flex; align-items:center; justify-content:center; overflow:hidden;">
      {'<span style="color:black; font-size:10px; white-space:nowrap; padding:0 4px; text-shadow:0 0 3px rgba(0,0,0,0.5);">Progress Made</span>' if row['gained'] > 5 else ''}
    </div>
    <div style="width:{row['remaining']}%; background:#f0f0f0;"></div>
  </div>
  <div style="width:70px; text-align:right; font-size:12px; color:#444; padding-left:8px;">{int(row['prev']+row['gained'])}% done</div>
</div>
"""
        bar_html += "</div></div>"
        st.html(bar_html)

    if not added_phases and not removed_phases and not changed_phases:
        st.info("No phase changes between these two uploads.")

    st.divider()

    st.divider()

    # TASK CHANGES
    st.markdown("#### Task Changes")

    def task_key(t):
        return f"{t.get('phase_id', '')}::{t.get('task', '')}"

    tasks_a = {task_key(t): t for t in snap_a['data'].get('tasks', [])}
    tasks_b = {task_key(t): t for t in snap_b['data'].get('tasks', [])}

    added_tasks, removed_tasks, changed_tasks = [], [], []

    for key, t in tasks_b.items():
        if key in tasks_a:
            ta = tasks_a[key]
            diffs = []
            if ta.get('status') != t.get('status'):
                diffs.append(f"status: {ta.get('status')} → {t.get('status')}")
            if ta.get('pct_complete') != t.get('pct_complete'):
                diffs.append(f"progress: {ta.get('pct_complete')}% → {t.get('pct_complete')}%")
            if ta.get('owner') != t.get('owner'):
                diffs.append(f"owner: {ta.get('owner')} → {t.get('owner')}")
            if ta.get('planned_end') != t.get('planned_end'):
                diffs.append(f"due date: {format_date(ta.get('planned_end'))} → {format_date(t.get('planned_end'))}")
            if diffs:
                changed_tasks.append({"task": t, "prev": ta, "diffs": diffs})
        else:
            added_tasks.append(t)

    for key, t in tasks_a.items():
        if key not in tasks_b:
            removed_tasks.append(t)

    def task_change_colour(t_new, t_old):
        status_new = t_new.get('status', '').upper()
        status_old = t_old.get('status', '').upper()
        pct_new = t_new.get('pct_complete', 0)
        pct_old = t_old.get('pct_complete', 0)

        status_order = {'UPCOMING': 1, 'PENDING': 2, 'ACTIVE': 2, 'IN FLIGHT': 3, 'DONE': 4, 'COMPLETED': 4}

        if status_new in ('DONE', 'COMPLETED'):
            return st.success
        elif status_order.get(status_new, 0) > status_order.get(status_old, 0):
            return st.warning  # status progressed forward
        elif pct_new > pct_old:
            return st.warning  # percentage progressed
        elif pct_new < pct_old:
            return st.error    # regressed
        else:
            return st.warning  # something changed but neutral — don't penalise

    if added_tasks:
        st.markdown("**Added:**")
        for t in added_tasks:
            st.info(f"+ [{t.get('phase_id')}] {t.get('task')} · {t.get('status')} · {t.get('pct_complete')}%")
    if removed_tasks:
        st.markdown("**Removed:**")
        for t in removed_tasks:
            st.markdown(f"<div style='color:#6e7781; padding:4px 0;'>— [{t.get('phase_id')}] {t.get('task')}</div>", unsafe_allow_html=True)
    if changed_tasks:
        st.markdown("**Changed:**")
        for c in changed_tasks:
            fn = task_change_colour(c['task'], c['prev'])
            fn(f"~ [{c['task'].get('phase_id')}] {c['task'].get('task')}: {', '.join(c['diffs'])}")
    if not added_tasks and not removed_tasks and not changed_tasks:
        st.info("No task changes between these two uploads.")

    st.divider()

    # RISK CHANGES
    st.markdown("#### Risk Changes")
    risks_a_map = {r['id']: r for r in snap_a['data'].get('risks', [])}
    risks_b_map = {r['id']: r for r in snap_b['data'].get('risks', [])}

    added_risks, removed_risks, changed_risks = [], [], []

    for rid, r in risks_b_map.items():
        if rid in risks_a_map:
            ra = risks_a_map[rid]
            diffs = []
            if ra.get('impact') != r.get('impact'):
                diffs.append(f"impact: {ra.get('impact')} → {r.get('impact')}")
            if ra.get('mitigation') != r.get('mitigation'):
                diffs.append("mitigation updated")
            if ra.get('owner') != r.get('owner'):
                diffs.append(f"owner: {ra.get('owner')} → {r.get('owner')}")
            if diffs:
                changed_risks.append({"risk": r, "prev": ra, "diffs": diffs})
        else:
            added_risks.append(r)

    for rid, r in risks_a_map.items():
        if rid not in risks_b_map:
            removed_risks.append(r)

    def risk_change_colour(r_new, r_old):
        impact_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        new_impact = impact_order.get(r_new.get('impact', '').upper(), 2)
        old_impact = impact_order.get(r_old.get('impact', '').upper(), 2)
        if new_impact < old_impact:
            return st.success
        elif new_impact > old_impact:
            return st.error
        else:
            return st.warning

    if added_risks:
        st.markdown("**New risks:**")
        for r in added_risks:
            st.error(f"+ {r.get('id')} · {r.get('description')} · {r.get('impact')}")
    if removed_risks:
        st.markdown("**Closed risks:**")
        for r in removed_risks:
            st.success(f"✓ {r.get('id')} · {r.get('description')}")
    if changed_risks:
        st.markdown("**Changed risks:**")
        for c in changed_risks:
            fn = risk_change_colour(c['risk'], c['prev'])
            fn(f"~ {c['risk'].get('id')} · {c['risk'].get('description')}: {', '.join(c['diffs'])}")
    if not added_risks and not removed_risks and not changed_risks:
        st.info("No risk changes between these two uploads.")

    st.divider()

    # CRITICAL ACTION CHANGES
    st.markdown("#### Critical Action Changes")
    actions_a = {a.get('action', ''): a for a in snap_a['data'].get('critical_actions', [])}
    actions_b = {a.get('action', ''): a for a in snap_b['data'].get('critical_actions', [])}

    added_actions, removed_actions, changed_actions = [], [], []

    for key, a in actions_b.items():
        if key in actions_a:
            aa = actions_a[key]
            diffs = []
            if aa.get('status') != a.get('status'):
                diffs.append(f"status: {aa.get('status')} → {a.get('status')}")
            if aa.get('due_date') != a.get('due_date'):
                diffs.append(f"due date: {format_date(aa.get('due_date'))} → {format_date(a.get('due_date'))}")
            if aa.get('owner') != a.get('owner'):
                diffs.append(f"owner: {aa.get('owner')} → {a.get('owner')}")
            if diffs:
                changed_actions.append({"action": a, "prev": aa, "diffs": diffs})
        else:
            added_actions.append(a)

    for key, a in actions_a.items():
        if key not in actions_b:
            removed_actions.append(a)

    def action_change_colour(a_new, a_old):
        status = a_new.get('status', '').upper()
        if status == 'DONE':
            return st.success
        elif a_new.get('due_date', '') > a_old.get('due_date', ''):
            return st.error
        else:
            return st.warning

    if added_actions:
        st.markdown("**New actions:**")
        for a in added_actions:
            st.info(f"+ {a.get('action')} · Due {format_date(a.get('due_date'))} · {a.get('owner')}")
    if removed_actions:
        st.markdown("**Removed actions:**")
        for a in removed_actions:
            st.markdown(f"<div style='color:#6e7781; padding:4px 0;'>— {a.get('action')}</div>", unsafe_allow_html=True)
    if changed_actions:
        st.markdown("**Changed actions:**")
        for c in changed_actions:
            fn = action_change_colour(c['action'], c['prev'])
            fn(f"~ {c['action'].get('action')}: {', '.join(c['diffs'])}")
    if not added_actions and not removed_actions and not changed_actions:
        st.info("No action changes between these two uploads.")


# MAIN

latest = get_latest()

tab1, tab2 = st.tabs(["Current Dashboard", "History & Comparison"])

with tab1:
    if latest:
        st.caption(f"Last updated: {format_date(latest['uploaded_at'])}")
        render_dashboard(latest['data'])
    else:
        st.info("No data yet. Admin needs to upload the tracker file.")

with tab2:
    snapshots = get_all_snapshots()
    if snapshots:
        render_history(snapshots)
    else:
        st.info("No snapshots yet.")