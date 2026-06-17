import streamlit as st
import streamlit.components.v1 as components
import pdfplumber
import pandas as pd
import re, io, datetime

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_OK = True
except ImportError:
    PDF2IMAGE_OK = False

try:
    import pytesseract
    TESS_OK = True
except ImportError:
    TESS_OK = False

OCR_AVAILABLE = PDF2IMAGE_OK and TESS_OK

# ── STREAMLIT CONFIG ──────────────────────────────────────────────────────────
st.set_page_config(page_title="HKMA Disclosure Analyser", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');
*,*::before,*::after{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stHeader"],
[data-testid="stToolbar"],[data-testid="stSidebar"],
.main,.block-container,[data-testid="stVerticalBlock"],[class*="css"]{
  font-family:'DM Sans',sans-serif !important;
  background-color:#ffffff !important;color:#111111 !important;}
.stApp,[data-testid="stAppViewContainer"]{background:#ffffff !important;}
.block-container{max-width:900px !important;padding:2.5rem 2rem 5rem !important;}
p,span,div,li{color:#111111 !important;}
h1{font-family:'DM Sans',sans-serif !important;font-size:.72rem !important;font-weight:700 !important;
   letter-spacing:.18em !important;text-transform:uppercase !important;color:#E60028 !important;
   border-bottom:1.5px solid #E60028 !important;padding-bottom:10px !important;margin-bottom:4px !important;}
h2{font-family:'DM Sans',sans-serif !important;font-size:.65rem !important;font-weight:600 !important;
   letter-spacing:.18em !important;text-transform:uppercase !important;color:#555555 !important;
   border-bottom:1px solid #eeeeee !important;padding-bottom:5px !important;
   margin-top:36px !important;margin-bottom:10px !important;}
h3{font-family:'DM Sans',sans-serif !important;font-size:.63rem !important;font-weight:600 !important;
   letter-spacing:.14em !important;text-transform:uppercase !important;color:#888888 !important;
   margin-top:22px !important;margin-bottom:8px !important;}
.pg-header{display:flex;justify-content:space-between;align-items:flex-end;
           border-bottom:2px solid #111111;padding-bottom:12px;margin-bottom:4px;}
.pg-bank{font-size:1.45rem;font-weight:700;color:#111111 !important;letter-spacing:-.01em;line-height:1.1;}
.pg-meta{font-size:.68rem;color:#999999 !important;text-align:right;line-height:1.7;}
.unit-tag{display:inline-block;font-size:.62rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
          color:#E60028 !important;border:1px solid #E60028;padding:2px 8px;margin:10px 0 20px 0;}
.desc-block{border-left:3px solid #E60028;padding:10px 14px;background:#fafafa !important;margin-bottom:28px;}
.desc-text{font-size:.78rem;color:#444444 !important;line-height:1.65;}
.snapshot{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
          gap:1px;background:#e8e8e8;border:1px solid #e8e8e8;margin-bottom:32px;}
.kpi{background:#ffffff !important;padding:14px 16px;}
.kpi-label{font-size:.6rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#999999 !important;margin-bottom:6px;}
.kpi-val{font-size:1.05rem;font-weight:700;color:#111111 !important;line-height:1;}
.kpi-chg-pos{font-size:.65rem;color:#1a7a3a !important;margin-top:4px;}
.kpi-chg-neg{font-size:.65rem;color:#E60028 !important;margin-top:4px;}
.ratio-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0 28px;}
.ratio-card{border:1px solid #e8e8e8;border-top:2.5px solid #E60028;padding:16px 18px;background:#ffffff !important;}
.ratio-label{font-size:.6rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#aaaaaa !important;margin-bottom:10px;}
.ratio-main{font-size:1.6rem;font-weight:700;color:#111111 !important;line-height:1;}
.ratio-prior{font-size:.72rem;color:#cccccc !important;margin-left:6px;}
.chg-pos{font-size:.68rem;font-weight:600;color:#1a7a3a !important;}
.chg-neg{font-size:.68rem;font-weight:600;color:#E60028 !important;}
table{width:100%;border-collapse:collapse;font-size:.77rem;margin:6px 0 20px;background:#ffffff !important;}
thead tr{border-bottom:2px solid #111111;}
th{font-size:.6rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#999999 !important;
   background:#ffffff !important;padding:0 12px 8px;text-align:right;white-space:nowrap;}
th:first-child{text-align:left;}
td{padding:8px 12px;border-bottom:1px solid #f2f2f2;color:#222222 !important;text-align:right;background:#ffffff !important;}
td:first-child{text-align:left;font-weight:500;color:#111111 !important;}
tr:last-child td{border-bottom:none;}
tr:hover td{background:#fef5f5 !important;}
.pos{color:#1a7a3a !important;font-weight:600;}.neg{color:#E60028 !important;font-weight:600;}.muted{color:#bbbbbb !important;}
.rank{display:inline-block;width:18px;height:18px;line-height:18px;text-align:center;
      font-size:.6rem;font-weight:700;color:#E60028 !important;border:1px solid #E60028;margin-right:8px;vertical-align:middle;}
.rule{border:none;border-top:1px solid #e8e8e8;margin:32px 0 0;}
.analysis-block{background:#fafafa !important;border:1px solid #eeeeee;padding:20px 24px;margin:16px 0;}
.analysis-label{font-size:.58rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#E60028;margin-bottom:10px;}
.analysis-text{font-size:.82rem;color:#333 !important;line-height:1.8;}
.analysis-text b{color:#111 !important;}
.prov-sentence{background:#fff !important;border-left:3px solid #E60028;padding:10px 14px;
               margin:12px 0;font-size:.82rem;color:#333 !important;line-height:1.75;}
.ocr-badge{display:inline-block;font-size:.58rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
           background:#f5f0e8;color:#a07030 !important;border:1px solid #d4a84b;padding:2px 8px;margin-left:10px;vertical-align:middle;}
.text-badge{display:inline-block;font-size:.58rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
            background:#f0f7f0;color:#1a7a3a !important;border:1px solid #8bc88b;padding:2px 8px;margin-left:10px;vertical-align:middle;}
[data-testid="stFileUploader"]{border:1px dashed #dddddd !important;background:#fafafa !important;padding:6px !important;}
[data-testid="stDownloadButton"]>button{background:#ffffff !important;border:1.5px solid #111111 !important;
    color:#111111 !important;font-family:'DM Sans',sans-serif !important;font-size:.68rem !important;
    font-weight:600 !important;letter-spacing:.1em !important;text-transform:uppercase !important;
    padding:8px 20px !important;border-radius:0 !important;}
[data-testid="stDownloadButton"]>button:hover{background:#E60028 !important;border-color:#E60028 !important;color:#ffffff !important;}
[data-testid="stExpander"]{border:1px solid #eeeeee !important;background:#fafafa !important;}
details summary{color:#cccccc !important;font-size:.68rem !important;}
</style>
""", unsafe_allow_html=True)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def clean_num(s):
    if not isinstance(s, str): return None
    s = s.strip().replace(",","").replace("\xa0","").replace("\u202f","").replace(" ","")
    s = re.sub(r"HK\$|US\$|EUR|GBP|'000|HKD","",s).strip()
    if s in ("","--","Nil","nil","N/A","n/a","-","/"): return None
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[()$]","",s)
    try:
        v = float(s)
        return -v if neg else v
    except:
        return None

def trailing_nums(line):
    tokens = re.findall(r"\([\d,]+(?:\.\d+)?\)|[\d,]+(?:\.\d+)?", line)
    return [v for t in tokens for v in [clean_num(t)] if v is not None]

def raw_label(line):
    s = re.sub(r"\|","",line)
    s = re.sub(r"\*{1,2}","",s)
    s = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+"," ",s)
    s = re.sub(r"(\s+[\(\-]?[\d,]+[\)]?)+\s*$","",s).strip()
    s = re.sub(r",?\s*net\s+of\s+impairment\s+allowance","",s,flags=re.IGNORECASE).strip()
    s = re.sub(r",?\s*net\s+of\s+allowance","",s,flags=re.IGNORECASE).strip()
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]+"," ",s)
    s = re.sub(r"\s+"," ",s).strip()
    return s[:70].rsplit(" ",1)[0].strip() if len(s)>70 else s

CANONICAL = {
    r"cash and short.term funds|cash and balances with banks": "Cash and balances with banks",
    r"balances with the monetary authority|balances with central bank|monetary authority": "Balances with Monetary Authority",
    r"due from exchange fund|receivable.*exchange fund": "Due from Exchange Fund",
    r"placements with banks": "Placements with banks",
    r"amounts? due from overseas|due from overseas offices": "Amounts due from overseas offices",
    r"trade bills?": "Trade bills",
    r"certificates? of deposit held": "Certificates of deposit held",
    r"securities held for trading": "Securities held for trading",
    r"advances and other accounts": "Advances and other accounts",
    r"loans and receivables|loans and advances to customers|customer loans": "Loans and receivables",
    r"investment securities|debt securities held": "Investment securities",
    r"other investments": "Other investments",
    r"property.*plant.*equipment|right.of.use assets": "Property, plant and equipment",
    r"amount receivable under reverse repo": "Amount receivable under reverse repos",
    r"deposits.*from central bank|from monetary authority": "Deposits from central banks/MA",
    r"deposits and balances from banks|balances from banks": "Deposits and balances from banks",
    r"due to exchange fund|payable.*exchange fund": "Due to Exchange Fund",
    r"demand deposits and current accounts": "Demand deposits and current accounts",
    r"saving deposits|savings deposits": "Saving deposits",
    r"time.*call.*notice deposits": "Time, call and notice deposits",
    r"amounts? due to overseas|due to overseas offices": "Amount due to overseas offices",
    r"certificates? of deposit issued": "Certificates of deposit issued",
    r"issued debt securities": "Issued debt securities",
    r"amount payable under repo": "Amount payable under repos",
    r"other accounts and provisions|other liabilities": "Other liabilities",
    r"deposits from customers": "Deposits from customers",
    r"^provisions$": "Provisions",
}

def canonicalize(raw):
    ll = raw.lower().strip()
    for pat, clean in CANONICAL.items():
        if re.search(pat, ll, re.IGNORECASE):
            return clean
    return raw

def fmt_n(v):
    return "n/a" if v is None else "{:,.0f}".format(abs(v))

def pct_chg(c,p):
    return None if (c is None or p is None or p==0) else round((c-p)/abs(p)*100,2)

def fmt_chg(v):
    if v is None: return '<span class="muted">n/a</span>'
    css = "pos" if v>0 else "neg"
    return '<span class="{}">{}{}%</span>'.format(css, "+" if v>0 else "", "{:.2f}".format(v))

def pp_html(v):
    if v is None: return '<span class="muted">n/a</span>'
    css="chg-pos" if v>0 else "chg-neg"
    return '<span class="{}">{}{}pp</span>'.format(css, "+" if v>0 else "", "{:.2f}".format(v))

def fmt_snapshot(v, mult):
    if v is None: return "n/a"
    hkd = abs(v)*mult
    if hkd>=1e12: return "{:.2f}T".format(hkd/1e12)
    if hkd>=1e9:  return "{:.1f}B".format(hkd/1e9)
    if hkd>=1e6:  return "{:.0f}M".format(hkd/1e6)
    return "{:,.0f}".format(hkd)

# ── PDF TEXT EXTRACTION ───────────────────────────────────────────────────────
def extract_text_pdfplumber(pdf_bytes):
    """Returns (lines, char_count)."""
    lines = []
    char_count = 0
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            char_count += len(t.strip())
            for l in t.splitlines():
                l = l.strip()
                if l: lines.append(l)
    return lines, char_count

def ocr_pdf(pdf_bytes):
    """OCR all pages and return lines."""
    imgs = convert_from_bytes(pdf_bytes, dpi=300)
    lines = []
    for img in imgs:
        t = pytesseract.image_to_string(img, config="--psm 6")
        for l in t.splitlines():
            l = l.strip()
            if l: lines.append(l)
    return lines

def get_all_lines(pdf_bytes):
    """
    Detect whether the PDF has selectable text.
    If yes: use pdfplumber fast path.
    If no (image-only): fall back to OCR.
    Returns (lines, is_ocr, ocr_available).
    """
    lines, char_count = extract_text_pdfplumber(pdf_bytes)
    total_pages = 0
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        total_pages = len(pdf.pages)
    threshold = total_pages * 80  # expect at least 80 chars per page for real text
    if char_count >= threshold:
        return lines, False, True  # text PDF, no OCR needed
    # Image PDF
    if not OCR_AVAILABLE:
        return lines, True, False  # OCR needed but unavailable
    ocr_lines = ocr_pdf(pdf_bytes)
    return ocr_lines, True, True

def detect_unit(lines):
    for line in lines[:300]:
        if re.search(r"in\s+millions|millions\s+of\s+hk|HKD\s+million|HKD\s*'?\s*million", line, re.IGNORECASE):
            return "HKD millions", 1_000_000
        if re.search(r"HK\$\s*'?\s*0{3}|'000|in\s+HKD\s+thousand|in\s+thousands|HKD000", line, re.IGNORECASE):
            return "HKD thousands", 1_000
    return "HKD thousands", 1_000

# ── UNIVERSAL BALANCE SHEET PARSER ───────────────────────────────────────────
SKIP_LINE = re.compile(
    r"^total\s+(assets|liabilities)|^\s*total\s+assets\s*$|^\s*total\s+liabilities\s*$|"
    r"^assets\s*$|^liabilities\s*$|equity\s+and\s+liabilities\s*$|"
    r"^less:\s*impairment|^impairment\s+allowance|^balance\s+sheet|"
    r"^section\s+[a-z]|\bpage\b.*\d|^note\s|\bfigures\s+in\b|"
    r"^unaudited|^currency\s+risk|^remuneration|^declaration|"
    r"^[-_=\s]+$|^\d+\s*$|^international\s+claims|^capital\s+and\s+reserves",
    re.IGNORECASE)

INCOME_SKIP = re.compile(
    r"profit\s+(before|after)\s+tax|net\s+profit\s*$|"
    r"interest\s+income|interest\s+expense|operating\s+(income|expense|profit)|"
    r"taxation\s+charge|tax\s+expense|net\s+(fees|interest|write)",
    re.IGNORECASE)

def is_noise(line):
    s = line.strip()
    if not s or len(s)<3: return True
    alnum = sum(c.isalnum() for c in s)
    if alnum < 2: return True
    if re.match(r"^[^a-zA-Z\(]",s): return True
    return False

def find_section_bounds(lines, section):
    """
    Returns (start_idx, end_idx) for the asset or liability section.
    Handles multiple common layouts.
    """
    if section == "assets":
        START = re.compile(
            r"^\**\s*assets\s*\**\s*$|"
            r"balance\s+sheet\s+information|"
            r"statement\s+of\s+financial\s+position|"
            r"^\(*i\)*\s+cash\s|"
            r"^i\.\s+cash",
            re.IGNORECASE)
        END = re.compile(
            r"total\s+assets", re.IGNORECASE)
        ALT_END = re.compile(
            r"^liabilities\s*$|equity\s+and\s+liabilities", re.IGNORECASE)
    else:
        START = re.compile(
            r"^liabilities\s*$|equity\s+and\s+liabilities", re.IGNORECASE)
        END = re.compile(
            r"total\s+liabilities", re.IGNORECASE)
        ALT_END = re.compile(
            r"^equity\s*$|^capital\s+and\s+reserves", re.IGNORECASE)

    start = None
    for i, line in enumerate(lines):
        if START.search(line.strip()):
            start = i
            break

    if start is None:
        return None, None

    end = None
    for i in range(start+1, len(lines)):
        if END.search(lines[i].strip()):
            end = i
            break
        if section == "assets" and ALT_END.search(lines[i].strip()) and i > start+3:
            end = i
            break

    return start, end

def parse_section(lines, section):
    """
    Layout-agnostic parser.
    Finds the section, then collects every line that has a label + at least 1 number.
    """
    start, end = find_section_bounds(lines, section)
    if start is None:
        # fallback: search entire text
        search_lines = lines
    else:
        end_idx = end if end else len(lines)
        search_lines = lines[start+1:end_idx]

    items = []
    for line in search_lines:
        if is_noise(line): continue
        cm = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+"," ",line).strip()
        if SKIP_LINE.search(cm): continue
        if INCOME_SKIP.search(cm): continue
        nums = trailing_nums(line)
        if not nums: continue
        curr  = nums[-2] if len(nums)>=2 else nums[-1]
        prior = nums[-1] if len(nums)>=2 else None
        if curr is None or curr == 0: continue
        # reject lines where the label is just digits
        lbl_raw = raw_label(line)
        if not lbl_raw or len(lbl_raw)<2: continue
        if re.match(r"^[\d,.()\-\s]+$", lbl_raw): continue
        label = canonicalize(lbl_raw)
        if any(x["label"]==label for x in items): continue
        items.append({"label":label,"curr":abs(curr),"prior":abs(prior) if prior is not None else None})

    return items

# ── SCALAR EXTRACTORS ─────────────────────────────────────────────────────────
def find_two(lines, pattern, min_val=None, max_val=None):
    for i, line in enumerate(lines):
        if re.search(pattern, line, re.IGNORECASE):
            nums = trailing_nums(line)
            if len(nums)>=2:
                c,p = nums[0],nums[1]
                if min_val is not None and (c<min_val or p<min_val): continue
                if max_val is not None and (c>max_val or p>max_val): continue
                return c,p
            combined = line
            for j in range(i+1, min(i+5,len(lines))):
                combined += " "+lines[j]
                nums = trailing_nums(combined)
                if len(nums)>=2:
                    c,p=nums[0],nums[1]
                    if min_val and (c<min_val or p<min_val): continue
                    return c,p
    return None

def get_provisions(lines):
    spec,coll = None,None
    COLL = re.compile(
        r"collective\s+(impairment|provision)|collective\s+impairment\s+loss|"
        r"\(collective\s+provisions?\)|collective\s+loan\s+loss",
        re.IGNORECASE)
    SPEC = re.compile(
        r"specific\s+(impairment|provision)|individual\s+impairment|"
        r"specific\s+impairment\s+loss|\(specific\s+provisions?\)|credit\s+impairment\s+allowance",
        re.IGNORECASE)
    for i,line in enumerate(lines):
        if COLL.search(line) and coll is None:
            nums = trailing_nums(line)
            if not nums and i+1<len(lines): nums = trailing_nums(lines[i+1])
            if nums: coll=(abs(nums[0]),abs(nums[1]) if len(nums)>=2 else None)
        if SPEC.search(line) and spec is None:
            nums = trailing_nums(line)
            if not nums and i+1<len(lines): nums = trailing_nums(lines[i+1])
            if nums: spec=(abs(nums[0]),abs(nums[1]) if len(nums)>=2 else None)
    return spec, coll

def get_lmr_cfr(lines):
    lmr = find_two(lines, r"average\s+(liquidity\s+maintenance\s+ratio|lmr)", 0, 5000)
    if not lmr: lmr = find_two(lines, r"liquidity\s+maintenance\s+ratio.*average|average.*lmr", 0, 5000)
    if not lmr: lmr = find_two(lines, r"\blmr\b.*%|%.*\blmr\b", 0, 5000)
    cfr = find_two(lines, r"average\s+(core\s+funding\s+ratio|cfr)", 0, 10000)
    if not cfr: cfr = find_two(lines, r"core\s+funding\s+ratio.*average|average.*cfr", 0, 10000)
    if not cfr: cfr = find_two(lines, r"\bcfr\b.*%|%.*\bcfr\b", 0, 10000)
    return lmr, cfr

KNOWN_BANKS = [
    (r"barclays\s+bank\s+plc",         "Barclays Bank PLC, Hong Kong Branch"),
    (r"bnp\s+paribas",                  "BNP Paribas, Hong Kong Branch"),
    (r"jpmorgan\s+chase|j\.p\.\s*morgan\s+chase", "JPMorgan Chase Bank, N.A., Hong Kong Branch"),
    (r"ubs\s+ag",                       "UBS AG, Hong Kong Branch"),
    (r"credit\s+agricole\s+cib|credit\s+agricole\s+corporate", "Credit Agricole CIB, Hong Kong Branch"),
    (r"natixis",                        "Natixis, Hong Kong Branch"),
    (r"societe\s+generale|sghk",        "Societe Generale, Hong Kong Branch"),
    (r"deutsche\s+bank",                "Deutsche Bank AG, Hong Kong Branch"),
    (r"standard\s+chartered",           "Standard Chartered Bank, Hong Kong Branch"),
    (r"hsbc",                           "HSBC, Hong Kong Branch"),
    (r"citibank",                       "Citibank, N.A., Hong Kong Branch"),
    (r"mizuho",                         "Mizuho Bank, Ltd., Hong Kong Branch"),
    (r"mufg|mitsubishi\s+ufj",          "MUFG Bank, Ltd., Hong Kong Branch"),
    (r"sumitomo\s+mitsui",              "Sumitomo Mitsui Banking Corporation, Hong Kong Branch"),
]

def get_entity_name(lines):
    block = " ".join(lines[:120])
    for pat, name in KNOWN_BANKS:
        if re.search(pat, block, re.IGNORECASE):
            return name
    for line in lines[:80]:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
        clean = re.sub(r"\(.*?\)","",clean).strip()
        clean = re.sub(r"\s+"," ",clean).strip()
        if re.search(r"hong\s+kong\s+branch",clean,re.IGNORECASE) and len(clean)>8:
            return clean[:100]
    NON = re.compile(
        r"^(corporate|groupe|kpmg|financial\s+information|financial\s+statements|"
        r"incorporated\s+in|unaudited|figures\s+in|for\s+identification|key\s+financial|"
        r"investment\s+banking|and\s+investment)",re.IGNORECASE)
    for line in lines[:30]:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
        clean = re.sub(r"\(.*?\)","",clean).strip()
        clean = re.sub(r"\s+"," ",clean).strip()
        if not clean or len(clean)<4: continue
        if re.match(r"^[\d\s\-/]+$",clean): continue
        if NON.match(clean): continue
        if clean[0].isupper(): return clean[:100]
    return "HKMA Financial Disclosure Statement"

def get_branch_description(lines):
    para = []
    in_para = False
    HDR = re.compile(
        r"^(additional\s+profit|profit\s+and\s+loss|balance\s+sheet|off-balance|"
        r"supplementary|section\s+[a-z]|contents|for\s+the\s+(year|half)|remuneration|"
        r"liquidity|currency\s+risk|international\s+claims|mainland|group\s+consolidated)",
        re.IGNORECASE)
    for line in lines:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
        clean = re.sub(r"[^a-zA-Z0-9\s,&\.\-/()\!:@'\"]+","",clean).strip()
        clean = re.sub(r"\s+"," ",clean).strip()
        if re.search(r"branch activities|branch information|principal activities",clean,re.IGNORECASE):
            in_para=True; continue
        if in_para:
            if not clean or len(clean)<5: continue
            if HDR.match(clean) or re.match(r"^[-_=]+$",clean): break
            if re.match(r"^[\d\s]+$",clean): continue
            para.append(clean)
            if len(" ".join(para))>450: break
    desc = " ".join(para)
    if not desc:
        for line in lines:
            c = re.sub(r"[\u4e00-\u9fff]+","",line).strip()
            if re.search(r"we have pleasure|incorporated in|registered under|a branch of|principal activities|authorised under",c,re.IGNORECASE) and len(c.split())>8:
                desc=c; break
    if len(desc)>450: desc=desc[:450].rsplit(" ",1)[0]+"..."
    return desc

def get_period(lines):
    for line in lines:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
        if re.search(r"(year|period|half.year)\s+ended|for the year|as at|as of",clean,re.IGNORECASE):
            if re.search(r"\d{4}",clean):
                return re.sub(r"\s+"," ",clean).strip()[:80]
    return ""

# ── MAIN EXTRACT ──────────────────────────────────────────────────────────────
def run(pdf_bytes):
    lines, is_ocr, ocr_avail = get_all_lines(pdf_bytes)
    ul, mult = detect_unit(lines)
    ta     = find_two(lines, r"total\s+assets")
    tl     = find_two(lines, r"total\s+liabilities")
    profit = find_two(lines, r"profit\s+after\s+tax(?:ation)?|net\s+profit\s*$")
    spec, coll = get_provisions(lines)
    lmr, cfr   = get_lmr_cfr(lines)
    ai     = parse_section(lines, "assets")
    li     = parse_section(lines, "liabilities")
    entity = get_entity_name(lines)
    desc   = get_branch_description(lines)
    period = get_period(lines)
    return {"unit_label":ul,"multiplier":mult,"ta":ta,"tl":tl,"profit":profit,
            "spec":spec,"coll":coll,"lmr":lmr,"cfr":cfr,
            "asset_items":ai,"liab_items":li,"entity":entity,"desc":desc,
            "period":period,"raw_lines":lines,"is_ocr":is_ocr,"ocr_avail":ocr_avail}

# ── CHARTS (pie + bar-of-pie style using Plotly subplots) ─────────────────────
def make_pie_bar_html(items, total, title):
    """
    Bar-of-pie: left pie shows top-5 + 'Other'; right bar expands 'Other' slice.
    Falls back to a clean pie if not enough items for the bar segment.
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        valid = sorted([x for x in items if x.get("curr") and x["curr"]>0],
                       key=lambda x:x["curr"], reverse=True)
        if not valid or not total: return ""

        TOP_N = 5
        top   = valid[:TOP_N]
        rest  = valid[TOP_N:]
        other_val = sum(x["curr"] for x in rest) if rest else 0

        pie_labels = [x["label"] for x in top]
        pie_vals   = [x["curr"] for x in top]
        if rest:
            pie_labels.append("Other ({} items)".format(len(rest)))
            pie_vals.append(other_val)

        RED    = "#E60028"
        GRAYS  = ["#555555","#777777","#999999","#bbbbbb","#dddddd","#eeeeee"]
        colors = [RED] + GRAYS[:len(pie_labels)-1]

        if rest and len(rest)>=2:
            fig = make_subplots(rows=1, cols=2,
                specs=[[{"type":"pie"},{"type":"bar"}]],
                column_widths=[0.55,0.45])
            fig.add_trace(go.Pie(
                labels=pie_labels, values=pie_vals,
                marker_colors=colors,
                textinfo="percent+label",
                textfont_size=9,
                hole=0.3,
                pull=[0.04]+[0]*(len(pie_labels)-1),
                hovertemplate="%{label}<br>%{percent}<extra></extra>",
                showlegend=False), row=1, col=1)
            bar_labels = [x["label"] for x in rest]
            bar_vals   = [round(x["curr"]/total*100,2) for x in rest]
            fig.add_trace(go.Bar(
                y=bar_labels[::-1], x=bar_vals[::-1], orientation="h",
                marker_color=GRAYS[0],
                text=["{:.1f}%".format(v) for v in bar_vals[::-1]],
                textposition="outside",
                textfont_size=8,
                hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
                showlegend=False), row=1, col=2)
            fig.update_xaxes(ticksuffix="%",tickfont_size=8,gridcolor="#f0f0f0",row=1,col=2)
            fig.update_yaxes(tickfont_size=8,automargin=True,row=1,col=2)
            height = max(260, 30*len(rest)+120)
        else:
            fig = go.Figure(go.Pie(
                labels=pie_labels, values=pie_vals,
                marker_colors=colors,
                textinfo="percent+label",
                textfont_size=9,
                hole=0.3,
                hovertemplate="%{label}<br>%{percent}<extra></extra>",
                showlegend=True))
            height = 280

        fig.update_layout(
            title=dict(text=title, font=dict(size=11,family="DM Sans",color="#555555"), x=0, xanchor="left"),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=10,r=30,t=40,b=20),
            height=height,
            font=dict(family="DM Sans"))
        return fig.to_html(full_html=False, include_plotlyjs="cdn",
                           config={"displayModeBar":False})
    except Exception as e:
        return ""

# ── ANALYSIS ENGINE ───────────────────────────────────────────────────────────
def generate_analysis(d, ul):
    entity = d["entity"]
    ta, tl = d["ta"], d["tl"]
    prof   = d["profit"]
    spec   = d["spec"]
    coll   = d["coll"]
    lmr    = d["lmr"]
    cfr    = d["cfr"]
    ai     = d["asset_items"]
    li     = d["liab_items"]
    sn     = entity.split(",")[0].split()[0] if entity else "The branch"

    tc_c = ta[0] if ta else None
    tl_c = tl[0] if tl else None
    ai_s = sorted([x for x in ai if x.get("curr")], key=lambda x:x["curr"], reverse=True)
    li_s = sorted([x for x in li if x.get("curr")], key=lambda x:x["curr"], reverse=True)
    ai3  = ai_s[:3]
    li3  = li_s[:3]

    # Profitability
    pc = pct_chg(prof[0],prof[1]) if prof else None
    if prof and pc is not None:
        dir_p = "up" if pc>0 else "down"
        p_txt = "{} reported profit after taxation of {} {} for the period, {} {:.1f}% from {} {} in the prior period. ".format(
            sn, fmt_n(prof[0]), ul, dir_p, abs(pc), fmt_n(prof[1]), ul)
        if pc>20:    p_txt += "This acceleration points to a structural improvement in earnings capacity. Determine whether revenue growth, cost reduction, or one-off items are the primary driver before treating this as a durable trend."
        elif pc>0:   p_txt += "Modest growth is consistent with a stable operating base, though the underlying revenue and margin trends require verification to assess sustainability."
        elif pc>-20: p_txt += "The moderate decline requires scrutiny of revenue mix, margin compression, and the adequacy of cost controls relative to the prior period."
        else:        p_txt += "This level of contraction is a material risk signal. Management should be challenged on revenue sustainability, operating leverage, and whether any impairment acceleration is embedded in provisions rather than disclosed separately."
    else:
        p_txt = "Profitability data could not be extracted from this filing."

    # LMR
    lmr_pp = round(lmr[0]-lmr[1],2) if lmr else None
    if lmr:
        if lmr_pp is not None and lmr_pp < -20:
            l_txt = "The LMR fell {:.2f}pp to {:.2f}%, indicating the branch deployed liquid assets or absorbed more short-term liabilities during the period. This is consistent with active balance sheet deployment. The critical question is whether this reflects loan growth, interbank activity expansion, or a structural shift in the liability profile, and whether the resulting liquidity buffer holds under stressed outflow scenarios.".format(abs(lmr_pp), lmr[0])
        elif lmr_pp is not None and lmr_pp > 20:
            l_txt = "The LMR rose sharply {:.2f}pp to {:.2f}%, reflecting a significant build-up of liquid assets relative to short-term liabilities. This may indicate reduced lending appetite, deliberate buffer accumulation ahead of perceived market stress, or an increase in central bank deposits. An unusually elevated LMR signals under-deployment of capital and warrants review of the deployment strategy.".format(abs(lmr_pp), lmr[0])
        else:
            l_txt = "The LMR is broadly stable at {:.2f}% (prior: {:.2f}%), indicating an unchanged short-term liquidity management posture. No material shift in inflow/outflow assumptions is apparent. The ratio remains well above the 25% regulatory minimum, with ample headroom under both base case and stressed conditions.".format(lmr[0], lmr[1])
    else:
        l_txt = "LMR data was not disclosed or could not be extracted from this filing."

    # CFR
    cfr_pp = round(cfr[0]-cfr[1],2) if cfr else None
    if cfr:
        if cfr_pp is not None and cfr_pp < -30:
            c_txt = "The CFR declined {:.2f}pp to {:.2f}%, reflecting a reduction in stable funding relative to required stable funding. If this accompanies balance sheet expansion or longer-dated asset growth, the mechanical decline is expected; however, if stable funding sources have shortened, the structural funding profile has deteriorated. Monitor the trajectory toward the 75% regulatory minimum.".format(abs(cfr_pp), cfr[0])
        elif cfr_pp is not None and cfr_pp > 30:
            c_txt = "The CFR rose {:.2f}pp to {:.2f}%, signaling a stronger structural funding base relative to requirements. This suggests either liability maturity extension, reduction in long-dated assets, or inflows of stable funding. Excess stable funding capacity creates optionality for balance sheet growth without regulatory constraint.".format(abs(cfr_pp), cfr[0])
        else:
            c_txt = "The CFR is stable at {:.2f}% (prior: {:.2f}%), reflecting a consistent liability maturity structure and no material change in the long-term funding mix. Structural funding comfortably exceeds the 75% regulatory threshold.".format(cfr[0], cfr[1])
    else:
        c_txt = "CFR data was not disclosed or could not be extracted from this filing."

    # Assets
    if ai3 and tc_c:
        top_a = ai3[0]["label"]
        top_a_pct = round(ai3[0]["curr"]/tc_c*100,1)
        top3_pct  = round(sum(x["curr"] for x in ai3)/tc_c*100,1)
        overseas  = bool(re.search(r"overseas",top_a,re.IGNORECASE))
        loans     = bool(re.search(r"loans|receivable|advances",top_a,re.IGNORECASE))
        if overseas:
            risk_f = "With {:.1f}% of assets as intragroup receivables from overseas offices, the branch functions primarily as a capital conduit within the parent group. External borrower credit risk is secondary. The dominant risk vectors are parent-group solvency, HKMA intragroup concentration limits, and regulatory treatment of connected exposures in a resolution scenario.".format(top_a_pct)
        elif loans:
            risk_f = "Customer loans at {:.1f}% of assets place external borrower credit quality at the center of the risk profile. Impairment coverage ratios, sectoral concentration, and Stage 2 to Stage 3 migration trends are the leading indicators of emerging credit stress.".format(top_a_pct)
        else:
            risk_f = "{} at {:.1f}% of assets dominates the balance sheet. The counterparty composition and credit quality of this asset class require detailed scrutiny to establish where primary risk sits.".format(top_a, top_a_pct)
        a_txt = "The three largest assets ({}) account for {:.1f}% of total assets, creating a concentrated exposure that defines the risk profile of this branch. {}".format(
            ", ".join(x["label"] for x in ai3), top3_pct, risk_f)
    else:
        a_txt = "Asset concentration data could not be fully extracted from this filing."
        overseas = False; loans = False

    # Liabilities
    if li3 and tl_c:
        top_l = li3[0]["label"]
        top_l_pct  = round(li3[0]["curr"]/tl_c*100,1)
        top3_l_pct = round(sum(x["curr"] for x in li3)/tl_c*100,1)
        cust_dep = bool(re.search(r"customer|demand|time|saving",top_l,re.IGNORECASE))
        ov_liab  = bool(re.search(r"overseas|due to",top_l,re.IGNORECASE))
        if cust_dep:
            fund_f = "Customer deposits dominate at {:.1f}% of liabilities, indicating a retail and corporate-anchored funding structure with relatively stable maturity characteristics. Depositor concentration and the repricing profile of time deposits are the primary funding risk variables to monitor.".format(top_l_pct)
        elif ov_liab:
            fund_f = "The largest funding source is intragroup liabilities to overseas offices at {:.1f}%, confirming the branch is primarily funded by the parent rather than local deposit collection. Funding stability is therefore a direct function of parent group liquidity and the terms of intragroup arrangements.".format(top_l_pct)
        else:
            fund_f = "Wholesale and interbank funding at {:.1f}% represents the dominant liability, indicating sensitivity to market sentiment and counterparty confidence. Funding cliff risk from short-dated wholesale rollovers should be explicitly stress-tested.".format(top_l_pct)
        l_txt = "The top three liabilities ({}) account for {:.1f}% of total liabilities. {}".format(
            ", ".join(x["label"] for x in li3), top3_l_pct, fund_f)
    else:
        l_txt = "Liability concentration data could not be fully extracted from this filing."

    # Provisions
    spec_c = spec[0] if spec else None
    spec_p = spec[1] if spec else None
    coll_c = coll[0] if coll else None
    coll_p = coll[1] if coll else None
    spec_chg = pct_chg(spec_c,spec_p)
    coll_chg = pct_chg(coll_c,coll_p)

    if spec_c is not None and spec_p is not None:
        spec_dir = "rose" if spec_c>spec_p else "fell"
        spec_s = "Specific provisions {} {:.1f}%, driven by individual loan impairments, implying {} identified credit risk on specific borrowers.".format(
            spec_dir, abs(spec_chg), "more" if spec_c>spec_p else "less")
    elif spec_c is not None:
        spec_s = "Specific provisions stand at {} {} (no prior period comparison available).".format(fmt_n(spec_c), ul)
    else:
        spec_s = "Specific provision data was not available in this filing."

    if coll_c is not None and coll_p is not None:
        coll_dir = "rose" if coll_c>coll_p else "fell"
        coll_s = " Collective provisions {} {:.1f}%, reflecting a portfolio-level reassessment, implying {} systemic credit concern across the loan book.".format(
            coll_dir, abs(coll_chg), "heightened" if coll_c>coll_p else "reduced")
    elif coll_c is not None:
        coll_s = " Collective provisions stand at {} {} (no prior period comparison available).".format(fmt_n(coll_c), ul)
    else:
        coll_s = " Collective provision data was not available."

    top_a_name = ai3[0]["label"] if ai3 else "primary asset"
    if re.search(r"overseas",top_a_name,re.IGNORECASE):
        dom = "the dominant asset is amounts due from overseas offices, so credit risk sits primarily with the parent group"
    elif re.search(r"loans|receivable|advances",top_a_name,re.IGNORECASE):
        dom = "the dominant asset is {}, so credit risk sits primarily with external borrowers".format(top_a_name.lower())
    else:
        dom = "the dominant asset is {}".format(top_a_name.lower())
    prov_sentence = spec_s + coll_s + " " + dom.capitalize() + "."

    # Executive
    signals = []
    if prof and pc is not None:
        if   pc>15:  signals.append("strong earnings growth (+{:.1f}%)".format(pc))
        elif pc<-15: signals.append("material earnings contraction ({:.1f}%)".format(pc))
        else:        signals.append("stable profitability ({:+.1f}%)".format(pc))
    if lmr:
        if   lmr[0]>200: signals.append("very high LMR ({:.0f}%), well above the 25% regulatory floor".format(lmr[0]))
        elif lmr[0]>75:  signals.append("healthy LMR ({:.0f}%)".format(lmr[0]))
        else:            signals.append("LMR at {:.0f}%".format(lmr[0]))
    if ta and ta[0] and ta[1]:
        ta_chg = pct_chg(ta[0],ta[1])
        if ta_chg and ta_chg>15:  signals.append("significant balance sheet growth (+{:.1f}%)".format(ta_chg))
        elif ta_chg and ta_chg<-10: signals.append("balance sheet contraction ({:.1f}%)".format(ta_chg))

    if signals:
        if overseas:
            risk_note = "As a capital conduit, the primary risk vector is parent-group solvency and HKMA intragroup exposure limits. Standalone domestic credit quality is secondary. Resolution planning and intragroup funding dependency warrant supervisory attention."
        elif loans:
            risk_note = "With customer lending as the core asset, standalone credit quality drives the risk profile. Track impairment coverage, collateral quality, and sector concentration as the leading stress indicators."
        else:
            risk_note = "The counterparty and credit quality of the dominant asset class require further investigation for a complete risk assessment."
        exec_txt = "Key signals: {}. {}".format("; ".join(signals), risk_note)
    else:
        exec_txt = "Insufficient data to generate a complete takeaway. Cross-reference with the original filing."

    return {"profitability":p_txt,"lmr":l_txt,"cfr":c_txt,
            "assets":a_txt,"liabilities":l_txt,"prov_sentence":prov_sentence,"executive":exec_txt}

# ── HTML REPORT GENERATOR ────────────────────────────────────────────────────
def generate_report_html(d, filename, ul, mult, analysis):
    entity = d["entity"] or filename
    period = d["period"] or ""
    desc   = d["desc"] or ""
    ta,tl  = d["ta"],d["tl"]
    prof   = d["profit"]
    spec   = d["spec"]
    coll   = d["coll"]
    lmr    = d["lmr"]
    cfr    = d["cfr"]
    ai,li  = d["asset_items"],d["liab_items"]
    tc_c   = ta[0] if ta else None
    tc_p   = ta[1] if ta else None
    tl_c   = tl[0] if tl else None
    tl_p   = tl[1] if tl else None
    tot_prov = None
    if spec and coll:
        c2 = (spec[1]+coll[1]) if (spec[1] and coll[1]) else None
        tot_prov = (spec[0]+coll[0], c2)
    elif coll: tot_prov = coll
    elif spec: tot_prov = spec
    ai_s = sorted([x for x in ai if x.get("curr")], key=lambda x:x["curr"], reverse=True)
    li_s = sorted([x for x in li if x.get("curr")], key=lambda x:x["curr"], reverse=True)
    ai3,li3 = ai_s[:3],li_s[:3]
    lmr_pp = round(lmr[0]-lmr[1],2) if lmr else None
    cfr_pp = round(cfr[0]-cfr[1],2) if cfr else None
    today  = datetime.date.today().strftime("%d %B %Y")

    def kfr(label,pair):
        if not pair:
            return "<tr><td>{}</td><td class='muted'>n/a</td><td class='muted'>n/a</td><td class='muted'>n/a</td></tr>".format(label)
        c,p=pair[0],pair[1]; ch=pct_chg(c,p)
        chs=("{}{}%".format("+" if ch and ch>0 else "","{:.2f}".format(ch))) if ch is not None else "n/a"
        css="pos" if (ch and ch>0) else("neg" if (ch and ch<0) else "")
        return "<tr><td>{}</td><td class='num'>{}</td><td class='num'>{}</td><td class='num {}'>{}</td></tr>".format(
            label,fmt_n(c),fmt_n(p),css,chs)

    def top3_rows(items, tc, tp):
        if not items or not tc:
            return "<tr><td colspan='5' class='muted'>No data available</td></tr>"
        rows=""
        for i,x in enumerate(items,1):
            pc = "{:.2f}%".format(round(x["curr"]/tc*100,2))
            pp_v = x.get("prior")
            pp = "{:.2f}%".format(round(pp_v/tp*100,2)) if (tp and pp_v) else "n/a"
            rows += ("<tr><td><b>{}</b> {}</td><td class='num'>{}</td><td class='num muted'>{}</td>"
                     "<td class='num'>{}</td><td class='num muted'>{}</td></tr>").format(
                         i,x["label"],pc,fmt_n(x["curr"]),pp,fmt_n(pp_v))
        return rows

    def chg_s(v):
        if v is None: return ""
        css="chg-pos" if v>0 else "chg-neg"
        return "<span class='{}'>{}{:.2f}pp</span>".format(css,"+" if v>0 else "",v)

    kf_pairs=[("Profit after taxation",prof),("Total assets",ta),("Total liabilities",tl),
              ("Specific provisions",spec),("Collective provisions",coll),("Total provisions",tot_prov)]

    return """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>{entity} - HKMA Disclosure</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'DM Sans',sans-serif;background:#fff;color:#111;font-size:10pt;line-height:1.6;max-width:800px;margin:0 auto;padding:40px 48px;}}
@media print{{body{{padding:20px 28px;}}@page{{margin:18mm;}}}}
.doc-header{{border-bottom:2px solid #111;padding-bottom:14px;margin-bottom:8px;}}
.doc-bank{{font-size:1.5rem;font-weight:700;letter-spacing:-.01em;line-height:1.1;margin-bottom:3px;}}
.doc-sub{{font-size:.72rem;color:#999;}}.doc-meta{{font-size:.68rem;color:#bbb;margin-top:4px;}}
.unit-tag{{display:inline-block;font-size:.6rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
           color:#E60028;border:1px solid #E60028;padding:1px 7px;margin:8px 0 18px;}}
.desc{{border-left:3px solid #E60028;padding:8px 14px;background:#fafafa;margin-bottom:24px;font-size:.8rem;color:#444;line-height:1.7;}}
h2{{font-size:.62rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#555;
    border-bottom:1px solid #eee;padding-bottom:4px;margin-top:32px;margin-bottom:12px;}}
.narrative{{font-size:.83rem;color:#333;line-height:1.8;margin-bottom:10px;}}
.narrative b{{color:#111;}}
.prov-sentence{{font-size:.83rem;color:#333;line-height:1.8;border-left:2px solid #E60028;padding:8px 14px;background:#fafafa;margin:10px 0;}}
.exec-box{{border:1px solid #e8e8e8;border-top:2.5px solid #E60028;padding:16px 20px;margin-top:20px;background:#fafafa;}}
.exec-label{{font-size:.58rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#E60028;margin-bottom:8px;}}
.exec-text{{font-size:.83rem;color:#222;line-height:1.8;}}
table{{width:100%;border-collapse:collapse;font-size:.78rem;margin:8px 0 18px;}}
thead tr{{border-bottom:2px solid #111;}}
th{{font-size:.58rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#999;padding:0 10px 7px;text-align:right;}}
th:first-child{{text-align:left;}}
td{{padding:7px 10px;border-bottom:1px solid #f0f0f0;color:#222;text-align:right;}}
td:first-child{{text-align:left;font-weight:500;color:#111;}}
tr:last-child td{{border-bottom:none;}}
.num{{font-variant-numeric:tabular-nums;}}.pos{{color:#1a7a3a;font-weight:600;}}.neg{{color:#E60028;font-weight:600;}}.muted{{color:#bbb;}}
.chg-pos{{font-size:.66rem;font-weight:600;color:#1a7a3a;}}.chg-neg{{font-size:.66rem;font-weight:600;color:#E60028;}}
.ratio-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0 20px;}}
.ratio-card{{border:1px solid #e8e8e8;border-top:2.5px solid #E60028;padding:14px 16px;}}
.ratio-label{{font-size:.58rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#aaa;margin-bottom:8px;}}
.ratio-main{{font-size:1.4rem;font-weight:700;color:#111;line-height:1;}}
.ratio-prior{{font-size:.68rem;color:#ccc;margin-left:6px;}}
.doc-footer{{margin-top:48px;padding-top:12px;border-top:1px solid #eee;font-size:.62rem;color:#bbb;display:flex;justify-content:space-between;}}
</style></head><body>
<div class="doc-header">
  <div class="doc-bank">{entity}</div>
  <div class="doc-sub">HKMA Financial Information Disclosure Statement</div>
  <div class="doc-meta">{period} | Generated {today}</div>
</div>
<div class="unit-tag">Reported in {ul}</div>
{desc_html}
<h2>Key Metrics</h2>
<table><thead><tr><th>Metric</th><th>Current ({ul})</th><th>Prior ({ul})</th><th>Change</th></tr></thead><tbody>
{kf_html}</tbody></table>
<h2>Liquidity Ratios</h2>
<div class="ratio-grid">
  <div class="ratio-card">
    <div class="ratio-label">3-Month Average LMR</div>
    <div><span class="ratio-main">{lmr_c}</span><span class="ratio-prior">{lmr_p}</span></div>
    <div style="margin-top:6px">{lmr_ch}</div>
  </div>
  <div class="ratio-card">
    <div class="ratio-label">3-Month Average CFR</div>
    <div><span class="ratio-main">{cfr_c}</span><span class="ratio-prior">{cfr_p}</span></div>
    <div style="margin-top:6px">{cfr_ch}</div>
  </div>
</div>
<h2>Asset Concentration - Top 3</h2>
<table><thead><tr><th>Item</th><th>Curr %</th><th>Current ({ul})</th><th>Prior %</th><th>Prior ({ul})</th></tr></thead>
<tbody>{asset_rows}</tbody></table>
<h2>Liability Concentration - Top 3</h2>
<table><thead><tr><th>Item</th><th>Curr %</th><th>Current ({ul})</th><th>Prior %</th><th>Prior ({ul})</th></tr></thead>
<tbody>{liab_rows}</tbody></table>
<h2>Analysis</h2>
<p class="narrative">{profitability}</p>
<p class="narrative"><b>LMR:</b> {lmr_analysis}</p>
<p class="narrative"><b>CFR:</b> {cfr_analysis}</p>
<p class="narrative">{assets_analysis}</p>
<p class="narrative">{liab_analysis}</p>
<div class="prov-sentence">{prov_sentence}</div>
<div class="exec-box">
  <div class="exec-label">Key Takeaway</div>
  <div class="exec-text">{executive}</div>
</div>
<div class="doc-footer">
  <span>HKMA Disclosure Analyser | {today}</span>
  <span>Confidential | Internal use only</span>
</div>
</body></html>""".format(
        entity=entity, period=period, today=today, ul=ul,
        desc_html="<div class='desc'>{}</div>".format(desc) if desc else "",
        kf_html="".join(kfr(l,p) for l,p in kf_pairs),
        lmr_c="{:.2f}%".format(lmr[0]) if lmr else "n/a",
        lmr_p="prev {:.2f}%".format(lmr[1]) if lmr else "",
        lmr_ch=chg_s(lmr_pp),
        cfr_c="{:.2f}%".format(cfr[0]) if cfr else "n/a",
        cfr_p="prev {:.2f}%".format(cfr[1]) if cfr else "",
        cfr_ch=chg_s(cfr_pp),
        asset_rows=top3_rows(ai3,tc_c,tc_p),
        liab_rows=top3_rows(li3,tl_c,tl_p),
        profitability=analysis["profitability"],
        lmr_analysis=analysis["lmr"],
        cfr_analysis=analysis["cfr"],
        assets_analysis=analysis["assets"],
        liab_analysis=analysis["liabilities"],
        prov_sentence=analysis["prov_sentence"],
        executive=analysis["executive"])

# ── STREAMLIT UI ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:28px;">
  <div style="font-size:1.35rem;font-weight:700;color:#111;letter-spacing:-.01em;line-height:1.2">
    HKMA Disclosure Analyser
  </div>
  <div style="font-size:.75rem;color:#aaa;margin-top:4px;">
    Upload any HKMA Financial Information Disclosure Statement
  </div>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Drop a PDF here or click to upload",
    type=["pdf"], label_visibility="collapsed")

if not uploaded:
    st.markdown(
        '<p style="font-size:.8rem;color:#bbbbbb;margin-top:20px;">'
        'Compatible with all HKMA fd_fin formats: Societe Generale, BNP Paribas, '
        'Natixis, Barclays, JPMorgan Chase, UBS, Credit Agricole, and more.</p>',
        unsafe_allow_html=True)
    st.stop()

with st.spinner("Extracting data..."):
    try:
        pdf_bytes = uploaded.read()
        d = run(pdf_bytes)
    except Exception as e:
        st.error("Could not process this PDF. Error: {}".format(e))
        st.stop()

ul   = d["unit_label"]
mult = d["multiplier"]
ta   = d["ta"]
tl   = d["tl"]
prof = d["profit"]
spec = d["spec"]
coll = d["coll"]
lmr  = d["lmr"]
cfr  = d["cfr"]
ai   = d["asset_items"]
li   = d["liab_items"]
entity  = d["entity"]
desc    = d["desc"] or ""
period  = d["period"] or ""
is_ocr  = d["is_ocr"]
ocr_avail = d["ocr_avail"]

# OCR status banner
if is_ocr:
    if ocr_avail:
        st.success("Image-only PDF detected. OCR was used to extract text from scanned pages.")
    else:
        st.warning(
            "Image-only PDF detected but OCR (Tesseract) is not available on this server. "
            "Data could not be extracted. If deploying on Streamlit Cloud, ensure "
            "packages.txt contains 'tesseract-ocr' and 'poppler-utils'.")
        st.stop()

# Missing data warnings
missing = []
if not ta:  missing.append("total assets")
if not ai:  missing.append("asset breakdown")
if missing:
    st.warning("Could not extract: {}. These fields will show as n/a. Check the debug panel below.".format(", ".join(missing)))

tot_prov = None
if spec and coll:
    c2 = (spec[1]+coll[1]) if (spec[1] and coll[1]) else None
    tot_prov = (spec[0]+coll[0], c2)
elif coll: tot_prov = coll
elif spec: tot_prov = spec

# Header
ocr_tag = '<span class="ocr-badge">OCR</span>' if is_ocr else '<span class="text-badge">DIGITAL TEXT</span>'
st.markdown("""
<div class="pg-header">
  <div class="pg-bank">{} {}</div>
  <div class="pg-meta">HKMA Key Financial Disclosure<br><span>{}</span></div>
</div>
<div class="unit-tag">Reported in {} &nbsp;|&nbsp; Snapshot in HKD</div>
""".format(entity, ocr_tag, period, ul), unsafe_allow_html=True)

if desc:
    st.markdown('<div class="desc-block"><div class="desc-text">{}</div></div>'.format(desc), unsafe_allow_html=True)

# KPI snapshot
def kpi_block(label,rv,rp,is_ratio=False):
    if rv is None: return ""
    display = "{:.2f}%".format(rv) if is_ratio else "HKD {}".format(fmt_snapshot(rv,mult))
    chg_html = ""
    if rp is not None:
        chg = round(rv-rp,2) if is_ratio else pct_chg(rv,rp)
        if chg is not None:
            sfx = "pp" if is_ratio else "%"
            css = "kpi-chg-pos" if chg>0 else "kpi-chg-neg"
            chg_html = '<div class="{}">{}{}{}  vs prior</div>'.format(
                css, "+" if chg>0 else "", "{:.2f}".format(chg), sfx)
    return '<div class="kpi"><div class="kpi-label">{}</div><div class="kpi-val">{}</div>{}</div>'.format(
        label,display,chg_html)

kpis = "".join(filter(None,[
    kpi_block("Total Assets",    ta[0] if ta else None,   ta[1] if ta else None),
    kpi_block("Profit after Tax",prof[0] if prof else None,prof[1] if prof else None),
    kpi_block("Avg LMR",         lmr[0] if lmr else None, lmr[1] if lmr else None, True),
    kpi_block("Avg CFR",         cfr[0] if cfr else None, cfr[1] if cfr else None, True),
    kpi_block("Total Provisions",tot_prov[0] if tot_prov else None,
                                 tot_prov[1] if tot_prov else None),
]))
if kpis:
    st.markdown('<div class="snapshot">{}</div>'.format(kpis), unsafe_allow_html=True)

# Liquidity ratios
st.markdown("<h2>Liquidity Ratios</h2>", unsafe_allow_html=True)
lpp = round(lmr[0]-lmr[1],2) if lmr else None
cpp = round(cfr[0]-cfr[1],2) if cfr else None
st.markdown("""<div class="ratio-grid">
  <div class="ratio-card">
    <div class="ratio-label">3-Month Average LMR</div>
    <div><span class="ratio-main">{lmr_c}</span><span class="ratio-prior">{lmr_p}</span></div>
    <div style="margin-top:6px">{lmr_ch}</div>
  </div>
  <div class="ratio-card">
    <div class="ratio-label">3-Month Average CFR</div>
    <div><span class="ratio-main">{cfr_c}</span><span class="ratio-prior">{cfr_p}</span></div>
    <div style="margin-top:6px">{cfr_ch}</div>
  </div>
</div>""".format(
    lmr_c="{:.2f}%".format(lmr[0]) if lmr else "n/a",
    lmr_p="prev {:.2f}%".format(lmr[1]) if lmr else "",
    lmr_ch=pp_html(lpp),
    cfr_c="{:.2f}%".format(cfr[0]) if cfr else "n/a",
    cfr_p="prev {:.2f}%".format(cfr[1]) if cfr else "",
    cfr_ch=pp_html(cpp)), unsafe_allow_html=True)

# Key financials table
st.markdown("<h2>Key Financials</h2>", unsafe_allow_html=True)
kf_rows = [("Profit after taxation",prof),("Total assets",ta),("Total liabilities",tl),
           ("Specific provisions",spec),("Collective provisions",coll),("Total provisions",tot_prov)]
rows_html = ""
for label,pair in kf_rows:
    if pair:
        c,p = pair[0],pair[1]
        rows_html += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            label, fmt_n(c), fmt_n(p), fmt_chg(pct_chg(c,p)))
    else:
        rows_html += '<tr><td>{}</td><td class="muted">n/a</td><td class="muted">n/a</td><td class="muted">n/a</td></tr>'.format(label)
st.markdown("""<table><thead><tr>
  <th>Metric</th><th>Current ({ul})</th><th>Prior ({ul})</th><th>Change</th>
</tr></thead><tbody>{rows}</tbody></table>""".format(ul=ul,rows=rows_html), unsafe_allow_html=True)

# Top-3 tables + bar-of-pie charts
def render_top3(items, total_pair, title):
    tc = total_pair[0] if total_pair else None
    tp = total_pair[1] if total_pair else None
    valid = sorted([x for x in items if x.get("curr") and x["curr"]>0],
                   key=lambda x:x["curr"], reverse=True)[:3]
    st.markdown("<h2>{}</h2>".format(title), unsafe_allow_html=True)
    if not valid or not tc:
        st.markdown('<p style="font-size:.75rem;color:#bbb">No items extracted.</p>', unsafe_allow_html=True)
        return
    rows_h = ""
    for i,x in enumerate(valid,1):
        pct_c = "{:.2f}%".format(round(x["curr"]/tc*100,2))
        pp_v  = x.get("prior")
        pct_p = "{:.2f}%".format(round(pp_v/tp*100,2)) if (tp and pp_v) else '<span class="muted">n/a</span>'
        rows_h += ('<tr><td><span class="rank">{}</span>{}</td>'
                   '<td><b>{}</b></td><td class="muted">{}</td>'
                   '<td>{}</td><td class="muted">{}</td></tr>').format(
                       i, x["label"], pct_c, fmt_n(x["curr"]), pct_p, fmt_n(pp_v))
    st.markdown("""<table><thead><tr><th>Item</th>
      <th>Curr %</th><th>Current ({ul})</th><th>Prior %</th><th>Prior ({ul})</th>
    </tr></thead><tbody>{rows}</tbody></table>""".format(ul=ul,rows=rows_h), unsafe_allow_html=True)

def render_pie_bar(items, total_pair, title):
    tc = total_pair[0] if total_pair else None
    if not tc: return
    valid = sorted([x for x in items if x.get("curr") and x["curr"]>0],
                   key=lambda x:x["curr"], reverse=True)
    chart_html = make_pie_bar_html(valid, tc, title)
    if chart_html:
        h = max(260, 30*max(0,len(valid)-5)+160)
        components.html(chart_html, height=h, scrolling=False)

render_top3(ai, ta, "Asset Concentration - Top 3")
render_pie_bar(ai, ta, "Asset Composition")

render_top3(li, tl, "Liability Concentration - Top 3")
render_pie_bar(li, tl, "Liability Composition")

# Full breakdown
st.markdown('<hr class="rule">', unsafe_allow_html=True)
st.markdown("<h2>Full Balance Sheet Breakdown</h2>", unsafe_allow_html=True)

def render_full(items, total_pair, title):
    tc = total_pair[0] if total_pair else None
    tp = total_pair[1] if total_pair else None
    valid = sorted([x for x in items if x.get("curr") is not None],
                   key=lambda x:x.get("curr") or 0, reverse=True)
    st.markdown("<h3>{}</h3>".format(title), unsafe_allow_html=True)
    if not valid or not tc:
        st.markdown('<p style="font-size:.75rem;color:#bbb">No items extracted.</p>', unsafe_allow_html=True)
        return
    rows_h = ""
    for x in valid:
        pct_c = "<b>{:.2f}%</b>".format(round(x["curr"]/tc*100,2)) if x.get("curr") else '<span class="muted">n/a</span>'
        pp_v  = x.get("prior")
        pct_p = "{:.2f}%".format(round(pp_v/tp*100,2)) if (tp and pp_v) else '<span class="muted">n/a</span>'
        rows_h += "<tr><td>{}</td><td>{}</td><td>{}</td><td class='muted'>{}</td><td>{}</td></tr>".format(
            x["label"], fmt_n(x.get("curr")), pct_c, fmt_n(pp_v), pct_p)
    st.markdown("""<table><thead><tr>
      <th>Item</th><th>Current ({ul})</th><th>% of Total</th><th>Prior ({ul})</th><th>% (Prior)</th>
    </tr></thead><tbody>{rows}</tbody></table>""".format(ul=ul,rows=rows_h), unsafe_allow_html=True)

render_full(ai, ta, "Assets")
render_full(li, tl, "Liabilities")

# Analysis
st.markdown('<hr class="rule">', unsafe_allow_html=True)
st.markdown("<h2>Analysis</h2>", unsafe_allow_html=True)
analysis = generate_analysis(d, ul)

st.markdown("<h3>Profitability</h3>", unsafe_allow_html=True)
st.markdown('<div class="analysis-block"><div class="analysis-text">{}</div></div>'.format(
    analysis["profitability"]), unsafe_allow_html=True)

st.markdown("<h3>Liquidity Interpretation</h3>", unsafe_allow_html=True)
st.markdown('<div class="analysis-block"><div class="analysis-text"><b>LMR:</b> {}<br><br><b>CFR:</b> {}</div></div>'.format(
    analysis["lmr"], analysis["cfr"]), unsafe_allow_html=True)

st.markdown("<h3>Asset and Liability Quality</h3>", unsafe_allow_html=True)
st.markdown('<div class="analysis-block"><div class="analysis-text">{}<br><br>{}</div></div>'.format(
    analysis["assets"], analysis["liabilities"]), unsafe_allow_html=True)

st.markdown("<h3>Credit Risk and Provisions</h3>", unsafe_allow_html=True)
st.markdown('<div class="prov-sentence">{}</div>'.format(analysis["prov_sentence"]), unsafe_allow_html=True)

st.markdown("<h3>Key Takeaway</h3>", unsafe_allow_html=True)
st.markdown('<div class="analysis-block" style="border-top:2.5px solid #E60028;"><div class="analysis-text">{}</div></div>'.format(
    analysis["executive"]), unsafe_allow_html=True)

# Export
st.markdown('<hr class="rule">', unsafe_allow_html=True)
st.markdown("<h2>Export Report</h2>", unsafe_allow_html=True)
report_html = generate_report_html(d, uploaded.name, ul, mult, analysis)
base = re.sub(r"\.pdf$","", uploaded.name, flags=re.IGNORECASE)
col1,col2 = st.columns(2)
with col1:
    st.download_button(
        "Download Report (HTML)", data=report_html.encode("utf-8"),
        file_name="{}_report.html".format(base), mime="text/html")
with col2:
    export = []
    for label,pair in kf_rows:
        if pair: export.append({"Section":"Key Financials","Item":label,
                                 "Current":pair[0],"Prior":pair[1],"Change%":pct_chg(pair[0],pair[1])})
    if lmr: export.append({"Section":"Liquidity","Item":"Avg LMR (%)","Current":lmr[0],"Prior":lmr[1],"Change pp":lpp})
    if cfr:  export.append({"Section":"Liquidity","Item":"Avg CFR (%)","Current":cfr[0],"Prior":cfr[1],"Change pp":cpp})
    for x in sorted(ai, key=lambda x:x.get("curr") or 0, reverse=True):
        export.append({"Section":"Assets","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),
                       "% of Total":round(x["curr"]/ta[0]*100,2) if ta and x.get("curr") else None})
    for x in sorted(li, key=lambda x:x.get("curr") or 0, reverse=True):
        export.append({"Section":"Liabilities","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),
                       "% of Total":round(x["curr"]/tl[0]*100,2) if tl and x.get("curr") else None})
    csv = pd.DataFrame(export).to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Raw Data (CSV)", data=csv,
        file_name="{}_data.csv".format(base), mime="text/csv")

st.markdown(
    '<div style="font-size:.68rem;color:#aaa;margin-top:8px;">'
    'To save as PDF: open the HTML file in your browser, Print, then Save as PDF.</div>',
    unsafe_allow_html=True)

with st.expander("Debug: raw extracted lines (first 400)"):
    st.text("\n".join(d["raw_lines"][:400]))
