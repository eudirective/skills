#!/usr/bin/env python3
"""C18 deterministic source audit; local hashes and a targeted official excerpt only.

The report does not assert current legality, full text equivalence to EUR-Lex,
or suitability for private applicant cases. Identity notes are unresolved gaps.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from contract_validate import load_json, digest_obj, validate_obj
from verify_bundled_source_pack import inspect as inspect_source_pack
from source_library_paths import compatibility_root

ROOT = Path(__file__).resolve().parents[1]
PACK = compatibility_root()
MANIFEST = PACK/'core-source-pack-manifest-0.6.1.json'
ARCHIVE = PACK/'core-source-pack-manifest-0.6.0.json'
REPAIR = PACK/'c18-directive-art2-restoration.json'
ART2_ID = 'eu:32004l0038'
ART2_REL = 'sources/eu/CELEX_02004L0038-20110616_EN_TXT.md'
OFFICIAL_ART2_WORDING = '(a)\n\nthe spouse;'
PINNED_REPAIR_JSON_SHA256 = '3fd63233fa15fc2bddac344236324abd32d37a23ef25d22a5c78295e05163ccb'

class C18AuditError(ValueError): pass

def insist(ok, code):
    if not ok: raise C18AuditError(code)

def audit() -> dict:
    inspection = inspect_source_pack()  # C7 trust + all 47 hashes and exact file inventory
    m = load_json(MANIFEST)
    prev = load_json(ARCHIVE)
    proof = load_json(REPAIR)
    insist(hashlib.sha256(REPAIR.read_bytes()).hexdigest() == PINNED_REPAIR_JSON_SHA256, 'art2_provenance_bytes_modified')
    validate_obj('core-source-pack', m)
    insist(m.get('pack_version') == '0.6.1' and m.get('manifest_version') == '0.6.1', 'active_pack_not_0_6_1')
    insist(prev.get('pack_version') == '0.6.0' and len(prev['sources']) == 46, 'archive_not_retained')
    insist(proof['old_pack_manifest_canonical_sha256'] == digest_obj(prev), 'archived_pack_digest_changed')
    insist(proof['new_pack_manifest_canonical_sha256'] == digest_obj(m), 'active_pack_digest_or_proof_changed')
    old_sources = {s['source_id']:s for s in prev['sources']}
    new_sources = {s['source_id']:s for s in m['sources']}
    insist(old_sources.keys() == new_sources.keys() and len(new_sources) == 46, 'source_registry_changed_outside_scope')
    changed = sorted(k for k in new_sources if old_sources[k] != new_sources[k])
    insist(changed == [ART2_ID], 'unexpected_source_record_change')
    oldrep = old_sources[ART2_ID]['representations'][0]
    rep = new_sources[ART2_ID]['representations'][0]
    insist(oldrep['sha256'] == proof['old_representation_sha256'] and
           oldrep['bytes'] == proof['old_representation_bytes'] and
           rep['sha256'] == proof['new_representation_sha256'] and
           rep['bytes'] == proof['new_representation_bytes'] and
           rep['relative_path'] == ART2_REL, 'art2_repair_provenance_inconsistent')
    insist(proof['exact_article_fragment'] == OFFICIAL_ART2_WORDING and
           proof['official_consolidation_url'] ==
             'https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02004L0038-20110616' and
           proof['verified_date'] == '2026-10-10', 'art2_official_excerpt_provenance_changed')
    # Prevent promotional provenance tampering: only the explicitly checked clause may be labelled verified.
    insist(
        proof.get('official_initial_act_url') ==
          'https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32004L0038' and
        proof.get('verified_scope') ==
          'Directive 2004/38 Article 2(2)(a), English definition of spouse, and article-local placement only' and
        proof.get('verified_method') ==
          'manual visual textual cross-check of EUR-Lex HTML versions (not official-file byte comparison)' and
        proof.get('legal_semantic_validation') == 'not_performed' and
        proof.get('inherited_material_warning') ==
          'All other source passages and source notes retain previous provenance; they were not independently compared with official EUR-Lex content in C18.',
        'art2_verification_scope_untrusted')
    text = (PACK/ART2_REL).read_text(encoding='utf-8')
    start = text.index('\nArticle 2\n\nDefinitions\n')
    end = text.index('\nArticle 3\n',start)
    art2 = text[start:end]
    insist(art2.count(OFFICIAL_ART2_WORDING) == 1, 'art2_a_missing_or_repeated')
    insist(art2.index("‘family member’ means:") < art2.index(OFFICIAL_ART2_WORDING) <
           art2.index('(b)\n\nthe partner'), 'art2_a_wrong_article_or_order')
    assert inspection['source_representations'] == 47
    sources=[]
    for src in m['sources']:
        reps=[]
        for r in src['representations']:
            raw = (PACK/r['relative_path']).read_bytes()
            insist(len(raw) == r['bytes'] and hashlib.sha256(raw).hexdigest() == r['sha256'],
                   'c18_representation_integrity_changed:' + r['relative_path'])
            kind = r['kind']
            extent = ('identity_version_note_only' if kind == 'verified_source_note' else
                      'bundled_text_extent_not_independently_assessed' if kind == 'bundled_text' else
                      'other_unassessed_representation')
            if src['source_id'] == ART2_ID:
                extent = 'bundled_text_with_article_2_2_a_locally_restored_and_official_html_excerpt_checked'
            reps.append({'path':r['relative_path'],'kind':kind,'bytes':len(raw),
                         'sha256':r['sha256'],'content_extent':extent,
                         'local_byte_integrity':'sha256_verified',
                         'official_original_byte_equivalence':'not_verified'})
        sources.append({'source_id':src['source_id'],'source_type':src['source_type'],
                        'owner_family':'core','official_url':src['canonical_url'],
                        'source_verification_date_on_manifest':src['verification_date'],
                        'freshness':'manifest_date_only_not_independent_currentness_check',
                        'has_full_source_gap':any(r['kind']=='verified_source_note' for r in src['representations']),
                        'representations':reps})
    gaps=[s['source_id'] for s in sources if s['has_full_source_gap']]
    insist(len(gaps) == 21 and inspection['verified_source_notes'] == 21, 'c18_gap_count_changed')
    return {
        'audit_version':'0.1.0','release':'C18','date':'2026-10-10',
        'verification_scope':'local_byte_integrity_plus_targeted_article_2_2_a_official_html_excerpt',
        'pack_version':m['pack_version'],'manifest_canonical_sha256':digest_obj(m),
        'physical_integrity':'47_of_47_locally_sha256_verified',
        'logical_source_count':len(sources),'representation_count':47,
        'bundled_text_count':inspection['bundled_text_representations'],
        'identity_only_note_count':len(gaps),
        'identity_only_gap_source_ids':gaps,
        'article_2_2_a':{'source_id':ART2_ID,'status':'restored_targeted_official_html_excerpt_checked',
                         'verified_date':proof['verified_date'], 'source_representation_sha256':rep['sha256'],
                         'official_consolidation_url':proof['official_consolidation_url'],
                         'full_directive_official_byte_comparison':'not_performed'},
        'other_official_source_text_and_live_currency_verification':'not_performed',
        'independent_legal_semantic_validation':'not_performed',
        'private_applicant_readiness':'blocked',
        'source_records':sources,
    }

def render(a:dict)->str:
    lines=['# C18 — Source-integrity and completeness register','',
           f"- Active C1: `{a['pack_version']}`, manifest SHA-256 `{a['manifest_canonical_sha256']}`",
           f"- Local physical audit: **{a['physical_integrity']}**; {a['logical_source_count']} logical sources.",
           '- Targeted verified clause: Directive 2004/38 Article 2(2)(a), English spouse definition (official EUR-Lex HTML manual comparison).',
           f"- Incomplete authoritative text: **{a['identity_only_note_count']} identity/version notes**, not full judgments or operational pages.",
           '- Official byte equivalence of the full pack, all-source currency, legal merits and private-case readiness: **not verified**.',
           '', '## Remaining full-text gaps','']
    for s in a['source_records']:
        if s['has_full_source_gap']:
            lines.append(f"- `{s['source_id']}` — {s['source_type']} — {s['official_url']}")
    lines.extend(['','## Interpretive constraints','',
                  'A SHA-256 match proves that bundled bytes match the pinned local manifest. It does not establish official-source authenticity, completeness of judgments, legislative currency, lawful applicability, or sound legal reasoning.',
                  'No national legal texts were changed. The two country modules remain owned by their respective maintainers.', ''])
    return '\n'.join(lines)

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--json-output',type=Path)
    p.add_argument('--markdown-output',type=Path)
    args=p.parse_args()
    a=audit()
    for dest,body in ((args.json_output,json.dumps(a,indent=2,sort_keys=True,ensure_ascii=False)+'\n'),
                      (args.markdown_output,render(a))):
        if dest:
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(body,encoding='utf-8')
    print(json.dumps({'status':'verified_local_integrity_with_text_gaps',
                      'pack_version':a['pack_version'],'representation_count':a['representation_count'],
                      'identity_only_gaps':len(a['identity_only_gap_source_ids']),
                      'legal_semantic_validation':'not_performed'},sort_keys=True))
    return 0
if __name__=='__main__':raise SystemExit(main())
