#!/usr/bin/env python3
"""Validate direct-review candidate Q&A against current SEBI primary sources and
promote only high-confidence extractive items to the active mock-test bank.

The script is deliberately conservative:
- only candidates mapped to a named current SEBI rulebook can pass;
- the candidate source context must be evidenced in the current consolidated PDF;
- the source answer must be extractive from that context (derived/calculated answers are
  retained in the audit but are not promoted automatically);
- the existing 370-question bank is preserved and only a new additive bank is written.
"""

from __future__ import annotations

import hashlib
import io
import json
import random
import re
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
AUDIT = ROOT / "audit"
CANDIDATES = DATA / "candidates" / "additional_source_candidates.jsonl"
VALIDATED_JS = DATA / "additional_validated_questions.js"
RESULTS_JSONL = AUDIT / "ADDITIONAL_VALIDATION_RESULTS.jsonl"
REPORT_MD = AUDIT / "ADDITIONAL_VALIDATION_REPORT.md"
VALIDATED_AT = "2026-09-16"

# Current SEBI consolidated primary-source PDFs resolved from SEBI's legal pages on
# 16 September 2026. The PDF month can be newer than the legal-page title because SEBI
# updates the consolidated attachment in place.
RULEBOOKS = {
    "CRA_1999": {
        "match": ["credit rating agencies"],
        "title": "SEBI (Credit Rating Agencies) Regulations, 1999",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1788347189060.pdf",
    },
    "SAST_2011": {
        "match": ["substantial acquisition of shares and takeovers"],
        "title": "SEBI (Substantial Acquisition of Shares and Takeovers) Regulations, 2011",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785911192198.pdf",
    },
    "ICDR_2018": {
        "match": ["issue of capital and disclosure requirements"],
        "title": "SEBI (Issue of Capital and Disclosure Requirements) Regulations, 2018",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/mar-2026/1774592300989.pdf",
    },
    "LODR_2015": {
        "match": ["listing obligations and disclosure requirements"],
        "title": "SEBI (Listing Obligations and Disclosure Requirements) Regulations, 2015",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1784630770711.pdf",
    },
    "AIF_2012": {
        "match": ["alternative investment funds"],
        "title": "SEBI (Alternative Investment Funds) Regulations, 2012",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1785301664601.pdf",
    },
    "INVIT_2014": {
        "match": ["infrastructure investment trusts"],
        "title": "SEBI (Infrastructure Investment Trusts) Regulations, 2014",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1785306756282.pdf",
    },
    "PIT_2015": {
        "match": ["prohibition of insider trading"],
        "title": "SEBI (Prohibition of Insider Trading) Regulations, 2015",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786963663321.pdf",
    },
    "REIT_2014": {
        "match": ["real estate investment trusts"],
        "title": "SEBI (Real Estate Investment Trusts) Regulations, 2014",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/apr-2026/1776685013526.pdf",
    },
    "MUNICIPAL_2015": {
        "match": ["issue and listing of municipal debt securities"],
        "title": "SEBI (Issue and Listing of Municipal Debt Securities) Regulations, 2015",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1784286369601.pdf",
    },
    "RTI_STA_2025": {
        "match": ["registrars to an issue and share transfer agents"],
        "title": "SEBI (Registrars to an Issue and Share Transfer Agents) Regulations, 2025",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/dec-2025/1766125665223.pdf",
    },
    "SECC_2018": {
        "match": ["stock exchanges and clearing corporations"],
        "title": "Securities Contracts (Regulation) (Stock Exchanges and Clearing Corporations) Regulations, 2018",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786956590250.pdf",
    },
    "DP_2018": {
        "match": ["depositories and participants"],
        "title": "SEBI (Depositories and Participants) Regulations, 2018",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786957172778.pdf",
    },
    "MERCHANT_1992": {
        "match": ["merchant bankers"],
        "title": "SEBI (Merchant Bankers) Regulations, 1992",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785910555405.pdf",
    },
    "MF_2026": {
        "match": ["mutual funds"],
        "title": "SEBI (Mutual Funds) Regulations, 2026",
        "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1783933012694.pdf",
        "supersedes": "SEBI (Mutual Funds) Regulations, 1996",
    },
}

