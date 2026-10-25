#!/usr/bin/env python3
"""Validate Croatia source, coverage, dependency, attachment, and discovery registers."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

PACK=Path(__file__).resolve().parents[1]
ROOT=PACK.parents[1]
REF=PACK/'references'
def load(name): return json.loads((REF/name).read_text(encoding='utf-8'))

rules=load('source-rules.json')
acceptance=load('source-acceptance.json')
coverage=load('coverage-model.json')
deps=load('source-dependencies.json')
cases=load('case-law-discovery.json')
ops=load('operational-discovery.json')
attachments=load('attachment-review.json')
shared=load('shared-core.json')
records=acceptance.get('records',{})
source_ids=set(records)
rule_ids={sid for rule in rules.get('rules',[]) for sid in rule.get('source_ids',[])}
reference_reviews=acceptance.get('official_reference_reviews',{})
errors=[]; blockers=[]; local_copy_backlog=[]

def usable_reference(sid):
    ref=reference_reviews.get(sid,{})
    required=('publisher','url','checked_on','language','version_or_cutoff','scope','reviewed_content','limitations')
    return ref.get('status')=='usable_official_reference' and all(ref.get(k) for k in required) and str(ref.get('url','')).startswith('https://')

for sid,ref in reference_reviews.items():
    if sid not in source_ids: errors.append(f'{sid}: official-reference review references unknown source')
    elif ref.get('status')=='usable_official_reference' and not usable_reference(sid): errors.append(f'{sid}: official-reference review lacks publisher/version/scope evidence')
for sid in sorted(source_ids-rule_ids): errors.append(f'{sid}: missing retrieval/conversion disposition')
for sid in sorted(rule_ids-source_ids): errors.append(f'{sid}: source rule references unknown source')

accepted=[]
for sid,row in records.items():
    if row.get('status')=='accepted':
        accepted.append(sid)
        for name in acceptance.get('required_checks',[]):
            check=row.get('checks',{}).get(name,{})
            not_applicable=(name=='attachments_review' and check.get('status')=='not_applicable' and check.get('evidence'))
            if (check.get('status')!='pass' and not not_applicable) or not check.get('evidence'): errors.append(f'{sid}: accepted with open/missing {name}')
        sem=row.get('semantic_review',{})
        if sem.get('status')!='passed' or not sem.get('method') or not sem.get('evidence'): errors.append(f'{sid}: accepted without evidence-bearing semantic review')
        doc=row.get('document_path','')
        if not doc.startswith('source-library/croatia/documents/'): errors.append(f'{sid}: accepted source has no final path under documents/')
        elif not (ROOT/doc).is_file(): errors.append(f'{sid}: accepted document is missing: {doc}')
        else:
            expected=row.get('local_file_sha256')
            actual=hashlib.sha256((ROOT/doc).read_bytes()).hexdigest()
            if not expected: errors.append(f'{sid}: accepted document has no local_file_sha256')
            elif expected!=actual: errors.append(f'{sid}: accepted document hash mismatch: {doc}')
    elif row.get('candidate_archive_path') and not row['candidate_archive_path'].startswith(('candidates/','discovery/')):
        errors.append(f'{sid}: invalid archive path for nonterminal review material')

# Local research material is held only in the Monitor archive.
for directory in (PACK/'candidates',PACK/'captures'):
    if directory.exists(): errors.append(f'local-only research directory remains in country pack: {directory.relative_to(ROOT)}')
for filename in ('candidate-manifest.json','capture-ledger.json','croatia-capture-results.json'):
    if (REF/filename).exists(): errors.append(f'local-only manifest remains in country pack references: references/{filename}')

for entry in shared.get('entries',[]):
    path=entry.get('english_shared_path')
    if path and not (ROOT/path).exists(): errors.append(f"shared-core entry {entry.get('identity')}: English shared path missing: {path}")
    if entry.get('storage_state')=='external_only_not_mirrored' and entry.get('canonical_path') is not None: errors.append(f"shared-core entry {entry.get('identity')}: external-only item has a local canonical path")
for rule in rules.get('rules',[]):
    if str(rule.get('selector','')).lower() in {'body','body (filtered fallback)'}: errors.append(f"{rule['rule_id']}: generic body selector prohibited")
    if rule.get('status') in {'rule_not_yet_executable','planned_selector_validation_required','planned_visual_review_required','selector_observed_semantics_not_reviewed','selector_observed_on_seed_pages_or_planned','source_specific_validation_pending'}:
        local_copy_backlog.append(f"local capture/conversion review not ready: {', '.join(rule.get('source_ids',[]))}")
if source_ids!=rule_ids: errors.append('source-rule and source-acceptance registers do not describe the same IDs')
if len(accepted)!=acceptance.get('accepted_source_count'): errors.append('source-acceptance count does not match accepted records')
if coverage.get('accepted_source_count')!=len(accepted): errors.append('coverage accepted-source count does not match source-acceptance')
if coverage.get('source_record_count')!=len(source_ids): errors.append('coverage source-record count does not match source-acceptance')
if not attachments.get('records'): errors.append('attachment review register has no records')

topic_ids=[x.get('id') for x in coverage.get('topics',[])]
if len(topic_ids)!=len(set(topic_ids)): errors.append('coverage model has duplicate topic IDs')
if set(topic_ids)!=set(coverage.get('required_topic_ids',[])): errors.append('required topic IDs do not match coverage topics')
for topic in coverage.get('topics',[]):
    for layer in coverage.get('required_layers',[]):
        row=topic.get('layers',{}).get(layer)
        if not row: errors.append(f"{topic.get('id')}: missing layer {layer}"); continue
        if row.get('status')=='covered' and not row.get('source_ids'): errors.append(f"{topic['id']}/{layer}: covered without source IDs")
        for sid in row.get('source_ids',[]):
            if sid not in source_ids: errors.append(f"{topic['id']}/{layer}: unknown source {sid}")
            elif row.get('status')=='covered' and records[sid].get('status')!='accepted' and not usable_reference(sid): errors.append(f"{topic['id']}/{layer}: source has neither accepted local copy nor usable official reference: {sid}")
        if row.get('status') not in {'covered','not_applicable'}: blockers.append(f"coverage open: {topic.get('id')}/{layer}={row.get('status','missing')}")

for article in deps.get('required_directive_articles',[]):
    rows=[x for x in deps.get('directive_article_map',[]) if str(x.get('article'))==str(article)]
    if len(rows)!=1: errors.append(f'Directive article {article}: expected exactly one map row')
    elif rows[0].get('mapping_status') not in {'mapped','not_applicable'}: blockers.append(f"Directive article {article}: {rows[0].get('mapping_status')}")
dep_ids={x.get('id') for x in deps.get('dependencies',[])}
scan_map={}
for scan in deps.get('source_dependency_scans',[]):
    sid=scan.get('source_id')
    if sid in scan_map: errors.append(f'{sid}: duplicate dependency scan')
    scan_map[sid]=scan
    if sid not in source_ids: errors.append(f'{sid}: dependency scan references unknown source')
    status=scan.get('status'); edges=scan.get('dependency_ids',[])
    if status in {'not_applicable','reviewed_no_material_dependencies'}:
        if not scan.get('evidence'): errors.append(f'{sid}: terminal dependency scan lacks evidence')
        if status=='reviewed_no_material_dependencies' and edges: errors.append(f'{sid}: no-dependency disposition has edges')
    elif status=='reviewed_with_dependencies':
        if not edges: errors.append(f'{sid}: reviewed-with-dependencies has no IDs')
        for dep in edges:
            if dep not in dep_ids: errors.append(f'{sid}: unknown dependency {dep}')
        if not scan.get('evidence'): errors.append(f'{sid}: reviewed dependency scan lacks evidence')
    elif status=='known_edges_not_exhaustive':
        if not edges: errors.append(f'{sid}: partial dependency scan has no known edges')
        for dep in edges:
            if dep not in dep_ids: errors.append(f'{sid}: unknown dependency {dep}')
        blockers.append(f'source dependency scan incomplete: {sid}=known_edges_not_exhaustive')
    elif status=='not_reviewed': blockers.append(f'source dependency scan open: {sid}=not_reviewed')
    else: errors.append(f'{sid}: invalid dependency-scan status {status!r}')
for sid in sorted(source_ids-set(scan_map)): errors.append(f'{sid}: missing per-source dependency scan')
for sid in sorted(set(scan_map)-source_ids): errors.append(f'{sid}: dependency scan source not in source register')
for dep in deps.get('dependencies',[]):
    if dep.get('dependency_review_status') not in {'resolved','resolved_with_alert','not_applicable'}: blockers.append(f"dependency open: {dep.get('id')}={dep.get('dependency_review_status')}")
for item in attachments.get('records',[]):
    if item.get('parent_source_id') not in source_ids: errors.append(f"attachment {item.get('id')}: unknown parent source")
    if item.get('visual_review_status')!='reviewed': blockers.append(f"attachment review open: {item.get('id')}={item.get('visual_review_status')}")
    if item.get('currentness_status') not in {'verified_current','not_applicable'}: blockers.append(f"attachment currentness open: {item.get('id')}={item.get('currentness_status')}")
if not cases.get('runs'): blockers.append('no documented case-law search batch')
for track in ops.get('tracks',[]):
    if track.get('status') not in {'complete','complete_with_evidence'}: blockers.append(f"operational discovery open: {track.get('id')}={track.get('status')}")

completed_topics=sum(1 for x in coverage.get('topics',[]) if x.get('status')=='complete')
scan_counts={s:sum(1 for x in deps.get('source_dependency_scans',[]) if x.get('status')==s) for s in ['reviewed_with_dependencies','reviewed_no_material_dependencies','known_edges_not_exhaustive','not_reviewed','not_applicable']}
print(f"Croatia review gates: {len(accepted)}/{len(source_ids)} local copies accepted; {completed_topics}/{len(coverage.get('topics',[]))} topics complete; country status {coverage.get('country_review_status')}.")
print(f"Official references usable by link: {sum(1 for x in reference_reviews.values() if x.get('status')=='usable_official_reference')}; dependency scans: {scan_counts}; {len(dep_ids)} dependency records; {len(cases.get('planned_search_tasks',[]))} planned court searches.")
print(f"Structural errors: {len(errors)}; completion blockers: {len(blockers)}; local-copy follow-ups: {len(local_copy_backlog)}")
for x in errors: print('ERROR:',x)
for x in blockers: print('OPEN:',x)
for x in local_copy_backlog: print('LOCAL COPY:',x)
