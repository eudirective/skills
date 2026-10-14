#!/usr/bin/env python3
"""C17b/c/d: source-owned, REVIEW-ONLY remedies for pinned fictional C10 cases.

Neither deterministic route filtering nor correspondence rendering verifies a legal
entitlement, an actual fact, a deadline, recipient competence or reviewer identity.
No networking, transmission, personal-case inputs or automatic decisions.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from contract_validate import load_json, validate_obj
from module_conformance import validate_pair
from c17_applicant_drafts import generate as old_generate, digest
from source_library_paths import compatibility_root, module_notes_root

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PINS = ROOT / 'references/c17/catalog-pins.json'
CATALOG_PINS_SHA256 = 'ee850583ff97fe2f467c7f32cdcc7c575a7e36c63483283c181ca7281d2c08cd'
ALLOWED_CASES = set(range(1, 9))
COUNTRIES = {'SE': 'eudirective-ms-sweden', 'TR': 'eudirective-ac-turkiye'}
FAMILY = {'EU': 'core', 'SE': 'member_state', 'TR': 'applicant_country'}
OWNER_NAMESPACE = {'EU': 'eu:', 'SE': 'se:', 'TR': 'tr:'}


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_file(root, rel):
    if not root.is_dir() or root.is_symlink():
        raise ValueError('c17_module_not_a_safe_directory')
    p = root / rel
    if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
        raise ValueError('c17_missing_or_unsafe_file:' + str(p))
    return p


def verify_module_notes(module_root, export):
    for src in export['source_records']:
        if src.get('content_kind') != 'verified_source_note' or src.get('authenticity_state') != 'verified_identity_version':
            raise ValueError('c17_unenrolled_source_class')
        src_id = src['source_id']
        if ':src:' not in src_id:
            raise ValueError('c17_bad_source_namespace')
        country = 'sweden' if module_root.name == 'eudirective-ms-sweden' else 'turkiye'
        local_note = module_root / 'references' / 'source-notes' / (src_id.split(':src:')[1] + '.md')
        path = local_note if local_note.is_file() else module_notes_root(country) / (src_id.split(':src:')[1] + '.md')
        if sha_file(path) != src['content_sha256']:
            raise ValueError('c17_module_source_note_tampered:' + src_id)


def load_catalogs(sweden_root, turkiye_root):
    """Cross-package composition: country catalogues remain physically country-owned."""
    if sha_file(CATALOG_PINS) != CATALOG_PINS_SHA256:
        raise ValueError('c17_catalog_pin_manifest_modified')
    metadata = load_json(CATALOG_PINS)
    excerpt = safe_file(compatibility_root(), 'c17/article2-official-excerpt.json')
    if sha_file(excerpt) != metadata['official_article2_excerpt_sha256']:
        raise ValueError('c17_article2_excerpt_modified')
    article = load_json(excerpt)
    if (article['doc_id'] != 'eu:32004l0038' or article['article'] != '2(2)(a)' or
            article['wording'] != 'the spouse;' or article['source_state'] != 'official_page_excerpt_verified_manually'):
        raise ValueError('c17_article2_excerpt_unreliable')
    pins = metadata['catalogs']
    roots = {'EU': ROOT, 'SE': Path(sweden_root), 'TR': Path(turkiye_root)}
    catalogs = {}
    exps = {}
    extensions = {}
    source_ids = {item['source_id'] for item in load_json(ROOT/'references/source-pack/core-source-pack-manifest-0.6.1.json')['sources']}
    for jurisdiction, root in roots.items():
        cfile = safe_file(root, 'references/c17-remedy-catalog.json')
        if sha_file(cfile) != pins[jurisdiction]['catalog_file_sha256']:
            raise ValueError('c17_untrusted_catalog_bytes:' + jurisdiction)
        cat = load_json(cfile)
        validate_obj('c17-remedy-catalog', cat)
        if cat['jurisdiction'] != jurisdiction or cat['module_family'] != FAMILY[jurisdiction]:
            raise ValueError('c17_wrong_catalog_ownership:' + jurisdiction)
        owner = 'eudirective-core' if jurisdiction == 'EU' else None
        if jurisdiction != 'EU':
            mpath = safe_file(root, 'references/module-manifest.json')
            epath = safe_file(root, 'references/module-export.json')
            if (sha_file(mpath) != pins[jurisdiction]['module_manifest_file_sha256'] or
                    sha_file(epath) != pins[jurisdiction]['module_export_file_sha256']):
                raise ValueError('c17_country_module_release_mismatch:' + jurisdiction)
            manifest, export = load_json(mpath), load_json(epath)
            validate_pair(manifest, export)
            verify_module_notes(root, export)
            if ((manifest['module_family'], manifest['jurisdiction']) != (FAMILY[jurisdiction], jurisdiction) or
                    jurisdiction == 'TR' and 'SE' not in manifest['destination_state_profiles_available']):
                raise ValueError('c17_wrong_module_competence:' + jurisdiction)
            owner = export['module_id']
            exp_sources = {r['source_id'] for r in export['source_records']}
            authorities = {r['authority_id'] for r in export['authority_records']}
            exps[jurisdiction] = export
            sidecar = load_json(safe_file(root, 'references/c12-rule-extension.json'))
            fixture = ROOT/'references/fixtures/c12'/('sweden-rule-extension.json' if jurisdiction == 'SE' else 'turkiye-rule-extension.json')
            if sha_file(root/'references/c12-rule-extension.json') != sha_file(fixture):
                raise ValueError('c17_c12_fixture_sidecar_drift:' + jurisdiction)
            extensions[jurisdiction] = {r['rule_id'] for r in sidecar['rules']}
        else:
            exp_sources = source_ids
            authorities = {'eu:authority:solvit-network','eu:authority:european-commission','eu:authority:european-ombudsman'}
        if cat['owner_module_id'] != owner:
            raise ValueError('c17_catalog_module_identity_mismatch:' + jurisdiction)
        names = set()
        for route in cat['remedies']:
            rid = route['remedy_id']
            if rid in names or not rid.startswith(OWNER_NAMESPACE[jurisdiction]+'c17:'):
                raise ValueError('c17_duplicate_or_unowned_remedy:' + rid)
            names.add(rid)
            if (route['authority_ref'] not in authorities or
                    not set(route['source_refs']).issubset(exp_sources)):
                raise ValueError('c17_unbound_remedy_authority_or_source:' + rid)
            for rule in route['trigger_rule_ids']:
                if not rule.startswith(OWNER_NAMESPACE[jurisdiction]):
                    raise ValueError('c17_cross_owner_rule_trigger:' + rid)
                if jurisdiction != 'EU' and rule not in extensions[jurisdiction]:
                    raise ValueError('c17_trigger_not_in_owned_rule_sidecar:' + rule)
            if route['deadline']['calculation'] != 'human_only':
                raise ValueError('c17_deadline_calculation_not_authorized')
        catalogs[jurisdiction] = cat
    return catalogs, {jur: sha_file(safe_file(root,'references/c17-remedy-catalog.json')) for jur,root in roots.items()}


def _target_ok(remedy, case):
    challenged = case['geography']['challenged_authority_state']
    lvl = remedy['target_authority_level']
    if lvl == 'eu_institution':
        # Swedish foreign missions remain Member-State authorities even when abroad.
        return False, 'EU Ombudsman supervises EU bodies, not Swedish consulates'
    if lvl in {'member_state_authority', 'member_state_authority_abroad'}:
        return (challenged == 'SE', 'target not an enrolled Swedish Member-State authority')
    if lvl == 'applicant_country_document_authority':
        return (case['geography']['document_issuing_country'] == 'TR', 'document issuer not enrolled as Türkiye')
    return False, 'unrecognised target authority level'


def _review_letter(route, relevant, case_id):
    category=route['category']
    title = {'administrative_appeal_then_judicial_referral':'DRAFT APPEAL OUTLINE',
             'supervisory_complaint':'DRAFT SUPERVISORY COMPLAINT',
             'eu_law_enforcement_complaint':'DRAFT SYSTEMIC EU-LAW COMPLAINT',
             'evidence_acquisition':'DRAFT DOCUMENT VERIFICATION REQUEST'}.get(category,'DRAFT PROCEDURAL CLARIFICATION')
    topics = '; '.join(x['topic'] for x in relevant)
    sources = ', '.join(route['source_refs'])
    if category == 'administrative_appeal_then_judicial_referral':
        action = ('Subject to confirmation of the appealable decision and service date, I request reconsideration '
                  'of [DECISION REFERENCE — HUMAN TO VERIFY]. My requested change is [SPECIFY]. '
                  'If unchanged, please apply the competent forwarding procedure. '
                  'Please confirm the filing date recorded and any need for additional procedural information.')
    elif category == 'supervisory_complaint':
        action = ('Subject to verification of competence and the underlying facts, I request supervisory '
                  'examination of the described conduct. I do not seek reversal or monetary compensation from this body.')
    elif category == 'eu_law_enforcement_complaint':
        action = ('This is submitted as a proposed issue for EU-law enforcement review, not an individual appeal. '
                  'The factual pattern, Member-State attribution and applicable Union law must be independently established.')
    elif category == 'evidence_acquisition':
        action = ('Please identify an official method for confirming this document\'s provenance and authenticity. '
                  'No private documents should be disclosed without a separate lawful procedure and review.')
    else:
        action = ('Please clarify in writing the competent procedure, source of the reported requirement, '
                  'any applicable exception, and available means to present relevant evidence. '
                  'If the report is inaccurate, please identify the applicable procedure instead.')
    content = (title+' — FICTIONAL REVIEW ONLY / DO NOT SEND\n'
      'To: [VERIFY CURRENT COMPETENT AUTHORITY; NO ADDRESS INSERTED]\n'
      'Re: [FICTIONAL '+case_id+' — REPLACE WITH HUMAN-VERIFIED REFERENCE ONLY IF AUTHORIZED]\n\n'
      'The fictional review record raises the following matters for verification: '+topics+'.\n'
      'These are unverified allegations and source-qualified questions, not findings.\n\n'+action+'\n\n'
      'Relevant source identifiers for a human to inspect: '+sources+'.\n'
      'Documents and dates must be checked independently; attach only material required and lawfully shareable.\n'
      'The recipient, competence, applicable law, filing requirements and deadline remain unverified.\n')
    return {'remedy_id':route['remedy_id'],'format':category,
            'recipient_placeholder':'[VERIFY CURRENT COMPETENT AUTHORITY]',
            'text':content,'send_authorized':False,'human_review_required':True}


def build(n, catalogs, catalog_digests, *, question_artifact=None, case=None):
    if n not in ALLOWED_CASES:
        raise ValueError('c17_case_not_allowlisted')
    import test_c16_coverage as fixtures
    from c7_trust_gate import require_approved
    if case is None:
        case,*_ = fixtures.load_case(n)
    require_approved('case',case)
    if case['case_id'] != f'CASE-C10-L{n}' or case['privacy_classification'] != 'synthetic':
        raise ValueError('c17_case_identity_or_privacy_mismatch')
    q = question_artifact if question_artifact is not None else old_generate(n)
    if q['case_id'] != 'L'+str(n) or q['mode'] != 'fictional_review_only' or q['send_authorized'] or q['legal_violation_status'] != 'not_determined':
        raise ValueError('c17_untrusted_upstream_questions')
    # Recompute and compare to the trusted, passage-anchored C7-enrolled upstream stages.
    expected = old_generate(n)
    if digest(q) != digest(expected):
        raise ValueError('c17_modified_c12_c13_review_questions')
    by_rule = {a['rule_id']:a for a in q['questions']}
    if len(by_rule) != len(q['questions']):
        raise ValueError('c17_duplicate_upstream_rule_id')
    candidates=[];blocked=[];letters=[]
    for jurisdiction in ('SE','TR','EU'):
        for route in catalogs[jurisdiction]['remedies']:
            relevant = [by_rule[rid] for rid in route['trigger_rule_ids'] if rid in by_rule]
            if not relevant:
                continue
            if case['procedure_stage'] not in route['allowed_stages']:
                blocked.append({'remedy_id':route['remedy_id'], 'reason':'stage_not_permitted_for_filing_review',
                                'source_scope':route['scope_note']})
                continue
            ok, reason = _target_ok(route,case)
            if not ok:
                blocked.append({'remedy_id':route['remedy_id'], 'reason':reason,'source_scope':route['scope_note']})
                continue
            if route['category']=='administrative_appeal_then_judicial_referral' and case['procedure_type']!='visa_appeal':
                blocked.append({'remedy_id':route['remedy_id'], 'reason':'no_visa_refusal_appeal_procedure_enrolled',
                                'source_scope':route['scope_note']})
                continue
            route_candidate={k:route[k] for k in ('remedy_id','category','authority_ref','priority_class','deadline',
                'prerequisites_to_verify','powers_to_verify','limits','evidence_to_preserve','source_refs',
                'filing_channel_for_review','intended_outcome_for_review')}
            route_candidate.update({'matched_rule_ids':[x['rule_id'] for x in relevant],
                'jurisdiction':jurisdiction,'status':'candidate_for_human_review','human_review_required':True,
                'outstanding_checks':['Verify jurisdiction and present official source text','Verify factual predicates and contrary evidence',
                 'Verify current authority competence, prerequisites and deadlines',
                 'Check whether this route affects or leaves untouched other remedies']})
            candidates.append(route_candidate)
            letters.append(_review_letter(route,relevant,'L'+str(n)))
    precedence={'deadline_preservation_review_first':0,'parallel_review':1,
                'fact_gathering_parallel_review':2,'nonbinding_parallel_review':3,'systemic_parallel_review':4}
    candidates.sort(key=lambda x:(precedence[x['priority_class']],x['remedy_id']))
    letters.sort(key=lambda x:(precedence[next(y['priority_class'] for y in candidates if y['remedy_id']==x['remedy_id'])],x['remedy_id']))
    warnings = ['Candidate order is a review queue, not a recommendation or sequence of legally required steps.',
      'Clarification, SOLVIT, Commission or JO complaints do not automatically suspend national appeal deadlines.',
      'Do not calculate dates, send correspondence, or infer violation or eligibility from a fictional source-anchored predicate.',
      'Review potentially urgent formal appeal independently and in parallel; no waiting step is authorized.']
    missing = ['Official current and operative national legislation and any exceptions',
        'Authenticated communications and independent fact assessment',
        'Current competent recipient and applicable court/appeal procedure',
        'Decision service dates, extension/suspension rules and filing proof',
        'Independent legal-semantic review including unresolved C15f, 21 incomplete C1 source notes, and independent full-source verification',
        'Private-data authorization and trustworthy human approval before any real use']
    result={'milestone':'C17b-c-d','mode':'fictional_review_only','case_id':'L'+str(n),
       'procedure_stage':case['procedure_stage'],'input_digests':{'case':digest(case),'upstream_c17':digest(q),**q['input_digests']},
       'catalog_digests':catalog_digests,
       'source_assurance_warning':'National-law modules contain curated identity notes, not complete authoritative statutes; C1 active Article 2(2)(a) targeted repair does not establish full-source completeness; 21 C1 identity-only notes persist; no real-case merits review.',
       'legal_violation_status':'not_determined','verified_legal_merits':False,'send_authorized':False,
       'requires_human_review':True, 'c17_questions':q['questions'],'remedy_candidates':candidates,
       'excluded_routes':blocked,'parallelism_warnings':warnings,'correspondence_drafts':letters,
       'decision_gate':'blocked_pending_source_factual_and_human_review','missing_prerequisites':missing,
       'review_facts':[{'rule_id':x['rule_id'],'facts_to_check':x['factual_items_for_verification']} for x in q['questions']]}
    validate_obj('c17-review-plan',result)
    return result


def bind_verified_c6_release(plan, workdir):
    """Bind an already completed C6/C7 *synthetic* release, without promoting it.

    Replays the C6 verifier (which rechecks the controller, source bytes, issue
    index and stage hashes), then compares original C12/C13 to the C17 inputs.
    """
    from c6_integration import verify_release
    path=Path(workdir)
    if path.is_symlink() or not path.is_dir():
        raise ValueError('c17_missing_safe_c6_workdir')
    verification=verify_release(path.resolve())
    if (verification['status']!='verified_c6_synthetic_release' or
            verification['case_id'] != 'CASE-C10-'+plan['case_id']):
        raise ValueError('c17_c6_case_or_release_mismatch')
    c12=load_json(safe_file(path,'stages/c12.json'))
    c13=load_json(safe_file(path,'stages/c13.json'))
    if (digest(c12)!=plan['input_digests']['c12'] or
            digest(c13)!=plan['input_digests']['c13']):
        raise ValueError('c17_c6_stage_does_not_match_c17_source_anchored_inputs')
    plan['c6_verified_release_binding']={'status':'verified_c6_synthetic_release',
       'case_id':verification['case_id'],'c6_release_sha256':verification['c6_release_sha256'],
       'c12_sha256':digest(c12),'c13_sha256':digest(c13),
       'verification_assurance':'deterministic_replay_only_not_legal_validation'}
    validate_obj('c17-review-plan',plan)
    return plan


def render(plan):
    lines=[f'# C17b/c/d fictional remedy review: {plan["case_id"]}','',
           '**NOT FOR SENDING. NOT LEGAL ADVICE. NO AUTOMATED REMEDY SELECTION.**',
           '', f'Procedure stage (fictional): `{plan["procedure_stage"]}`.',
           'No alleged breach, remedy eligibility, legal deadline or competent recipient is established.','',
           'C6/C7 synthetic-release binding: '+('verified deterministic replay (not legal merits)' if 'c6_verified_release_binding' in plan else 'not bound to a released C6 case')+'.','',
           '## Source-qualified remedy candidates (not recommendations)','']
    for c in plan['remedy_candidates']:
        lines.extend([f'### {c["remedy_id"]} — {c["category"]}','',
          'Status: `candidate_for_human_review` · Review queue: `'+c['priority_class']+'`',
          'Matched issue IDs: '+', '.join('`'+r+'`' for r in c['matched_rule_ids']),
          'Authority identifier: `'+c['authority_ref']+'` (competence unverified).',
          'Proposed purpose: '+c['intended_outcome_for_review'],'',
          '**Powers to verify:** '+ '; '.join(c['powers_to_verify']),
          '**Limits:** '+ '; '.join(c['limits']),
          '**Deadline status:** '+c['deadline']['rule']+' Calculation: HUMAN ONLY.','',
          '**Prerequisites to verify:**'])
        lines.extend('- '+v for v in c['prerequisites_to_verify'])
        lines+=['','**Evidence to preserve or assess:**']
        lines.extend('- '+v for v in c['evidence_to_preserve'])
        lines+=['','**Source IDs (inspect current official text):** '+', '.join('`'+r+'`' for r in c['source_refs']),'']
    lines+=['## Excluded routes and competence gates','']
    lines.extend('- `'+r['remedy_id']+'`: '+r['reason'] for r in plan['excluded_routes'])
    if not plan['excluded_routes']:lines.append('- No triggered route was excluded by a structural gate; eligibility remains unverified.')
    lines+=['','## Parallel-remedy and deadline warnings','']
    lines.extend('- '+v for v in plan['parallelism_warnings'])
    lines+=['','## Drafts for explicit human redrafting (DO NOT SEND)','']
    for d in plan['correspondence_drafts']:
        lines+=['### '+d['remedy_id'],'','```text',d['text'].strip(),'```','']
    lines+=['## Unresolved gates','']
    lines.extend('- '+v for v in plan['missing_prerequisites'])
    lines+=['', '**Final gate: `blocked_pending_source_factual_and_human_review`**','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--sweden-module',type=Path,required=True)
    p.add_argument('--turkiye-module',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--case',type=int,action='append',choices=range(1,9))
    p.add_argument('--c6-evidence-root',type=Path,help='Directory with already released C6 workdirs L1 ... L8; each is independently replay-verified')
    args=p.parse_args()
    catalogs,digests=load_catalogs(args.sweden_module,args.turkiye_module)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for n in args.case or range(1,9):
        data=build(n,catalogs,digests)
        if args.c6_evidence_root is not None:
            bind_verified_c6_release(data,args.c6_evidence_root/f'L{n}')
        target=args.output_dir / f'L{n}-c17-remedies'
        target.with_suffix('.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        target.with_suffix('.md').write_text(render(data),encoding='utf-8')
        print(f'L{n}: candidates={len(data["remedy_candidates"])} blocked={len(data["excluded_routes"])} drafts={len(data["correspondence_drafts"])}')

if __name__=='__main__':main()
