#!/usr/bin/env python3
"""Extract additional open/licensed source questions into a review-only candidate pack.

This script MUST NOT modify the active 370-question mock-test bank. It writes only
under data/candidates/ and audit/.
"""

from __future__ import annotations

import csv
import io
import json
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "candidates"
AUDIT = ROOT / "audit"
OUT.mkdir(parents=True, exist_ok=True)
AUDIT.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "INDIAFINBENCH": {
        "url": "https://raw.githubusercontent.com/Rajveer-code/IndiaFinBench/main/data/benchmark/indiafinbench_v1.csv",
        "project": "https://github.com/Rajveer-code/IndiaFinBench",
        "license": "CC BY 4.0",
        "attribution": "IndiaFinBench — Rajveer Singh Pall",
    },
    "INDIAN_REGULATORY_BFSI": {
        "url": "https://raw.githubusercontent.com/uditjainstjis/indian-regulatory-bfsi-benchmark/main/questions.jsonl",
        "project": "https://github.com/uditjainstjis/indian-regulatory-bfsi-benchmark",
        "license": "CC BY-SA 4.0",
        "attribution": "Indian Regulatory BFSI Benchmark v1 — Udit Jain",
    },
}

CORE_SECURITIES_TERMS = (
    "listing obligations", "lodr", "substantial acquisition", "takeover",
    "prohibition of insider trading", "insider trading", "issue of capital and disclosure",
    "icdr", "depositories", "securities contracts", "stock exchange",
    "sebi act", "related party transaction", "material subsidiary",
    "credit rating agenc", "registrars to an issue", "share transfer agent",
)
GOVERNANCE_TERMS = (
    "audit committee", "independent director", "board of directors", "board composition",
    "nomination and remuneration", "stakeholders relationship", "related party transaction",
    "corporate governance", "woman director", "director", "key managerial personnel",
)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "DirectorMockIndia-source-extractor/1.0"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read().decode("utf-8-sig", errors="replace")


