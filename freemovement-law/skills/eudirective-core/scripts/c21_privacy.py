#!/usr/bin/env python3
"""C21: deterministic, Python-only, non-send SYNTHETIC privacy previews.

The tool does NOT establish anonymity, GDPR compliance, protected host isolation,
secure deletion, or suitability of its output for publication or telemetry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

from contract_validate import ContractError, canonical_bytes, digest_obj, load_json, validate_obj

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / 'references/privacy/c21-synthetic-purpose-policy.json'
# Changing policy requires a reviewed edit to the skill code AND regeneration of this pin.
POLICY_BYTES_SHA256 = 'cfb42ae7bb3cabf96dce3bdf501c950ecc43672e5900c59c167dbff47fe96fc0'
REGISTRY_PATH = ROOT / 'references/privacy/c21-enrolled-fixtures.json'
REGISTRY_BYTES_SHA256 = '76254ce9056a81cbea8d503e7dd98b553915dd61ebc123dc649ea48cb2e43dfe'
VERSION = '0.1.0'
STORY_PROFILES = {'internal_review_preview', 'public_story_preview'}
REVIEW_BLOCKING_TAGS = {
    'unusual_family', 'unique_topology', 'public_searchable_quote',
    'precise_procedural_event', 'repeated_pseudonym',
}
DIRECT_TEXT_CLASSES = {'direct_identifier', 'sensitive', 'quasi_identifier'}

# Deliberately bounded patterns. Unrecognised formats/names are NOT deemed safe.
EMAIL = re.compile(r'(?i)(?<![\w@])[a-z0-9._%+\-]{1,65}@[a-z0-9.\-]{1,180}\.[a-z]{2,24}(?!\w)')
URL = re.compile(r'(?i)\b(?:https?://|www\.)[^\s<>\]})]+')
IBAN = re.compile(r'(?i)(?<!\w)[a-z]{2}\d{2}(?:[\s-]?[a-z0-9]){11,30}(?!\w)')
ISO_DATE = re.compile(r'(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)')
EU_DATE = re.compile(r'(?<!\d)\d{1,2}[./]\d{1,2}[./]\d{4}(?!\d)')
MONTH_DATE = re.compile(r'(?i)\b\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|januari|februari|mars|maj|juni|juli|augusti|september|oktober|november|december|ocak|subat|şubat|mart|nisan|mayis|mayıs|haziran|temmuz|agustos|ağustos|eylul|eylül|ekim|kasim|kasım|aralik|aralık)\s+\d{4}\b')
PHONE = re.compile(r'(?<!\w)(?:\+|00)?\d[\d ()\-.]{7,22}\d(?!\w)')
LABELED = re.compile(r'(?i)\b(?:passport|case\s+(?:id|number)|reference\s+(?:number|no\.?|#)|file\s+(?:number|no\.?|#)|residence\s+card\s+(?:number|no\.?|#))\s*[:#]?\s*[a-z0-9][a-z0-9/\-]{5,}\b')
IPV4 = re.compile(r'(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)')
QUOTED = re.compile(r'[“\"]([^”\"]{28,})[”\"]')
PATTERNS = [
    (EMAIL, '[EMAIL]'), (URL, '[URL]'), (IBAN, '[FINANCIAL_ID]'),
    (ISO_DATE, '[DATE]'), (EU_DATE, '[DATE]'), (MONTH_DATE, '[DATE]'),
    (LABELED, '[REFERENCE]'), (PHONE, '[PHONE]'), (IPV4, '[NETWORK_ID]'),
    (QUOTED, '[REMOVED_QUOTE]'),
]


class PrivacyError(Exception):
    """Only fixed error codes are emitted to avoid reflecting raw case text."""


def norm(s: str) -> str:
    return unicodedata.normalize('NFKC', s)


def policy():
    if hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest() != POLICY_BYTES_SHA256:
        raise PrivacyError('modified_policy_not_bound_to_engine')
    try:
        obj = load_json(POLICY_PATH)
        validate_obj('c21-privacy-policy', obj)
    except (ContractError, ValueError):
        raise PrivacyError('invalid_bundled_policy') from None
    names = [p['name'] for p in obj['profiles']]
    if len(names) != len(set(names)) or set(names) != {
        'internal_review_preview', 'public_story_preview',
        'feedback_aggregate_preview', 'c17_feedback_preview',
    }:
        raise PrivacyError('missing_or_duplicate_locked_profile')
    for profile in obj['profiles']:
        ids = [r['field_id'] for r in profile['fields']]
        if len(ids) != len(set(ids)):
            raise PrivacyError('duplicate_locked_field')
        for rule in profile['fields']:
            if (rule['transform'] == 'enum') != ('allowed_values' in rule):
                raise PrivacyError('invalid_locked_field_constraint')
    return obj


def enrolled_registry():
    # A self-asserted synthetic flag is insufficient: this release accepts
    # only developer-enrolled fixture digests through its public CLI.
    try:
        if hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest() != REGISTRY_BYTES_SHA256:
            raise PrivacyError('modified_fixture_registry_not_bound_to_engine')
        obj = load_json(REGISTRY_PATH)
        if not (obj.get('registry_version') == VERSION and
                isinstance(obj.get('inputs'), dict) and
                isinstance(obj.get('c17_plans'), dict) and
                set(obj['c17_plans']) == {'L1','L2','L3','L4','L5','L6','L7','L8'}):
            raise PrivacyError('invalid_fixture_registry')
        return obj
    except (ContractError,OSError,ValueError):
        raise PrivacyError('invalid_fixture_registry') from None


def vetted_input(path: Path):
    try:
        inp = load_json(path)
        validate_obj('c21-privacy-input', inp)
    except (ContractError, OSError, ValueError):
        raise PrivacyError('invalid_or_unsafe_fixture') from None
    # A self-declared synthetic flag is an engineering guard, not proof of fiction.
    if inp['data_class'] != 'synthetic':
        raise PrivacyError('real_or_public_person_data_not_authorized')
    fields = [r['field_id'] for r in inp['fields']]
    if len(fields) != len(set(fields)):
        raise PrivacyError('duplicate_field_id')
    pins = enrolled_registry()['inputs']
    if digest_obj(inp) != pins.get(inp['case_ref']):
        raise PrivacyError('unapproved_synthetic_fixture')
    return inp


def aliases(inp):
    """Explicit roles first; all dropped quasi/direct strings then become generic terms."""
    dictionary = {}
    for rec in inp['redaction_terms']:
        term = norm(rec['value']).strip()
        if len(term) < 3:
            raise PrivacyError('redaction_term_too_short')
        key = term.casefold()
        if key in dictionary and dictionary[key][1] != rec['role']:
            raise PrivacyError('ambiguous_redaction_alias')
        dictionary[key] = (term, rec['role'])
    for rec in inp['fields']:
        if rec['classification'] in DIRECT_TEXT_CLASSES and rec['field_id'] != 'narrative' and isinstance(rec['value'], str):
            term = norm(rec['value']).strip()
            if len(term) < 3:
                continue
            if term.casefold() not in dictionary:
                role = ('DATE' if rec['field_id'].endswith('_date') and ISO_DATE.fullmatch(term)
                        else 'PLACE' if rec['classification'] == 'quasi_identifier' else 'IDENTIFIER')
                dictionary[term.casefold()] = (term, role)
    case_ref = norm(inp['case_ref']).strip()
    if len(case_ref) >= 3 and case_ref.casefold() not in dictionary:
        dictionary[case_ref.casefold()] = (case_ref, 'IDENTIFIER')
    return sorted(dictionary.values(), key=lambda x: (-len(x[0]), x[0].casefold()))


def scrub(text: str, known):
    text = norm(text)
    for term, role in sorted(known, key=lambda x: (-len(x[0]), x[0].casefold())):
        # Word boundaries avoid rewriting the middle of unrelated words.
        pat = re.compile(r'(?<!\w)' + re.escape(term) + r'(?!\w)', flags=re.IGNORECASE)
        text = pat.sub('[' + role + ']', text)
    for pat, marker in PATTERNS:
        text = pat.sub(marker, text)
    # Detect still-matched identifiers; a failed scan blocks the entire preview.
    if any(p.search(text) for p, _ in PATTERNS):
        raise PrivacyError('residual_known_identifier_pattern')
    for term, _ in known:
        if re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', text, flags=re.IGNORECASE):
            raise PrivacyError('declared_sensitive_term_retained')
    return text


def profile_rules(pol, selected):
    profiles = [x for x in pol['profiles'] if x['name'] == selected]
    if len(profiles) != 1:
        raise PrivacyError('unknown_profile')
    return profiles[0]['fields']


def transform(rule, field, known):
    name = rule['field_id']
    kind = rule['transform']
    value = field['value']
    classification = field['classification']
    if kind == 'enum':
        if (classification in DIRECT_TEXT_CLASSES or not isinstance(value, str) or
                value not in rule['allowed_values']):
            raise PrivacyError('unsafe_or_non_whitelisted_enum_' + name)
        return value
    if kind == 'year_only':
        if classification != 'quasi_identifier' or not isinstance(value, str):
            raise PrivacyError('invalid_date_classification_' + name)
        # Strict complete ISO date, no arbitrary slicing or forged date.
        from datetime import date
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise PrivacyError('invalid_date_' + name)
        try:
            date.fromisoformat(value)
        except ValueError:
            raise PrivacyError('invalid_date_' + name) from None
        return value[:4]
    if kind == 'scrub_text':
        if (not isinstance(value, str) or classification not in {'sensitive', 'case_fact'} or
                len(value) > 12000):
            raise PrivacyError('unsafe_text_classification_' + name)
        return scrub(value, known)
    raise PrivacyError('unrecognized_policy_transform')


def build(inp, pol, selected):
    if inp['data_class'] != 'synthetic':
        raise PrivacyError('real_or_public_person_data_not_authorized')
    selected_rules = profile_rules(pol, selected)
    given = {f['field_id']: f for f in inp['fields']}
    known = aliases(inp)
    retained = {}
    flags = {'anonymity_unproven', 'external_auxiliary_data_not_checked', 'editorial_review_required'}
    # Linkability can arise from facts excluded by the purpose allowlist. If a
    # dropped fact is tagged as highly linkable, a retained narrative may still
    # describe or paraphrase it. Withhold the entire narrative in the external-
    # facing story rehearsal instead of relying on text matching alone.
    cross_field_story_risk = selected == 'public_story_preview' and any(
        REVIEW_BLOCKING_TAGS & set(f['risk_tags'])
        for f in inp['fields'] if f['field_id'] != 'narrative'
    )
    for rule in selected_rules:
        field = given.get(rule['field_id'])
        if field is None:
            continue  # No fabricated facts or default values.
        if selected == 'public_story_preview' and rule['transform'] == 'scrub_text':
            if REVIEW_BLOCKING_TAGS & set(field['risk_tags']):
                raise PrivacyError('high_linkability_story_requires_redesign')
            if cross_field_story_risk:
                # Suppression must not become a validation bypass for unsafe
                # classifications, oversized payloads or non-text values.
                if (not isinstance(field['value'], str) or
                        field['classification'] not in {'sensitive', 'case_fact'} or
                        len(field['value']) > 12000):
                    raise PrivacyError('unsafe_text_classification_narrative')
                flags.add('narrative_suppressed_due_to_cross_field_linkability')
                continue  # No narrative, even after scrubbing known identifiers.
        value = transform(rule, field, known)
        retained[rule['field_id']] = value
        if rule['transform'] == 'scrub_text':
            flags.add('free_text_can_contain_undetected_identifiers')
        if field['risk_tags']:
            flags.add('case_context_linkability_requires_review')
    if not retained:
        raise PrivacyError('no_necessary_fields_present')
    if selected in {'feedback_aggregate_preview', 'c17_feedback_preview'}:
        flags.add('cohort_aggregation_not_performed')
        flags.add('single_record_not_releasable')
    if any(f['risk_tags'] for f in inp['fields'] if f['field_id'] not in retained):
        flags.add('dropped_rare_facts_may_still_be_in_narrative')
    if selected == 'public_story_preview':
        flags.add('public_search_reidentification_not_tested')
    view = {
        'c21_version': VERSION,
        'status': 'synthetic_preview_only',
        'profile': selected,
        'policy_id': pol['policy_id'],
        'fields': retained,
        'minimisation': {
            'input_fields': len(given),
            'retained_fields': len(retained),
            'dropped_fields': len(given) - len(retained),
        },
        'risk_flags': sorted(flags),
        'external_disclosure_authorized': False,
        'human_review_required': True,
        'private_data_enabled': False,
        'limitations': [
            'Preview only: not anonymous by proof, not safe to publish or transmit.',
            'Unknown names, paraphrases, images and rare cross-case details may remain.',
            'No independent host, secure-deletion, identity, legal-merits or GDPR-compliance verification.',
        ],
    }
    # No stable pseudonym, input digest, source case ID, raw label or local path in output.
    validate_obj('c21-privacy-view', view)
    rendered = json.dumps(view, ensure_ascii=False, sort_keys=True)
    for term, _ in known:
        if re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', rendered, flags=re.IGNORECASE):
            raise PrivacyError('declared_identifier_in_output')
    return view


def from_c17_plan(plan):
    """Build deliberately coarse C17 preview; never copy full text or case identity."""
    try:
        validate_obj('c17-review-plan', plan)
    except ContractError:
        raise PrivacyError('invalid_c17_plan') from None
    if not (plan['mode'] == 'fictional_review_only' and
            plan['case_id'] in {'L1','L2','L3','L4','L5','L6','L7','L8'} and
            plan['legal_violation_status'] == 'not_determined' and
            plan['verified_legal_merits'] is False and
            plan['send_authorized'] is False and
            plan['requires_human_review'] is True and
            plan['decision_gate'] == 'blocked_pending_source_factual_and_human_review' and
            all(c['human_review_required'] for c in plan['remedy_candidates']) and
            all(d['send_authorized'] is False and d['human_review_required'] is True
                for d in plan['correspondence_drafts'])):
        raise PrivacyError('c17_approval_or_legal_merit_gate_failed')
    if digest_obj(plan) not in enrolled_registry()['c17_plans'].get(plan['case_id'],[]):
        raise PrivacyError('unenrolled_c17_plan')
    return {
        'input_version': VERSION,
        'data_class': 'synthetic',
        'case_ref': 'SYN-C17-' + plan['case_id'],
        'fields': [
            {'field_id':'plan_kind','classification':'case_fact','value':'fictional_review','risk_tags':[]},
            {'field_id':'route_presence','classification':'case_fact',
             'value':'present' if plan['remedy_candidates'] else 'none','risk_tags':[]},
        ],
        'redaction_terms': [],
    }


def receipt_for(view, pol):
    receipt = {
        'c21_version': VERSION,
        'policy_sha256': POLICY_BYTES_SHA256,
        'view_sha256': digest_obj(view),
        'profile': view['profile'],
        'verification': 'deterministic_only_not_anonymity_or_host_attestation',
        'external_disclosure_authorized': False,
        'private_data_enabled': False,
    }
    validate_obj('c21-privacy-receipt', receipt)
    return receipt


def atomic_new(path: Path, obj):
    # Never overwrite a previous review artifact, and do not follow a symlink.
    if path.exists() or path.is_symlink():
        raise PrivacyError('output_already_exists')
    payload = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False).encode('utf-8') + b'\n'
    fd, tmp = tempfile.mkstemp(prefix='.c21-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        # Exclusive creation prevents overwriting targets under a racing process.
        os.link(tmp, path)
        os.unlink(tmp)
    finally:
        if os.path.lexists(tmp):
            os.unlink(tmp)


def write_preview(outdir: Path, view, receipt):
    if outdir.exists() or outdir.is_symlink():
        raise PrivacyError('output_directory_must_be_new')
    if outdir.parent.is_symlink():
        raise PrivacyError('unsafe_output_parent')
    outdir.mkdir(mode=0o700, parents=True, exist_ok=False)
    try:
        atomic_new(outdir / 'minimised-view.json', view)
        atomic_new(outdir / 'privacy-receipt.json', receipt)
    except Exception:
        # The input is synthetic, but fail closed and avoid publishing partial previews.
        for p in outdir.glob('*.json'):
            p.unlink()
        outdir.rmdir()
        raise


def main():
    parser = argparse.ArgumentParser(description='C21 deterministic synthetic privacy review (non-send)')
    sub = parser.add_subparsers(dest='command', required=True)
    s = sub.add_parser('preview')
    s.add_argument('--input', type=Path, required=True)
    s.add_argument('--profile', choices=['internal_review_preview','public_story_preview','feedback_aggregate_preview'], required=True)
    s.add_argument('--output-dir', type=Path, required=True)
    s = sub.add_parser('c17-preview')
    s.add_argument('--plan', type=Path, required=True)
    s.add_argument('--output-dir', type=Path, required=True)
    s = sub.add_parser('verify')
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument('--input', type=Path)
    g.add_argument('--plan', type=Path)
    s.add_argument('--profile', choices=['internal_review_preview','public_story_preview','feedback_aggregate_preview','c17_feedback_preview'], required=True)
    s.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        pol = policy()
        if args.command == 'c17-preview' or (args.command == 'verify' and args.plan):
            if args.command == 'verify' and args.profile != 'c17_feedback_preview':
                raise PrivacyError('plan_requires_c17_profile')
            try:
                plan = load_json(args.plan)
            except (OSError, ContractError):
                raise PrivacyError('invalid_c17_plan') from None
            inp = from_c17_plan(plan)
            selected = 'c17_feedback_preview'
        else:
            if args.profile == 'c17_feedback_preview':
                raise PrivacyError('c17_profile_requires_validated_plan')
            inp = vetted_input(args.input)
            selected = args.profile
        view = build(inp, pol, selected)
        receipt = receipt_for(view, pol)
        if args.command == 'verify':
            try:
                previous_view = load_json(args.output_dir/'minimised-view.json')
                previous_receipt = load_json(args.output_dir/'privacy-receipt.json')
                validate_obj('c21-privacy-view', previous_view)
                validate_obj('c21-privacy-receipt', previous_receipt)
            except (OSError, ContractError, ValueError):
                raise PrivacyError('missing_or_invalid_view_or_receipt') from None
            if previous_view != view or previous_receipt != receipt:
                raise PrivacyError('replay_or_digest_mismatch')
            status = 'verified_synthetic_replay_only'
        else:
            write_preview(args.output_dir, view, receipt)
            status = 'synthetic_preview_written'
        print(json.dumps({'status': status, 'profile': selected,
                          'view_sha256': receipt['view_sha256'],
                          'external_disclosure_authorized': False,
                          'private_data_enabled': False}, sort_keys=True))
        return 0
    except (PrivacyError, ContractError, OSError, ValueError) as err:
        code = str(err) if isinstance(err, PrivacyError) else 'privacy_boundary_failure'
        print(json.dumps({'status': 'blocked', 'reason': code}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
