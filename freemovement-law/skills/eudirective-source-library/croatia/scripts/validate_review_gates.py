#!/usr/bin/env python3
"""Report Croatia national-source review gate state; incomplete research is expected to be reported, not hidden."""
from __future__ import annotations
import json
from pathlib import Path
PACK=Path(__file__).resolve().parents[1]
REF=PACK/'references'
def load(name): return json.loads((REF/name).read_text(encoding='utf-8'))
manifest=load('candidate-manifest.json'); rules=load('source-rules.json'); acceptance=load('source-acceptance.json'); coverage=load('coverage-model.json'); deps=load('source-dependencies.json'); cases=load('case-law-discovery.json'); ops=load('operational-discovery.json'); attachments=load('attachment-review.json'); shared=load('shared-core.json')
docs={x['id']:x for x in manifest.get('documents',[])}
rule_ids={sid for r in rules.get('rules',[]) for sid in r.get('source_ids',[])}
reviews=acceptance.get('records',{})
reference_reviews=acceptance.get('official_reference_reviews',{})
errors=[]; blockers=[]; local_copy_backlog=[]

def usable_official_reference(sid):
 ref=reference_reviews.get(sid,{})
 required=('publisher','url','checked_on','language','version_or_cutoff','scope','reviewed_content','limitations')
 return (ref.get('status')=='usable_official_reference' and all(ref.get(k) for k in required) and str(ref.get('url','')).startswith('https://'))

for sid,ref in reference_reviews.items():
 if sid not in docs: errors.append(f'{sid}: official-reference review references unknown source')
 elif ref.get('status')=='usable_official_reference' and not usable_official_reference(sid): errors.append(f'{sid}: official-reference review is missing required publisher/version/scope evidence')
for sid in sorted(set(docs)-rule_ids): errors.append(f'{sid}: missing retrieval/conversion disposition')
for sid in sorted(set(docs)-set(reviews)): errors.append(f'{sid}: missing source acceptance record')
for sid,row in reviews.items():
 if sid not in docs: errors.append(f'{sid}: acceptance record references unknown source')
 if row.get('status')=='accepted':
  for name in acceptance.get('required_checks',[]):
   c=row.get('checks',{}).get(name,{})
   if c.get('status')!='pass' or not c.get('evidence'): errors.append(f'{sid}: accepted with open/missing {name}')
  if row.get('semantic_review',{}).get('status')!='passed' or not row.get('semantic_review',{}).get('method'): errors.append(f'{sid}: accepted without semantic validation')

# Captured candidate payloads must exist in the manifest-listed, type-organized location; uncaptured leads must not masquerade as payload files.
listed_paths=set()
for sid,row in docs.items():
 path=row.get('candidate_text_path')
 if row.get('retrieval_status')=='converted_review_candidate':
  if not path: errors.append(f'{sid}: converted record has no candidate text path')
  elif not (Path(__file__).resolve().parents[3]/path).exists(): errors.append(f'{sid}: candidate text path does not exist: {path}')
  else: listed_paths.add(path)
 elif row.get('retrieval_status')=='located_not_captured' and path:
  errors.append(f'{sid}: uncaptured lead points to a candidate text file')
actual_paths={str(x.relative_to(Path(__file__).resolve().parents[3])) for x in (PACK/'candidates').rglob('*.md')}
for path in sorted(actual_paths-listed_paths): errors.append(f'unlisted candidate payload file: {path}')
for path in sorted(listed_paths-actual_paths): errors.append(f'missing candidate payload file: {path}')
for entry in shared.get('entries',[]):
 p=entry.get('english_shared_path')
 if p and not (Path(__file__).resolve().parents[3]/p).exists(): errors.append(f"shared-core entry {entry.get('identity')}: English shared path missing: {p}")
 if entry.get('storage_state')=='external_only_not_mirrored' and entry.get('canonical_path') is not None: errors.append(f"shared-core entry {entry.get('identity')}: external-only item has local canonical path")
for r in rules.get('rules',[]):
 if r.get('selector','').lower() in {'body','body (filtered fallback)'}: errors.append(f"{r['rule_id']}: generic body selector prohibited")
 if r.get('status') in {'rule_not_yet_executable','planned_selector_validation_required','planned_visual_review_required','selector_observed_semantics_not_reviewed','selector_observed_on_seed_pages_or_planned','source_specific_validation_pending'}:
  local_copy_backlog.append(f"local capture/conversion review not ready: {', '.join(r.get('source_ids',[]))}")
if len(docs)!=len(rule_ids): errors.append('some manifest sources lack a source route/disposition')
if len(docs)!=len(reviews): local_copy_backlog.append('local-copy acceptance register does not yet cover every manifest source')
accepted=[sid for sid,r in reviews.items() if r.get('status')=='accepted']
if len(accepted)!=manifest.get('accepted_source_count'): errors.append('manifest accepted count does not match acceptance register')
if coverage.get('accepted_source_count')!=len(accepted): errors.append('coverage-model accepted source count does not match acceptance register')
if coverage.get('manifest_source_count')!=len(docs): errors.append('coverage-model manifest source count does not match manifest')
# Local artifact acceptance is inventory metadata, not a prerequisite for using
# human-reviewed official references or for establishing topic coverage.
if not attachments.get('records'): errors.append('attachment review register has no records')
topic_ids=[x.get('id') for x in coverage.get('topics',[])]
if len(topic_ids)!=len(set(topic_ids)): errors.append('coverage model has duplicate topic IDs')
if set(topic_ids)!=set(coverage.get('required_topic_ids',[])): errors.append('required topic IDs do not match coverage topics')
for topic in coverage.get('topics',[]):
 for layer in coverage.get('required_layers',[]):
  x=topic.get('layers',{}).get(layer)
  if not x: errors.append(f"{topic.get('id')}: missing layer {layer}"); continue
  if x.get('status')=='covered' and not x.get('source_ids'): errors.append(f"{topic['id']}/{layer}: covered without source IDs")
  for sid in x.get('source_ids',[]):
   if sid not in docs: errors.append(f"{topic['id']}/{layer}: unknown source {sid}")
   elif x.get('status')=='covered' and reviews.get(sid,{}).get('status')!='accepted' and not usable_official_reference(sid): errors.append(f"{topic['id']}/{layer}: covered by neither accepted local artifact nor usable official reference {sid}")
  if x.get('status')!='covered' and x.get('status')!='not_applicable': blockers.append(f"coverage open: {topic.get('id')}/{layer}={x.get('status','missing')}")
