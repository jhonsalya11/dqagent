"""Self-contained static HTML report — the "UI review" from the deep
research mockup (docs/research/2026-10-12-open-data-quality-deep-research.md),
implemented without a server: just open the .html file in any browser.

Accept/Edit/Reject decisions are stored in the browser's localStorage only
(keyed by dataset name) — nothing is sent anywhere, no backend, no spend.
Export button lets the reviewer download their decisions as JSON.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from .rules import Issue

_TEMPLATE = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>DQ Agent — Review: {dataset_name}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; margin: 0; background: #0f1115; color: #e6e6e6; }}
  header {{ padding: 16px 24px; background: #171a21; border-bottom: 1px solid #2a2e37; position: sticky; top: 0; }}
  header h1 {{ margin: 0 0 4px; font-size: 18px; }}
  header .stats {{ color: #9aa0ab; font-size: 13px; }}
  .controls {{ padding: 10px 24px; display: flex; gap: 8px; flex-wrap: wrap; background: #12141a; border-bottom: 1px solid #2a2e37; }}
  .controls button {{ background: #1f232c; color: #e6e6e6; border: 1px solid #2a2e37; border-radius: 6px; padding: 6px 12px; cursor: pointer; font-size: 12px; }}
  .controls button.active {{ background: #3b4252; border-color: #5e81ac; }}
  .controls .export {{ margin-left: auto; background: #2e7d32; border-color: #2e7d32; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ text-align: left; padding: 8px 24px; border-bottom: 1px solid #22252c; font-size: 13px; vertical-align: top; }}
  th {{ color: #9aa0ab; font-weight: 600; position: sticky; top: 92px; background: #0f1115; }}
  tr.resolved-terima {{ opacity: 0.45; }}
  tr.resolved-tolak {{ opacity: 0.6; }}
  .rule-badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; background: #2a2e37; font-size: 11px; color: #9aa0ab; }}
  .suggestion {{ color: #8bc48b; }}
  .actions button {{ margin-right: 4px; font-size: 11px; padding: 4px 8px; border-radius: 4px; border: 1px solid #2a2e37; background: #1f232c; color: #e6e6e6; cursor: pointer; }}
  .actions button.chosen {{ background: #5e81ac; border-color: #5e81ac; }}
  .hidden {{ display: none; }}
  .empty-state {{ padding: 40px 24px; color: #9aa0ab; text-align: center; }}
</style>
</head>
<body>
<header>
  <h1>Data Quality Review — {dataset_name}</h1>
  <div class="stats" id="stats"></div>
</header>
<div class="controls">
  <button data-filter="all" class="active">Semua</button>
  {rule_filter_buttons}
  <button class="export" id="exportBtn">Export keputusan (.json)</button>
</div>
<table>
  <thead>
    <tr><th>Baris</th><th>Kolom</th><th>Rule</th><th>Pesan</th><th>Saran</th><th>Keputusan</th></tr>
  </thead>
  <tbody id="issueBody"></tbody>
</table>
<div class="empty-state hidden" id="emptyState">Tidak ada isu untuk filter ini.</div>

<script>
const DATASET_NAME = {dataset_name_json};
const ISSUES = {issues_json};
const STORAGE_KEY = "dqagent_decisions::" + DATASET_NAME;

function loadDecisions() {{
  try {{ return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{{}}"); }}
  catch (e) {{ return {{}}; }}
}}
function saveDecisions(d) {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(d)); }}

let decisions = loadDecisions();
let currentFilter = "all";

function issueKey(issue, idx) {{ return idx + ":" + issue.row + ":" + issue.column + ":" + issue.rule; }}

function render() {{
  const tbody = document.getElementById("issueBody");
  tbody.innerHTML = "";
  const visible = ISSUES
    .map((issue, idx) => ({{issue, idx}}))
    .filter(({{issue}}) => currentFilter === "all" || issue.rule === currentFilter);

  document.getElementById("emptyState").classList.toggle("hidden", visible.length > 0);

  for (const {{issue, idx}} of visible) {{
    const key = issueKey(issue, idx);
    const decision = decisions[key];
    const tr = document.createElement("tr");
    if (decision) tr.className = "resolved-" + decision;

    tr.innerHTML = `
      <td>${{issue.row === -1 ? "(kolom)" : issue.row}}</td>
      <td>${{escapeHtml(issue.column)}}</td>
      <td><span class="rule-badge">${{escapeHtml(issue.rule)}}</span></td>
      <td>${{escapeHtml(issue.message)}}</td>
      <td class="suggestion">${{issue.suggestion ? escapeHtml(String(issue.suggestion)) : "-"}}</td>
      <td class="actions">
        <button data-action="terima" class="${{decision === "terima" ? "chosen" : ""}}">Terima</button>
        <button data-action="tolak" class="${{decision === "tolak" ? "chosen" : ""}}">Tolak</button>
        <button data-action="reset" class="${{!decision ? "chosen" : ""}}">Belum</button>
      </td>
    `;
    tr.querySelectorAll("button").forEach(btn => {{
      btn.addEventListener("click", () => {{
        const action = btn.dataset.action;
        if (action === "reset") delete decisions[key];
        else decisions[key] = action;
        saveDecisions(decisions);
        render();
      }});
    }});
    tbody.appendChild(tr);
  }}
  updateStats();
}}

function updateStats() {{
  const total = ISSUES.length;
  const terima = Object.values(decisions).filter(d => d === "terima").length;
  const tolak = Object.values(decisions).filter(d => d === "tolak").length;
  const belum = total - terima - tolak;
  document.getElementById("stats").textContent =
    `${{total}} isu total — ${{terima}} diterima, ${{tolak}} ditolak, ${{belum}} belum diputuskan`;
}}

function escapeHtml(s) {{
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}}

document.querySelectorAll(".controls button[data-filter]").forEach(btn => {{
  btn.addEventListener("click", () => {{
    currentFilter = btn.dataset.filter;
    document.querySelectorAll(".controls button[data-filter]").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    render();
  }});
}});

document.getElementById("exportBtn").addEventListener("click", () => {{
  const payload = ISSUES
    .map((issue, idx) => ({{issue, idx}}))
    .filter(({{issue, idx}}) => decisions[issueKey(issue, idx)])
    .map(({{issue, idx}}) => ({{ ...issue, decision: decisions[issueKey(issue, idx)] }}));
  const blob = new Blob([JSON.stringify(payload, null, 2)], {{type: "application/json"}});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = DATASET_NAME.replace(/[^a-z0-9_.-]/gi, "_") + "_decisions.json";
  a.click();
}});

render();
</script>
</body>
</html>
"""


def _rule_filter_buttons(issues: list[Issue]) -> str:
    rules = sorted({issue.rule for issue in issues})
    return "\n  ".join(
        f'<button data-filter="{html.escape(rule)}">{html.escape(rule)}</button>' for rule in rules
    )


def generate_html_report(issues: list[Issue], dataset_name: str, output_path: str) -> str:
    """Write a self-contained HTML review page. No server, no network calls."""
    issues_json = json.dumps([issue.to_dict() for issue in issues], ensure_ascii=False)
    html_out = _TEMPLATE.format(
        dataset_name=html.escape(dataset_name),
        dataset_name_json=json.dumps(dataset_name),
        issues_json=issues_json,
        rule_filter_buttons=_rule_filter_buttons(issues),
    )
    Path(output_path).write_text(html_out, encoding="utf-8")
    return output_path
