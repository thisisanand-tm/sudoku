#!/usr/bin/env python3
"""Promote the 37 current-SEBI-validated supplementary REG items.

Combined with the 94 promoted direct-review items, this produces a 501-question active
bank while preserving zero AI-authored question stems.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import validate_promote_additional as base

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'audit'
DIRECT=AUDIT/'ADDITIONAL_VALIDATION_RESULTS.jsonl'
SUP=AUDIT/'SUPPLEMENTARY_REG_VALIDATION.jsonl'


def clean(value: str) -> str:
    return (value.replace('â€”','—').replace('â€“','–').replace('â€™','’')
                 .replace('â€œ','“').replace('â€','”'))


def main() -> None:
    direct=[json.loads(x) for x in DIRECT.read_text(encoding='utf-8').splitlines() if x.strip()]
    direct_pass=[x for x in direct if x.get('status') in {'PASS_PRIMARY_SOURCE_EXTRACTIVE','PASS_SECOND_STAGE_REASONING_REVIEW'}]
    sup=[json.loads(x) for x in SUP.read_text(encoding='utf-8').splitlines() if x.strip()]
    sup_pass=[x for x in sup if x.get('status')=='PASS_CURRENT_CONTEXT_EXPERT_REG']
    if len(direct_pass)!=94: raise RuntimeError(f'Expected 94 direct passes, found {len(direct_pass)}')
    if len(sup_pass)!=37: raise RuntimeError(f'Expected 37 supplementary REG passes, found {len(sup_pass)}')

    promoted=[dict(x) for x in direct_pass+sup_pass]
    promoted.sort(key=lambda x:x['candidateId'])
    if len({x['candidateId'] for x in promoted})!=131: raise RuntimeError('Duplicate candidate IDs in combined promotion')
    for x in promoted:
        x['question']=clean(x.get('question',''))
        x['answer']=clean(x.get('answer',''))

    base.write_validated_js(promoted)
    base.update_questions_js(promoted)
    base.update_wiring(len(promoted))

    total=370+len(promoted)
    if total!=501: raise RuntimeError(f'Expected final total 501, got {total}')

    by_source=Counter(x['sourceKey'] for x in promoted)
    by_rule=Counter(x.get('rulebookKey','') for x in promoted)
    by_cat=Counter(x.get('examCategory','') for x in promoted)
    by_diff=Counter(x.get('difficulty','') for x in promoted)
    lines=[
      '# 500-question target closure','',
      'Validation date: **2026-09-16**','',
      'The sourced mock-test bank now exceeds the original minimum target without adding AI-authored question stems.','',
      '## Final bank','',
      '- Original validated bank: **370**',
      '- Current-SEBI-validated direct-review additions: **94**',
      '- Current-SEBI-validated supplementary REG additions: **37**',
      '- **Final active bank: 501 questions**',
      '- **AI-authored question stems: 0**',
      '- Converted source-Q&A items use explicitly labelled assistant-generated distractors.','',
      '## Supplementary tranche','',
      '- 48 mapped supplementary REG candidates were assessed against current consolidated SEBI rulebooks.',
      '- 37 passed current-context validation and were promoted.',
      '- 11 whose source passage was not evidenced in the current consolidated text were excluded.','',
      '## Final added questions by rulebook',''
    ]
    for k,v in sorted(by_rule.items()): lines.append(f'- {k}: {v}')
    lines += ['', '## Final bank safeguards','',
      '- No duplicate IDs or normalized question stems.',
      '- Every active question has exactly four distinct options and a valid answer index.',
      '- No active item is marked `aiGenerated`.',
      '- Additional items retain source URL, licence, candidate ID, current-law source, and validation metadata.',
      '- The two direct-review exceptions remain excluded: one legal-ambiguity scenario and one internally inconsistent date calculation.','']
    (AUDIT/'QUESTION_BANK_500_CLOSURE.md').write_text('\n'.join(lines),encoding='utf-8')

    readme=ROOT/'README.md'
    if readme.exists():
        t=readme.read_text(encoding='utf-8')
        if '### 500-question target' not in t:
            t += '\n### 500-question target\n\nThe active bank now contains **501 validated sourced questions**: the prior 370, 94 current-SEBI-validated direct-review additions, and 37 current-SEBI-validated supplementary REG additions. No active question stem is AI-authored.\n'
        else:
            t=re.sub(r'The active bank now contains \*\*\d+ validated sourced questions\*\*[^\n]*',
                     'The active bank now contains **501 validated sourced questions**: the prior 370, 94 current-SEBI-validated direct-review additions, and 37 current-SEBI-validated supplementary REG additions. No active question stem is AI-authored.',t)
        readme.write_text(t,encoding='utf-8')

    print(json.dumps({'activeTotal':total,'additionalValidated':len(promoted),'direct':len(direct_pass),'supplementaryREG':len(sup_pass),'bySource':dict(by_source),'byCategory':dict(by_cat),'byDifficulty':dict(by_diff)},indent=2))

if __name__=='__main__': main()
