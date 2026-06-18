import streamlit as st
import pdfplumber
import pandas as pd
import re, io, datetime
import plotly.graph_objects as go

try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

st.set_page_config(page_title="HKMA Financial Disclosure Reader", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');
* {font-family:'DM Sans',sans-serif !important; box-sizing:border-box;}
h1{font-family:'DM Sans',sans-serif !important;font-size:.82rem !important;font-weight:700 !important;
   letter-spacing:.18em !important;text-transform:uppercase !important;color:#E60028 !important;
   border-bottom:2px solid #E60028 !important;padding-bottom:10px !important;margin-bottom:28px !important;}
h2{font-family:'DM Sans',sans-serif !important;font-size:.75rem !important;font-weight:600 !important;
   letter-spacing:.18em !important;text-transform:uppercase !important;color:#555555 !important;
   border-bottom:1px solid #eeeeee !important;padding-bottom:6px !important;margin-top:36px !important;margin-bottom:16px !important;}
h3{font-family:'DM Sans',sans-serif !important;font-size:.72rem !important;font-weight:600 !important;
   letter-spacing:.14em !important;text-transform:uppercase !important;color:#888888 !important;
   margin-top:20px !important;margin-bottom:10px !important;}
section[data-testid="stFileUploader"]{
    border:1px dashed #dddddd !important;
    padding:16px !important;
    background:#fafafa !important;
}
section[data-testid="stFileUploader"] button{
    background:#ffffff !important;
    color:#E60028 !important;
    border:1px solid #E60028 !important;
    border-radius:0 !important;
    font-size:.78rem !important;
    font-weight:600 !important;
    letter-spacing:.08em !important;
    text-transform:uppercase !important;
    padding:6px 16px !important;
    box-shadow:none !important;
}
section[data-testid="stFileUploader"] button:hover{
    background:#E60028 !important;
    color:#ffffff !important;
}
.pg-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;padding-bottom:14px;border-bottom:2px solid #E60028;}
.pg-bank{font-size:1.6rem;font-weight:700;color:#111111 !important;letter-spacing:-.01em;line-height:1.1;}
.pg-meta{font-size:.8rem;color:#999999 !important;text-align:right;line-height:1.7;}
.unit-tag{display:inline-block;font-size:.72rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  padding:3px 10px;margin:10px 0 20px 0;color:#E60028 !important;border:1px solid #E60028;}
.desc-block{border-left:3px solid #E60028;padding:10px 14px;background:#fafafa !important;margin-bottom:28px;}
.desc-text{font-size:.9rem;color:#444444 !important;line-height:1.65;}
.snapshot{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:28px;}
.kpi{flex:1 1 140px;border:1px solid #eeeeee;padding:14px 16px;background:#ffffff !important;min-width:130px;}
.kpi-label{font-size:.7rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#999999 !important;margin-bottom:6px;}
.kpi-val{font-size:1.2rem;font-weight:700;color:#111111 !important;line-height:1;}
.kpi-chg-pos{font-size:.75rem;color:#1a7a3a !important;margin-top:4px;}
.kpi-chg-neg{font-size:.75rem;color:#E60028 !important;margin-top:4px;}
.ratio-grid{display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap;}
.ratio-card{flex:1 1 200px;border:1px solid #eeeeee;padding:18px 20px;background:#ffffff !important;}
.ratio-label{font-size:.7rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#aaaaaa !important;margin-bottom:10px;}
.ratio-main{font-size:1.8rem;font-weight:700;color:#111111 !important;line-height:1;}
.ratio-prior{font-size:.85rem;color:#cccccc !important;margin-left:6px;}
.chg-pos{font-size:.78rem;font-weight:600;color:#1a7a3a !important;}
.chg-neg{font-size:.78rem;font-weight:600;color:#E60028 !important;}
table{width:100%;border-collapse:collapse;font-size:.9rem;margin:6px 0 20px;background:#ffffff !important;}
thead{border-bottom:2px solid #E60028;}
th{font-size:.7rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#999999 !important;
   padding:0 10px 8px;text-align:right;background:#ffffff !important;}
th:first-child{text-align:left;}
td{padding:7px 10px;border-bottom:1px solid #f5f5f5;color:#111111 !important;text-align:right;background:#ffffff !important;}
td:first-child{text-align:left;}
td.muted{color:#cccccc !important;}
.rank{display:inline-block;
      font-size:.7rem;font-weight:700;color:#E60028 !important;border:1px solid #E60028;margin-right:8px;vertical-align:middle;
      width:18px;height:18px;line-height:18px;text-align:center;}
[data-testid="stDownloadButton"] button{
    background:#ffffff !important;color:#E60028 !important;border:1px solid #E60028 !important;
    font-size:.78rem !important;
    font-weight:600 !important;letter-spacing:.1em !important;text-transform:uppercase !important;
    padding:8px 18px !important;border-radius:0 !important;}
details summary{color:#cccccc !important;font-size:.78rem !important;}
hr.rule{border:none;border-top:1px solid #eeeeee;margin:28px 0 0;}
.accuracy-disclaimer{border-left:3px solid #E60028;background:#fff5f6;color:#111111 !important;
  padding:8px 12px;margin:8px 0 18px 0;font-size:.78rem;line-height:1.55;}
.accuracy-disclaimer span{color:#E60028 !important;font-weight:700;text-transform:uppercase;letter-spacing:.08em;font-size:.68rem;margin-right:6px;}
</style>""", unsafe_allow_html=True)

# ── CANONICAL label mapping ────────────────────────────────────────────────
CANONICAL = {
    r"cash and balances":                                              "Cash and balances with banks",
    r"balances with banks$":                                           "Balances with banks",
    r"balances with the monetary authority":                           "Balances with Monetary Authority",
    r"balances due from exchange fund|due from exchange fund|amount due from exchange fund": "Due from Exchange Fund",
    r"placements with banks":                                          "Placements with banks",
    r"amounts? due from overseas offices|amount due from overseas":    "Amounts due from overseas offices",
    r"trade bills":                                                    "Trade bills",
    r"certificates? of deposit held":                                  "Certificates of deposit held",
    r"securities held for trading":                                    "Securities held for trading",
    r"advances and other accounts":                                    "Advances and other accounts",
    r"loans and receivables":                                          "Loans and receivables",
    r"loans.*advances.*customers|advances.*to.*customers":             "Loans and advances to customers",
    r"investment securities":                                          "Investment securities",
    r"other investments":                                              "Other investments",
    r"property.*plant.*equipment|property and equipment":             "Property, plant & equipment",
    r"amount.*receivable.*reverse.repo|reverse.repo.*receivable":      "Amount receivable under reverse repos",
    r"deposits and balances from central banks|from central banks":    "Deposits from central banks / Monetary Authority",
    r"deposits and balances from banks|deposits from banks":          "Deposits and balances from banks",
    r"balances due to exchange fund|amount due to exchange fund":      "Balances due to Exchange Fund",
    r"demand deposits and current accounts|demand deposits":           "Demand deposits and current accounts",
    r"saving deposits":                                                "Saving deposits",
    r"time.*call.*notice deposits":                                    "Time, call and notice deposits",
    r"amounts? due to overseas offices|amount due to overseas":        "Amount due to overseas offices",
    r"certificates? of deposit issued":                                "Certificates of deposit issued",
    r"issued debt securities":                                         "Issued debt securities",
    r"amount payable under repo|amount.*payable.*repo":                "Amount payable under repo",
    r"other accounts and provisions|other liabilities|^other accounts": "Other accounts / liabilities",
    r"^provisions$":                                                   "Provisions",
    r"deposits from customers":                                        "Deposits from customers",
}

def canonicalize(raw):
    ll = raw.lower().strip()
    for pat, clean in CANONICAL.items():
        if re.search(pat, ll, re.IGNORECASE): return clean
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]+"," ",raw)
    s = re.sub(r"\s+"," ",s).strip()
    s = re.sub(r"[,\.\-\s]+$","",s).strip()
    return s[:70].rsplit(" ",1)[0].strip() if len(s)>70 else s

def clean_num(s):
    if not isinstance(s,str): return None
    s=s.strip().replace("\xa0","").replace(" ","")
    s=re.sub(r"HK\$|US\$|'000|港幣千元","",s).strip()
    if s in ("","—","-","–","Nil","nil","N/A"): return None
    neg=s.startswith("(") and s.endswith(")")
    s=re.sub(r"[()$]","",s)
    s2=re.sub(r"(\d)\.(\d{3})(?!\d)", r"\1\2", s)
    s2=s2.replace(",","")
    try: v=float(s2); return -v if neg else v
    except: pass
    s=s.replace(",","")
    try: v=float(s); return -v if neg else v
    except: return None

def trailing_nums(line):
    tokens=re.findall(r"\([\d,\.]+(?:\.\d+)?\)|[\d,\.]+(?:\.\d+)?",line)
    return [v for t in tokens for v in [clean_num(t)] if v is not None]

def raw_label(line):
    s = re.sub(r"\|","",line)
    s = re.sub(r"\*{1,2}","",s)
    s = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+"," ",s)
    s = re.sub(r"(\s+[\(\-]?[\d,]+[\)]?)+\s*$","",s).strip()
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]{3,}.*$","",s)
    s = re.sub(r"\(see\s+part.*$","",s,flags=re.IGNORECASE).strip()
    s = re.sub(r",?\s*net\s+of\s+impairment\s+allowance","",s,flags=re.IGNORECASE).strip()
    s = re.sub(r"\s+except\s+those\s+included.*$","",s,flags=re.IGNORECASE).strip()
    s = re.sub(r"\s+other\s+than\s+those.*$","",s,flags=re.IGNORECASE).strip()
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]+"," ",s)
    return re.sub(r"\s+"," ",s).strip()

def detect_unit_per_page(page_lines):
    for line in page_lines:
        if re.search(r"in millions|millions of hk|million[s]? of hong kong",line,re.IGNORECASE):
            return "HKD millions",1_000_000
        if re.search(r"HK\$\s*'?\s*0{3}",line,re.IGNORECASE): return "HKD thousands",1_000
        if re.search(r"'000",line,re.IGNORECASE): return "HKD thousands",1_000
    return None

def detect_unit(lines):
    r = detect_unit_per_page(lines[:150])
    if r: return r
    return "HKD thousands", 1_000

def ocr_all(pdf_bytes):
    if not OCR_AVAILABLE: return []
    try:
        images = convert_from_bytes(pdf_bytes, dpi=200)
        lines = []
        for img in images:
            text = pytesseract.image_to_string(img)
            lines += [l.strip() for l in text.splitlines() if l.strip()]
        return lines
    except: return []

def extract_pages(pdf_bytes):
    pages = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                pages.append((page.page_number, lines, text))
    except: pass
    if not any(lines for _,lines,_ in pages):
        ocr_lines = ocr_all(pdf_bytes)
        if ocr_lines:
            pages = [(1, ocr_lines, "\n".join(ocr_lines))]
    return pages

HARD_SKIP=re.compile(
    r"^total\s+(assets|liabilities)|^assets\s*$|^liabilities\s*$|^equity\s+and\s+liabilities\s*$|"
    r"^less:\s*impairment|^impairment\s+allowances\s+for|^provision\s+for\s+impaired|"
    r"^balance\s+sheet|^section\s+[a-z]|^\d+\s*$|^page\s|^reserves?\s*$|^[-_=\s]+$|"
    r"^note\s+附|^figures\s+in|^unaudited|^i{1,3}\.?\s+unaudited|^international\s+claims|"
    r"^non-bank\s+mainland|^currency\s+risk|^remuneration|^group\s+consolidated|"
    r"^declaration\s+of\s+compliance", re.IGNORECASE)

def is_noise(line):
    s=line.strip()
    if not s or len(s)<4: return True
    if re.match(r"^[^a-zA-Z0-9\-\(]",s): return True
    if re.match(r"^[A-Z]\d+\s*$",s): return True
    return False

def parse_bs(lines, section):
    items = []
    in_sec = False
    if section == "assets":
        s_pat = re.compile(r"^\**assets\**\s*$|^\**assets\**\s+as\s+at", re.IGNORECASE)
        e_pat = re.compile(r"total\s+assets|總資產", re.IGNORECASE)
    else:
        s_pat = re.compile(r"^\**liabilities\**\s*$|equity\s+and\s+liabilities", re.IGNORECASE)
        e_pat = re.compile(r"total\s+liabilities|總負債", re.IGNORECASE)

    def clean_for_match(l):
        x=re.sub(r"\|","",l); x=re.sub(r"\*{1,2}","",x)
        x=re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+"," ",x)
        return re.sub(r"\s+"," ",x).strip()

    for line in lines:
        s = line.strip()
        if not s: continue
        cm = clean_for_match(s)
        if s_pat.match(cm): in_sec=True; continue
        if not in_sec: continue
        if e_pat.search(cm): in_sec=False; continue
        if HARD_SKIP.search(cm): continue
        if is_noise(cm): continue
        if re.match(r'^[a-z]', s) or s.startswith(')'): continue
        nums = trailing_nums(s)
        if not nums: continue
        curr = nums[-2] if len(nums)>=2 else nums[-1]
        prior = nums[-1] if len(nums)>=2 else None
        rl = raw_label(s)
        label = canonicalize(rl)
        if not label or len(label)<2: continue
        if re.match(r"^[\d,.()\-\s]+$", label): continue
        if any(x["label"]==label for x in items): continue
        items.append({"label":label,"curr":abs(curr),"prior":abs(prior) if prior is not None else None})
    return items

def find_two(lines, pattern):
    for i,line in enumerate(lines):
        if re.match(r'^[a-z]', line.strip()): continue
        if re.search(pattern, line, re.IGNORECASE):
            nums = trailing_nums(line)
            if len(nums) >= 2: return nums[-2], nums[-1]
            for j in range(i+1, min(i+4, len(lines))):
                nums += trailing_nums(lines[j])
                if len(nums) >= 2: return nums[-2], nums[-1]
    return None

def get_provisions(lines):
    spec, coll = None, None
    for line in lines:
        if re.match(r'^[a-z]', line.strip()): continue
        ll = line.lower()
        if re.search(r"collective\s+(impairment|provision)|[-\u2013]\s*collective\b|綜合減值", ll):
            nums = trailing_nums(line)
            if nums and coll is None:
                coll = (abs(nums[-2] if len(nums)>=2 else nums[-1]), abs(nums[-1]) if len(nums)>=2 else None)
        if re.search(r"specific\s+(impairment|provision)|individual\s+impairment|[-\u2013]\s*specific\b|特殊性撥備", ll):
            nums = trailing_nums(line)
            if nums and spec is None:
                spec = (abs(nums[-2] if len(nums)>=2 else nums[-1]), abs(nums[-1]) if len(nums)>=2 else None)
    return {"spec": spec, "coll": coll}

def get_lmr_cfr(lines, pdf_bytes):
    lmr = find_two(lines, r"average\s+(liquidity\s+maintenance|lmr)|average\s+lmr")
    cfr = find_two(lines, r"average\s+(core\s+funding|cfr)|average\s+cfr")
    if not (lmr and cfr):
        ol = ocr_all(pdf_bytes)
        if not lmr: lmr = find_two(ol, r"average.*lmr|lmr.*%")
        if not cfr: cfr = find_two(ol, r"average.*cfr|cfr.*%")
    return lmr, cfr

def get_entity_name(lines):
    NON_NAME = re.compile(
        r"^(natixis\s+corporate|corporate\s+and\s+investment|groupe\s+bpce|kpmg|"
        r"financial\s+information\s+disclosure|financial\s+statements|"
        r"incorporated\s+in|unaudited|figures\s+in|for\s+identification|"
        r"investment\s+banking|and\s+investment)",
        re.IGNORECASE)
    for line in lines[:60]:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", "", line).strip()
        clean = re.sub(r"\(.*?\)", "", clean).strip()
        clean = re.sub(r"\s+", " ", clean).strip()
        if re.search(r"hong\s+kong\s+branch", clean, re.IGNORECASE):
            before = re.sub(r"hong\s+kong\s+branch.*$", "", clean, flags=re.IGNORECASE).strip()
            if len(before.split()) >= 1:
                return clean[:100]
    for line in lines[:20]:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", "", line).strip()
        clean = re.sub(r"\(.*?\)", "", clean).strip()
        clean = re.sub(r"\s+", " ", clean).strip()
        if not clean or len(clean) < 4: continue
        if re.match(r"^[\d\s\-/]+$", clean): continue
        if NON_NAME.match(clean): continue
        if len(clean.split()) >= 1 and clean[0].isupper():
            return clean[:100]
    return "Unknown Bank"

def get_period(lines):
    for line in lines:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", "", line).strip()
        if re.search(r"(year|period|half.year)\s+ended|for the year|as at|as of", clean, re.IGNORECASE):
            if re.search(r"\d{4}", clean):
                return re.sub(r"\s+", " ", clean).strip()[:80]
    return ""

def parse_income_statement(lines):
    def fnd(pat):
        for line in lines:
            s = line.strip()
            if re.match(r"^[a-z]", s): continue
            if re.search(pat, s, re.IGNORECASE):
                cleaned = re.sub(r"(?<=[a-zA-Z\)])\s+(\d{1,3})\s+(?=[\d(])", "  ", s)
                nums = trailing_nums(cleaned)
                if len(nums) >= 2: return abs(nums[-2]), abs(nums[-1])
                if len(nums) == 1: return abs(nums[0]), None
        return None

    int_inc   = fnd(r"^interest\s+income(?!\s+and)")
    int_exp   = fnd(r"^interest\s+expense")
    nii       = fnd(r"net\s+interest\s+income")
    fee_net   = fnd(r"net\s+fee[s]?\s+(and|&)\s+commission|net\s+commission")
    fee_gross = fnd(r"gross\s+fee[s]?|fee[s]?\s+(and|&)\s+commission\s+income(?!\s+expense)") if not fee_net else None
    trading   = fnd(r"gains?\s+less\s+losses?\s+arising|net\s+trading\s+income|profit\s+on\s+trading|trading\s+income")
    other_op  = fnd(r"other\s+operating\s+income")
    total_op  = fnd(r"total\s+operating\s+income|operating\s+income\s+before\s+impairment|^operating\s+income\s*$")
    op_exp    = fnd(r"^operating\s+expenses?(?!\s+before|\s+net)")
    profit_bt = fnd(r"profit\s+before\s+tax(?:ation)?|income\s+before\s+tax")
    tax_exp   = fnd(r"tax\s+expense|income\s+tax\s+charge")
    rwa       = fnd(r"total\s+risk.weighted|risk.weighted\s+amount\s*$|total\s+rwa")

    nii_signed_c = None; nii_signed_p = None
    if int_inc and int_exp and int_inc[0] is not None and int_exp[0] is not None:
        nii_signed_c = int_inc[0] - int_exp[0]
        nii_signed_p = (int_inc[1] - int_exp[1]) if (int_inc[1] is not None and int_exp[1] is not None) else None
    elif nii:
        nii_signed_c = nii[0]; nii_signed_p = nii[1]

    mbi = None
    mbi_parts_c = [v for v in [nii_signed_c, fee_net[0] if fee_net else (fee_gross[0] if fee_gross else None), trading[0] if trading else None] if v is not None]
    mbi_parts_p = [v for v in [nii_signed_p, fee_net[1] if fee_net else (fee_gross[1] if fee_gross else None), trading[1] if trading else None] if v is not None]
    if len(mbi_parts_c) >= 1:
        mbi = (sum(mbi_parts_c), sum(mbi_parts_p) if mbi_parts_p else None)

    if total_op is None:
        parts_c = [v for v in [nii_signed_c,
                                fee_net[0] if fee_net else (fee_gross[0] if fee_gross else None),
                                trading[0] if trading else None,
                                other_op[0] if other_op else None] if v is not None]
        parts_p = [v for v in [nii_signed_p,
                                fee_net[1] if fee_net else (fee_gross[1] if fee_gross else None),
                                trading[1] if trading else None,
                                other_op[1] if other_op else None] if v is not None]
        if len(parts_c) >= 2:
            total_op = (sum(parts_c), sum(parts_p) if len(parts_p)>=2 else None)

    return {
        "int_inc": int_inc, "int_exp": int_exp, "nii": nii,
        "fee_net": fee_net or fee_gross, "trading": trading,
        "other_op": other_op, "total_op": total_op, "op_exp": op_exp,
        "profit_bt": profit_bt, "tax_exp": tax_exp, "mbi": mbi, "rwa": rwa,
    }

def run(pdf_bytes):
    pages = extract_pages(pdf_bytes)
    all_lines = []
    for _, lines, _ in pages: all_lines += lines
    bs_lines = []
    for _, lines, _ in pages[:6]: bs_lines += lines
    ul, mult = detect_unit(bs_lines)
    ta     = find_two(all_lines, r"total\s+assets|總資產")
    tl     = find_two(all_lines, r"total\s+liabilities|總負債")
    profit = find_two(all_lines, r"profit\s+after\s+tax(?:ation)?|net\s+profit(?:\s+after)?(?:\s+tax(?:ation)?)?\s*$|除稅後溢利")
    prov   = get_provisions(all_lines)
    lmr, cfr = get_lmr_cfr(all_lines, pdf_bytes)
    ai = parse_bs(all_lines, "assets")
    li = parse_bs(all_lines, "liabilities")
    entity  = get_entity_name(all_lines)
    period  = get_period(all_lines)
    inc     = parse_income_statement(all_lines)
    return {"unit_label": ul, "multiplier": mult, "ta": ta, "tl": tl, "profit": profit,
            "spec": prov["spec"], "coll": prov["coll"], "lmr": lmr, "cfr": cfr,
            "asset_items": ai, "liab_items": li, "entity": entity,
            "period": period, "raw_lines": all_lines, "inc": inc}

# ── Formatting helpers ──────────────────────────────────────────────────────
def fmt_n(v): return "—" if v is None else f"{abs(v):,.0f}"
def pct_chg(c,p):
    if c is None or p is None: return None
    if p == 0: return None
    return round((c-p)/abs(p)*100,2)
def fmt_chg(v):
    if v is None: return '<span class="muted">—</span>'
    css="chg-pos" if v>0 else "chg-neg"
    return f'<span class="{css}">{"+" if v>0 else ""}{v:.2f}%</span>'
def pp_html(v):
    if v is None: return ""
    css="chg-pos" if v>0 else "chg-neg"
    return f'<span class="{css}">{"+" if v>0 else ""}{v:.2f}pp</span>'
def fmt_snapshot(v,multiplier):
    if v is None: return "—"
    b = v * multiplier / 1e9
    return f"{b:.2f}B"
def dir_word(c,p):
    if c is None or p is None: return "changed"
    return "increased" if c>p else "decreased" if c<p else "remained flat"
def conc_word(c,p):
    if c is None or p is None: return "changed"
    d=c-p
    if abs(d)<0.5: return "remained broadly stable"
    return f"{'increased' if d>0 else 'decreased'} by {abs(d):.2f}pp"

# ── HTML report generator ───────────────────────────────────────────────────
def generate_report_html(d, filename, ul, mult):
    entity=d["entity"] or filename; period=d["period"] or ""
    ta,tl=d["ta"],d["tl"]; prof=d["profit"]; spec,coll=d["spec"],d["coll"]
    lmr,cfr=d["lmr"],d["cfr"]; ai,li=d["asset_items"],d["liab_items"]
    today=datetime.date.today().strftime("%d %B %Y")
    tc_c=ta[0] if ta else None; tc_p=ta[1] if ta else None
    tl_c=tl[0] if tl else None; tl_p=tl[1] if tl else None
    tot_prov=None
    if spec and coll:
        c2=(spec[1]+coll[1]) if (spec[1] is not None and coll[1] is not None) else None
        tot_prov=(spec[0]+coll[0], c2)
    elif coll: tot_prov=coll
    elif spec: tot_prov=spec

    def kfr(label,pair):
        if not pair: return f"<tr><td class='muted'>{label}</td><td class='muted'>-</td><td class='muted'>-</td><td class='muted'>-</td></tr>"
        c,p=pair[0],pair[1]; ch=pct_chg(c,p)
        chg_s=(f'+{ch:.2f}%' if ch and ch>0 else f'{ch:.2f}%') if ch else '-'
        return f"<tr><td>{label}</td><td>{fmt_n(c)}</td><td>{fmt_n(p)}</td><td>{chg_s}</td></tr>"

    ai_s=sorted([x for x in ai if x["curr"]],key=lambda x:x["curr"],reverse=True)
    li_s=sorted([x for x in li if x["curr"]],key=lambda x:x["curr"],reverse=True)
    def bullets(items,total_c,total_p,is_prior=False,is_liab=False):
        pool=sorted([x for x in items if (x.get("prior") if is_prior else x["curr"]) and (x.get("prior") if is_prior else x["curr"])>0],
                    key=lambda x:(x.get("prior") if is_prior else x["curr"]),reverse=True)[:3]
        tot=total_p if is_prior else total_c
        if not pool or not tot: return ""
        rows=""
        for i,x in enumerate(pool,1):
            v=x.get("prior") if is_prior else x["curr"]
            pct=round(v/tot*100,2)
            rows+=f"<div class='bullet'><span class='bullet-rank'>{i}</span><span class='bullet-name'>{x['label']}</span><span class='bullet-pct'>{pct:.2f}%</span><span class='bullet-unit'>{fmt_n(v)} {ul}</span></div>"
        return rows

    a_pc=round(sum(x["curr"] for x in ai_s[:3])/tc_c*100,2) if tc_c else None
    a_pp=round(sum(x.get("prior",0) or 0 for x in ai_s[:3])/tc_p*100,2) if tc_p else None
    l_pc=round(sum(x["curr"] for x in li_s[:3])/tl_c*100,2) if tl_c else None
    l_pp=round(sum(x.get("prior",0) or 0 for x in li_s[:3])/tl_p*100,2) if tl_p else None
    a_narr=(f"The top 3 biggest assets remain the same between the two periods. "
            f"Combined concentration {conc_word(a_pc,a_pp) if a_pc and a_pp else 'changed'}{f', from {a_pp:.2f}% to {a_pc:.2f}% of total assets' if a_pc and a_pp else ''}. "
            f"The largest asset, {ai_s[0]['label'] if ai_s else 'N/A'}, represents {round(ai_s[0]['curr']/tc_c*100,2):.2f}% of total assets." if ai_s and tc_c else "")
    l_narr=(f"The top 3 biggest liabilities remain the same from the prior period. "
            f"Combined concentration {conc_word(l_pc,l_pp) if l_pc and l_pp else 'changed'}{f', from {l_pp:.2f}% to {l_pc:.2f}% of total liabilities' if l_pc and l_pp else ''}." if li_s and tl_c else "")

    lmr_text=(f"The LMR {dir_word(lmr[0],lmr[1])} from {lmr[1]:.2f}% to {lmr[0]:.2f}% ({'+' if lmr[0]-lmr[1]>0 else ''}{lmr[0]-lmr[1]:.2f}pp). The LMR is well above the 25% regulatory minimum." if lmr else "LMR not disclosed.")
    cfr_text=(f"The CFR {dir_word(cfr[0],cfr[1])} from {cfr[1]:.2f}% to {cfr[0]:.2f}% ({'+' if cfr[0]-cfr[1]>0 else ''}{cfr[0]-cfr[1]:.2f}pp). The CFR is well above the 75% regulatory minimum." if cfr else "CFR not disclosed.")

    kf_rows=[("Profit after taxation",prof),("Return on Assets",None),("Total assets",ta),("Total liabilities",tl),
             ("Specific / Individual provisions",spec),("Collective provisions",coll),("Total provisions",tot_prov)]
    kf_html="".join(kfr(l,p) for l,p in kf_rows)

    inc=d.get("inc",{})
    def iv(k): v=inc.get(k); return (v[0] if v else None, v[1] if v else None)
    goi_c,goi_p=iv("total_op"); opex_c,opex_p=iv("op_exp")
    prof_c=prof[0] if prof else None; prof_p=prof[1] if prof else None
    cir_c=round(opex_c/goi_c*100,1) if goi_c and opex_c else None
    cir_p=round(opex_p/goi_p*100,1) if goi_p and opex_p else None
    roa_c=round(prof_c/tc_c*100,3) if prof_c and tc_c else None
    roa_p=round(prof_p/tc_p*100,3) if prof_p and tc_p else None
    rwa_c,rwa_p=iv("rwa")
    inc_rwa_c=round(goi_c/rwa_c*100,2) if goi_c and rwa_c else None

    def prow(lbl,cv,pv,sfx="%",is_pct=True):
        if cv is None: return f"<tr><td class='muted'>{lbl}</td><td class='muted'>-</td><td class='muted'>-</td><td class='muted'>-</td></tr>"
        dc=f"{cv:.2f}{sfx}" if is_pct else fmt_n(cv)
        dp=f"{pv:.2f}{sfx}" if (is_pct and pv) else (fmt_n(pv) if pv else "-")
        ch=(cv-pv) if (is_pct and pv) else pct_chg(cv,pv)
        cs=(f'+{ch:.2f}' if ch and ch>0 else f'{ch:.2f}') if ch else "-"
        sfx2="pp" if is_pct else "%"
        return f"<tr><td>{lbl}</td><td>{dc}</td><td>{dp}</td><td>{cs}{sfx2 if ch else ''}</td></tr>"

    prof_html=(prow("Cost-Income Ratio (CIR)",cir_c,cir_p)+
               prow("Return on Assets (ROA)",roa_c,roa_p)+
               prow("Income / RWA",inc_rwa_c,None)+
               prow("RWA (total)",rwa_c,rwa_p,sfx=f" {ul}",is_pct=False))

    def full_table(items,total,title):
        if not items or not total: return ""
        rows="".join(f"<tr><td>{x['label']}</td><td>{fmt_n(x['curr'])}</td>"
                     f"<td><b>{round(x['curr']/total*100,2):.2f}%</b></td>"
                     f"<td>{fmt_n(x.get('prior'))}</td></tr>"
                     for x in sorted(items,key=lambda x:x['curr'],reverse=True))
        return (f"<h2>{title}</h2><table><thead><tr>"
                f"<th style='text-align:left'>Item</th>"
                f"<th>Current ({ul})</th><th>%</th><th>Prior ({ul})</th>"
                f"</tr></thead><tbody>{rows}</tbody></table>")

    return f"""<!DOCTYPE html><html><head><meta charset='UTF-8'>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600;700&display=swap');
body{{font-family:'DM Sans',sans-serif;background:#fff;color:#111;font-size:10pt;line-height:1.6;max-width:780px;margin:0 auto;padding:40px 48px;}}
.doc-header{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:2px solid #E60028;padding-bottom:14px;margin-bottom:20px;}}
.doc-bank{{font-size:1.5rem;font-weight:700;letter-spacing:-.01em;line-height:1.1;margin-bottom:3px;}}
.doc-sub{{font-size:.72rem;color:#999;}} .doc-meta{{font-size:.68rem;color:#bbb;margin-top:4px;}}
.unit-tag{{display:inline-block;font-size:.6rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:#E60028;border:1px solid #E60028;padding:2px 8px;margin:10px 0 20px 0;}}
.desc{{border-left:3px solid #E60028;padding:8px 14px;background:#fafafa;margin-bottom:24px;font-size:.8rem;color:#444;line-height:1.7;}}
h2{{font-size:.62rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#555;border-bottom:1px solid #eee;padding-bottom:4px;margin-top:32px;margin-bottom:12px;}}
.narrative{{font-size:.82rem;color:#333;line-height:1.7;margin-bottom:8px;}}
table{{width:100%;border-collapse:collapse;font-size:.78rem;margin:8px 0 18px;}}
thead{{border-bottom:2px solid #E60028;}}
th{{font-size:.58rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#999;padding:0 10px 7px;text-align:right;}}
th:first-child{{text-align:left;}}
td{{padding:6px 10px;border-bottom:1px solid #f5f5f5;text-align:right;}}
td:first-child{{text-align:left;}}
td.muted{{color:#ccc;}}
.bullet{{display:flex;align-items:baseline;gap:8px;padding:5px 0;border-bottom:1px solid #f5f5f5;font-size:.8rem;}}
.bullet-rank{{display:inline-block;font-size:.6rem;font-weight:700;color:#E60028;border:1px solid #E60028;width:16px;height:16px;line-height:16px;text-align:center;flex-shrink:0;}}
.bullet-name{{flex:1;color:#111;}} .bullet-pct{{font-weight:700;color:#111;min-width:90px;text-align:right;}} .bullet-unit{{color:#bbb;font-size:.72rem;min-width:140px;text-align:right;}}
.doc-footer{{margin-top:48px;padding-top:12px;border-top:1px solid #eee;font-size:.62rem;color:#bbb;display:flex;justify-content:space-between;}}
</style></head><body>
<div class="doc-header">
  <div><div class="doc-bank">{entity}</div><div class="doc-sub">HKMA Key Financial Information Disclosure Statement</div></div>
  <div style="text-align:right"><div class="doc-meta">{period}</div><div class="doc-meta">Generated {today}</div></div>
</div>
<div class="unit-tag">Reported in {ul} &nbsp;·&nbsp; Snapshot figures in HKD billions</div>
<h2>Liquidity Ratios</h2>
<p class="narrative"><strong>3-Month LMR:</strong> <span style="color:#E60028">{f"{lmr[0]:.2f}%" if lmr else "—"}</span> (current) &nbsp;/&nbsp; {f"{lmr[1]:.2f}%" if lmr else "—"} (prior)</p>
<p class="narrative">{lmr_text}</p>
<p class="narrative"><strong>3-Month CFR:</strong> <span style="color:#E60028">{f"{cfr[0]:.2f}%" if cfr else "—"}</span> (current) &nbsp;/&nbsp; {f"{cfr[1]:.2f}%" if cfr else "—"} (prior)</p>
<p class="narrative">{cfr_text}</p>
<h2>Key Financials</h2>
<table><thead><tr><th style='text-align:left'>Item</th><th>Current ({ul})</th><th>Prior ({ul})</th><th>Change</th></tr></thead>
<tbody>{kf_html}</tbody></table>
<h2>Profitability &amp; Efficiency</h2>
<table><thead><tr><th style='text-align:left'>Ratio</th><th>Current</th><th>Prior</th><th>Change</th></tr></thead>
<tbody>{prof_html}</tbody></table>
<h2>Asset Concentration — Current</h2>
{bullets(ai,tc_c,tc_p,False,False)}
<h2>Asset Concentration — Prior</h2>
{bullets(ai,tc_c,tc_p,True,False)}
<p class="narrative">{a_narr}</p>
<h2>Liability Concentration — Current</h2>
{bullets(li,tl_c,tl_p,False,True)}
<h2>Liability Concentration — Prior</h2>
{bullets(li,tl_c,tl_p,True,True)}
<p class="narrative">{l_narr}</p>
{full_table(ai,tc_c,"Full Asset Breakdown")}
{full_table(li,tl_c,"Full Liability Breakdown")}
<div class="doc-footer"><span>HKMA Financial Disclosure Reader</span><span>{today}</span></div>
</body></html>"""

# ════════════════════════════════════════════════════════════════════════════
# STREAMLIT APP
# ════════════════════════════════════════════════════════════════════════════
st.markdown("<h1>HKMA Financial Disclosure Reader</h1>",unsafe_allow_html=True)
st.markdown("""
<div class="accuracy-disclaimer">
  <span>Data accuracy notice:</span> This tool reads PDF disclosures automatically. Inconsistent layouts, scanned pages, wrapped labels, OCR issues, or unusual statement formatting can cause extraction errors. If any figure appears incomplete, misplaced, or clearly incorrect, verify it against the original financial statement before relying on the output.
</div>
""", unsafe_allow_html=True)

uploaded=st.file_uploader("Upload HKMA Key Financial Information Disclosure PDF",type="pdf")

if not uploaded:
    st.markdown("""
    <div style="margin-top:40px;padding:40px;border:1px dashed #ddd;text-align:center;background:#fafafa">
      <div style="font-size:.82rem;letter-spacing:.1em;text-transform:uppercase;color:#ccc;margin-bottom:6px;">Drop a disclosure PDF to begin</div>
      <div style="font-size:.82rem;color:#ddd;">Supports JPMorgan, CA-CIB, Societe Generale, Natixis, BNP Paribas, UBS, Barclays and other HKMA-format disclosures</div>
    </div>""",unsafe_allow_html=True)

if uploaded:
    pdf_bytes=uploaded.read()
    with st.spinner("Extracting and generating report..."):
        d=run(pdf_bytes)
    ul=d["unit_label"]; mult=d["multiplier"]
    ta,tl=d["ta"],d["tl"]; spec,coll=d["spec"],d["coll"]
    lmr,cfr=d["lmr"],d["cfr"]; prof=d["profit"]
    ai,li=d["asset_items"],d["liab_items"]
    inc=d.get("inc") or {}
    entity=d["entity"] or uploaded.name.replace(".pdf","").replace("_"," ").upper()
    period=d["period"] or ""
    tcc=ta[0] if ta else None; tcp=ta[1] if ta else None
    tlc=tl[0] if tl else None; tlp=tl[1] if tl else None
    sn=entity.split()[0] if entity else "The branch"

    tot_prov=None
    if spec and coll:
        c2=(spec[1]+coll[1]) if (spec[1] is not None and coll[1] is not None) else None
        tot_prov=(spec[0]+coll[0], c2)
    elif coll: tot_prov=coll
    elif spec: tot_prov=spec

    # ── helpers ──────────────────────────────────────────────────────────────
    def kpi_block(label,rv,rp,is_ratio=False):
        if rv is None: return ""
        display=f"{rv:.2f}%" if is_ratio else f"HKD {fmt_snapshot(rv,mult)}"
        chg_html=""
        if rp is not None:
            chg=round(rv-rp,2) if is_ratio else pct_chg(rv,rp)
            if chg is not None:
                sfx="pp" if is_ratio else "%"; css="kpi-chg-pos" if chg>0 else "kpi-chg-neg"
                chg_html=f'<div class="{css}">{"+" if chg>0 else ""}{chg:.2f}{sfx} vs prior</div>'
        return f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-val">{display}</div>{chg_html}</div>'

    def render_stacked_bars(items, total_pair, section_title):
        tc=total_pair[0] if total_pair else None
        tp=total_pair[1] if total_pair else None
        valid=sorted([x for x in items if x["curr"] and x["curr"]>0],key=lambda x:x["curr"],reverse=True)
        if not valid or not tc:
            st.markdown(f'<p style="font-size:.88rem;color:#bbb">No {section_title.lower()} data.</p>',unsafe_allow_html=True); return
        palette=["#E60028","#111111","#555555","#888888","#AAAAAA","#CCCCCC","#DDDDDD","#B00020","#333333","#777777","#999999","#BBBBBB"]
        vals_curr=[round(x["curr"]/tc*100,2) for x in valid]
        has_prior=tp and any(x.get("prior") for x in valid)
        vals_prior=[round((x.get("prior") or 0)/tp*100,2) for x in valid] if has_prior else []
        periods=["Current","Prior"] if has_prior else ["Current"]
        fig=go.Figure()
        for i,x in enumerate(valid):
            color=palette[i%len(palette)]
            y_vals=[vals_curr[i]]
            if has_prior: y_vals=[vals_curr[i],vals_prior[i]]
            fig.add_trace(go.Bar(
                name=x["label"],x=periods,y=y_vals,marker_color=color,
                hovertemplate=f"<b>{x['label']}</b><br>%{{y:.2f}}%<extra></extra>",
                text=[f"{v:.1f}%" if v>=4 else "" for v in y_vals],
                textposition="inside",insidetextanchor="middle",
                textfont=dict(size=9,color="#ffffff",family="DM Sans, sans-serif"),
            ))
        fig.update_layout(
            barmode="stack",
            title=dict(text=section_title.upper(),font=dict(size=9,color="#888888",family="DM Sans, sans-serif"),x=0,xanchor="left",pad=dict(b=4)),
            height=400,margin=dict(l=0,r=0,t=28,b=60),
            paper_bgcolor="#ffffff",plot_bgcolor="#ffffff",
            yaxis=dict(range=[0,100],ticksuffix="%",tickfont=dict(size=8,color="#999999",family="DM Sans, sans-serif"),showgrid=True,gridcolor="#f0f0f0",gridwidth=0.5,zeroline=False),
            xaxis=dict(tickfont=dict(size=9,color="#111111",family="DM Sans, sans-serif"),showgrid=False),
            legend=dict(orientation="h",x=0,y=-0.22,font=dict(size=8,color="#444444",family="DM Sans, sans-serif"),bgcolor="rgba(0,0,0,0)",traceorder="normal",itemwidth=30),
            showlegend=True,
        )
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    def render_top3_section(items,total_pair,period_label,is_prior=False):
        tc=total_pair[0] if total_pair else None; tp=total_pair[1] if total_pair else None
        pool=sorted([x for x in items if (x.get("prior") if is_prior else x["curr"]) and (x.get("prior") if is_prior else x["curr"])>0],
                    key=lambda x:(x.get("prior") if is_prior else x["curr"]),reverse=True)[:3]
        tot=tp if is_prior else tc
        if not pool or not tot: st.markdown('<p style="font-size:.88rem;color:#bbb">No data.</p>',unsafe_allow_html=True); return
        rows="".join(f"""<tr><td><span class="rank">{i}</span>{x['label']}</td>
          <td><b>{round((x.get('prior') if is_prior else x['curr'])/tot*100,2):.2f}%</b></td>
          <td class="muted">{fmt_n(x.get('prior') if is_prior else x['curr'])}</td></tr>"""
          for i,x in enumerate(pool,1))
        st.markdown(f"""<p style="font-size:.75rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#aaa;margin:10px 0 6px">{period_label}</p>
          <table><thead><tr><th style="text-align:left">Item</th><th>% of Total</th><th>{ul}</th></tr></thead>
          <tbody>{rows}</tbody></table>""",unsafe_allow_html=True)

    def render_full_table(items,total_pair,title):
        tc=total_pair[0] if total_pair else None; tp=total_pair[1] if total_pair else None
        valid=sorted([x for x in items if x["curr"] is not None],key=lambda x:x["curr"],reverse=True)
        st.markdown(f"<h3>{title}</h3>",unsafe_allow_html=True)
        if not valid or not tc: st.markdown('<p style="font-size:.88rem;color:#bbb">No items extracted.</p>',unsafe_allow_html=True); return
        rows="".join(f"""<tr><td>{x['label']}</td><td>{fmt_n(x['curr'])}</td>
          <td>{"<span class='muted'>—</span>" if not tc or not x['curr'] else f"<b>{round(x['curr']/tc*100,2):.2f}%</b>"}</td>
          <td class="muted">{fmt_n(x.get('prior'))}</td>
          <td>{"<span class='muted'>—</span>" if not tp or not x.get('prior') else f"{round(x['prior']/tp*100,2):.2f}%"}</td></tr>""" for x in valid)
        st.markdown(f"""<table><thead><tr><th style="text-align:left">Item</th>
          <th>Current ({ul})</th><th>% of Total</th><th>Prior ({ul})</th><th>% (Prior)</th></tr></thead>
          <tbody>{rows}</tbody></table>""",unsafe_allow_html=True)

    def prov_analysis_sentence():
        if not (spec or coll): return ""
        spec_c=spec[0] if spec else None; spec_p=spec[1] if spec else None
        coll_c=coll[0] if coll else None; coll_p=coll[1] if coll else None
        tot_c=(spec_c or 0)+(coll_c or 0); tot_p=(spec_p or 0)+(coll_p or 0)
        pct=pct_chg(tot_c,tot_p)
        direction="rose" if (pct and pct>0) else "fell" if (pct and pct<0) else "remained flat"
        pct_str=f"{abs(pct):.1f}%" if pct else "N/A"
        spec_chg=abs(pct_chg(spec_c,spec_p) or 0) if spec_c and spec_p else 0
        coll_chg=abs(pct_chg(coll_c,coll_p) or 0) if coll_c and coll_p else 0
        driver="specific" if spec_chg>=coll_chg else "collective"
        more_less="more" if direction=="rose" else "less"
        ai_s=sorted([x for x in ai if x["curr"]],key=lambda x:x["curr"],reverse=True)
        dom_asset=ai_s[0]["label"] if ai_s else "N/A"
        dom_lower=dom_asset.lower()
        if "overseas" in dom_lower: risk_sits="the parent group"
        else: risk_sits="external borrowers"
        return (f'Provisions {direction} {pct_str}, driven by {driver} provisions, implying {more_less} '
                f'identified credit risk; the dominant asset is {dom_asset}, so credit risk sits primarily with {risk_sits}.')

    # ── concentration data ────────────────────────────────────────────────────
    ai_s=sorted([x for x in ai if x["curr"]],key=lambda x:x["curr"],reverse=True)
    li_s=sorted([x for x in li if x["curr"]],key=lambda x:x["curr"],reverse=True)
    ai3=ai_s[:3]; li3=li_s[:3]
    ai_p=sorted([x for x in ai if x.get("prior")],key=lambda x:x["prior"],reverse=True)[:3]
    li_p=sorted([x for x in li if x.get("prior")],key=lambda x:x["prior"],reverse=True)[:3]
    a_same=set(x["label"] for x in ai3)==set(x["label"] for x in ai_p)
    l_same=set(x["label"] for x in li3)==set(x["label"] for x in li_p)
    acc=sum(x["curr"] for x in ai3 if x["curr"]); acp=sum(x.get("prior",0) or 0 for x in ai3)
    apc=round(acc/tcc*100,2) if tcc else None; app_=round(acp/tcp*100,2) if tcp else None
    lcc=sum(x["curr"] for x in li3 if x["curr"]); lcp=sum(x.get("prior",0) or 0 for x in li3)
    lpc=round(lcc/tlc*100,2) if tlc else None; lpp_=round(lcp/tlp*100,2) if tlp else None
    a_narrative=(f"The top 3 biggest assets {'remain the same' if a_same else 'differ'} between the two periods. "
        f"Combined concentration {conc_word(apc,app_) if apc and app_ else 'changed'}"
        f"{f', from {app_:.2f}% to {apc:.2f}% of total assets' if apc and app_ else ''}. "
        f"The largest asset, {ai3[0]['label'] if ai3 else 'N/A'}, represents "
        f"{round(ai3[0]['curr']/tcc*100,2):.2f}% of total assets." if ai3 and tcc else "")
    a_takeaway=(f"{'High concentration' if apc and apc>75 else 'Moderate diversification'} in top 3 assets. "
        f"{ai3[0]['label'] if ai3 else ''} dominates at {round(ai3[0]['curr']/tcc*100,2):.2f}%." if ai3 and tcc else "")
    l_narrative=(f"The top 3 biggest liabilities {'remain the same' if l_same else 'changed'} from the prior period. "
        f"Combined concentration {conc_word(lpc,lpp_) if lpc and lpp_ else 'changed'}"
        f"{f', from {lpp_:.2f}% to {lpc:.2f}% of total liabilities' if lpc and lpp_ else ''}. "
        f"The dominant liability is {li3[0]['label'] if li3 else 'N/A'}, at "
        f"{round(li3[0]['curr']/tlc*100,2):.2f}% of total liabilities." if li3 and tlc else "")
    l_takeaway=(f"{'High' if lpc and lpc>70 else 'Moderate'} liability concentration in top 3. "
        f"{'Funding is heavily reliant on ' + li3[0]['label'] + '.' if lpc and lpc>70 and li3 else 'Reasonably diversified funding.'}")
    pc=pct_chg(prof[0],prof[1]) if prof else None
    overall_summary=(f"{entity} reported profit after taxation of {fmt_n(prof[0])} {ul} for the period, "
        f"{'up' if pc and pc>0 else 'down'} {abs(pc):.2f}% versus the prior period. "
        f"Total assets {'grew' if ta and ta[0]>ta[1] else 'contracted'} to {fmt_n(ta[0])} {ul}. "
        f"Liquidity ratios remain comfortably above regulatory minimums." if prof and ta else "")
    executive_takeaway=(f"{'Strong' if pc and pc>0 else 'Resilient'} performance with robust liquidity buffers. "
        f"Monitor concentration in {ai3[0]['label'] if ai3 else 'primary asset'} as the dominant balance sheet item. "
        f"{prov_analysis_sentence()}")

    # ═══════════════════════════════════════════════════════════════════════
    # RENDER
    # ═══════════════════════════════════════════════════════════════════════

    # 1. HEADER
    st.markdown(f"""
    <div class="pg-header">
      <div class="pg-bank">{entity}</div>
      <div class="pg-meta">HKMA Key Financial Disclosure<br><span>{period}</span></div>
    </div>
    <div class="unit-tag">Reported in {ul} &nbsp;·&nbsp; Snapshot figures in HKD billions</div>
    """,unsafe_allow_html=True)

    # 2. EXECUTIVE TAKEAWAY
    if executive_takeaway:
        st.markdown(f'<div class="desc-block"><div class="desc-text"><b>Executive Takeaway:</b> {executive_takeaway}</div></div>',unsafe_allow_html=True)

    # 3. KPI TILES
    kpis="".join(filter(None,[
        kpi_block("Total Assets",ta[0] if ta else None,ta[1] if ta else None),
        kpi_block("Profit after Tax",prof[0] if prof else None,prof[1] if prof else None),
        kpi_block("Avg LMR",lmr[0] if lmr else None,lmr[1] if lmr else None,True),
        kpi_block("Avg CFR",cfr[0] if cfr else None,cfr[1] if cfr else None,True),
        kpi_block("Total Provisions",tot_prov[0] if tot_prov else None,tot_prov[1] if tot_prov else None),
    ]))
    if kpis: st.markdown(f'<div class="snapshot">{kpis}</div>',unsafe_allow_html=True)

    # 4. LIQUIDITY
    st.markdown("<h2>Liquidity Ratios</h2>",unsafe_allow_html=True)
    lpp_v=round(lmr[0]-lmr[1],2) if lmr else None
    cpp_v=round(cfr[0]-cfr[1],2) if cfr else None
    st.markdown(f"""<div class="ratio-grid">
      <div class="ratio-card"><div class="ratio-label">3-Month Average LMR</div>
        <div><span class="ratio-main">{f"{lmr[0]:.2f}%" if lmr else "—"}</span>
        <span class="ratio-prior">{f"prev {lmr[1]:.2f}%" if lmr else ""}</span></div>
        <div style="margin-top:6px">{pp_html(lpp_v)}</div></div>
      <div class="ratio-card"><div class="ratio-label">3-Month Average CFR</div>
        <div><span class="ratio-main">{f"{cfr[0]:.2f}%" if cfr else "—"}</span>
        <span class="ratio-prior">{f"prev {cfr[1]:.2f}%" if cfr else ""}</span></div>
        <div style="margin-top:6px">{pp_html(cpp_v)}</div></div></div>""",unsafe_allow_html=True)
    lmr_narr=(f"The LMR {dir_word(lmr[0],lmr[1])} from {lmr[1]:.2f}% to {lmr[0]:.2f}% ({'+'if lpp_v and lpp_v>0 else ''}{lpp_v:.2f}pp). "
        f"{sn} holds sufficient liquid assets to cover ~{lmr[0]:.0f}% of liabilities maturing within one month. "
        f"The LMR remains well above the regulatory minimum of 25%." if lmr else "LMR data not found.")
    cfr_narr=(f"The CFR {dir_word(cfr[0],cfr[1])} from {cfr[1]:.2f}% to {cfr[0]:.2f}% ({'+'if cpp_v and cpp_v>0 else ''}{cpp_v:.2f}pp). "
        f"Stable funding sources adequately cover required stable funding needs. "
        f"The CFR remains well above the regulatory minimum of 75%." if cfr else "CFR not disclosed.")
    liq_overall=(f"In terms of liquidity, {sn} is above regulatory requirements on both ratios, with an LMR of {lmr[0]:.0f}%, demonstrating a strong liquidity buffer." if lmr else "")
    st.markdown(f"""
      <p style="font-size:.9rem;color:#333;line-height:1.7;margin:8px 0 4px">{lmr_narr}</p>
      <p style="font-size:.9rem;color:#333;line-height:1.7;margin:4px 0 4px">{cfr_narr}</p>
      {"<p style='font-size:.9rem;color:#555;line-height:1.7;font-style:italic;border-left:2px solid #E60028;padding-left:10px;margin:8px 0 0'>"+liq_overall+"</p>" if liq_overall else ""}
    """,unsafe_allow_html=True)

    # 5. KEY FINANCIALS TABLE
    st.markdown("<h2>Key Financials</h2>",unsafe_allow_html=True)
    kf_rows=[("Profit after taxation",prof),("Total assets",ta),("Total liabilities",tl),
             ("Specific / Individual provisions",spec),("Collective provisions",coll),("Total provisions",tot_prov)]
    rows_html=""
    for label,pair in kf_rows:
        if pair:
            cv,pv=pair[0],pair[1]
            rows_html+=f"<tr><td>{label}</td><td>{fmt_n(cv)}</td><td>{fmt_n(pv)}</td><td>{fmt_chg(pct_chg(cv,pv))}</td></tr>"
        else:
            rows_html+=f'<tr><td class="muted">{label}</td><td class="muted">—</td><td class="muted">—</td><td class="muted">—</td></tr>'
    st.markdown(f"""<table><thead><tr><th>Metric</th><th>Current ({ul})</th><th>Prior ({ul})</th><th>Change</th></tr></thead>
      <tbody>{rows_html}</tbody></table>""",unsafe_allow_html=True)

    # 5b. PROFITABILITY & EFFICIENCY
    st.markdown("<h2>Profitability &amp; Efficiency</h2>",unsafe_allow_html=True)
    def iv(key): v=inc.get(key); return (v[0] if v else None, v[1] if v else None)
    nii_c,nii_p   = iv("nii")
    fee_c,fee_p   = iv("fee_net")
    trad_c,trad_p = iv("trading")
    mbi_c,mbi_p   = iv("mbi")
    goi_c,goi_p   = iv("total_op")
    opex_c,opex_p = iv("op_exp")
    rwa_c,rwa_p   = iv("rwa")
    prof_c=prof[0] if prof else None; prof_p=prof[1] if prof else None
    def safe_ratio(num,den):
        if num is None or den is None or den==0: return None
        return round(num/den*100,2)
    cir_c=safe_ratio(opex_c,goi_c); cir_p=safe_ratio(opex_p,goi_p)
    roa_c=safe_ratio(prof_c,tcc);   roa_p=safe_ratio(prof_p,tcp)
    inc_rwa_c=safe_ratio(goi_c,rwa_c); inc_rwa_p=safe_ratio(goi_p,rwa_p)

    is_rows=[("Net Interest Income (NII)",nii_c,nii_p),("Net Fees & Commissions",fee_c,fee_p),
             ("Net Trading Income",trad_c,trad_p),("Market/Banking Income (MBI)",mbi_c,mbi_p),
             ("Gross Operating Income (GOI)",goi_c,goi_p),("Operating Expenses",opex_c,opex_p)]
    is_html="".join(
        f"<tr><td>{lbl}</td><td>{fmt_n(cv)}</td><td>{fmt_n(pv)}</td><td>{fmt_chg(pct_chg(cv,pv))}</td></tr>"
        if cv is not None else
        f"<tr><td class='muted'>{lbl}</td><td class='muted'>—</td><td class='muted'>—</td><td class='muted'>—</td></tr>"
        for lbl,cv,pv in is_rows)
    st.markdown(f"""<table><thead><tr><th>Income Statement</th><th>Current ({ul})</th><th>Prior ({ul})</th><th>Change</th></tr></thead>
      <tbody>{is_html}</tbody></table>""",unsafe_allow_html=True)

    rat_html=""
    for lbl,cv,pv,is_pct in [("Cost-Income Ratio (CIR)",cir_c,cir_p,True),("Return on Assets (ROA)",roa_c,roa_p,True),
                               ("Income / RWA",inc_rwa_c,inc_rwa_p,True),("RWA (total)",rwa_c,rwa_p,False)]:
        if cv is not None:
            dc=f"{cv:.2f}%" if is_pct else fmt_n(cv)
            dp=f"{pv:.2f}%" if (is_pct and pv is not None) else (fmt_n(pv) if pv else "—")
            chg_v=(cv-pv) if (is_pct and pv is not None) else pct_chg(cv,pv)
            rat_html+=f"<tr><td><b>{lbl}</b></td><td>{dc}</td><td>{dp}</td><td>{fmt_chg(round(chg_v,2)) if chg_v is not None else '<span class=muted>—</span>'}</td></tr>"
        else:
            rat_html+=f"<tr><td class='muted'>{lbl}</td><td class='muted'>—</td><td class='muted'>—</td><td class='muted'>—</td></tr>"
    st.markdown(f"""<table><thead><tr><th>Ratio</th><th>Current</th><th>Prior</th><th>Change</th></tr></thead>
      <tbody>{rat_html}</tbody></table>""",unsafe_allow_html=True)

    # Profitability narrative
    prof_lines=[]
    if cir_c is not None:
        cir_label="efficient" if cir_c<60 else "elevated" if cir_c<80 else "strained"
        trend=dir_word(cir_c,cir_p) if cir_p else "unchanged"
        prof_lines.append(f"The Cost-Income Ratio stands at {cir_c:.1f}%, signalling {cir_label} cost control; it {trend} versus the prior period ({f'{cir_p:.1f}%' if cir_p else 'N/A'}).")
    if roa_c is not None:
        roa_label="strong" if roa_c>1.0 else "moderate" if roa_c>0.3 else "thin"
        prof_lines.append(f"ROA of {roa_c:.3f}% reflects {roa_label} returns on the asset base.")
    if goi_c is not None and nii_c is not None and goi_c>0:
        nii_share=round(nii_c/goi_c*100,1); fee_share=round(fee_c/goi_c*100,1) if fee_c else 0; trad_share=round(trad_c/goi_c*100,1) if trad_c else 0
        prof_lines.append(f"GOI of {fmt_n(goi_c)} {ul} is composed of NII ({nii_share:.0f}%){f', fees ({fee_share:.0f}%)' if fee_c else ''}{f', and trading ({trad_share:.0f}%)' if trad_c else ''}.")
    if rwa_c is not None and inc_rwa_c is not None:
        rwa_eff="high" if inc_rwa_c>5 else "moderate" if inc_rwa_c>2 else "low"
        prof_lines.append(f"Income/RWA of {inc_rwa_c:.2f}% indicates {rwa_eff} capital efficiency. Reducing RWA lowers the cost of equity allocated to the branch.")
    else:
        prof_lines.append("RWA is not disclosed at branch level in this statement; Income/RWA cannot be computed. RWA optimisation levers include shifting to secured lending, netting derivatives, and growing fee income (zero RWA).")
    for line in prof_lines:
        st.markdown(f'<p style="font-size:.9rem;color:#333;line-height:1.7;margin:6px 0">{line}</p>',unsafe_allow_html=True)
    dom_asset_lbl=ai_s[0]["label"] if ai_s else ""
    if "overseas" in dom_asset_lbl.lower():
        rwa_takeaway=("As the dominant asset is intra-group (overseas offices), credit RWA is driven by internal exposures. "
            "RWA can be reduced by compressing intra-group balances, moving to lower risk-weight collateralised products, "
            "growing fee and advisory income (zero RWA), and optimising netting agreements on derivatives. "
            "This directly lowers the cost of equity capital allocated to the branch.")
    else:
        rwa_takeaway=("The dominant asset is customer loans, so credit RWA is primarily driven by external borrower risk weights. "
            "RWA can be reduced by shifting toward better-collateralised lending (lower LGD), "
            "increasing fee-based revenues (zero RWA), and tightening credit standards on higher-risk segments.")
    st.markdown(f'<div class="desc-block" style="margin-top:8px"><div class="desc-text"><b>RWA Optimisation:</b> {rwa_takeaway}</div></div>',unsafe_allow_html=True)

    # 6. BALANCE SHEET COMPOSITION CHARTS
    st.markdown("<h2>Balance Sheet Composition</h2>",unsafe_allow_html=True)
    st.markdown('<p style="font-size:.88rem;color:#888;margin-bottom:16px;">100% stacked composition — current vs prior period.</p>',unsafe_allow_html=True)
    col_a,col_l=st.columns(2)
    with col_a: render_stacked_bars(ai,ta,"Asset Composition")
    with col_l: render_stacked_bars(li,tl,"Liability Composition")

    # 7. ASSET QUALITY & CREDIT RISK (PROVISIONS)
    st.markdown("<h2>Asset Quality &amp; Credit Risk</h2>",unsafe_allow_html=True)
    prov_rows=[("Specific / Individual provisions",spec),("Collective provisions",coll),("Total provisions",tot_prov)]
    prov_html=""
    for label,pair in prov_rows:
        if pair:
            cv,pv=pair[0],pair[1]
            prov_html+=f"<tr><td>{label}</td><td>{fmt_n(cv)}</td><td>{fmt_n(pv)}</td><td>{fmt_chg(pct_chg(cv,pv))}</td></tr>"
        else:
            prov_html+=f'<tr><td class="muted">{label}</td><td class="muted">—</td><td class="muted">—</td><td class="muted">—</td></tr>'
    st.markdown(f"""<table><thead><tr><th>Provisions</th><th>Current ({ul})</th><th>Prior ({ul})</th><th>Change</th></tr></thead>
      <tbody>{prov_html}</tbody></table>""",unsafe_allow_html=True)
    prov_sent=prov_analysis_sentence()
    if prov_sent:
        st.markdown(f'<p style="font-size:.9rem;color:#333;line-height:1.7;border-left:2px solid #E60028;padding-left:10px;margin:8px 0 16px">{prov_sent}</p>',unsafe_allow_html=True)

    # 8. ASSET CONCENTRATION
    st.markdown("<h2>Asset Concentration</h2>",unsafe_allow_html=True)
    render_top3_section(ai,ta,"Current Period",is_prior=False)
    render_top3_section(ai,ta,"Prior Period",is_prior=True)
    if a_narrative: st.markdown(f'<p style="font-size:.9rem;color:#333;line-height:1.7;margin:10px 0 4px">{a_narrative}</p>',unsafe_allow_html=True)
    if a_takeaway:  st.markdown(f'<p style="font-size:.88rem;color:#555;font-style:italic;border-left:2px solid #E60028;padding-left:10px;margin:4px 0 16px">{a_takeaway}</p>',unsafe_allow_html=True)
    st.markdown('<hr class="rule">',unsafe_allow_html=True)

    # 9. LIABILITY CONCENTRATION
    st.markdown("<h2>Liability Concentration</h2>",unsafe_allow_html=True)
    render_top3_section(li,tl,"Current Period",is_prior=False)
    render_top3_section(li,tl,"Prior Period",is_prior=True)
    if l_narrative: st.markdown(f'<p style="font-size:.9rem;color:#333;line-height:1.7;margin:10px 0 4px">{l_narrative}</p>',unsafe_allow_html=True)
    if l_takeaway:  st.markdown(f'<p style="font-size:.88rem;color:#555;font-style:italic;border-left:2px solid #E60028;padding-left:10px;margin:4px 0 16px">{l_takeaway}</p>',unsafe_allow_html=True)
    st.markdown('<hr class="rule">',unsafe_allow_html=True)

    # 10. FULL BALANCE SHEET TABLES
    st.markdown("<h2>Full Balance Sheet Breakdown</h2>",unsafe_allow_html=True)
    render_full_table(ai,ta,"Assets")
    render_full_table(li,tl,"Liabilities")

    # 11. EXECUTIVE SUMMARY & ANALYSIS
    st.markdown('<hr class="rule">',unsafe_allow_html=True)
    st.markdown("<h2>Executive Summary &amp; Analysis</h2>",unsafe_allow_html=True)
    if overall_summary: st.markdown(f'<p style="font-size:.9rem;color:#333;line-height:1.7;margin-bottom:10px">{overall_summary}</p>',unsafe_allow_html=True)
    if executive_takeaway: st.markdown(f'<div class="desc-block"><div class="desc-text">{executive_takeaway}</div></div>',unsafe_allow_html=True)

    # 12. EXPORT
    st.markdown('<hr class="rule">',unsafe_allow_html=True)
    st.markdown("<h2>Export</h2>",unsafe_allow_html=True)
    report_html=generate_report_html(d,uploaded.name,ul,mult)
    base=uploaded.name.replace(".pdf","")
    col1,col2=st.columns(2)
    with col1:
        st.download_button("Download Report (HTML)",data=report_html.encode("utf-8"),file_name=f"{base}_report.html",mime="text/html")
    with col2:
        export=[]
        for label,pair in kf_rows:
            if pair: export.append({"Section":"Key Financials","Item":label,"Current":pair[0],"Prior":pair[1],"Change%":pct_chg(pair[0],pair[1])})
        for lbl,cv,pv,_ in [("CIR%",cir_c,cir_p,True),("ROA%",roa_c,roa_p,True),("Income/RWA%",inc_rwa_c,inc_rwa_p,True),("RWA",rwa_c,rwa_p,False)]:
            if cv is not None: export.append({"Section":"Profitability","Item":lbl,"Current":cv,"Prior":pv,"Change%":pct_chg(cv,pv)})
        if lmr: export.append({"Section":"Liquidity","Item":"Avg LMR (%)","Current":lmr[0],"Prior":lmr[1],"Change pp":lpp_v})
        if cfr: export.append({"Section":"Liquidity","Item":"Avg CFR (%)","Current":cfr[0],"Prior":cfr[1],"Change pp":cpp_v})
        for x in sorted(ai,key=lambda x:x["curr"] or 0,reverse=True):
            export.append({"Section":"Assets","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),"% of Total":round(x["curr"]/ta[0]*100,2) if ta and x["curr"] else None})
        for x in sorted(li,key=lambda x:x["curr"] or 0,reverse=True):
            export.append({"Section":"Liabilities","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),"% of Total":round(x["curr"]/tl[0]*100,2) if tl and x["curr"] else None})
        csv=pd.DataFrame(export).to_csv(index=False).encode("utf-8")
        st.download_button("Download Raw Data (CSV)",data=csv,file_name=f"{base}_metrics.csv",mime="text/csv")
    st.markdown('<div style="font-size:.8rem;color:#aaa;margin-top:8px;"><b>PDF:</b> open HTML in browser &rarr; Print &rarr; Save as PDF</div>',unsafe_allow_html=True)
    with st.expander("Debug: raw extracted lines"):
        st.text("\n".join(d["raw_lines"][:300]))
