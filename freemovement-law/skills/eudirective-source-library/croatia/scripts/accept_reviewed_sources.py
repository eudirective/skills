#!/usr/bin/env python3
"""Promote an optional retained source copy after its local-artifact checks pass. This does not gate use of a human-reviewed official link.

The script moves a reviewed source payload into the type-organized documents/
folder and updates the manifest, capture ledger and acceptance register. Topic
coverage and country-completion statuses remain separate and are not promoted.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PACK=ROOT/'source-library/croatia'
REF=PACK/'references'
CATEGORY={
 'national_act':'legislation','amending_act':'legislation','amending_regulation':'legislation',
 'implementing_regulation':'legislation','access_to_information_act':'legislation',
 'administrative_remedies_act':'legislation','general_procedure_act':'legislation',
 'annual_budget_execution_act':'legislation','legal_aid_act':'legislation',
 'oversight_act':'legislation','visa_regulation':'legislation',
}

def load(name): return json.loads((REF/name).read_text(encoding='utf-8'))
def save(name,value): (REF/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--source-id',action='append',required=True)
 ap.add_argument('--dry-run',action='store_true')
 args=ap.parse_args()
 manifest=load('candidate-manifest.json'); acceptance=load('source-acceptance.json'); ledger=load('capture-ledger.json'); captures=load('croatia-capture-results.json'); rules=load('source-rules.json')
 docs={r['id']:r for r in manifest['documents']}
 capture_rows={r.get('candidate_id'):r for r in captures.get('records',[])}
 ledger_rows={r.get('source_id'):r for r in ledger.get('records',[])}
 acceptance_rows=acceptance.get('records',{})
 errors=[]; moves=[]
 for sid in args.source_id:
  if sid not in docs or sid not in acceptance_rows:
   errors.append(f'{sid}: missing manifest or acceptance record'); continue
  doc=docs[sid]; review=acceptance_rows[sid]
  if review.get('status')=='accepted' and doc.get('source_status')=='accepted':
   print(f'{sid}: already accepted'); continue
  category=CATEGORY.get(doc.get('source_type'))
  if not category:
   errors.append(f'{sid}: no approved document category for source type {doc.get("source_type")}'); continue
  for name in acceptance.get('required_checks',[]):
   check=review.get('checks',{}).get(name,{})
   if check.get('status')!='pass' or not check.get('evidence'):
    errors.append(f'{sid}: {name} is not passed with evidence')
  sem=review.get('semantic_review',{})
  if sem.get('status')!='passed' or not sem.get('method') or not sem.get('evidence'):
   errors.append(f'{sid}: semantic review is not passed with evidence')
  source_path=doc.get('candidate_text_path')
  if not source_path:
   errors.append(f'{sid}: candidate_text_path missing'); continue
  source=ROOT/source_path
  if not source.is_file():
   errors.append(f'{sid}: source file missing: {source_path}'); continue
  destination=PACK/'documents'/category/source.name
  if destination.exists() and destination.resolve()!=source.resolve():
   errors.append(f'{sid}: destination already exists: {destination.relative_to(ROOT)}'); continue
  moves.append((sid,doc,review,source,destination,category))
 if errors:
  for e in errors: print('ERROR:',e)
  return 2
 for sid,doc,review,source,destination,category in moves:
  print(f'{sid}: {source.relative_to(ROOT)} -> {destination.relative_to(ROOT)}')
 if args.dry_run: return 0
 for sid,doc,review,source,destination,category in moves:
  destination.parent.mkdir(parents=True,exist_ok=True)
  if source.resolve()!=destination.resolve(): source.replace(destination)
  markdown=destination.read_text(encoding='utf-8')
  accepted_notice='> **Accepted source record.** This individual source passed the checks recorded in `references/source-acceptance.json`. Acceptance does not establish legal-topic coverage, legal equivalence, or country completion.'
  markdown=re.sub(r'^> \*\*Review candidate\.\*\*[^\n]*$',accepted_notice,markdown,flags=re.M)
  markdown=markdown.replace(accepted_notice+'\n## Official text-only capture',accepted_notice+'\n\n## Official text-only capture')
  destination.write_text(markdown,encoding='utf-8')
  rel=destination.relative_to(ROOT).as_posix()
  doc.update({'retrieval_status':'accepted_source','accepted':True,'source_status':'accepted','review_state':'accepted','candidate_text_path':rel,'source_text_path':rel})
  review.update({'status':'accepted','accepted_on':'2026-10-19','document_path':rel})
  review.pop('candidate_path',None)
  if sid in capture_rows:
   capture_rows[sid]['retrieval_status']='accepted_source'; capture_rows[sid]['accepted']=True; capture_rows[sid]['document_text_path']=rel
  if sid in ledger_rows:
   ledger_rows[sid]['state']='accepted_reviewed_source'; ledger_rows[sid]['accepted']=True
   ledger_rows[sid]['accepted_on']='2026-10-19'
   ledger_rows[sid]['note']=(ledger_rows[sid].get('note','')+' Accepted after all source checks and independent visible-text equivalence passed; topic coverage remains separate.').strip()
  for rule in rules.get('rules',[]):
   if sid in rule.get('source_ids',[]):
    rule['status']='replayable_dom_fragment; source_accepted'
    rule['acceptance_policy']='A human-reviewed official link is usable within its checked scope; this rule governs optional local-copy review only. Check material changes and relied-on attachments, not a full amendment chain by default.'
 accepted=sum(1 for r in acceptance_rows.values() if r.get('status')=='accepted')
 manifest['accepted_source_count']=accepted
 manifest['candidate_source_count']=len(docs)-accepted
 manifest['status']='review_incomplete_issue_led_coverage_and_country_completion_open'
 manifest['retrieval_status']=f'{accepted} accepted source records; {manifest["candidate_source_count"]} remaining unaccepted, including located uncaptured leads; country review incomplete'
 acceptance['accepted_source_count']=accepted
 acceptance['last_acceptance_review']={'date':'2026-10-19','method':'optional local-copy promotion after the recorded artifact checks; this does not gate human-reviewed official references','source_ids':[sid for sid,*_ in moves]}
 ledger['accepted_source_count']=accepted
 ledger['policy']='This ledger tracks optional retained local artifacts. Human-reviewed official links may be used within their checked scope without capture or conversion. Local-copy checks are proportionate to format and intended reuse; source acceptance does not establish topic coverage or country completion.'
 save('candidate-manifest.json',manifest); save('source-acceptance.json',acceptance); save('capture-ledger.json',ledger); save('croatia-capture-results.json',captures); save('source-rules.json',rules)
 print(f'Accepted {len(moves)} reviewed records; {accepted} accepted in total. Coverage and country status were not promoted.')
 return 0
if __name__=='__main__': raise SystemExit(main())
