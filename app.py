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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body,
[data-testid="stAppViewContainer"],[data-testid="stHeader"],
[data-testid="stToolbar"],[data-testid="stSidebar"],
.main,.block-container,[data-testid="stVerticalBlock"],[class*="css"] {
    font-family:'DM Sans',sans-serif !important;
    background-color:#ffffff !important; color:#111111 !important;
}
.stApp,[data-testid="stAppViewContainer"]{background:#ffffff !important;}
.block-container{max-width:860px !important;padding:2.5rem 2rem 5rem !important;}
p,span,div,li{color:#111111 !important;}
h1{font-family:'DM Sans',sans-serif !important;font-size:.82rem !important;font-weight:700 !important;
   letter-spacing:.18em !important;text-transform:uppercase !important;color:#E60028 !important;
   border-bottom:1.5px solid #E60028 !important;padding-bottom:10px !important;margin-bottom:4px !important;}
h2{font-family:'DM Sans',sans-serif !important;font-size:.75rem !important;font-weight:600 !important;
   letter-spacing:.18em !important;text-transform:uppercase !important;color:#555555 !important;
   border-bottom:1px solid #eeeeee !important;padding-bottom:5px !important;
   margin-top:36px !important;margin-bottom:10px !important;}
h3{font-family:'DM Sans',sans-serif !important;font-size:.72rem !important;font-weight:600 !important;
   letter-spacing:.14em !important;text-transform:uppercase !important;color:#888888 !important;
   margin-top:22px !important;margin-bottom:8px !important;}
.pg-header{display:flex;justify-content:space-between;align-items:flex-end;
           border-bottom:2px solid #111111;padding-bottom:12px;margin-bottom:4px;}
.pg-bank{font-size:1.6rem;font-weight:700;color:#111111 !important;letter-spacing:-.01em;line-height:1.1;}
.pg-meta{font-size:.8rem;color:#999999 !important;text-align:right;line-height:1.7;}
.unit-tag{display:inline-block;font-size:.72rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
          color:#E60028 !important;border:1px solid #E60028;padding:3px 10px;margin:10px 0 20px 0;}
.desc-block{border-left:3px solid #E60028;padding:10px 14px;background:#fafafa !important;margin-bottom:28px;}
.desc-text{font-size:.9rem;color:#444444 !important;line-height:1.65;}
.snapshot{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
          gap:1px;background:#e8e8e8;border:1px solid #e8e8e8;margin-bottom:32px;}
.kpi{background:#ffffff !important;padding:14px 16px;}
.kpi-label{font-size:.7rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#999999 !important;margin-bottom:6px;}
.kpi-val{font-size:1.2rem;font-weight:700;color:#111111 !important;line-height:1;}
.kpi-chg-pos{font-size:.75rem;color:#1a7a3a !important;margin-top:4px;}
.kpi-chg-neg{font-size:.75rem;color:#E60028 !important;margin-top:4px;}
.ratio-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0 28px;}
.ratio-card{border:1px solid #e8e8e8;border-top:2.5px solid #E60028;padding:16px 18px;background:#ffffff !important;}
.ratio-label{font-size:.7rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#aaaaaa !important;margin-bottom:10px;}
.ratio-main{font-size:1.8rem;font-weight:700;color:#111111 !important;line-height:1;}
.ratio-prior{font-size:.85rem;color:#cccccc !important;margin-left:6px;}
.chg-pos{font-size:.78rem;font-weight:600;color:#1a7a3a !important;}
.chg-neg{font-size:.78rem;font-weight:600;color:#E60028 !important;}
table{width:100%;border-collapse:collapse;font-size:.9rem;margin:6px 0 20px;background:#ffffff !important;}
thead tr{border-bottom:2px solid #111111;}
th{font-size:.7rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#999999 !important;
   background:#ffffff !important;padding:0 12px 8px;text-align:right;white-space:nowrap;}
th:first-child{text-align:left;}
td{padding:8px 12px;border-bottom:1px solid #f2f2f2;color:#222222 !important;text-align:right;background:#ffffff !important;}
td:first-child{text-align:left;font-weight:500;color:#111111 !important;}
tr:last-child td{border-bottom:none;}
tr:hover td{background:#fef5f5 !important;}
.pos{color:#1a7a3a !important;font-weight:600;} .neg{color:#E60028 !important;font-weight:600;} .muted{color:#bbbbbb !important;}
.rank{display:inline-block;width:18px;height:18px;line-height:18px;text-align:center;
      font-size:.7rem;font-weight:700;color:#E60028 !important;border:1px solid #E60028;margin-right:8px;vertical-align:middle;}
.rule{border:none;border-top:1px solid #e8e8e8;margin:32px 0 0;}
[data-testid="stFileUploader"]{border:1px dashed #dddddd !important;background:#fafafa !important;padding:6px !important;}
[data-testid="stDownloadButton"]>button{background:#ffffff !important;border:1.5px solid #111111 !important;
    color:#111111 !important;font-family:'DM Sans',sans-serif !important;font-size:.78rem !important;
    font-weight:600 !important;letter-spacing:.1em !important;text-transform:uppercase !important;
    padding:8px 20px !important;border-radius:0 !important;}
[data-testid="stDownloadButton"]>button:hover{background:#E60028 !important;border-color:#E60028 !important;color:#ffffff !important;}
[data-testid="stExpander"]{border:1px solid #eeeeee !important;background:#fafafa !important;}
details summary{color:#cccccc !important;font-size:.78rem !important;}
</style>
""", unsafe_allow_html=True)

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
    r"investment securities":                                          "Investment securities",
    r"other investments":                                              "Other investments",
    r"property.*plant.*equipment|property and equipment":             "Property, plant & equipment",
    r"deposits and balances from central banks|from central banks":    "Deposits from central banks / Monetary Authority",
    r"deposits and balances from banks|deposits from banks":          "Deposits and balances from banks",
    r"balances due to exchange fund|amount due to exchange fund":      "Balances due to Exchange Fund",
    r"demand deposits and current accounts|demand deposits":           "Demand deposits and current accounts",
    r"saving deposits":                                                "Saving deposits",
    r"time.*call.*notice deposits":                                    "Time, call and notice deposits",
    r"amounts? due to overseas offices|amount due to overseas":        "Amount due to overseas offices",
    r"certificates? of deposit issued":                                "Certificates of deposit issued",
    r"issued debt securities":                                         "Issued debt securities",
    r"amount payable under repo":                                      "Amount payable under repo",
    r"other accounts and provisions|other liabilities":                "Other accounts / liabilities",
    r"^provisions$":                                                   "Provisions",
    r"deposits from customers":                                        "Deposits from customers",
    r"amount.*receivable.*reverse.repo|reverse.repo.*receivable":      "Amount receivable under reverse repos",
    r"amount.*payable.*repo|payable.*under.*repo|repo.*payable":       "Amount payable under repo",
    r"loans.*advances.*customers|advances.*to.*customers":             "Loans and advances to customers",
    r"other.*liabilities$|other liabilities":                          "Other accounts / liabilities",
    r"^other accounts":                                                 "Other accounts / liabilities",
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
    s=s.strip().replace(",","").replace("\xa0","").replace(" ","")
    s=re.sub(r"HK\$|US\$|'000|港幣千元","",s).strip()
    if s in ("","—","-","–","Nil","nil","N/A"): return None
    neg=s.startswith("(") and s.endswith(")")
    s=re.sub(r"[()$]","",s)
    try: v=float(s); return -v if neg else v
    except: return None

def trailing_nums(line):
    tokens=re.findall(r"\([\d,]+(?:\.\d+)?\)|[\d,]+(?:\.\d+)?",line)
    return [v for t in tokens for v in [clean_num(t)] if v is not None]

def raw_label(line):
    # Strip markdown table pipes and bold markers
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
    """Return (unit_label, multiplier) for a specific page's lines."""
    for line in page_lines:
        if re.search(r"in millions|millions of hk|million[s]? of hong kong",line,re.IGNORECASE):
            return "HKD millions",1_000_000
        if re.search(r"HK\$\s*'?\s*0{3}",line,re.IGNORECASE): return "HKD thousands",1_000
        if re.search(r"'000",line,re.IGNORECASE): return "HKD thousands",1_000
    return None

def detect_unit(lines):
    # Check first 150 lines for unit declaration
    r = detect_unit_per_page(lines[:150])
    if r: return r
    for line in lines:
        if re.search(r"HK\$\s*'?\s*0{3}|'000",line,re.IGNORECASE): return "HKD thousands",1_000
    for line in lines:
        if re.search(r"in millions|millions of hk",line,re.IGNORECASE): return "HKD millions",1_000_000
    return "HKD thousands",1_000

def fmt_n(v): return "—" if v is None else f"{abs(v):,.0f}"
def pct_chg(c,p): return None if (c is None or p is None or p==0) else round((c-p)/abs(p)*100,2)
def fmt_chg(v):
    if v is None: return '<span class="muted">—</span>'
    return f'<span class="{"pos" if v>0 else "neg"}">{"+" if v>0 else ""}{v:.2f}%</span>'
def pp_html(v):
    if v is None: return '<span class="muted">—</span>'
    return f'<span class="{"chg-pos" if v>0 else "chg-neg"}">{"+" if v>0 else ""}{v:.2f}pp</span>'
def fmt_snapshot(v,multiplier):
    if v is None: return "—"
    hkd=abs(v)*multiplier
    if hkd>=1e12: return f"{hkd/1e12:.2f}T"
    if hkd>=1e9:  return f"{hkd/1e9:.1f}B"
    if hkd>=1e6:  return f"{hkd/1e6:.0f}M"
    return f"{hkd:,.0f}"
def is_noise(line):
    s=line.strip()
    if not s or len(s)<4: return True
    if re.match(r"^[^a-zA-Z0-9\-\(]",s): return True
    if re.match(r"^[A-Z]\d+\s*$",s): return True
    return False

# ── FIX: strip markdown/pipe chars before section matching ──
def clean_for_match(line):
    s = re.sub(r"\|","",line)
    s = re.sub(r"\*{1,2}","",s)
    s = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+"," ",s)
    return re.sub(r"\s+"," ",s).strip()

def extract_pages(pdf_bytes):
    pages=[]
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i,page in enumerate(pdf.pages):
            text=page.extract_text() or ""
            lines=[l.strip() for l in text.splitlines() if l.strip()]
            rows=[]
            for tbl in (page.extract_tables() or []):
                for row in tbl:
                    rows.append([c.strip() if isinstance(c,str) else (c or "") for c in row])
            pages.append((i,lines,rows))
    return pages

def ocr_all(pdf_bytes):
    if not OCR_AVAILABLE: return []
    imgs=convert_from_bytes(pdf_bytes,dpi=200)
    out=[]
    for img in imgs:
        t=pytesseract.image_to_string(img)
        out+=[l.strip() for l in t.splitlines() if l.strip()]
    return out

HARD_SKIP=re.compile(
    r"^total\s+(assets|liabilities)|^assets\s*$|^liabilities\s*$|^equity\s+and\s+liabilities\s*$|"
    r"^less:\s*impairment|^impairment\s+allowances\s+for|^provision\s+for\s+impaired|"
    r"^balance\s+sheet|^section\s+[a-z]|^\d+\s*$|^page\s|^reserves?\s*$|^[-_=\s]+$|"
    r"^note\s+附|^figures\s+in|^unaudited|^i{1,3}\.?\s+unaudited|^international\s+claims|"
    r"^non-bank\s+mainland|^currency\s+risk|^remuneration|^group\s+consolidated|"
    r"^declaration\s+of\s+compliance",
    re.IGNORECASE)
INCOME_SKIP=re.compile(
    r"profit\s+before\s+tax|profit\s+after\s+tax|net\s+profit\s*$|interest\s+income|interest\s+expense|"
    r"operating\s+income|operating\s+expense|taxation\s+charge|tax\s+expense|"
    r"reversal\s+of\s+impairment|net\s+write\s+(back|charge)|net\s+fees|net\s+interest|"
    r"gains\s+less\s+losses|total\s+operating",re.IGNORECASE)
DED_SKIP=re.compile(r"^\s*[-–]\s+(collective|specific)\b",re.IGNORECASE)
# Skip Natixis page-header lines that appear on every page
HEADER_SKIP=re.compile(r"^natixis\s*$|^corporate\s+and\s+investment\s+banking\s*$|^groupe\s+bpce\s*$|^kpmg",re.IGNORECASE)

def parse_bs(lines, section="assets"):
    """
    Parse balance sheet items. Handles both plain-text and table-extracted (pipe-delimited) formats.
    Units are assumed to be whatever detect_unit() found for the balance sheet pages.
    """
    items = []
    in_sec = False
    if section == "assets":
        s_pat = re.compile(r"^\**assets\**\s*$|^\**assets\**\s+as\s+at", re.IGNORECASE)
        e_pat = re.compile(r"total\s+assets|總資產", re.IGNORECASE)
    else:
        s_pat = re.compile(r"^\**liabilities\**\s*$|equity\s+and\s+liabilities", re.IGNORECASE)
        e_pat = re.compile(r"total\s+liabilities|總負債", re.IGNORECASE)

    for line in lines:
        s = line.strip()
        if not s: continue
        cm = clean_for_match(s)
        if s_pat.match(cm): in_sec = True; continue
        if not in_sec: continue
        if e_pat.search(cm): in_sec = False; continue
        if HARD_SKIP.search(cm) or INCOME_SKIP.search(cm) or DED_SKIP.match(cm): continue
        if HEADER_SKIP.match(cm): continue
        if is_noise(cm): continue
        # Skip wrapped-line tails (UBS wraps long labels — tail starts lowercase or with ")")
        if re.match(r'^[a-z]', s) or s.startswith(')'): continue

        nums = trailing_nums(s)
        if not nums: continue
        curr = nums[-2] if len(nums) >= 2 else nums[-1]
        prior = nums[-1] if len(nums) >= 2 else None
        if curr == 0 and (prior is None or prior == 0): continue
        rl = raw_label(s); label = canonicalize(rl)
        if not label or len(label) < 2: continue
        if re.match(r"^[\d,.()\-\s]+$", label): continue
        # Deduplicate
        if any(x["label"] == label for x in items): continue
        items.append({"label": label, "curr": abs(curr), "prior": abs(prior) if prior is not None else None})
    return items

def find_two(lines, pattern):
    for i,line in enumerate(lines):
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
        ll = line.lower()
        if re.search(r"collective\s+(impairment|provision)|[-–]\s*collective\b|綜合減值", ll):
            nums = trailing_nums(line)
            if nums and coll is None:
                coll = (abs(nums[-2] if len(nums)>=2 else nums[-1]), abs(nums[-1]) if len(nums)>=2 else None)
        if re.search(r"specific\s+(impairment|provision)|individual\s+impairment|[-–]\s*specific\b|特殊性撥備", ll):
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
    """
    Extract the bank name from the cover page.
    Strategy 1: find a line containing 'Hong Kong Branch' — this is always the entity name.
    Strategy 2: scan the first 60 lines, skip known non-name headers, return first substantive name.
    Never falls back to the filename.
    """
    NON_NAME = re.compile(
        r"^(natixis\s+corporate|corporate\s+and\s+investment|groupe\s+bpce|kpmg|"
        r"financial\s+information\s+disclosure|financial\s+statements|"
        r"incorporated\s+in|unaudited|figures\s+in|for\s+identification|"
        r"investment\s+banking|and\s+investment)",
        re.IGNORECASE)

    # Pass 1: explicit "Hong Kong Branch" line — most reliable signal
    for line in lines[:60]:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", "", line).strip()
        clean = re.sub(r"\(.*?\)", "", clean).strip()   # drop legal brackets
        clean = re.sub(r"\s+", " ", clean).strip()
        if re.search(r"hong\s+kong\s+branch", clean, re.IGNORECASE):
            # Must have at least one word before "Hong Kong Branch"
            before = re.sub(r"hong\s+kong\s+branch.*$", "", clean, flags=re.IGNORECASE).strip()
            if len(before.split()) >= 1:
                return clean[:100]

    # Pass 2: first substantive capitalized line on the cover
    for line in lines[:20]:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", "", line).strip()
        clean = re.sub(r"\(.*?\)", "", clean).strip()
        clean = re.sub(r"\s+", " ", clean).strip()
        if not clean or len(clean) < 4: continue
        if re.match(r"^[\d\s\-/]+$", clean): continue
        if NON_NAME.match(clean): continue
        # Must look like a proper name (has letters, not all lowercase prose)
        if len(clean.split()) >= 1 and clean[0].isupper():
            return clean[:100]
    return "Unknown Bank"

def get_branch_description(lines):
    """Extract 'Branch activities' or compliance-declaration paragraph."""
    in_para = False; para_lines = []
    section_headers = re.compile(
        r"^(additional\s+profit|profit\s+and\s+loss|balance\s+sheet|off-balance|"
        r"supplementary|section\s+[a-z]|contents|for\s+the\s+(year|half)|remuneration|"
        r"liquidity|currency\s+risk|international\s+claims|mainland|group\s+consolidated)",
        re.IGNORECASE)
    for line in lines:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", "", line).strip()
        clean = re.sub(r"[^a-zA-Z0-9\s,&\.\-/()\!:@'\"]+" , " ", clean).strip()
        clean = re.sub(r"\s+", " ", clean).strip()
        if re.search(r"branch activities|branch information", clean, re.IGNORECASE):
            in_para = True; continue
        if in_para:
            if not clean or len(clean) < 5: continue
            if section_headers.match(clean) or re.match(r"^[-_=]+$", clean): break
            if re.match(r"^[\d\s]+$", clean): continue
            para_lines.append(clean)
            if len(" ".join(para_lines)) > 350: break
    desc = " ".join(para_lines)
    # Fallback: use compliance declaration paragraph for entity description
    if not desc:
        for i, line in enumerate(lines):
            clean = re.sub(r"[\u4e00-\u9fff]+", "", line).strip()
            if re.search(r"we have pleasure in presenting|incorporated in|registered under|a branch of", clean, re.IGNORECASE) and len(clean.split()) > 8:
                desc = clean; break
    if len(desc) > 350: desc = desc[:350].rsplit(" ", 1)[0] + "…"
    return desc

def get_period(lines):
    for line in lines:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", "", line).strip()
        if re.search(r"(year|period|half.year)\s+ended|for the year|as at|as of", clean, re.IGNORECASE):
            if re.search(r"\d{4}", clean):
                return re.sub(r"\s+", " ", clean).strip()[:80]
    return ""

def run(pdf_bytes):
    pages = extract_pages(pdf_bytes)
    all_lines = []
    for _, lines, _ in pages: all_lines += lines

    # Detect unit from balance sheet pages (pages 1-5 typically) — avoid mixed-unit later pages
    bs_lines = []
    for _, lines, _ in pages[:6]: bs_lines += lines
    ul, mult = detect_unit(bs_lines)

    ta     = find_two(all_lines, r"total\s+assets|總資產")
    tl     = find_two(all_lines, r"total\s+liabilities|總負債")
    profit = find_two(all_lines, r"profit\s+after\s+tax(?:ation)?|net\s+profit\s*$|除稅後溢利")
    prov   = get_provisions(all_lines)
    lmr, cfr = get_lmr_cfr(all_lines, pdf_bytes)
    ai = parse_bs(all_lines, "assets")
    li = parse_bs(all_lines, "liabilities")
    entity  = get_entity_name(all_lines)
    desc    = get_branch_description(all_lines)
    period  = get_period(all_lines)
    return {"unit_label": ul, "multiplier": mult, "ta": ta, "tl": tl, "profit": profit,
            "spec": prov["spec"], "coll": prov["coll"], "lmr": lmr, "cfr": cfr,
            "asset_items": ai, "liab_items": li, "entity": entity, "desc": desc,
            "period": period, "raw_lines": all_lines}

def dir_word(c,p):
    if c is None or p is None: return "changed"
    return "increased" if c>p else "decreased" if c<p else "remained flat"
def conc_word(c,p):
    if c is None or p is None: return "changed"
    d=c-p
    if abs(d)<0.5: return "remained broadly stable"
    return f"{'increased' if d>0 else 'decreased'} by {abs(d):.2f}pp"

def generate_report_html(d,filename,ul,mult):
    entity=d["entity"] or filename; period=d["period"] or ""; desc=d["desc"] or ""
    ta,tl=d["ta"],d["tl"]; prof=d["profit"]; spec,coll=d["spec"],d["coll"]
    lmr,cfr=d["lmr"],d["cfr"]; ai,li=d["asset_items"],d["liab_items"]
    tc_c=ta[0] if ta else None; tc_p=ta[1] if ta else None
    tl_c=tl[0] if tl else None; tl_p=tl[1] if tl else None
    tot_prov=None
    if spec and coll:
        c2=(spec[1]+coll[1]) if spec[1] and coll[1] else None
        tot_prov=(spec[0]+coll[0],c2)
    elif coll: tot_prov=coll
    elif spec: tot_prov=spec
    ai_s=sorted([x for x in ai if x["curr"]],key=lambda x:x["curr"],reverse=True)
    li_s=sorted([x for x in li if x["curr"]],key=lambda x:x["curr"],reverse=True)
    ai3=ai_s[:3]; li3=li_s[:3]
    ai_p=sorted([x for x in ai if x.get("prior")],key=lambda x:x["prior"],reverse=True)[:3]
    li_p=sorted([x for x in li if x.get("prior")],key=lambda x:x["prior"],reverse=True)[:3]

    def bullets(items,total_c,total_p,is_prior=False,is_liab=False):
        if not items: return "<p style='color:#bbb;font-size:.78rem'>No data extracted.</p>"
        s="liabilities" if is_liab else "assets"; html=""
        for x in items:
            val=x.get("prior") if is_prior else x["curr"]
            tot=total_p if is_prior else total_c
            pct=round(val/tot*100,2) if val and tot else None
            html+=f"""<div class="bullet"><span class="arrow">↠</span>
              <span class="bullet-name">{x['label']}</span>
              <span class="bullet-pct">{"n/a" if pct is None else f"{pct:.2f}%"} of total {s}</span>
              <span class="bullet-unit">({ul}: {fmt_n(val)})</span></div>"""
        return html

    sn=entity.split()[0] if entity else "The branch"
    lmr_pp=round(lmr[0]-lmr[1],2) if lmr else None
    cfr_pp=round(cfr[0]-cfr[1],2) if cfr else None
    lmr_text=(f"The LMR {dir_word(lmr[0],lmr[1])} from {lmr[1]:.2f}% to {lmr[0]:.2f}%, a change of "
              f"{'+'if lmr_pp and lmr_pp>0 else ''}{lmr_pp:.2f}pp. {sn} holds sufficient liquid assets "
              f"to cover approximately {lmr[0]:.0f}% of its liabilities maturing within one month. "
              f"The LMR remains well above the regulatory minimum of 25%.") if lmr else "LMR data not found."
    cfr_text=(f"The CFR {dir_word(cfr[0],cfr[1])} from {cfr[1]:.2f}% to {cfr[0]:.2f}%, a change of "
              f"{'+'if cfr_pp and cfr_pp>0 else ''}{cfr_pp:.2f}pp. "
              f"Stable funding sources adequately cover required stable funding needs. "
              f"The CFR remains well above the regulatory minimum of 75%.") if cfr else "CFR not disclosed by this institution."
    liq_min=round(min(lmr[0],cfr[0]),0) if lmr and cfr else (lmr[0] if lmr else None)
    liq_s=(f"In terms of liquidity, {sn} is above regulatory requirements. "
           f"The LMR stands at {liq_min:.0f}%, demonstrating a strong liquidity buffer.") if liq_min else ""

    def kfr(label,pair):
        if not pair: return f'<tr><td>{label}</td><td class="num muted">—</td><td class="num muted">—</td><td class="num muted">—</td></tr>'
        c,p=pair[0],pair[1]; ch=pct_chg(c,p)
        chs=(f"{'+'if ch and ch>0 else ''}{ch:.2f}%") if ch is not None else "—"
        css="pos" if ch and ch>0 else ("neg" if ch and ch<0 else "")
        return f'<tr><td>{label}</td><td class="num">{fmt_n(c)}</td><td class="num">{fmt_n(p)}</td><td class="num {css}">{chs}</td></tr>'

    a_same=set(x["label"] for x in ai3)==set(x["label"] for x in ai_p)
    a_cc=sum(x["curr"] for x in ai3 if x["curr"]); a_cp=sum(x.get("prior",0) or 0 for x in ai3)
    a_pc=round(a_cc/tc_c*100,2) if tc_c else None; a_pp=round(a_cp/tc_p*100,2) if tc_p else None
    a_tp=round(ai3[0]["curr"]/tc_c*100,2) if ai3 and tc_c else None
    a_com=(f"The top 3 biggest assets {'remain the same' if a_same else 'differ'} between the two periods. "
           f"Combined concentration {conc_word(a_pc,a_pp)}, from {a_pp:.2f}% to {a_pc:.2f}% of total assets. "
           f"The largest asset, {ai3[0]['label'] if ai3 else 'n/a'}, represents {a_tp:.2f}% of total assets.") if ai3 and tc_c and tc_p else ""
    a_take=(f"Key takeaway: {ai3[0]['label'] if ai3 else 'Primary asset'} dominates at {a_tp:.2f}% of total assets. "
            f"{'High concentration in top 3.' if a_pc and a_pc>80 else 'Moderate asset diversification.'}") if a_tp else ""

    l_same=set(x["label"] for x in li3)==set(x["label"] for x in li_p)
    l_cc=sum(x["curr"] for x in li3 if x["curr"]); l_cp=sum(x.get("prior",0) or 0 for x in li3)
    l_pc=round(l_cc/tl_c*100,2) if tl_c else None; l_pp=round(l_cp/tl_p*100,2) if tl_p else None
    l_tp=round(li3[0]["curr"]/tl_c*100,2) if li3 and tl_c else None
    l_mv=[]
    for x in li3:
        if x["curr"] and x.get("prior") and tl_c and tl_p:
            d=round(x["curr"]/tl_c*100-x["prior"]/tl_p*100,2)
            l_mv.append((x["label"],d,x["curr"]-x["prior"]))
    l_mv.sort(key=lambda x:abs(x[1]),reverse=True)
    bm=l_mv[0] if l_mv else None
    l_com=(f"The top 3 biggest liabilities {'remain the same' if l_same else 'changed'} from the prior period. "
           f"Combined concentration {conc_word(l_pc,l_pp)}, from {l_pp:.2f}% to {l_pc:.2f}% of total liabilities."
           +(f" Most notable shift: {bm[0]}, {'increased' if bm[1]>0 else 'decreased'} by {abs(bm[1]):.2f}pp "
             f"({fmt_n(abs(bm[2]))} {ul})." if bm else "")) if li3 and tl_c and tl_p else ""
    l_take=(f"Key takeaway: {li3[0]['label'] if li3 else 'Primary liability'} is dominant at {l_tp:.2f}% of total liabilities. "
            f"{'High liability concentration in top 3.' if l_pc and l_pc>70 else 'Reasonably diversified funding.'}") if l_tp else ""

    pc=pct_chg(prof[0],prof[1]) if prof else None
    summary=(f"{entity} reported profit after taxation of {fmt_n(prof[0])} {ul} for the period, "
             f"{'up' if pc and pc>0 else 'down'} {abs(pc):.2f}% versus the prior period. "
             f"Total assets {'grew' if ta and ta[0]>ta[1] else 'contracted'} to {fmt_n(ta[0])} {ul}. "
             f"Liquidity ratios remain comfortably above regulatory minimums.") if prof and ta else ""
    overall=(f"{'Strong' if pc and pc>0 else 'Resilient'} performance with robust liquidity buffers. "
             f"Monitor concentration in {ai3[0]['label'] if ai3 else 'primary asset'} as the dominant balance sheet item.") if ai3 else ""
    today=datetime.date.today().strftime("%d %B %Y")

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>{entity} — HKMA Disclosure Report</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'DM Sans',sans-serif;background:#fff;color:#111;font-size:10pt;line-height:1.6;max-width:780px;margin:0 auto;padding:40px 48px;}}
@media print{{body{{padding:20px 28px;}}@page{{margin:20mm;}}}}
.doc-header{{border-bottom:2px solid #111;padding-bottom:14px;margin-bottom:8px;}}
.doc-bank{{font-size:1.5rem;font-weight:700;letter-spacing:-.01em;line-height:1.1;margin-bottom:3px;}}
.doc-sub{{font-size:.72rem;color:#999;}} .doc-meta{{font-size:.68rem;color:#bbb;margin-top:4px;}}
.unit-tag{{display:inline-block;font-size:.6rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
           color:#E60028;border:1px solid #E60028;padding:1px 7px;margin:8px 0 18px;}}
.desc{{border-left:3px solid #E60028;padding:8px 14px;background:#fafafa;margin-bottom:24px;font-size:.8rem;color:#444;line-height:1.7;}}
h2{{font-size:.62rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#555;border-bottom:1px solid #eee;padding-bottom:4px;margin-top:32px;margin-bottom:12px;}}
.narrative{{font-size:.82rem;color:#333;line-height:1.7;margin-bottom:8px;}}
.takeaway{{font-size:.78rem;color:#555;font-style:italic;border-left:2px solid #E60028;padding-left:10px;margin:10px 0 16px;}}
table{{width:100%;border-collapse:collapse;font-size:.78rem;margin:8px 0 18px;}}
thead tr{{border-bottom:2px solid #111;}}
th{{font-size:.58rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#999;padding:0 10px 7px;text-align:right;}}
th:first-child{{text-align:left;}}
td{{padding:7px 10px;border-bottom:1px solid #f0f0f0;color:#222;text-align:right;}}
td:first-child{{text-align:left;font-weight:500;color:#111;}}
tr:last-child td{{border-bottom:none;}}
.num{{font-variant-numeric:tabular-nums;}} .pos{{color:#1a7a3a;font-weight:600;}} .neg{{color:#E60028;font-weight:600;}} .muted{{color:#bbb;}}
.period-label{{font-size:.6rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#aaa;margin:14px 0 6px;}}
.bullet{{display:flex;align-items:baseline;gap:8px;padding:5px 0;border-bottom:1px solid #f5f5f5;font-size:.8rem;}}
.bullet:last-child{{border-bottom:none;}}
.arrow{{color:#E60028;font-weight:700;min-width:14px;}} .bullet-name{{font-weight:600;color:#111;flex:1;}}
.bullet-pct{{font-weight:700;color:#111;min-width:90px;text-align:right;}} .bullet-unit{{color:#bbb;font-size:.72rem;min-width:140px;text-align:right;}}
.doc-footer{{margin-top:48px;padding-top:12px;border-top:1px solid #eee;font-size:.62rem;color:#bbb;display:flex;justify-content:space-between;}}
.red{{color:#E60028;}} hr{{border:none;border-top:1px solid #eee;margin:28px 0 0;}}
</style></head><body>
<div class="doc-header">
  <div class="doc-bank">{entity}</div>
  <div class="doc-sub">HKMA Key Financial Information Disclosure Statement</div>
  <div class="doc-meta">{period} &nbsp;·&nbsp; Generated {today}</div>
</div>
<div class="unit-tag">Reported in {ul} &nbsp;·&nbsp; Snapshot figures in HKD billions</div>
{"<div class='desc'>" + desc + "</div>" if desc else ""}
<h2>Liquidity Ratios</h2>
<p class="narrative"><strong>3-Month LMR:</strong> <span style="color:#E60028">{f"{lmr[0]:.2f}%" if lmr else "—"}</span> (current) &nbsp;/&nbsp; {f"{lmr[1]:.2f}%" if lmr else "—"} (prior)</p>
<p class="narrative">{lmr_text}</p>
<p class="narrative" style="margin-top:12px"><strong>3-Month CFR:</strong> <span style="color:#E60028">{f"{cfr[0]:.2f}%" if cfr else "—"}</span> (current) &nbsp;/&nbsp; {f"{cfr[1]:.2f}%" if cfr else "—"} (prior)</p>
<p class="narrative">{cfr_text}</p>
{"<p class='narrative' style='margin-top:12px'>" + liq_s + "</p>" if liq_s else ""}
<h2>Key Financials</h2>
<table><thead><tr><th>Item</th><th>Current ({ul})</th><th>Prior ({ul})</th><th>Change</th></tr></thead>
<tbody>
{kfr("Profit after taxation",prof)}{kfr("Total assets",ta)}{kfr("Total liabilities",tl)}
{kfr("Specific / Individual provisions",spec)}{kfr("Collective provisions",coll)}{kfr("Total provisions",tot_prov)}
</tbody></table>
<h2>Asset Concentration</h2>
<div class="period-label">Current period — top 3 assets</div>{bullets(ai3,tc_c,tc_p,is_prior=False,is_liab=False)}
<div class="period-label" style="margin-top:14px">Prior period — top 3 assets</div>{bullets(ai_p or ai3,tc_c,tc_p,is_prior=True,is_liab=False)}
<p class="narrative" style="margin-top:12px">{a_com}</p><p class="takeaway">{a_take}</p>
<h2>Liability Concentration</h2>
<div class="period-label">Current period — top 3 liabilities</div>{bullets(li3,tl_c,tl_p,is_prior=False,is_liab=True)}
<div class="period-label" style="margin-top:14px">Prior period — top 3 liabilities</div>{bullets(li_p or li3,tl_c,tl_p,is_prior=True,is_liab=True)}
<p class="narrative" style="margin-top:12px">{l_com}</p><p class="takeaway">{l_take}</p>
<hr><h2>Summary</h2>
<p class="narrative">{summary}</p><p class="takeaway">{overall}</p>
<div class="doc-footer">
  <span>Source: HKMA Key Financial Information Disclosure Statement</span>
  <span>Generated by <span class="red">HKMA Disclosure Reader</span> · {today}</span>
</div></body></html>"""

st.markdown("<h1>HKMA Financial Disclosure Reader</h1>",unsafe_allow_html=True)
uploaded=st.file_uploader("Upload HKMA Key Financial Information Disclosure PDF",type="pdf")

if not uploaded:
    st.markdown("""
    <div style="margin-top:40px;padding:40px;border:1px dashed #ddd;text-align:center;background:#fafafa">
      <div style="font-size:.82rem;letter-spacing:.1em;text-transform:uppercase;color:#ccc;margin-bottom:6px;">Drop a disclosure PDF to begin</div>
      <div style="font-size:.82rem;color:#ddd;">Supports JPMorgan, CA-CIB, Société Générale, Natixis, BNP Paribas, and other HKMA-format disclosures</div>
    </div>""",unsafe_allow_html=True)

if uploaded:
    pdf_bytes=uploaded.read()
    with st.spinner("Extracting and generating report…"):
        d=run(pdf_bytes)
    ul=d["unit_label"]; mult=d["multiplier"]
    ta,tl=d["ta"],d["tl"]; spec,coll=d["spec"],d["coll"]
    lmr,cfr=d["lmr"],d["cfr"]; prof=d["profit"]
    ai,li=d["asset_items"],d["liab_items"]
    entity=d["entity"] or uploaded.name.replace(".pdf","").replace("_"," ").upper()
    desc=d["desc"] or ""; period=d["period"] or ""
    tot_prov=None
    if spec and coll:
        c2=(spec[1]+coll[1]) if spec[1] and coll[1] else None; tot_prov=(spec[0]+coll[0],c2)
    elif coll: tot_prov=coll
    elif spec: tot_prov=spec

    st.markdown(f"""
    <div class="pg-header">
      <div class="pg-bank">{entity}</div>
      <div class="pg-meta">HKMA Key Financial Disclosure<br><span>{period}</span></div>
    </div>
    <div class="unit-tag">Reported in {ul} &nbsp;·&nbsp; Snapshot figures in HKD billions</div>
    """,unsafe_allow_html=True)
    if desc:
        st.markdown(f'<div class="desc-block"><div class="desc-text">{desc}</div></div>',unsafe_allow_html=True)

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

    kpis="".join(filter(None,[kpi_block("Total Assets",ta[0] if ta else None,ta[1] if ta else None),
        kpi_block("Profit after Tax",prof[0] if prof else None,prof[1] if prof else None),
        kpi_block("Avg LMR",lmr[0] if lmr else None,lmr[1] if lmr else None,True),
        kpi_block("Avg CFR",cfr[0] if cfr else None,cfr[1] if cfr else None,True),
        kpi_block("Total Provisions",tot_prov[0] if tot_prov else None,tot_prov[1] if tot_prov else None)]))
    if kpis: st.markdown(f'<div class="snapshot">{kpis}</div>',unsafe_allow_html=True)

    lpp=round(lmr[0]-lmr[1],2) if lmr else None; cpp=round(cfr[0]-cfr[1],2) if cfr else None
    st.markdown("<h2>Liquidity</h2>",unsafe_allow_html=True)
    st.markdown(f"""<div class="ratio-grid">
      <div class="ratio-card"><div class="ratio-label">3-Month Average LMR</div>
        <div><span class="ratio-main">{f"{lmr[0]:.2f}%" if lmr else "—"}</span>
        <span class="ratio-prior">{f"prev {lmr[1]:.2f}%" if lmr else ""}</span></div>
        <div style="margin-top:6px">{pp_html(lpp)}</div></div>
      <div class="ratio-card"><div class="ratio-label">3-Month Average CFR</div>
        <div><span class="ratio-main">{f"{cfr[0]:.2f}%" if cfr else "—"}</span>
        <span class="ratio-prior">{f"prev {cfr[1]:.2f}%" if cfr else ""}</span></div>
        <div style="margin-top:6px">{pp_html(cpp)}</div></div></div>""",unsafe_allow_html=True)

    st.markdown("<h2>Key Financials</h2>",unsafe_allow_html=True)
    kf_rows=[("Profit after taxation",prof),("Total assets",ta),("Total liabilities",tl),
             ("Specific / Individual provisions",spec),("Collective provisions",coll),("Total provisions",tot_prov)]
    rows_html=""
    for label,pair in kf_rows:
        if pair:
            c,p=pair[0],pair[1]
            rows_html+=f"<tr><td>{label}</td><td>{fmt_n(c)}</td><td>{fmt_n(p)}</td><td>{fmt_chg(pct_chg(c,p))}</td></tr>"
        else:
            rows_html+=f'<tr><td class="muted">{label}</td><td class="muted">—</td><td class="muted">—</td><td class="muted">—</td></tr>'
    st.markdown(f"""<table><thead><tr><th>Metric</th><th>Current ({ul})</th><th>Prior ({ul})</th><th>Change</th></tr></thead>
      <tbody>{rows_html}</tbody></table>""",unsafe_allow_html=True)


    # ── 100% Stacked Bar Charts ──
    st.markdown("<h2>Balance Sheet Composition</h2>", unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:.88rem;color:#888;margin-bottom:16px;">'
        "100% stacked composition — current vs prior period. "
        "Each band shows one item's share of total assets or liabilities."
        '</p>',
        unsafe_allow_html=True
    )

    def render_stacked_bars(items, total_pair, section_title):
        tc = total_pair[0] if total_pair else None
        tp = total_pair[1] if total_pair else None
        valid = sorted([x for x in items if x["curr"] and x["curr"] > 0],
                       key=lambda x: x["curr"], reverse=True)
        if not valid or not tc:
            st.markdown(
                f'<p style="font-size:.88rem;color:#bbb">No {section_title.lower()} data.</p>',
                unsafe_allow_html=True
            )
            return

        palette = [
            "#E60028","#111111","#555555","#888888","#AAAAAA",
            "#CCCCCC","#DDDDDD","#B00020","#333333","#777777",
            "#999999","#BBBBBB"
        ]

        labels_curr = [x["label"] for x in valid]
        vals_curr   = [round(x["curr"] / tc * 100, 2) for x in valid]

        has_prior = tp and any(x.get("prior") for x in valid)
        if has_prior:
            labels_prior = [x["label"] for x in valid]
            vals_prior   = [round((x.get("prior") or 0) / tp * 100, 2) for x in valid]
            periods = ["Current", "Prior"]
        else:
            periods = ["Current"]

        fig = go.Figure()
        for i, lbl in enumerate(labels_curr):
            color = palette[i % len(palette)]
            y_curr = vals_curr[i]
            y_prior = vals_prior[i] if has_prior else None
            y_vals = [y_curr]
            if has_prior:
                y_vals = [y_curr, y_prior]
            fig.add_trace(go.Bar(
                name=lbl,
                x=periods,
                y=y_vals,
                marker_color=color,
                hovertemplate=f"<b>{lbl}</b><br>%{{y:.2f}}%<extra></extra>",
                text=[f"{v:.1f}%" if v >= 4 else "" for v in y_vals],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=9, color="#ffffff", family="DM Sans, sans-serif"),
            ))

        fig.update_layout(
            barmode="stack",
            title=dict(
                text=section_title.upper(),
                font=dict(size=9, color="#888888", family="DM Sans, sans-serif"),
                x=0, xanchor="left", pad=dict(b=4)
            ),
            height=400,
            margin=dict(l=0, r=0, t=28, b=0),
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            yaxis=dict(
                range=[0, 100],
                ticksuffix="%",
                tickfont=dict(size=8, color="#999999", family="DM Sans, sans-serif"),
                showgrid=True,
                gridcolor="#f0f0f0",
                gridwidth=0.5,
                zeroline=False,
            ),
            xaxis=dict(
                tickfont=dict(size=9, color="#111111", family="DM Sans, sans-serif"),
                showgrid=False,
            ),
            legend=dict(
                orientation="h",
                x=0, y=-0.18,
                font=dict(size=8, color="#444444", family="DM Sans, sans-serif"),
                bgcolor="rgba(0,0,0,0)",
                traceorder="normal",
                itemwidth=30,
            ),
            showlegend=True,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    col_a, col_l = st.columns(2)
    with col_a:
        render_stacked_bars(ai, ta, "Asset Composition")
    with col_l:
        render_stacked_bars(li, tl, "Liability Composition")

    def render_top3(items,total_pair,title):
        tc=total_pair[0] if total_pair else None; tp=total_pair[1] if total_pair else None
        valid=sorted([x for x in items if x["curr"] and x["curr"]>0],key=lambda x:x["curr"],reverse=True)[:3]
        st.markdown(f"<h2>{title} — Top 3</h2>",unsafe_allow_html=True)
        if not valid or not tc:
            st.markdown('<p style="font-size:.88rem;color:#bbb">No items extracted.</p>',unsafe_allow_html=True); return
        rows_h="".join(f"""<tr><td><span class="rank">{i}</span>{x['label']}</td>
          <td><b>{round(x['curr']/tc*100,2):.2f}%</b></td><td class="muted">{fmt_n(x['curr'])}</td>
          <td>{"<span class='muted'>—</span>" if not(tp and x.get('prior')) else f"{round(x['prior']/tp*100,2):.2f}%"}</td>
          <td class="muted">{fmt_n(x.get('prior'))}</td></tr>""" for i,x in enumerate(valid,1))
        st.markdown(f"""<table><thead><tr><th style="text-align:left">Item</th>
          <th>Curr %</th><th>Current ({ul})</th><th>Prior %</th><th>Prior ({ul})</th></tr></thead>
          <tbody>{rows_h}</tbody></table>""",unsafe_allow_html=True)

    render_top3(ai,ta,"Asset Concentration")
    render_top3(li,tl,"Liability Concentration")

    st.markdown('<hr class="rule">',unsafe_allow_html=True)
    st.markdown("<h2>Full Balance Sheet Breakdown</h2>",unsafe_allow_html=True)

    def render_full(items,total_pair,title):
        tc=total_pair[0] if total_pair else None; tp=total_pair[1] if total_pair else None
        valid=sorted([x for x in items if x["curr"] is not None],key=lambda x:x["curr"],reverse=True)
        st.markdown(f"<h3>{title}</h3>",unsafe_allow_html=True)
        if not valid or not tc:
            st.markdown('<p style="font-size:.75rem;color:#bbb">No items extracted.</p>',unsafe_allow_html=True); return
        rows_h="".join(f"""<tr><td>{x['label']}</td><td>{fmt_n(x['curr'])}</td>
          <td>{"<span class='muted'>—</span>" if not tc or not x['curr'] else f"<b>{round(x['curr']/tc*100,2):.2f}%</b>"}</td>
          <td class="muted">{fmt_n(x.get('prior'))}</td>
          <td>{"<span class='muted'>—</span>" if not tp or not x.get('prior') else f"{round(x['prior']/tp*100,2):.2f}%"}</td></tr>""" for x in valid)
        st.markdown(f"""<table><thead><tr><th style="text-align:left">Item</th>
          <th>Current ({ul})</th><th>% of Total</th><th>Prior ({ul})</th><th>% (Prior)</th></tr></thead>
          <tbody>{rows_h}</tbody></table>""",unsafe_allow_html=True)

    render_full(ai,ta,"Assets")
    render_full(li,tl,"Liabilities")

    st.markdown('<hr class="rule">',unsafe_allow_html=True)
    st.markdown("<h2>Export</h2>",unsafe_allow_html=True)
    report_html=generate_report_html(d,uploaded.name,ul,mult)
    base=uploaded.name.replace(".pdf","")
    col1,col2=st.columns(2)
    with col1:
        st.download_button("↓  Download Report (HTML)",data=report_html.encode("utf-8"),
                           file_name=f"{base}_report.html",mime="text/html")
    with col2:
        export=[]
        for label,pair in kf_rows:
            if pair: export.append({"Section":"Key Financials","Item":label,"Current":pair[0],"Prior":pair[1],"Change%":pct_chg(pair[0],pair[1])})
        if lmr: export.append({"Section":"Liquidity","Item":"Avg LMR (%)","Current":lmr[0],"Prior":lmr[1],"Change pp":lpp})
        if cfr:  export.append({"Section":"Liquidity","Item":"Avg CFR (%)","Current":cfr[0],"Prior":cfr[1],"Change pp":cpp})
        for x in sorted(ai,key=lambda x:x["curr"] or 0,reverse=True):
            export.append({"Section":"Assets","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),"% of Total":round(x["curr"]/ta[0]*100,2) if ta and x["curr"] else None})
        for x in sorted(li,key=lambda x:x["curr"] or 0,reverse=True):
            export.append({"Section":"Liabilities","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),"% of Total":round(x["curr"]/tl[0]*100,2) if tl and x["curr"] else None})
        csv=pd.DataFrame(export).to_csv(index=False).encode("utf-8")
        st.download_button("↓  Download Raw Data (CSV)",data=csv,file_name=f"{base}_metrics.csv",mime="text/csv")
    st.markdown('<div style="font-size:.8rem;color:#aaa;margin-top:8px;"><b>PDF:</b> open HTML in browser → Print → Save as PDF</div>',unsafe_allow_html=True)
    with st.expander("Debug — raw extracted lines"):
        st.text("\n".join(d["raw_lines"][:300]))
