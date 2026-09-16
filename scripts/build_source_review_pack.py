#!/usr/bin/env python3
from __future__ import annotations

import csv, json, re, sys, unicodedata
from pathlib import Path
from urllib.parse import quote
import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "review_pack"
RAW = OUT / "raw"
RAW.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "DirectorMockIndia-source-review/1.0"}

SOURCE_REGISTRY = [
    {
        "source_id": "SAKIB_INDIANLEGAL_QA",
        "title": "IndianLegal-QA",
        "url": "https://huggingface.co/datasets/Sakib-Dalal/IndianLegal-QA",
        "license": "Apache-2.0",
        "author": "Sakib Dalal",
        "format": "Q&A dataset",
        "status": "OPEN_REUSE",
    },
    {
        "source_id": "RMANI_INDIAN_LEGAL",
        "title": "Indian Legal Dataset - Indian Law",
        "url": "https://huggingface.co/datasets/RMani1/indian-legal-dataset-indian-law",
        "license": "MIT",
        "author": "RMani1",
        "format": "Q&A dataset",
        "status": "OPEN_REUSE",
    },
    {
        "source_id": "NPTEL_ETHICAL_CORPORATION",
        "title": "The Ethical Corporation",
        "url": "https://archive.nptel.ac.in/noc/courses/noc19/SEM2/noc19-mg56/",
        "license": "CC BY-NC-SA",
        "author": "NPTEL / IIT Kharagpur",
        "format": "Assignment MCQs",
        "status": "OPEN_REUSE_NONCOMMERCIAL",
    },
    {
        "source_id": "NPTEL_BUSINESS_LAW_MANAGERS",
        "title": "Business Law for Managers",
        "url": "https://onlinecourses.nptel.ac.in/noc21_mg100/preview",
        "license": "CC BY-NC-SA",
        "author": "NPTEL / IIT Kharagpur",
        "format": "Assignment MCQs",
        "status": "OPEN_REUSE_NONCOMMERCIAL",
    },
    {
        "source_id": "NPTEL_CSR",
        "title": "Corporate Social Responsibility",
        "url": "https://archive.nptel.ac.in/content/syllabus_pdf/110105081.pdf",
        "license": "CC BY-NC-SA",
        "author": "NPTEL / IIT Kharagpur",
        "format": "Assignment MCQs",
        "status": "OPEN_REUSE_NONCOMMERCIAL",
    },
]

RESTRICTED_SOURCES = [
    ("Testbook - Company Law", "https://testbook.com/objective-questions/mcq-on-company-law--65e74199de8e76b6f2931c37", "Provider advertises free solution PDFs but current download route redirects to sign-up/login; do not bypass."),
    ("Testbook - The Companies Act", "https://testbook.com/objective-questions/mcq-on-the-companies-act--61795bef73f974b13f8e4b2a", "Provider advertises free PDF; account-gated download flow observed."),
    ("Testbook - Corporate Governance", "https://testbook.com/objective-questions/mcq-on-corporate-governance--66f699317b967dbbc5c11b07", "Relevant MCQs; provider download/reuse restrictions apply."),
    ("Scribd - IICA Independent Director Exam 500 Full", "https://www.scribd.com/document/1074668343/IICA-Independent-Director-Exam-500-Full", "Download only if uploader enables it and account permits; no open redistribution licence."),
    ("Scribd - 50-question Independent Director mock", "https://www.scribd.com/document/887310608/Free-Mock-on-Independent-Directors-Exam-With-Answer-Key-50-Questio", "Document is marked all-rights-reserved; no open reuse."),
    ("Filebob Independent Director Mock Test", "https://filebob.in/independent_director_mocktest/index.php", "Terms prohibit unauthorized copying/distribution."),
    ("SkillArbitrage Independent Director", "https://skillarbitra.ge/v24-professionals-independent-directors/", "Course material restricted to personal use; no open reuse licence."),
    ("Udemy - IICA mock tests", "https://www.udemy.com/course/independent-directors-exam-prep-indian-iica-mock-tests/", "Offline access may be encrypted/in-app; no open reuse."),
    ("Udemy - Independent Director Exam Preparation", "https://www.udemy.com/course/independent-director-exam-preparation/", "Proprietary instructor content; no open reuse."),
    ("ImportantMCQ - SEBI LODR & Corporate Governance", "https://importantmcq.com/mcq-module/sebi-lodr-corporate-governance-frameworks/?pid=124", "Relevant public page but no open redistribution licence found."),
    ("Dynamic Tutorials - Board of Directors", "https://www.dynamictutorialsandservices.org/2021/08/mcqs-on-board-of-directors-company-law.html", "No open licence found; also potentially stale."),
    ("EduRev Corporate Governance", "https://edurev.in/course/quiz/-1_test/9f9e9cd6-608e-474f-befd-699ba9670d4e", "User-contributed/proprietary content; provenance not safe for reuse."),
    ("McqMate Corporate Laws", "https://mcqmate.com/index.php/topic/corporate-laws", "No open redistribution licence found; substantial historical Companies Act 1956 content."),
]