for a in deps.get('required_directive_articles',[]):
 rows=[x for x in deps.get('directive_article_map',[]) if str(x.get('article'))==str(a)]
 if len(rows)!=1: errors.append(f'Directive article {a}: expected exactly one map row')
 elif rows[0].get('mapping_status') not in {'mapped','not_applicable'}: blockers.append(f"Directive article {a}: {rows[0].get('mapping_status')}")
dependency_ids={x.get('id') for x in deps.get('dependencies',[])}
scans=deps.get('source_dependency_scans',[])
scan_map={}
for scan in scans:
 sid=scan.get('source_id')
 if sid in scan_map: errors.append(f'{sid}: duplicate source dependency scan')
 scan_map[sid]=scan
 if sid not in docs: errors.append(f'{sid}: source dependency scan references unknown source')
 status=scan.get('status')
 edge_ids=scan.get('dependency_ids',[])
 if status in {'not_applicable','reviewed_no_material_dependencies'}:
  if not scan.get('evidence'): errors.append(f'{sid}: terminal dependency scan has no evidence')
  if status=='reviewed_no_material_dependencies' and edge_ids: errors.append(f'{sid}: no-material-dependencies disposition has dependency edges')
 elif status=='reviewed_with_dependencies':
  if not edge_ids: errors.append(f'{sid}: reviewed-with-dependencies disposition has no dependency IDs')
  for did in edge_ids:
   if did not in dependency_ids: errors.append(f'{sid}: dependency scan references unknown dependency {did}')
  if not scan.get('evidence'): errors.append(f'{sid}: reviewed dependency scan has no evidence')
 elif status=='known_edges_not_exhaustive':
  if not edge_ids: errors.append(f'{sid}: partial dependency scan has no known dependency edges')
  for did in edge_ids:
   if did not in dependency_ids: errors.append(f'{sid}: dependency scan references unknown dependency {did}')
  blockers.append(f"source dependency scan incomplete: {sid}=known_edges_not_exhaustive")
 elif status=='not_reviewed': blockers.append(f"source dependency scan open: {sid}=not_reviewed")
 else: errors.append(f'{sid}: invalid or missing source dependency scan status {status!r}')
for sid in sorted(set(docs)-set(scan_map)): errors.append(f'{sid}: missing per-source dependency scan')
for sid in sorted(set(scan_map)-set(docs)): errors.append(f'{sid}: dependency scan source not in manifest')
for dep in deps.get('dependencies',[]):
 if dep.get('dependency_review_status') not in {'resolved','resolved_with_alert','not_applicable'}: blockers.append(f"dependency open: {dep.get('id')}={dep.get('dependency_review_status')}")
for attachment in attachments.get('records',[]):
 if attachment.get('parent_source_id') not in docs: errors.append(f"attachment {attachment.get('id')}: unknown parent source")
 if attachment.get('visual_review_status')!='reviewed': blockers.append(f"attachment review open: {attachment.get('id')}={attachment.get('visual_review_status')}")
 if attachment.get('currentness_status') not in {'verified_current','not_applicable'}: blockers.append(f"attachment currentness open: {attachment.get('id')}={attachment.get('currentness_status')}")
if not cases.get('runs'): blockers.append('no documented case-law search batch')
for t in ops.get('tracks',[]):
 if t.get('status') not in {'complete','complete_with_evidence'}: blockers.append(f"operational discovery open: {t.get('id')}={t.get('status')}")
completed_topics=sum(1 for t in coverage.get('topics',[]) if t.get('status')=='complete')
dependency_scan_counts={status:sum(1 for s in scans if s.get('status')==status) for status in ['reviewed_with_dependencies','reviewed_no_material_dependencies','known_edges_not_exhaustive','not_reviewed','not_applicable']}
print(f"Croatia review gates: {len(accepted)}/{len(docs)} sources accepted; {completed_topics}/{len(coverage.get('topics',[]))} topics complete; country status {coverage.get('country_review_status')}.")
print(f"Dependency scans: {dependency_scan_counts}; {len(deps.get('dependencies',[]))} cross-source dependency records; {len(deps.get('required_directive_articles',[]))} Directive articles; {len(cases.get('planned_search_tasks',[]))} planned court searches.")
print(f"Structural errors: {len(errors)}; completion blockers: {len(blockers)}; local-copy follow-ups: {len(local_copy_backlog)}")
for e in errors: print('ERROR:',e)
for b in blockers: print('OPEN:',b)
for item in local_copy_backlog: print('LOCAL COPY:',item)
