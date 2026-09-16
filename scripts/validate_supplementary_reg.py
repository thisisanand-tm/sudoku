#!/usr/bin/env python3
"""Validate mapped supplementary IndiaFinBench REG candidates against current SEBI PDFs.

This stage is validation-only. It does not change the active question bank.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import validate_promote_additional as base

ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / 'data' / 'candidates' / 'additional_source_candidates.jsonl'
OUT = ROOT / 'audit' / 'SUPPLEMENTARY_REG_VALIDATION.jsonl'
REPORT = ROOT / 'audit' / 'SUPPLEMENTARY_REG_VALIDATION.md'


def content_token_coverage(answer: str, context: str) -> float:
    a=[t for t in base.norm(answer).split() if t not in base.STOP and (len(t)>2 or t.isdigit())]
    c=set(base.norm(context).split())
    if not a: return 0.0
    return sum(1 for t in a if t in c)/len(a)


def main() -> None:
    rows=[json.loads(x) for x in CAND.read_text(encoding='utf-8').splitlines() if x.strip()]
    rows=[x for x in rows if x.get('disposition')=='SUPPLEMENTARY_REVIEW' and x.get('sourceKey')=='INDIAFINBENCH' and x.get('sourceTaskType')=='REG']
    mapped=[]
    for x in rows:
        k=base.map_rulebook(x.get('sourceDetail',''))
        if k:
            y=dict(x); y['rulebookKey']=k; mapped.append(y)
    if len(mapped)!=48:
        raise RuntimeError(f'Expected 48 mapped supplementary REG candidates, found {len(mapped)}')

    official={}; headers={}; errors={}
    for key in sorted({x['rulebookKey'] for x in mapped}):
        try:
            text,header=base.download_pdf_text(base.RULEBOOKS[key]['url'])
            official[key]=base.norm(text); headers[key]=header
            print(key,'chars',len(text))
        except Exception as exc:
            errors[key]=f'{type(exc).__name__}: {exc}'

    results=[]
    for x in mapped:
        y=dict(x); key=y['rulebookKey']
        y['currentLawSource']=base.RULEBOOKS[key]['url']
        y['currentRulebookTitle']=base.RULEBOOKS[key]['title']
        if key in errors:
            y.update(status='HOLD_PRIMARY_SOURCE_DOWNLOAD_ERROR',contextEvidenceScore=0.0,error=errors[key]); results.append(y); continue
        score,matched,sampled=base.context_evidence(y.get('context',''),official[key])
        y['contextEvidenceScore']=round(score,4); y['matchedContextShingles']=matched; y['sampledContextShingles']=sampled
        y['answerContentTokenCoverage']=round(content_token_coverage(y.get('answer',''),y.get('context','')),4)
        if matched<2 or score<0.18:
            y['status']='REJECT_CURRENT_TEXT_NOT_EVIDENCED'
        else:
            # REG is expert-annotated interpretation of the evidenced passage; unlike NUM/TMP,
            # it does not depend on a separate arithmetic or timeline derivation.
            y['status']='PASS_CURRENT_CONTEXT_EXPERT_REG'
        results.append(y)

    OUT.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in results),encoding='utf-8')
    c=Counter(x['status'] for x in results); rules=Counter(x['rulebookKey'] for x in results if x['status'].startswith('PASS_'))
    passes=[x for x in results if x['status'].startswith('PASS_')]
    lines=['# Supplementary REG current-law validation','',f'Mapped REG candidates assessed: **{len(results)}**',f'Passed current-context validation: **{len(passes)}**','','## Status counts']
    for k,v in sorted(c.items()): lines.append(f'- {k}: {v}')
    lines += ['', '## Passes by rulebook']
    for k,v in sorted(rules.items()): lines.append(f'- {k}: {v}')
    lines += ['', '## Policy', 'A pass requires the candidate source passage to be evidenced in the current consolidated SEBI rulebook. These are IndiaFinBench REG interpretation items, so no separate arithmetic/temporal inference is required. No item is promoted by this validation-only stage.', '']
    REPORT.write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'assessed':len(results),'passed':len(passes),'statuses':dict(c),'passRules':dict(rules),'downloadErrors':errors},indent=2))

if __name__=='__main__': main()