STRONG = [
    "companies act", "independent director", "board of directors", "memorandum of association", "articles of association",
    "corporate social responsibility", "corporate governance", "audit committee", "nomination and remuneration committee",
    "related party transaction", "key managerial personnel", "registrar of companies", "nclt", "nclat", "sebi",
    "securities and exchange board", "insider trading", "lodr", "listing obligations", "icdr", "takeover", "depositories act",
    "securities contracts", "oppression", "mismanagement", "prospectus", "debenture", "share capital", "winding up",
]
MEDIUM = [
    "director", "shareholder", "annual general meeting", "extraordinary general meeting", "company secretary", "auditor",
    "financial statement", "annual report", "dividend", "board meeting", "stakeholder", "csr", "governance",
]

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

def relevance(text: str):
    t = norm(text)
    strong = [k for k in STRONG if k in t]
    medium = [k for k in MEDIUM if k in t]
    score = len(strong) * 5 + len(medium) * 2
    direct = "HIGH" if strong else ("MEDIUM" if medium else "LOW")
    return score, direct, strong + medium

def topic(text: str) -> str:
    t = norm(text)
    if any(k in t for k in ["sebi", "insider trading", "lodr", "icdr", "takeover", "depositor", "securities"]): return "Securities Law"
    if any(k in t for k in ["corporate governance", "audit committee", "stakeholder", "board", "independent director", "csr", "corporate social responsibility"]): return "Corporate Governance"
    if any(k in t for k in ["financial statement", "accounting", "auditor", "audit", "dividend", "amortization"]): return "Basic Accountancy"
    return "Companies Law"

def difficulty(q: str) -> str:
    t = norm(q)
    if len(q) > 280 or any(k in t for k in ["scenario", "case", "consider the following", "match list", "assertion", "arrange"]): return "H"
    if any(k in t for k in ["within", "minimum", "maximum", "threshold", "percentage", "term", "section", "condition", "which of the following"]): return "M"
    return "S"

def validation_status(text: str, source_id: str) -> str:
    t = norm(text)
    if source_id.startswith("NPTEL") and not any(k in t for k in ["section", "companies act", "sebi", "law", "regulation", "days", "percent", "crore", "director"]):
        return "CONCEPTUAL_REVIEW"
    return "NEEDS_CURRENT_LAW_VALIDATION"

def hf_download(repo: str, preferred: list[str], dest: Path) -> Path | None:
    info = requests.get(f"https://huggingface.co/api/datasets/{repo}", headers=UA, timeout=60)
    info.raise_for_status()
    siblings = [s.get("rfilename") for s in info.json().get("siblings", []) if s.get("rfilename")]
    chosen = None
    for p in preferred:
        for s in siblings:
            if s == p or s.endswith(p): chosen = s; break
        if chosen: break
    if not chosen:
        for s in siblings:
            if Path(s).suffix.lower() in {".csv", ".json", ".jsonl", ".txt"} and "readme" not in s.lower():
                chosen = s; break
    if not chosen: return None
    url = f"https://huggingface.co/datasets/{repo}/resolve/main/{quote(chosen)}?download=true"
    r = requests.get(url, headers=UA, timeout=180)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest

