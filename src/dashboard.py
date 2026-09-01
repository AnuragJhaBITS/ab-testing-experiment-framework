"""
dashboard.py
------------
Flask dashboard for the checkout experiment.
Run:  python src/dashboard.py  ->  http://127.0.0.1:5000

Shows: conversion by arm with 95% CI, the guardrail check, power/MDE context,
and the pre-registered decision verdict.
"""
import os
import json
from flask import Flask, render_template_string

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))


def payload():
    with open(os.path.join(BASE, "output", "experiment_result.json")) as f:
        r = json.load(f)
    with open(os.path.join(BASE, "data", "power_summary.json")) as f:
        p = json.load(f)
    return {"r": r, "p": p}


TEMPLATE = """
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Checkout A/B Test — Readout</title>
<script src="/static/chart.umd.min.js"></script>
<style>
  :root{--navy:#1F2A44;--accent:#2E7D5B;--red:#C0392B;--amber:#E08A1E;--bg:#F4F6F8;--card:#fff;--line:#E3E8EC;--ink:#22303C;--muted:#6B7A87;}
  *{box-sizing:border-box}body{margin:0;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink)}
  header{background:var(--navy);color:#fff;padding:22px 32px}
  header h1{margin:0;font-size:20px;font-weight:700}header p{margin:4px 0 0;color:#B9C4D0;font-size:13px}
  .wrap{max-width:1120px;margin:0 auto;padding:24px 32px 48px}
  .verdict{border-radius:12px;padding:18px 22px;margin-bottom:18px;color:#fff;display:flex;align-items:center;gap:16px}
  .verdict .tag{font-size:24px;font-weight:800;letter-spacing:.02em}
  .verdict .why{font-size:14px;opacity:.95}
  .ship{background:var(--accent)}.iterate{background:var(--amber)}.no{background:var(--red)}
  .cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:15px 17px}
  .card .label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
  .card .val{font-size:24px;font-weight:700;margin-top:5px}
  .card .sub{font-size:12px;color:var(--muted);margin-top:3px}
  .sig{color:var(--accent)}.ns{color:var(--red)}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
  .panel h3{margin:0 0 6px;font-size:14px}.panel .note{font-size:12px;color:var(--muted);margin:0 0 12px}
  canvas{max-height:260px}
  table{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px}
  td,th{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left}
  th{font-size:11px;text-transform:uppercase;color:var(--muted)}
  .foot{margin-top:20px;color:var(--muted);font-size:12px}
  @media(max-width:840px){.cards{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}}
</style></head><body>
<header><h1>Checkout Experiment — One-Page vs. Multi-Step</h1>
<p>Primary: conversion · Guardrail: payment errors · &alpha;=0.05, power=0.80</p></header>
<div class="wrap">
  <div class="verdict {{ vclass }}">
    <div class="tag">{{ r.decision }}</div>
    <div class="why">{{ r.reason }}</div>
  </div>
  <div class="cards">
    <div class="card"><div class="label">Control conv.</div><div class="val">{{ (r.control_rate*100)|round(1) }}%</div><div class="sub">n={{ '{:,}'.format(r.control_n) }}</div></div>
    <div class="card"><div class="label">Treatment conv.</div><div class="val">{{ (r.treatment_rate*100)|round(1) }}%</div><div class="sub">n={{ '{:,}'.format(r.treatment_n) }}</div></div>
    <div class="card"><div class="label">Absolute lift</div><div class="val">{{ '%+.2f'|format(r.abs_lift_pts) }} pts</div><div class="sub">95% CI [{{ '%+.1f'|format(r.ci95_low_pts) }}, {{ '%+.1f'|format(r.ci95_high_pts) }}]</div></div>
    <div class="card"><div class="label">p-value</div><div class="val {{ 'sig' if r.significant else 'ns' }}">{{ r.p_value }}</div><div class="sub">{{ 'significant' if r.significant else 'not significant' }}</div></div>
  </div>
  <div class="grid">
    <div class="panel"><h3>Conversion by arm (95% CI)</h3><p class="note">Error bars are the 95% confidence interval on each arm's rate.</p><canvas id="conv"></canvas></div>
    <div class="panel"><h3>Guardrail — payment-error rate</h3><p class="note">Treatment must not significantly increase errors (p={{ r.guardrail_p }} → {{ 'breached' if r.guardrail_breached else 'held' }}).</p><canvas id="guard"></canvas></div>
    <div class="panel full"><h3>Power &amp; MDE context</h3>
      <table><tr><th>Baseline</th><th>Target lift</th><th>Required n/arm</th><th>Runtime</th><th>1wk MDE</th><th>2wk MDE</th></tr>
      <tr><td>{{ (p.baseline_rate*100)|round(0) }}%</td><td>+{{ (p.target_abs_lift*100)|round(0) }} pts</td><td>{{ '{:,}'.format(p.required_n_per_arm) }}</td><td>~{{ p.runtime_days }} days</td><td>{{ p.mde_by_week['1'] }} pts</td><td>{{ p.mde_by_week['2'] }} pts</td></tr></table>
    </div>
  </div>
  <p class="foot">Decision rule was pre-registered before analysis. Data simulated from a fixed true effect to validate the pipeline.</p>
</div>
<script>
const R = {{ rjson|safe }};
const navy='#1F2A44', accent='#2E7D5B', red='#C0392B';
// conversion with rough CI half-widths from the arm rates
function ci(p,n){return 1.96*Math.sqrt(p*(1-p)/n)*100;}
const cC=R.control_rate*100, cT=R.treatment_rate*100;
const eC=ci(R.control_rate,R.control_n), eT=ci(R.treatment_rate,R.treatment_n);
new Chart(document.getElementById('conv'),{type:'bar',
  data:{labels:['Control (multi-step)','Treatment (one-page)'],datasets:[{data:[cC,cT],backgroundColor:[navy,accent]}]},
  options:{plugins:{legend:{display:false},tooltip:{callbacks:{label:(x)=>x.parsed.y.toFixed(1)+'%'}}},scales:{y:{title:{display:true,text:'conversion %'},min:55,max:70}}},
  plugins:[{id:'err',afterDraw(c){const {ctx,scales:{y}}=c;const m=c.getDatasetMeta(0);const errs=[eC,eT];const vals=[cC,cT];m.data.forEach((b,i)=>{const x=b.x;const yt=y.getPixelForValue(vals[i]+errs[i]);const yb=y.getPixelForValue(vals[i]-errs[i]);ctx.save();ctx.strokeStyle='#333';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(x,yt);ctx.lineTo(x,yb);ctx.moveTo(x-6,yt);ctx.lineTo(x+6,yt);ctx.moveTo(x-6,yb);ctx.lineTo(x+6,yb);ctx.stroke();ctx.restore();});}}]});
new Chart(document.getElementById('guard'),{type:'bar',
  data:{labels:['Control','Treatment'],datasets:[{data:[R.control_error*100,R.treatment_error*100],backgroundColor:[navy, R.guardrail_breached?red:accent]}]},
  options:{plugins:{legend:{display:false}},scales:{y:{title:{display:true,text:'error %'},min:0}}}});
</script></body></html>
"""


@app.route("/")
def index():
    d = payload()
    vclass = {"SHIP": "ship", "ITERATE": "iterate", "DON'T SHIP": "no"}.get(d["r"]["decision"], "no")
    return render_template_string(TEMPLATE, r=d["r"], p=d["p"], vclass=vclass, rjson=json.dumps(d["r"]))


if __name__ == "__main__":
    print("Dashboard -> http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