def normalize(text: str) -> str:
    text = text.lower().replace("₹", "rs ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def token_jaccard(a: str, b: str) -> float:
    aa, bb = set(normalize(a).split()), set(normalize(b).split())
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def collect_active_questions() -> list[str]:
    texts: list[str] = []
    files = [ROOT / "data" / "open_questions.js", ROOT / "data" / "nptel_questions.js"]
    files += sorted((ROOT / "data").glob("source_qa_*.js"))
    patterns = [
        re.compile(r'"q"\s*:\s*"((?:\\.|[^"\\])*)"'),
        re.compile(r'"question"\s*:\s*"((?:\\.|[^"\\])*)"'),
        re.compile(r"question\s*:\s*'((?:\\.|[^'\\])*)'"),
    ]
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in patterns:
            for match in pattern.finditer(text):
                raw = match.group(1)
                try:
                    if pattern.pattern.startswith('"'):
                        value = json.loads('"' + raw + '"')
                    else:
                        value = raw.replace("\\'", "'").replace("\\n", " ")
                except Exception:
                    value = raw
                if len(value.strip()) >= 12:
                    texts.append(value.strip())
    # normalized de-duplication
    unique = {}
    for t in texts:
        unique.setdefault(normalize(t), t)
    return list(unique.values())


def duplicate_status(question: str, active: list[str], accepted: list[dict]) -> tuple[str, str | None, float]:
    nq = normalize(question)
    for existing in active:
        if nq == normalize(existing):
            return "EXACT_ACTIVE_DUPLICATE", "ACTIVE_BANK", 1.0
    for item in accepted:
        if nq == normalize(item["question"]):
            return "EXACT_CANDIDATE_DUPLICATE", item["candidateId"], 1.0

    best_score = 0.0
    best_id = None
    # Cheap token similarity is adequate for review-pack de-duplication.
    for existing in active:
        score = token_jaccard(question, existing)
        if score > best_score:
            best_score, best_id = score, "ACTIVE_BANK"
    for item in accepted:
        score = token_jaccard(question, item["question"])
        if score > best_score:
            best_score, best_id = score, item["candidateId"]
    if best_score >= 0.88:
        return "NEAR_DUPLICATE", best_id, round(best_score, 4)
    return "UNIQUE", None, round(best_score, 4)


def map_difficulty(value: str | None, fallback: str = "M") -> str:
    v = (value or "").strip().lower()
    if v in {"easy", "simple", "s", "1"}:
        return "S"
    if v in {"hard", "h", "3"}:
        return "H"
    if v in {"medium", "moderate", "m", "2"}:
        return "M"
    return fallback


def classify_sebi(text: str) -> tuple[str, str]:
    low = text.lower()
    category = "Corporate Governance" if any(k in low for k in GOVERNANCE_TERMS) else "Securities Law"
    if any(k in low for k in CORE_SECURITIES_TERMS) or category == "Corporate Governance":
        return "DIRECT_REVIEW", category
    return "SUPPLEMENTARY_REVIEW", category


def make_base(*, source_key: str, source_id: str, question: str, answer: str, context: str,
              difficulty: str, source_detail: str, task_type: str, disposition: str,
              category: str, ordinal: int) -> dict:
    src = SOURCES[source_key]
    return {
        "candidateId": f"CAND-{source_key}-{ordinal:04d}",
        "sourceKey": source_key,
        "sourceItemId": source_id,
        "question": question.strip(),
        "answer": answer.strip(),
        "context": context.strip(),
        "sourceDetail": source_detail.strip(),
        "sourceTaskType": task_type,
        "examCategory": category,
        "difficulty": difficulty,
        "disposition": disposition,
        "originType": "preexisting_source_qa",
        "conversionNeeded": "QA_TO_4_OPTION_MCQ",
        "questionStemAiAuthored": False,
        "distractorsPresent": False,
        "currentLawValidationRequired": True,
        "sourceUrl": src["project"],
        "license": src["license"],
        "attribution": src["attribution"],
    }


def extract_indiafinbench() -> list[dict]:
    text = fetch_text(SOURCES["INDIAFINBENCH"]["url"])
    rows = list(csv.DictReader(io.StringIO(text)))
    out: list[dict] = []
    for i, row in enumerate(rows, 1):
        regulator = (row.get("source") or "").strip().upper()
        combined = " ".join([
            row.get("regulation") or "", row.get("question") or "", row.get("context") or ""
        ])
        if regulator == "SEBI":
            disposition, category = classify_sebi(combined)
        else:
            disposition, category = "REJECT_OUT_OF_EXAM_SCOPE", "Securities Law"
        out.append(make_base(
            source_key="INDIAFINBENCH",
            source_id=row.get("id") or f"row-{i}",
            question=row.get("question") or "",
            answer=row.get("answer") or row.get("reference_answer") or "",
            context=row.get("context") or "",
            difficulty=map_difficulty(row.get("difficulty")),
            source_detail=row.get("regulation") or regulator,
            task_type=row.get("task_type") or row.get("answer_type") or "QA",
            disposition=disposition,
            category=category,
            ordinal=i,
        ))
    return out


def extract_regulatory_bfsi() -> list[dict]:
    text = fetch_text(SOURCES["INDIAN_REGULATORY_BFSI"]["url"])
    out: list[dict] = []
    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        regulator = str(row.get("regulator") or "").strip().upper()
        combined = " ".join([
            str(row.get("source_section") or ""), str(row.get("question") or ""),
            str(row.get("context") or ""), str(row.get("topic_tag") or "")
        ])
        if regulator == "SEBI":
            disposition, category = classify_sebi(combined)
        else:
            disposition, category = "REJECT_OUT_OF_EXAM_SCOPE", "Securities Law"
        out.append(make_base(
            source_key="INDIAN_REGULATORY_BFSI",
            source_id=str(row.get("benchmark_id") or f"row-{i}"),
            question=str(row.get("question") or ""),
            answer=str(row.get("gold_answer") or ""),
            context=str(row.get("context") or ""),
            difficulty=map_difficulty(str(row.get("difficulty") or "")),
            source_detail=" | ".join(x for x in [str(row.get("source_section") or ""), str(row.get("topic_tag") or "")] if x),
            task_type=f"tier-{row.get('tier', '')}",
            disposition=disposition,
            category=category,
            ordinal=i,
        ))
    return out


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def main() -> None:
    active = collect_active_questions()
    extracted = extract_indiafinbench() + extract_regulatory_bfsi()

    candidates: list[dict] = []
    excluded: list[dict] = []
    for item in extracted:
        if not item["question"] or not item["answer"]:
            item["disposition"] = "REJECT_MISSING_QA"
        status, duplicate_of, similarity = duplicate_status(item["question"], active, candidates)
        item["duplicateStatus"] = status
        item["duplicateOf"] = duplicate_of
        item["maxQuestionSimilarity"] = similarity
        if item["disposition"] in {"DIRECT_REVIEW", "SUPPLEMENTARY_REVIEW"} and status == "UNIQUE":
            candidates.append(item)
        else:
            excluded.append(item)

    # Cross-source exact de-dupe safety by normalized stem.
    seen = set()
    unique_candidates = []
    for item in candidates:
        key = normalize(item["question"])
        if key in seen:
            item["duplicateStatus"] = "EXACT_CANDIDATE_DUPLICATE"
            excluded.append(item)
            continue
        seen.add(key)
        unique_candidates.append(item)
    candidates = unique_candidates

    by_source = Counter(x["sourceKey"] for x in candidates)
    by_disp = Counter(x["disposition"] for x in candidates)
    by_cat = Counter(x["examCategory"] for x in candidates)
    by_diff = Counter(x["difficulty"] for x in candidates)
    extracted_by_source = Counter(x["sourceKey"] for x in extracted)
    excluded_by_reason = Counter(
        x["disposition"] if x.get("duplicateStatus") == "UNIQUE" else x.get("duplicateStatus", "UNKNOWN")
        for x in excluded
    )

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    manifest = {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "mode": "SOURCE_ONLY_CANDIDATE_PACK",
        "activeBankModified": False,
        "activeBankExpectedCount": 370,
        "activeQuestionTextsObservedForDedup": len(active),
        "sources": SOURCES,
        "totalExtracted": len(extracted),
        "reviewCandidateCount": len(candidates),
        "excludedOrDuplicateCount": len(excluded),
        "candidateCountsBySource": dict(sorted(by_source.items())),
        "extractedCountsBySource": dict(sorted(extracted_by_source.items())),
        "candidateCountsByDisposition": dict(sorted(by_disp.items())),
        "candidateCountsByCategory": dict(sorted(by_cat.items())),
        "candidateCountsByDifficulty": dict(sorted(by_diff.items())),
        "excludedCountsByReason": dict(sorted(excluded_by_reason.items())),
        "aiAuthoredQuestionStemCount": 0,
        "promotionPolicy": "No candidate is active. Each item requires current-law validation and QA-to-MCQ conversion before any later promotion into the mock-test bank.",
    }

    write_jsonl(OUT / "additional_source_candidates.jsonl", candidates)
    write_jsonl(OUT / "additional_source_excluded.jsonl", excluded)
    (OUT / "candidate_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Additional open-source question extraction",
        "",
        f"Generated: {generated_at}",
        "",
        "This is a **review-only candidate pack**. The active 370-question bank is not modified.",
        "",
        "## Result",
        f"- Source items extracted: **{len(extracted)}**",
        f"- Unique candidates retained for review: **{len(candidates)}**",
        f"- Excluded / duplicate / out-of-scope items: **{len(excluded)}**",
        "- AI-authored question stems: **0**",
        "- Every retained regulatory item is flagged for current-law validation before promotion.",
        "",
        "## Retained candidates by source",
    ]
    for key, count in sorted(by_source.items()):
        lines.append(f"- {key}: {count}")
    lines += ["", "## Retained candidates by exam category"]
    for key, count in sorted(by_cat.items()):
        lines.append(f"- {key}: {count}")
    lines += ["", "## Retained candidates by review disposition"]
    for key, count in sorted(by_disp.items()):
        lines.append(f"- {key}: {count}")
    lines += ["", "## Excluded / duplicate reasons"]
    for key, count in sorted(excluded_by_reason.items()):
        lines.append(f"- {key}: {count}")
    lines += [
        "",
        "## Source licences",
        "- IndiaFinBench: CC BY 4.0 — source Q&A retained with attribution.",
        "- Indian Regulatory BFSI Benchmark v1: CC BY-SA 4.0 — source Q&A retained with attribution and ShareAlike notice.",
        "",
        "## Promotion gate",
        "Candidates must not be loaded by the application until they pass current-law validation, exam-relevance review, four-option MCQ conversion, answer verification, and final duplicate checks.",
        "",
    ]
    (AUDIT / "ADDITIONAL_SOURCE_EXTRACTION.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