def load_existing_questions() -> set[str]:
    out = set()
    for path, var in [(ROOT / "data/open_questions.js", "OPEN_QUESTION_BANK"), (ROOT / "data/nptel_questions.js", "NPTEL_QUESTION_BANK")]:
        if not path.exists(): continue
        txt = path.read_text(encoding="utf-8")
        m = re.search(rf"window\.{var}\s*=\s*(\[.*?\]);", txt, re.S)
        if m:
            try:
                for q in json.loads(m.group(1)):
                    out.add(norm(q.get("question") or q.get("q") or ""))
            except Exception:
                pass
    return out

def append_candidate(rows, seen, existing, *, source_id, source_title, source_url, source_license, source_author, fmt, question, answer, source_item="", raw_text=""):
    qn = norm(question)
    if not qn or len(qn) < 12 or qn in seen or qn in existing: return
    score, direct, keys = relevance(question + " " + answer)
    if score < 2: return
    seen.add(qn)
    rows.append({
        "candidate_id": f"SRC-{len(rows)+1:05d}",
        "source_id": source_id,
        "source_title": source_title,
        "source_url": source_url,
        "source_license": source_license,
        "source_author_or_institution": source_author,
        "origin_type": "preexisting_verbatim_mcq" if fmt == "MCQ" else "source_qa",
        "format": fmt,
        "question": re.sub(r"\s+", " ", question).strip(),
        "answer": re.sub(r"\s+", " ", answer).strip(),
        "topic": topic(question + " " + answer),
        "difficulty": difficulty(question),
        "directness": direct,
        "relevance_score": score,
        "matched_terms": "; ".join(keys[:12]),
        "law_validation_status": validation_status(question + " " + answer, source_id),
        "import_status": "REVIEW_ONLY_NOT_IMPORTED",
        "ai_generated": "NO",
        "choices_generated": "source-original" if fmt == "MCQ" else "not-applicable",
        "source_item": source_item,
        "raw_excerpt": re.sub(r"\s+", " ", raw_text).strip()[:1000],
    })

def parse_sakib(path: Path, rows, seen, existing):
    with path.open(encoding="utf-8-sig", newline="", errors="replace") as f:
        rd = csv.DictReader(f)
        for rec in rd:
            q = rec.get("question") or rec.get("instruction") or ""
            a = rec.get("answer") or rec.get("output") or ""
            append_candidate(rows, seen, existing, source_id="SAKIB_INDIANLEGAL_QA", source_title="IndianLegal-QA", source_url="https://huggingface.co/datasets/Sakib-Dalal/IndianLegal-QA", source_license="Apache-2.0", source_author="Sakib Dalal", fmt="Q&A", question=q, answer=a)

def parse_rmani(path: Path, rows, seen, existing):
    text = path.read_text(encoding="utf-8", errors="replace")
    data = None
    try: data = json.loads(text)
    except Exception: pass
    items = []
    if isinstance(data, list): items = data
    elif isinstance(data, dict): items = data.get("data") or data.get("train") or []
    else:
        for line in text.splitlines():
            try: items.append(json.loads(line))
            except Exception: pass
    for rec in items:
        if not isinstance(rec, dict): continue
        q = rec.get("instruction") or rec.get("question") or rec.get("prompt") or ""
        a = rec.get("output") or rec.get("answer") or rec.get("response") or ""
        append_candidate(rows, seen, existing, source_id="RMANI_INDIAN_LEGAL", source_title="Indian Legal Dataset - Indian Law", source_url="https://huggingface.co/datasets/RMani1/indian-legal-dataset-indian-law", source_license="MIT", source_author="RMani1", fmt="Q&A", question=q, answer=a)

