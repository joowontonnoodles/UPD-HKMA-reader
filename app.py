
import re
import io
from html import escape
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    from pdf2image import convert_from_bytes
    import pytesseract
except Exception:
    convert_from_bytes = None
    pytesseract = None

RED = "#E60028"
BLACK = "#111111"
GRAY = "#777777"
BORDER = "#E6E6E6"
LIGHT = "#F7F7F7"

ASSET_PATTERNS = [
    ("Amounts due from overseas offices", r"amounts?\s+due\s+from\s+overseas\s+offices?"),
    ("Loans and receivables", r"loans?\s+and\s+receivables|loans?\s+and\s+advances\s+to\s+customers?|advances\s+to\s+customers?|loan\s+and\s+advances\s+to\s+customers"),
    ("Reverse repos", r"reverse\s+repos|securities\s+purchased\s+under\s+resale|amount\s+receivable\s+under\s+reverse"),
    ("Cash and balances with banks", r"cash\s+and\s+balances\s+with\s+banks|cash\s+and\s+short\s+term\s+funds"),
    ("Deposits and balances with banks", r"deposits?\s+and\s+balances\s+with\s+banks|placings?\s+with\s+banks|amounts?\s+due\s+from\s+banks|due\s+from\s+banks"),
    ("Amount due from Exchange Fund", r"amount\s+due\s+from\s+exchange\s+fund|due\s+from\s+hkma"),
    ("Investment securities", r"investment\s+securities|financial\s+assets\s+at\s+fair\s+value\s+through\s+other\s+comprehensive\s+income|debt\s+securities"),
    ("Trading assets", r"trading\s+assets|securities\s+held\s+for\s+trading|financial\s+assets\s+held\s+for\s+trading"),
    ("Derivative assets", r"derivative\s+assets|derivative\s+financial\s+instruments.*assets|fair\s+value\s+assets"),
    ("Other accounts", r"other\s+accounts|other\s+assets|other\s+receivables"),
    ("Property and equipment", r"property.*equipment|investment\s+properties|fixed\s+assets"),
]
LIABILITY_PATTERNS = [
    ("Deposits from customers", r"deposits?\s+from\s+customers|customer\s+deposits"),
    ("Demand deposits and current accounts", r"demand\s+deposits?\s+and\s+current\s+accounts|demand\s+and\s+saving\s+deposits"),
    ("Time, call and notice deposits", r"time,?\s+call\s+and\s+notice\s+deposits|term,?\s+call\s+and\s+notice\s+deposits"),
    ("Amounts due to overseas offices", r"amounts?\s+due\s+to\s+overseas\s+offices?"),
    ("Deposits and balances from banks", r"deposits?\s+and\s+balances\s+from\s+banks|deposits?\s+from\s+banks|amounts?\s+due\s+to\s+banks|due\s+to\s+banks"),
    ("Amount due to Exchange Fund", r"amount\s+due\s+to\s+exchange\s+fund|due\s+to\s+hkma"),
    ("Issued debt securities", r"issued\s+debt\s+securities|certificates\s+of\s+deposit|debt\s+issued"),
    ("Derivative liabilities", r"derivative\s+liabilities|derivative\s+financial\s+instruments.*liabilities|fair\s+value\s+liabilities"),
    ("Other liabilities", r"other\s+accounts\s+and\s+provisions|other\s+accounts\s+liabilities|other\s+liabilities"),
    ("Current tax liability", r"current\s+tax\s+liabilit"),
]
CSS = f'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Asta+Sans:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] {{font-family:'Asta Sans', Arial, sans-serif; color:{BLACK}; background:#fff;}}
.main .block-container {{max-width:1180px; padding-top:2rem; padding-bottom:4rem;}}
h1 {{font-size:2.05rem; font-weight:600; letter-spacing:-.03em; color:{BLACK}; margin-bottom:.2rem;}}
h2 {{font-size:.78rem; text-transform:uppercase; letter-spacing:.16em; color:{GRAY}; border-bottom:1px solid {BORDER}; padding-bottom:.45rem; margin-top:2.1rem;}}
h3 {{font-size:1rem; font-weight:600; color:{BLACK};}}
.smallcap {{font-size:.68rem; letter-spacing:.14em; text-transform:uppercase; color:{GRAY};}}
.redline {{height:3px; background:{RED}; width:58px; margin:.5rem 0 1.4rem 0;}}
.card {{background:#fff; border:1px solid {BORDER}; padding:1.05rem 1.1rem; margin:.65rem 0;}}
.kpi {{border-top:3px solid {RED}; background:#fff; border-left:1px solid {BORDER}; border-right:1px solid {BORDER}; border-bottom:1px solid {BORDER}; padding:.95rem;}}
.kpi-lab {{font-size:.66rem; text-transform:uppercase; letter-spacing:.12em; color:{GRAY};}}
.kpi-val {{font-size:1.45rem; font-weight:600; color:{BLACK}; margin-top:.3rem;}}
.kpi-sub {{font-size:.74rem; color:{GRAY}; margin-top:.15rem;}}
.note {{border-left:3px solid {RED}; background:{LIGHT}; padding:.8rem 1rem; color:#333; line-height:1.55; margin:.7rem 0;}}
.clean-table table {{font-size:.82rem;}}
.clean-table th {{text-transform:uppercase; letter-spacing:.08em; font-size:.66rem; color:{GRAY}; background:#fff !important;}}
.clean-table td {{border-bottom:1px solid #f0f0f0;}}
.pos {{color:#16833A; font-weight:600;}}
.neg {{color:{RED}; font-weight:600;}}
.muted {{color:#999;}}
section[data-testid="stFileUploader"] {{border:1px dashed #d8d8d8 !important; padding:1.1rem !important; background:#fafafa !important;}}
section[data-testid="stFileUploader"] button {{background:#fff !important; color:{RED} !important; border:1px solid {RED} !important; border-radius:0 !important; box-shadow:none !important; font-weight:600 !important;}}
section[data-testid="stFileUploader"] button:hover {{background:{RED} !important; color:#fff !important;}}
.stDownloadButton button {{border-radius:0 !important; border:1px solid {RED} !important; color:{RED} !important; background:#fff !important;}}
</style>
'''

def clean_text(s):
    return "" if s is None else str(s).replace("-", "-").replace("-", "-").replace("−", "-")

def norm(s):
    return re.sub(r"\s+", " ", clean_text(s)).strip()

def clean_num(tok):
    if tok is None:
        return None
    t = str(tok).strip()
    if t in ["", "--", "---", "n/a", "N/A"]:
        return None
    if t == "-":
        return 0.0
    neg = t.startswith("(") and t.endswith(")")
    if neg:
        t = t[1:-1]
    t = t.replace(",", "").replace("%", "").replace("HKD", "").strip()
    if re.fullmatch(r"\d{1,3}\.\d{3}", t):
        t = t.replace(".", "")
    try:
        v = float(t)
        return -v if neg else v
    except Exception:
        return None

def num_tokens(line):
    vals = []
    for tok in re.findall(r"\(?-?\d[\d,]*(?:\.\d+)?\)?|-", clean_text(line)):
        v = clean_num(tok)
        if v is not None:
            vals.append(v)
    return vals

def trailing_pair(line):
    vals = num_tokens(line)
    return (vals[-2], vals[-1]) if len(vals) >= 2 else None

def first_pair(lines, pattern):
    rx = re.compile(pattern, re.I)
    for line in lines:
        if rx.search(line):
            pair = trailing_pair(line)
            if pair:
                return pair
    return None

def pct_change(c, p):
    if c is None or p in [None, 0]:
        return None
    return (c - p) / abs(p) * 100

def fmt_num(v, unit=""):
    if v is None:
        return "-"
    return f"{v:,.0f}{unit}"

def fmt_pct(v):
    if v is None:
        return "-"
    return f"{v:.2f}%"

def direction(c, p):
    if c is None or p is None:
        return "was unavailable"
    if c > p:
        return "rose"
    if c < p:
        return "fell"
    return "was unchanged"

def extract_text(pdf_bytes):
    parts = []
    if pdfplumber:
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    parts.append(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
        except Exception:
            pass
    text = "\n".join(parts)
    if len(text.strip()) < 500 and convert_from_bytes and pytesseract:
        try:
            imgs = convert_from_bytes(pdf_bytes, dpi=200, first_page=1, last_page=8)
            text += "\n" + "\n".join(pytesseract.image_to_string(img) for img in imgs)
        except Exception:
            pass
    return clean_text(text)

def lines(text):
    return [norm(x) for x in text.splitlines() if norm(x)]

def detect_unit(text):
    t = text.lower()
    if "hkd thousand" in t or "in thousands" in t:
        return "HKD thousands"
    if "hkd million" in t or "in millions" in t:
        return "HKD millions"
    return "reported units"

def detect_bank(ls, filename):
    for line in ls[:25]:
        if re.search(r"key financial|disclosure statement|as at|section", line, re.I):
            continue
        if re.search(r"bank|branch|limited|ag|plc|bnp|barclays|ubs|jpmorgan|natixis|soci", line, re.I) and 6 <= len(line) <= 100:
            return line.upper()
    return re.sub(r"\.(pdf|PDF)$", "", filename).replace("_", " ").replace("-", " ").upper()

def balance_window(ls):
    start = 0
    for i, line in enumerate(ls):
        if re.search(r"balance sheet|statement of financial position", line, re.I):
            start = i
            break
    end = min(len(ls), start + 120)
    for i in range(start + 1, min(len(ls), start + 200)):
        if re.search(r"liquidity information|contingent liabilities|notes to the financial|section b|consolidated", ls[i], re.I):
            end = i
            break
    return ls[start:end]

def find_total(ls, pat):
    for line in ls:
        if re.search(pat, line, re.I) and not re.search(r"consolidated|group|percentage", line, re.I):
            pair = trailing_pair(line)
            if pair:
                return pair
    return None

def extract_items(ls, patterns):
    found = {}
    for label, pat in patterns:
        rx = re.compile(pat, re.I)
        for line in ls:
            if rx.search(line) and not re.search(r"income|expense|profit|liquidity|maturity|off-balance|commitment|currency|risk weighted", line, re.I):
                pair = trailing_pair(line)
                if pair:
                    found[label] = {"current": pair[0], "prior": pair[1]}
                    break
    return found

def extract_income(ls):
    pats = {
        "interest_income": r"^interest income\b",
        "interest_expense": r"^interest expense\b",
        "nii": r"net interest income",
        "other_income": r"other operating income",
        "fees": r"net fees? and commission|fees? and commission income",
        "op_exp": r"operating expenses|total operating expenses",
        "goi": r"total operating income|operating income before impairment|gross operating income",
        "profit": r"profit after taxation|profit after tax|net profit|profit for the year",
        "pbt": r"profit before taxation|profit before tax",
        "rwa": r"risk weighted assets|RWA",
    }
    d = {k:first_pair(ls, p) for k,p in pats.items()}
    if not d["nii"] and d["interest_income"] and d["interest_expense"]:
        d["nii"] = (d["interest_income"][0] - d["interest_expense"][0], d["interest_income"][1] - d["interest_expense"][1])
    if not d["goi"] and d["nii"] and d["other_income"]:
        d["goi"] = (d["nii"][0] + d["other_income"][0], d["nii"][1] + d["other_income"][1])
    if not d["profit"]:
        d["profit"] = d["pbt"]
    d["mbi"] = (d["goi"][0] - d["nii"][0], d["goi"][1] - d["nii"][1]) if d["goi"] and d["nii"] else d["other_income"]
    return d

def extract_liquidity(ls):
    return {
        "lmr": first_pair(ls, r"liquidity maintenance ratio|\bLMR\b"),
        "cfr": first_pair(ls, r"core funding ratio|\bCFR\b"),
    }

def extract_provisions(ls):
    spec = coll = total = None
    for line in ls:
        low = line.lower()
        pair = trailing_pair(line)
        if not pair:
            continue
        if re.search(r"specific.*provision|individual.*provision|individually assessed", low):
            spec = pair
        if re.search(r"collective.*provision|collectively assessed|stage 1|stage 2", low):
            coll = pair
        if re.search(r"credit impairment allowance|impairment allowance|allowance for impaired|total provision", low):
            total = pair
    if total is None and spec and coll:
        total = (spec[0] + coll[0], spec[1] + coll[1])
    if coll is None and total and not spec:
        coll = total
    if spec is None and (coll or total):
        spec = (0.0, 0.0)
    return {"specific": spec, "collective": coll, "total": total}

def parse(pdf_bytes, filename):
    text = extract_text(pdf_bytes)
    ls = lines(text)
    win = balance_window(ls)
    assets = extract_items(win, ASSET_PATTERNS)
    liabs = extract_items(win, LIABILITY_PATTERNS)
    ta = find_total(win, r"\btotal assets\b") or find_total(ls[:220], r"\btotal assets\b")
    tl = find_total(win, r"\btotal liabilities\b") or find_total(ls[:220], r"\btotal liabilities\b")
    if not ta and assets:
        ta = (sum(v["current"] for v in assets.values()), sum(v["prior"] for v in assets.values()))
    if not tl and liabs:
        tl = (sum(v["current"] for v in liabs.values()), sum(v["prior"] for v in liabs.values()))
    return {"bank": detect_bank(ls, filename), "unit": detect_unit(text), "text_len": len(text), "assets": assets, "liabs": liabs, "ta": ta, "tl": tl, "income": extract_income(ls[:260]), "liq": extract_liquidity(ls), "prov": extract_provisions(ls), "lines": ls[:35]}

def change_html(v):
    if v is None:
        return "-"
    cls = "pos" if v >= 0 else "neg"
    return f'<span class="{cls}">{v:.2f}%</span>'

def row(label, pair, unit=""):
    if not pair:
        return [escape(label), "-", "-", "-"]
    c, p = pair
    return [escape(label), fmt_num(c, f" {unit}" if unit else ""), fmt_num(p, f" {unit}" if unit else ""), change_html(pct_change(c, p))]

def table(rows, heads=("Metric", "Current", "Prior", "Change")):
    s = '<div class="clean-table"><table style="width:100%;border-collapse:collapse"><thead><tr>'
    s += ''.join(f'<th style="text-align:left;padding:8px 10px;border-bottom:2px solid #111">{h}</th>' for h in heads)
    s += '</tr></thead><tbody>'
    for r in rows:
        s += '<tr>' + ''.join(f'<td style="padding:8px 10px;border-bottom:1px solid #eee">{x}</td>' for x in r) + '</tr>'
    return s + '</tbody></table></div>'

def top_items(items, total):
    arr = []
    for lab, v in items.items():
        c, p = v["current"], v["prior"]
        if c:
            arr.append({"label": lab, "current": c, "prior": p, "pct": c / total * 100 if total else None, "chg": pct_change(c,p)})
    return sorted(arr, key=lambda x: abs(x["current"]), reverse=True)

def bar(items, total, unit):
    if not items or not total:
        st.markdown('<div class="note">No chart available because the relevant balance sheet lines were not extracted.</div>', unsafe_allow_html=True)
        return
    vals = items[:8][::-1]
    labels = [x["label"] for x in vals]
    pcts = [x["current"] / total * 100 for x in vals]
    fig = go.Figure(go.Bar(x=pcts, y=labels, orientation="h", marker_color=RED, text=[f"{x:.1f}%" for x in pcts], textposition="outside"))
    fig.update_layout(height=max(430, 72*len(labels)+120), margin=dict(l=220,r=70,t=15,b=45), plot_bgcolor="#fff", paper_bgcolor="#fff", font=dict(color=BLACK), xaxis=dict(ticksuffix="%", gridcolor="#eee", title="Percentage of total"), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def profit_rows(d):
    inc, unit, ta = d["income"], d["unit"], d["ta"]
    rows = [row("Net interest income", inc.get("nii"), unit), row("Net fees and commissions", inc.get("fees"), unit), row("Market and banking income", inc.get("mbi"), unit), row("Gross operating income", inc.get("goi"), unit), row("Operating expenses", inc.get("op_exp"), unit), row("Profit after taxation", inc.get("profit"), unit)]
    goi, opx, prof, rwa = inc.get("goi"), inc.get("op_exp"), inc.get("profit"), inc.get("rwa")
    cir = opx[0]/goi[0]*100 if opx and goi and goi[0] else None
    cirp = opx[1]/goi[1]*100 if opx and goi and goi[1] else None
    avg_assets = (ta[0]+ta[1])/2 if ta and ta[0] and ta[1] else None
    roa = prof[0]/avg_assets*100 if prof and avg_assets else None
    roap = prof[1]/ta[1]*100 if prof and ta and ta[1] else None
    irwa = goi[0]/rwa[0]*100 if goi and rwa and rwa[0] else None
    irwap = goi[1]/rwa[1]*100 if goi and rwa and rwa[1] else None
    ratios = [["Cost income ratio", fmt_pct(cir), fmt_pct(cirp), change_html(pct_change(cir,cirp))], ["Return on assets", fmt_pct(roa), fmt_pct(roap), change_html(pct_change(roa,roap))], ["Income over RWA", fmt_pct(irwa), fmt_pct(irwap), change_html(pct_change(irwa,irwap))], ["Risk weighted assets", fmt_num(rwa[0], f" {unit}") if rwa else "-", fmt_num(rwa[1], f" {unit}") if rwa else "-", change_html(pct_change(rwa[0],rwa[1])) if rwa else "-"]]
    return rows, ratios, {"cir": cir, "roa": roa, "irwa": irwa}

def render(d):
    unit = d["unit"]
    ta = d["ta"]; tl = d["tl"]
    at = ta[0] if ta else None; lt = tl[0] if tl else None
    assets = top_items(d["assets"], at)
    liabs = top_items(d["liabs"], lt)
    p_rows, r_rows, ratios = profit_rows(d)
    st.markdown(f'<div class="smallcap">HKMA Key Financial Information Disclosure</div><h1>{escape(d["bank"])}</h1><div class="redline"></div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    prof = d["income"].get("profit"); lmr = d["liq"].get("lmr")
    c1.markdown(f'<div class="kpi"><div class="kpi-lab">Total assets</div><div class="kpi-val">{fmt_num(at)}</div><div class="kpi-sub">{unit}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi"><div class="kpi-lab">Profit after tax</div><div class="kpi-val">{fmt_num(prof[0]) if prof else "-"}</div><div class="kpi-sub">{unit}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi"><div class="kpi-lab">LMR</div><div class="kpi-val">{fmt_pct(lmr[0]) if lmr else "-"}</div><div class="kpi-sub">Current period</div></div>', unsafe_allow_html=True)
    st.markdown("## Liquidity")
    liq_text = []
    for key,label,minv in [("lmr","LMR",25),("cfr","CFR",75)]:
        pair = d["liq"].get(key)
        if pair:
            liq_text.append(f"{label} {direction(pair[0], pair[1])} from {pair[1]:.2f}% to {pair[0]:.2f}%. The movement is likely explained by changes in liquid assets, maturity profile, funding mix and intra-group balances.")
        else:
            liq_text.append(f"{label} was not disclosed or could not be extracted.")
    st.markdown(f'<div class="note">{escape(" ".join(liq_text))}</div>', unsafe_allow_html=True)
    st.markdown(table([["LMR", fmt_pct(lmr[0]) if lmr else "-", fmt_pct(lmr[1]) if lmr else "-", f"{lmr[0]-lmr[1]:.2f} pp" if lmr else "-"], ["CFR", fmt_pct(d["liq"]["cfr"][0]) if d["liq"].get("cfr") else "-", fmt_pct(d["liq"]["cfr"][1]) if d["liq"].get("cfr") else "-", f"{d['liq']['cfr'][0]-d['liq']['cfr'][1]:.2f} pp" if d["liq"].get("cfr") else "-"]]), unsafe_allow_html=True)
    st.markdown("## Key Financials")
    st.markdown(table([row("Profit after taxation", prof, unit), row("Total assets", ta, unit), row("Total liabilities", tl, unit), row("Specific provisions", d["prov"].get("specific"), unit), row("Collective provisions", d["prov"].get("collective"), unit), row("Total provisions", d["prov"].get("total"), unit)]), unsafe_allow_html=True)
    st.markdown("## Profitability")
    inc = d["income"]; goi = inc.get("goi"); opx=inc.get("op_exp")
    txt = "Profitability indicators show the branch revenue trend, expense discipline and capital productivity. "
    if prof: txt += f"Profit after taxation {direction(prof[0], prof[1])} {abs(pct_change(prof[0], prof[1]) or 0):.2f}% versus the prior period. "
    if goi: txt += f"Gross operating income {direction(goi[0], goi[1])} {abs(pct_change(goi[0], goi[1]) or 0):.2f}%. "
    if ratios.get("cir") is not None: txt += f"Cost income ratio is {ratios['cir']:.2f}%, indicating operating efficiency."
    st.markdown(f'<div class="note">{escape(txt)}</div>', unsafe_allow_html=True)
    st.markdown("### Income statement indicators")
    st.markdown(table(p_rows), unsafe_allow_html=True)
    st.markdown("### Profitability ratios")
    st.markdown(table(r_rows), unsafe_allow_html=True)
    st.markdown("## Asset Composition")
    bar(assets, at, unit)
    st.markdown("## Provisions")
    prov = d["prov"]; dom = assets[0]["label"] if assets else "the dominant asset"
    risk = "the parent group or intra-group treasury book" if "overseas" in dom.lower() else "external borrowers and customer-facing credit exposures"
    spec = prov.get("specific"); coll = prov.get("collective"); total = prov.get("total")
    ptxt=[]
    if spec: ptxt.append(f"Specific provisions {direction(spec[0], spec[1])} {abs(pct_change(spec[0], spec[1]) or 0):.2f}%, indicating the movement in identified credit impairment risk.")
    else: ptxt.append("Specific provisions were not separately disclosed or could not be extracted.")
    if coll: ptxt.append(f"Collective provisions {direction(coll[0], coll[1])} {abs(pct_change(coll[0], coll[1]) or 0):.2f}%, indicating the movement in portfolio-level expected credit loss coverage.")
    else: ptxt.append("Collective provisions were not separately disclosed or could not be extracted.")
    if total: ptxt.append(f"Overall provisions {direction(total[0], total[1])} {abs(pct_change(total[0], total[1]) or 0):.2f}%. The dominant asset is {dom}, so credit risk sits primarily with {risk}.")
    st.markdown(f'<div class="note">{escape(" ".join(ptxt))}</div>', unsafe_allow_html=True)
    st.markdown(table([row("Specific provisions", spec, unit), row("Collective provisions", coll, unit), row("Total provisions", total, unit)]), unsafe_allow_html=True)
    st.markdown("## Asset Concentration")
    if assets:
        share = sum(x["current"] for x in assets[:3])/at*100 if at else None
        st.markdown(f'<div class="note">The top 3 assets represent {share:.2f}% of total assets. The largest asset is {assets[0]["label"]} at {assets[0]["pct"]:.2f}%, showing where the branch balance sheet risk is concentrated.</div>', unsafe_allow_html=True)
    st.markdown(table([[escape(x["label"]), fmt_num(x["current"], f" {unit}"), fmt_pct(x["pct"]), change_html(x["chg"])] for x in assets[:3]], ("Asset", "Current", "% of total", "Value change")), unsafe_allow_html=True)
    st.markdown("## Liability Composition")
    bar(liabs, lt, unit)
    st.markdown("## Liability Concentration")
    if liabs:
        share = sum(x["current"] for x in liabs[:3])/lt*100 if lt else None
        st.markdown(f'<div class="note">The top 3 liabilities represent {share:.2f}% of total liabilities. The largest liability is {liabs[0]["label"]} at {liabs[0]["pct"]:.2f}%, showing the branch funding dependence.</div>', unsafe_allow_html=True)
    st.markdown(table([[escape(x["label"]), fmt_num(x["current"], f" {unit}"), fmt_pct(x["pct"]), change_html(x["chg"])] for x in liabs[:3]], ("Liability", "Current", "% of total", "Value change")), unsafe_allow_html=True)
    st.markdown("## Executive Analysis")
    main_asset = assets[0]["label"] if assets else "not extracted"
    main_liab = liabs[0]["label"] if liabs else "not extracted"
    ex = f"Executive analysis: {d['bank']} is primarily defined by {main_asset} on the asset side and {main_liab} on the liability side. The key management question is whether balance sheet growth is coming from stable customer activity or from intra-group, market or treasury balances, because that distinction drives the risk interpretation more than headline asset size alone."
    st.markdown(f'<div class="note">{escape(ex)}</div>', unsafe_allow_html=True)
    with st.expander("Extraction diagnostics"):
        st.write({"text_length": d["text_len"], "assets_found": list(d["assets"].keys()), "liabilities_found": list(d["liabs"].keys()), "unit": d["unit"]})
        st.write(d["lines"])

def main():
    st.set_page_config(page_title="HKMA Financial Disclosure Reader", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="smallcap">Societe Generale themed disclosure reader</div><h1>HKMA Financial Statement Analyzer</h1><div class="redline"></div>', unsafe_allow_html=True)
    st.markdown('<div class="note">Upload a December HKMA key financial information disclosure PDF. The full report appears directly on this page for screenshotting. Missing fields show as a hyphen instead of breaking the app.</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("HKMA Key Financial Information Disclosure PDF", type=["pdf"])
    if uploaded is None:
        st.markdown('<div class="card"><div class="smallcap">Ready</div><h3>Drop a disclosure PDF to begin</h3><p class="muted">The button is native Streamlit with only clean visual styling, so no overlapping upload text hack is used.</p></div>', unsafe_allow_html=True)
        return
    with st.spinner("Reading PDF and extracting HKMA disclosure data"):
        d = parse(uploaded.read(), uploaded.name)
    render(d)

if __name__ == "__main__":
    main()