STOP = {
    "the","a","an","of","to","and","or","in","for","on","under","with","from","by","as","at",
    "is","are","be","must","shall","what","which","how","who","that","this","it","its","their",
    "least","more","than","not","only","per","cent","rupees","rupee","crore","lakh",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def norm(text: str) -> str:
    text = text.lower().replace("₹", " rs ").replace("–", "-").replace("—", "-")
    text = re.sub(r"\[\s*\d+\s*\]", " ", text)
    text = re.sub(r"[^a-z0-9%]+", " ", text)
    return " ".join(text.split())


def answer_core(text: str) -> str:
    n = norm(text)
    n = re.sub(r"\([^)]*\)", " ", n)
    return " ".join(n.split())


def map_rulebook(source_detail: str) -> str | None:
    low = source_detail.lower()
    for key, meta in RULEBOOKS.items():
        if any(m in low for m in meta["match"]):
            return key
    return None


def download_pdf_text(url: str) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 DirectorMockIndia/1.0"})
    with urllib.request.urlopen(req, timeout=90) as response:
        raw = response.read()
    reader = PdfReader(io.BytesIO(raw))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    text = "\n".join(pages)
    header = " ".join(" ".join(pages[:3]).split())[:700]
    return text, header


def context_evidence(context: str, official_norm: str) -> tuple[float, int, int]:
    tokens = norm(context).split()
    if len(tokens) < 8:
        return 0.0, 0, 0
    width = 8
    starts = list(range(0, max(1, len(tokens) - width + 1), 5))
    if starts and starts[-1] != len(tokens) - width:
        starts.append(max(0, len(tokens) - width))
    # Cap to 30 evenly distributed shingles for very long source contexts.
    if len(starts) > 30:
        idx = [round(i * (len(starts) - 1) / 29) for i in range(30)]
        starts = [starts[i] for i in idx]
    shingles = [" ".join(tokens[s:s+width]) for s in starts]
    matched = sum(1 for sh in shingles if sh in official_norm)
    score = matched / len(shingles) if shingles else 0.0
    return score, matched, len(shingles)


def extractive_answer_supported(answer: str, context: str) -> bool:
    a = answer_core(answer)
    c = norm(context)
    if not a or not c:
        return False
    if a in c:
        return True
    # Some gold answers add harmless lead-in words such as "at least" or "within".
    toks = [t for t in a.split() if t not in STOP]
    if len(toks) >= 2 and " ".join(toks) in c:
        return True
    # Require all distinctive answer tokens to occur for short extractive answers.
    distinct = [t for t in toks if len(t) > 2 or t.isdigit()]
    return bool(distinct) and all(t in c.split() for t in distinct)


def answer_kind(answer: str) -> str:
    a = norm(answer)
    if "%" in a or "per cent" in a or "percent" in a:
        return "percent"
    if any(x in a for x in ["crore", "lakh", "rupee", " rs "]):
        return "money"
    if any(x in a for x in ["day", "month", "year", "week", "hour"]):
        return "duration"
    if any(x in a for x in ["one third", "two thirds", "half", "quarter"]):
        return "fraction"
    if re.fullmatch(r"[a-z ]*\d+[a-z ]*", a):
        return "number"
    return "text"


def tidy_option(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).rstrip(".")


def distractor_pool(items: list[dict]) -> dict[tuple[str, str], list[str]]:
    pools: dict[tuple[str, str], list[str]] = defaultdict(list)
    for item in items:
        key = (item["rulebookKey"], answer_kind(item["answer"]))
        val = tidy_option(item["answer"])
        if val not in pools[key]:
            pools[key].append(val)
    return pools


def fallback_distractors(kind: str) -> list[str]:
    if kind == "percent":
        return ["Ten per cent", "Fifteen per cent", "Fifty per cent", "Seventy-five per cent"]
    if kind == "money":
        return ["One crore rupees", "Five crore rupees", "Ten crore rupees", "Fifty crore rupees"]
    if kind == "duration":
        return ["Thirty days", "Sixty days", "Ninety days", "One hundred and eighty days"]
    if kind == "fraction":
        return ["One-fourth", "One-half", "Two-thirds", "Three-fourths"]
    if kind == "number":
        return ["One", "Two", "Three", "Five"]
    return [
        "The regulations leave the matter entirely to the entity's internal policy",
        "No specific requirement is prescribed under the regulations",
        "The requirement applies only when SEBI issues a case-specific direction",
        "The matter is determined solely by the stock exchange's discretion",
    ]


def make_options(item: dict, pools: dict[tuple[str, str], list[str]]) -> tuple[list[str], int]:
    correct = tidy_option(item["answer"])
    kind = answer_kind(correct)
    candidates = [x for x in pools.get((item["rulebookKey"], kind), []) if norm(x) != norm(correct)]
    candidates += [x for x in fallback_distractors(kind) if norm(x) != norm(correct)]
    unique = []
    seen = {norm(correct)}
    for x in candidates:
        nx = norm(x)
        if not nx or nx in seen:
            continue
        seen.add(nx)
        unique.append(tidy_option(x))
        if len(unique) == 3:
            break
    if len(unique) < 3:
        raise RuntimeError(f"Unable to build distractors for {item['candidateId']}")
    opts = [correct] + unique
    seed = int(hashlib.sha256(item["candidateId"].encode()).hexdigest()[:16], 16)
    rng = random.Random(seed)
    rng.shuffle(opts)
    return opts, opts.index(correct)


def js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def write_validated_js(items: list[dict]) -> None:
    pools = distractor_pool(items)
    rows = []
    for n, item in enumerate(items, 1):
        options, answer_index = make_options(item, pools)
        q = item["question"]
        # The 1996 Mutual Fund Regulations were replaced in 2026. Even when a proposition
        # survives verbatim, do not leave an obsolete rulebook name in the promoted stem.
        if item["rulebookKey"] == "MF_2026":
            q = re.sub(r"SEBI\s*\(Mutual Funds\)\s*Regulations,?\s*1996(?:\s*\(as amended upto 2026\))?",
                       "SEBI (Mutual Funds) Regulations, 2026", q, flags=re.I)
            q = re.sub(r"SEBI Mutual Funds Regulations", "SEBI (Mutual Funds) Regulations, 2026", q, flags=re.I)
        rows.append({
            "id": f"MCQ-ADD-{n:04d}",
            "originalId": item["sourceItemId"],
            "candidateId": item["candidateId"],
            "sourceId": item["sourceKey"],
            "originType": "preexisting_qa_converted",
            "aiGenerated": False,
            "choicesGenerated": "assistant-generated-distractors",
            "sourceMode": "Open-licensed source Q&A validated against a current SEBI consolidated primary source and converted to a four-option MCQ; distractors were created for this tool.",
            "sourceDomain": item["examCategory"],
            "sourceTopic": item["rulebookKey"],
            "category": item["examCategory"],
            "subtopic": RULEBOOKS[item["rulebookKey"]]["title"],
            "difficulty": item["difficulty"],
            "difficultyLabel": {"S":"Simple","M":"Medium","H":"Hard"}.get(item["difficulty"], item["difficulty"]),
            "question": q,
            "options": options,
            "answer": answer_index,
            "explanation": f"Source answer: {tidy_option(item['answer'])}.",
            "reference": RULEBOOKS[item["rulebookKey"]]["url"],
            "examEligible": True,
            "validationRequired": False,
            "reviewed": "primary-source-validated-and-converted-2026-09-16",
            "qualityStatus": "Validated current SEBI source Q&A converted to MCQ",
            "qualityIssues": "",
            "needsCurrentnessReview": False,
            "sourceLicense": item["license"],
            "sourceUrl": item["sourceUrl"],
            "validatedAt": VALIDATED_AT,
            "currentLawSource": RULEBOOKS[item["rulebookKey"]]["url"],
        })
    VALIDATED_JS.write_text("'use strict';\n\nwindow.ADDITIONAL_VALIDATED_QUESTION_BANK=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")


def update_questions_js(promoted: list[dict]) -> None:
    path = DATA / "questions.js"
    text = path.read_text(encoding="utf-8")
    if "INDIAFINBENCH:" not in text:
        insert = """  INDIAFINBENCH: {\n    shortTitle: 'IndiaFinBench', title: 'IndiaFinBench',\n    url: 'https://github.com/Rajveer-code/IndiaFinBench', license: 'CC BY 4.0',\n    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/', author: 'Rajveer Singh Pall / IndiaFinBench contributors',\n    provenance: 'Expert-annotated India financial-regulation Q&A; promoted items were revalidated against current SEBI consolidated primary sources before MCQ conversion.'\n  },\n  INDIAN_REGULATORY_BFSI: {\n    shortTitle: 'Indian Regulatory BFSI Benchmark', title: 'Indian Regulatory BFSI Benchmark v1',\n    url: 'https://github.com/uditjainstjis/indian-regulatory-bfsi-benchmark', license: 'CC BY-SA 4.0',\n    licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0/', author: 'Udit Jain / benchmark contributors',\n    provenance: 'Hand-curated RBI/SEBI benchmark Q&A; promoted SEBI items were revalidated against current SEBI primary sources before MCQ conversion.'\n  },\n"""
        text = text.replace("  RMANI_INDIAN_LEGAL: {", insert + "  RMANI_INDIAN_LEGAL: {")
    if "const ADDITIONAL_VALIDATED_QUESTION_BANK" not in text:
        text = text.replace(
            "const SOURCE_QA_QUESTION_BANK = Array.isArray(window.SOURCE_QA_QUESTION_BANK) ? window.SOURCE_QA_QUESTION_BANK : [];\nconst QUESTION_BANK = [...OPEN_QUESTION_BANK, ...NPTEL_QUESTION_BANK, ...SOURCE_QA_QUESTION_BANK];",
            "const SOURCE_QA_QUESTION_BANK = Array.isArray(window.SOURCE_QA_QUESTION_BANK) ? window.SOURCE_QA_QUESTION_BANK : [];\nconst ADDITIONAL_VALIDATED_QUESTION_BANK = Array.isArray(window.ADDITIONAL_VALIDATED_QUESTION_BANK) ? window.ADDITIONAL_VALIDATED_QUESTION_BANK : [];\nconst QUESTION_BANK = [...OPEN_QUESTION_BANK, ...NPTEL_QUESTION_BANK, ...SOURCE_QA_QUESTION_BANK, ...ADDITIONAL_VALIDATED_QUESTION_BANK];"
        )
    # Replace manifest block from OPEN_BANK_MANIFEST to its terminating }; at EOF.
    total = 370 + len(promoted)
    cat = Counter({"Basic Accountancy":47,"Companies Law":188,"Corporate Governance":61,"Securities Law":74})
    diff = Counter({"H":7,"M":102,"S":261})
    src = Counter({"BHASHABENCH_FINANCE":37,"BHASHABENCH_LEGAL":81,"NPTEL_ETHICAL_CORPORATION":7,"INDIANLEGAL_QA":242,"RMANI_INDIAN_LEGAL":3})
    for x in promoted:
        cat[x["examCategory"]] += 1
        diff[x["difficulty"]] += 1
        src[x["sourceKey"]] += 1
    manifest = {
        "schemaVersion": 7,
        "build": f"V12-current-sebi-validated-{total}",
        "generatedAt": "2026-09-16T00:00:00Z",
        "activeQuestionCount": total,
        "preexistingCount": total,
        "corpusCount": total,
        "sourceOriginalMcqCount": 125,
        "sourceQaConvertedCount": 245 + len(promoted),
        "additionalPrimaryValidatedCount": len(promoted),
        "bhashaActiveCount": 118,
        "nptelImportedCount": 7,
        "indianLegalQaConvertedCount": 242,
        "rmaniConvertedCount": 3,
        "retiredAfterValidationCount": 13,
        "validationRequiredCount": 0,
        "sourceQualityPassCount": total,
        "aiQuestionCount": 0,
        "assistantGeneratedDistractorQuestionCount": 245 + len(promoted),
        "categoryCounts": dict(cat),
        "difficultyCounts": dict(diff),
        "sourceCounts": dict(src),
        "policy": f"V12 contains the prior 370 validated sourced questions plus {len(promoted)} additional open-licensed source Q&A items revalidated against current SEBI consolidated primary sources on 16 September 2026 and converted to MCQ. No active question stem is AI-authored; converted items use assistant-generated distractors and are explicitly labelled as such.",
    }
    js_manifest = "window.OPEN_BANK_MANIFEST = " + json.dumps(manifest, ensure_ascii=False, indent=2) + ";\n"
    text = re.sub(r"window\.OPEN_BANK_MANIFEST\s*=\s*\{.*?\n\};\s*$", js_manifest, text, flags=re.S)
    path.write_text(text, encoding="utf-8")
    (DATA / "bank_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_wiring(promoted_count: int) -> None:
    total = 370 + promoted_count
    idx = ROOT / "index.html"
    text = idx.read_text(encoding="utf-8")
    text = re.sub(r"using \d+ validated sourced questions", f"using {total} validated sourced questions", text)
    if 'data/additional_validated_questions.js' not in text:
        text = text.replace('  <script src="data/questions.js"></script>', '  <script src="data/additional_validated_questions.js"></script>\n  <script src="data/questions.js"></script>')
    idx.write_text(text, encoding="utf-8")

    sw = ROOT / "sw.js"
    s = sw.read_text(encoding="utf-8")
    s = re.sub(r"const CACHE='[^']+';", f"const CACHE='director-mock-v12-sebi-{total}';", s)
    if "data/additional_validated_questions.js" not in s:
        s = s.replace("'data/questions.js'", "'data/additional_validated_questions.js','data/questions.js'")
    sw.write_text(s, encoding="utf-8")


def update_docs(promoted: list[dict], results: list[dict], headers: dict[str, str]) -> None:
    total = 370 + len(promoted)
    readme = ROOT / "README.md"
    if readme.exists():
        t = readme.read_text(encoding="utf-8")
        t = re.sub(r"370 validated sourced questions", f"{total} validated sourced questions", t)
        t = re.sub(r"370-question", f"{total}-question", t)
        if "Additional current-SEBI validation" not in t:
            t += f"\n## Additional current-SEBI validation\n\nOn 16 September 2026, {len(promoted)} additional open-licensed source Q&A items were promoted only after matching their source proposition to current consolidated SEBI primary-source text. Derived/calculated and unmapped items were not auto-promoted.\n"
        readme.write_text(t, encoding="utf-8")

    sources = ROOT / "SOURCES.md"
    st = sources.read_text(encoding="utf-8")
    if "## IndiaFinBench" not in st:
        st += "\n## IndiaFinBench — additional validated conversions\n- https://github.com/Rajveer-code/IndiaFinBench\n- Licence: CC BY 4.0\n- Only items revalidated against current SEBI consolidated primary sources are loaded into the active bank.\n\n## Indian Regulatory BFSI Benchmark v1 — additional validated conversions\n- https://github.com/uditjainstjis/indian-regulatory-bfsi-benchmark\n- Licence: CC BY-SA 4.0\n- ShareAlike applies to adapted benchmark-derived items. Only current-SEBI-validated items are active.\n"
        sources.write_text(st, encoding="utf-8")

    lic = ROOT / "QUESTION_BANK_LICENSE.md"
    if lic.exists():
        lt = lic.read_text(encoding="utf-8")
        if "IndiaFinBench" not in lt:
            lt += "\n## Additional source licences\n- IndiaFinBench: CC BY 4.0.\n- Indian Regulatory BFSI Benchmark v1: CC BY-SA 4.0; adapted MCQ conversions are distributed subject to the source ShareAlike terms.\n"
            lic.write_text(lt, encoding="utf-8")

    status_counts = Counter(r["status"] for r in results)
    by_rule = Counter(x["rulebookKey"] for x in promoted)
    by_source = Counter(x["sourceKey"] for x in promoted)
    lines = [
        "# Additional candidate current-law validation",
        "",
        f"Validation date: **{VALIDATED_AT}**",
        "",
        f"Direct-review candidates assessed: **{len(results)}**",
        f"Promoted into the active bank: **{len(promoted)}**",
        f"Active bank after promotion: **{total}**",
        "",
        "## Validation policy",
        "Only candidates mapped to a named SEBI rulebook, evidenced in the current consolidated SEBI PDF, and whose answer is extractive from the evidenced source context are auto-promoted. Derived/calculated answers and generic/unmapped circular extracts remain candidates rather than being silently treated as validated.",
        "",
        "## Status counts",
    ]
    for k,v in sorted(status_counts.items()):
        lines.append(f"- {k}: {v}")
    lines += ["", "## Promoted by rulebook"]
    for k,v in sorted(by_rule.items()):
        lines.append(f"- {k}: {v}")
    lines += ["", "## Promoted by source"]
    for k,v in sorted(by_source.items()):
        lines.append(f"- {k}: {v}")
    lines += ["", "## Primary sources used"]
    used = sorted({x["rulebookKey"] for x in promoted})
    for key in used:
        lines.append(f"- {key}: {RULEBOOKS[key]['url']}")
        if headers.get(key):
            lines.append(f"  - PDF header excerpt: {headers[key][:220]}")
    lines += ["", "## Important exclusions", "- Generic `SEBI` / master-circular snippets without a precise current rulebook mapping were not promoted.", "- Calculated/derived benchmark answers were not auto-promoted even when their source context matched current law; they remain available for a later manual calculation review.", "- Mutual-fund items were validated against the 2026 Regulations rather than treating the superseded 1996 title as current.", ""]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    candidates = [x for x in read_jsonl(CANDIDATES) if x.get("disposition") == "DIRECT_REVIEW"]
    official_text: dict[str, str] = {}
    headers: dict[str, str] = {}
    download_errors: dict[str, str] = {}

    needed = sorted({k for x in candidates if (k := map_rulebook(x.get("sourceDetail", "")))})
    for key in needed:
        try:
            text, header = download_pdf_text(RULEBOOKS[key]["url"])
            official_text[key] = norm(text)
            headers[key] = header
            print(key, "pdf chars", len(text))
        except Exception as exc:
            download_errors[key] = f"{type(exc).__name__}: {exc}"
            print(key, "DOWNLOAD_ERROR", download_errors[key])

    results = []
    promoted = []
    for item in candidates:
        row = dict(item)
        key = map_rulebook(item.get("sourceDetail", ""))
        row["rulebookKey"] = key
        if not key:
            row.update(status="REJECT_NO_PRIMARY_SOURCE_MAPPING", contextEvidenceScore=0.0)
            results.append(row)
            continue
        if key in download_errors:
            row.update(status="HOLD_PRIMARY_SOURCE_DOWNLOAD_ERROR", contextEvidenceScore=0.0, error=download_errors[key])
            results.append(row)
            continue
        score, matched, sampled = context_evidence(item.get("context", ""), official_text[key])
        row["contextEvidenceScore"] = round(score, 4)
        row["matchedContextShingles"] = matched
        row["sampledContextShingles"] = sampled
        row["currentLawSource"] = RULEBOOKS[key]["url"]
        row["currentRulebookTitle"] = RULEBOOKS[key]["title"]
        if matched < 2 or score < 0.18:
            row["status"] = "REJECT_CURRENT_TEXT_NOT_EVIDENCED"
            results.append(row)
            continue
        if not extractive_answer_supported(item.get("answer", ""), item.get("context", "")):
            row["status"] = "HOLD_DERIVED_OR_NONEXTRACTIVE_ANSWER"
            results.append(row)
            continue
        row["status"] = "PASS_PRIMARY_SOURCE_EXTRACTIVE"
        results.append(row)
        promoted.append(row)

    # Stable ordering and IDs.
    promoted.sort(key=lambda x: x["candidateId"])
    RESULTS_JSONL.write_text("".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n" for x in results), encoding="utf-8")
    write_validated_js(promoted)
    update_questions_js(promoted)
    update_wiring(len(promoted))
    update_docs(promoted, results, headers)

    print(json.dumps({
        "directReviewed": len(candidates),
        "promoted": len(promoted),
        "activeTotal": 370 + len(promoted),
        "statuses": dict(Counter(x["status"] for x in results)),
        "promotedByRulebook": dict(Counter(x["rulebookKey"] for x in promoted)),
        "downloadErrors": download_errors,
    }, indent=2))


if __name__ == "__main__":
    main()