def download_nptel(course_id: str, source_id: str, source_title: str, source_url: str, rows, seen, existing):
    d = RAW / source_id.lower(); d.mkdir(parents=True, exist_ok=True)
    for week in range(1, 9):
        url = f"https://archive.nptel.ac.in/content/storage2/courses/downloads_new/{course_id}/Week_{week:02d}_Assignment_{week:02d}.pdf"
        try:
            r = requests.get(url, headers=UA, timeout=60)
            if r.status_code != 200 or not r.content.startswith(b"%PDF"): continue
            p = d / f"week_{week:02d}.pdf"; p.write_bytes(r.content)
            reader = PdfReader(str(p)); text = "\n".join((pg.extract_text() or "") for pg in reader.pages)
            starts = list(re.finditer(r"(?m)^\s*(\d{1,2})\)\s+", text))
            for i, m in enumerate(starts):
                block = text[m.start(): starts[i+1].start() if i+1 < len(starts) else len(text)]
                ans = ""
                am = re.search(r"Accepted Answers?:\s*(.*?)(?=\n\s*(?:Lecture|Quiz|Feedback|$))", block, re.S | re.I)
                if am: ans = am.group(1).strip()
                core = re.split(r"No, the answer is incorrect|Accepted Answers?:", block, maxsplit=1, flags=re.I)[0]
                core = re.sub(r"^\s*\d{1,2}\)\s*", "", core).strip()
                if len(core) < 20: continue
                append_candidate(rows, seen, existing, source_id=source_id, source_title=source_title, source_url=url, source_license="CC BY-NC-SA", source_author="NPTEL / IIT Kharagpur", fmt="MCQ", question=core, answer=ans or "Accepted answer not reliably extracted; review source PDF", source_item=f"Week {week}", raw_text=block)
        except Exception as e:
            print("NPTEL download/parse warning", source_id, week, e, file=sys.stderr)

def write_csv(path: Path, rows: list[dict]):
    if not rows: return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

def main():
    existing = load_existing_questions(); seen = set(); rows = []
    sakib = RAW / "IndianLegal-QA.csv"
    try:
        hf_download("Sakib-Dalal/IndianLegal-QA", ["question_answers.csv"], sakib)
        parse_sakib(sakib, rows, seen, existing)
    except Exception as e: print("Sakib warning", e, file=sys.stderr)

    rmani = RAW / "RMani1.json"
    try:
        p = hf_download("RMani1/indian-legal-dataset-indian-law", ["dataset.json", "train.json", "data.json", ".json"], rmani)
        if p: parse_rmani(p, rows, seen, existing)
    except Exception as e: print("RMani warning", e, file=sys.stderr)

    download_nptel("110105138", "NPTEL_ETHICAL_CORPORATION", "The Ethical Corporation", "https://archive.nptel.ac.in/noc/courses/noc19/SEM2/noc19-mg56/", rows, seen, existing)
    download_nptel("110105159", "NPTEL_BUSINESS_LAW_MANAGERS", "Business Law for Managers", "https://onlinecourses.nptel.ac.in/noc21_mg100/preview", rows, seen, existing)
    download_nptel("110105081", "NPTEL_CSR", "Corporate Social Responsibility", "https://archive.nptel.ac.in/content/syllabus_pdf/110105081.pdf", rows, seen, existing)

    rows.sort(key=lambda r: (-int(r["relevance_score"]), r["source_id"], r["question"]))
    for i, r in enumerate(rows, 1): r["candidate_id"] = f"SRC-{i:05d}"

    write_csv(OUT / "review_questions.csv", rows)
    (OUT / "review_questions.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "sources.json").write_text(json.dumps(SOURCE_REGISTRY, ensure_ascii=False, indent=2), encoding="utf-8")
    restricted = [{"source": a, "url": b, "status": "NOT_DOWNLOADED", "reason": c} for a,b,c in RESTRICTED_SOURCES]
    write_csv(OUT / "restricted_provider_sources.csv", restricted)
    summary = {
        "generated_at": "2026-09-16",
        "candidate_count": len(rows),
        "existing_bank_normalized_questions": len(existing),
        "ai_generated_count": 0,
        "source_counts": {},
        "topic_counts": {},
        "validation_counts": {},
        "restricted_source_count": len(restricted),
    }
    for r in rows:
        summary["source_counts"][r["source_id"]] = summary["source_counts"].get(r["source_id"],0)+1
        summary["topic_counts"][r["topic"]] = summary["topic_counts"].get(r["topic"],0)+1
        summary["validation_counts"][r["law_validation_status"]] = summary["validation_counts"].get(r["law_validation_status"],0)+1
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__": main()
