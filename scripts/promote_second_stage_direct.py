#!/usr/bin/env python3
"""Finish the 160-item direct-review promotion gate.

The first stage accepted only directly extractive answers. This second stage reviews the
69 IndiaFinBench items whose *current SEBI source context already matched* but whose gold
answers required interpretation, arithmetic, or temporal reasoning.

Two candidates are deliberately not promoted:
- CAND-INDIAFINBENCH-0348: the answer infers that a CRA promoter may drop below 26%
  immediately after the three-year minimum period; the consolidated text supports the
  three-year minimum but the scenario needs a more careful legal interpretation before use.
- CAND-INDIAFINBENCH-0391: the stated calendar answer conflicts with the question's own
  assumption that there are no intervening non-working days.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import validate_promote_additional as base

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit"
RESULTS = AUDIT / "ADDITIONAL_VALIDATION_RESULTS.jsonl"

LEGAL_AMBIGUITY = {"CAND-INDIAFINBENCH-0348"}
REASONING_ERROR = {"CAND-INDIAFINBENCH-0391"}


def clean_text(value: str) -> str:
    return (value.replace("â€”", "—").replace("â€“", "–")
                 .replace("â€™", "’").replace("â€œ", "“").replace("â€", "”"))


def main() -> None:
    rows = [json.loads(x) for x in RESULTS.read_text(encoding="utf-8").splitlines() if x.strip()]
    held = [x for x in rows if x.get("status") == "HOLD_DERIVED_OR_NONEXTRACTIVE_ANSWER"]
    if len(held) != 69:
        raise RuntimeError(f"Expected 69 first-stage held items, found {len(held)}")

    for row in rows:
        cid = row.get("candidateId")
        if cid in LEGAL_AMBIGUITY:
            row["status"] = "HOLD_SECOND_STAGE_LEGAL_AMBIGUITY"
            row["secondStageNote"] = "Current text confirms a 26% minimum for at least three years, but the scenario's conclusion about a reduction to 20% after that period is not promoted without a more specific authoritative interpretation."
        elif cid in REASONING_ERROR:
            row["status"] = "REJECT_SECOND_STAGE_REASONING_ERROR"
            row["secondStageNote"] = "The answer's calendar dates are inconsistent with the question's assumption of no intervening non-working days."
        elif row.get("status") == "HOLD_DERIVED_OR_NONEXTRACTIVE_ANSWER":
            row["status"] = "PASS_SECOND_STAGE_REASONING_REVIEW"
            row["secondStageNote"] = "Current SEBI source context was already evidenced in stage one; the expert-annotated interpretation/arithmetic/temporal answer was reviewed for internal consistency and retained."

    promoted = [dict(x) for x in rows if x.get("status") in {"PASS_PRIMARY_SOURCE_EXTRACTIVE", "PASS_SECOND_STAGE_REASONING_REVIEW"}]
    promoted.sort(key=lambda x: x["candidateId"])
    if len(promoted) != 94:
        raise RuntimeError(f"Expected 94 total promoted direct-review items, found {len(promoted)}")
    for x in promoted:
        x["question"] = clean_text(x.get("question", ""))
        x["answer"] = clean_text(x.get("answer", ""))

    RESULTS.write_text("".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n" for x in rows), encoding="utf-8")
    base.write_validated_js(promoted)
    base.update_questions_js(promoted)
    base.update_wiring(len(promoted))

    total = 370 + len(promoted)
    counts = Counter(x["status"] for x in rows)
    by_task = Counter(x.get("sourceTaskType", "") for x in promoted)
    by_rule = Counter(x.get("rulebookKey", "") for x in promoted)
    lines = [
        "# Direct-review validation — final",
        "",
        "Validation date: **2026-09-16**",
        "",
        "All **160** direct-review candidates have now passed through the two-stage gate.",
        f"- Promoted from the direct-review set: **{len(promoted)}**",
        f"- Active bank after direct-review completion: **{total}**",
        "- AI-authored question stems: **0**",
        "",
        "## Final status counts",
    ]
    for k,v in sorted(counts.items()): lines.append(f"- {k}: {v}")
    lines += ["", "## Promoted by source task type"]
    for k,v in sorted(by_task.items()): lines.append(f"- {k}: {v}")
    lines += ["", "## Promoted by rulebook"]
    for k,v in sorted(by_rule.items()): lines.append(f"- {k}: {v}")
    lines += [
        "",
        "## Second-stage exclusions",
        "- `CAND-INDIAFINBENCH-0348` — held for legal ambiguity: the current CRA text establishes the 26% minimum for at least three years, but the scenario's conclusion that 20% is necessarily permissible immediately afterwards is not used as an exam answer without stronger authority.",
        "- `CAND-INDIAFINBENCH-0391` — rejected: its stated tendering-period calendar dates conflict with the question's own assumption of no intervening non-working days.",
        "",
        "## Remaining direct-review non-promotions",
        "The other non-promoted candidates are the stage-one items whose supplied context could not be evidenced in the current consolidated rulebook or could not be mapped precisely enough to a current primary source. They remain outside the active bank.",
        "",
    ]
    (AUDIT / "DIRECT_REVIEW_FINAL_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    readme = ROOT / "README.md"
    if readme.exists():
        t = readme.read_text(encoding="utf-8")
        t = re.sub(r"On 16 September 2026, \d+ additional open-licensed source Q&A items were promoted only after matching their source proposition to current consolidated SEBI primary-source text\.",
                   f"On 16 September 2026, {len(promoted)} additional open-licensed source Q&A items were promoted from the direct-review set after current-SEBI source validation and a second-stage reasoning review.", t)
        if "Direct-review gate" not in t:
            t += f"\n### Direct-review gate\n\nThe 160-item direct-review set is complete: {len(promoted)} promoted, with current-source mismatches/unmapped items excluded and two reasoning-stage items withheld. The active bank now contains {total} validated sourced questions.\n"
        readme.write_text(t, encoding="utf-8")

    print(json.dumps({
        "directReviewed": 160,
        "promoted": len(promoted),
        "activeTotal": total,
        "statuses": dict(counts),
        "promotedByTask": dict(by_task),
        "promotedByRulebook": dict(by_rule),
    }, indent=2))


if __name__ == "__main__":
    main()
