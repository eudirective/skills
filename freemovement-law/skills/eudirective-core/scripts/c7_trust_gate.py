#!/usr/bin/env python3
"""C7 deterministic trust gate for a *fixed* synthetic fixture/source-metadata release.

An in-package code-pinned policy is a local release trust anchor, not a signature,
not evidence that the actual EU source texts were verified in this runtime, and
not a guarantee that the host can prevent other paths for real personal data.
"""
from pathlib import Path, PurePosixPath
import hashlib
import re
from datetime import date, datetime, timedelta, timezone

from contract_validate import load_json, digest_obj, ContractError
from source_library_paths import compatibility_root

ROOT = Path(__file__).resolve().parents[1]
POLICY_FILE = ROOT / 'references/trust/c7-trust-policy.json'
BUNDLED_SOURCE_ROOT = compatibility_root()
# Independent of the supplied source manifest or caller-provided fixture labels.
# Changing the trust inventory requires reviewing the fixture/source and releasing
# a changed trusted code root (including this constant).
TRUST_POLICY_SHA256 = '3a15f9ad3744071ba68698da14d214dcbd1c85df0e999954aef4c2ee6dc48bc8'


class C7TrustError(Exception):
    pass

# Only these fixture-only opaque labels can enter persistent C6 controller state.
# This is a development/test CLI, not a registration mechanism for user labels.
APPROVED_SYNTHETIC_RUN_IDS = frozenset({'RUN-C6-TEST', 'RUN-C6-1', 'RUN-C7-DEMO'} | {f'RUN-C10-L{i}' for i in range(1,9)})
UTC_TIMESTAMP = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$')
SOURCE_AS_OF_POLICY_VERSION = '0.1.0'
SOURCE_AGE_LIMITS_DAYS = {
    'legislation_consolidation': 30,
    'commission_guidance': 14,
    'operational_guidance': 7,
}
FIXED_SOURCE_TYPES = frozenset({'cjeu_judgment', 'charter', 'commission_recommendation', 'commission_staff_working_document'})
SOURCE_TYPE_AGE_CLASS = {
    'directive_consolidated': 'legislation_consolidation',
    'regulation_consolidated': 'legislation_consolidation',
    'commission_staff_working_document': 'commission_guidance',
    'commission_recommendation': 'commission_guidance',
    'commission_notice': 'commission_guidance',
    'commission_handbook': 'commission_guidance',
    'commission_operational_guidance_page': 'operational_guidance',
    'ombudsman_operational_guidance_page': 'operational_guidance',
}


def require_synthetic_run_metadata(run_id, time_of_check):
    """Fail before workspace creation; never persist arbitrary caller identifiers."""
    if not isinstance(run_id, str) or run_id not in APPROVED_SYNTHETIC_RUN_IDS:
        raise C7TrustError('unapproved_synthetic_run_id')
    return parse_utc_time_of_check(time_of_check)


def parse_utc_time_of_check(value):
    """Canonical second-resolution UTC only; no unstructured text or time-zone ambiguity."""
    if not isinstance(value, str) or not UTC_TIMESTAMP.fullmatch(value):
        raise C7TrustError('invalid_synthetic_time_of_check')
    try:
        parsed = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise C7TrustError('invalid_synthetic_time_of_check') from e
    if parsed.strftime('%Y-%m-%dT%H:%M:%SZ') != value:
        raise C7TrustError('noncanonical_synthetic_time_of_check')
    return parsed


def strict_source_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        raise C7TrustError('invalid_source_verification_date')
    try:
        return date.fromisoformat(value)
    except ValueError as e:
        raise C7TrustError('invalid_source_verification_date') from e


def source_freshness_class(source):
    """Identity-fixed authorities never inherit mutable-page age thresholds."""
    kind = source.get('source_type')
    state = source.get('freshness_state')
    if kind in FIXED_SOURCE_TYPES and state == 'fixed_verified':
        return 'fixed_identity'
    if kind in SOURCE_TYPE_AGE_CLASS and state == 'current':
        return SOURCE_TYPE_AGE_CLASS[kind]
    raise C7TrustError('unsupported_source_as_of_classification')


def require_source_as_of(pack, time_of_check):
    """A dated *local metadata-age* check, never a live source-status certification.

    A fixed-identity judgment is checked for chronology, not mutable-page expiry.
    Every mutable source must have a supported type, a recorded verified date,
    and an age within the class-specific bounded local review window.
    """
    instant = parse_utc_time_of_check(time_of_check)
    as_of = instant.date()
    require_source_pack(pack)  # Always bind against the pinned, trusted pack.
    pack_check = strict_source_date(pack.get('live_verification_date'))
    if pack_check > as_of:
        raise C7TrustError('source_verification_after_run_as_of')
    fixed = 0
    mutable = 0
    expired = []
    for source in pack['sources']:
        verification = strict_source_date(source.get('verification_date'))
        if verification > as_of:
            raise C7TrustError('source_verification_after_run_as_of')
        source_class = source_freshness_class(source)
        version_date = source.get('current_version_date')
        if version_date and strict_source_date(version_date) > as_of:
            raise C7TrustError('source_version_after_run_as_of')
        if source_class == 'fixed_identity':
            fixed += 1
            continue
        mutable += 1
        if (as_of - verification).days > SOURCE_AGE_LIMITS_DAYS[source_class]:
            expired.append(source['source_id'])
    if expired:
        raise C7TrustError('source_freshness_as_of_blocked:' + ','.join(sorted(expired)))
    return {
        'as_of_time': time_of_check,
        'policy_version': SOURCE_AS_OF_POLICY_VERSION,
        'pack_manifest_sha256': digest_obj(pack),
        'pack_last_verification_date': pack.get('live_verification_date'),
        'fixed_identity_source_count': fixed,
        'mutable_current_source_count': mutable,
        'metadata_age_assurance': 'pinned_source_metadata_within_local_as_of_windows',
        'official_live_reverification': False,
    }


def trusted_policy():
    if POLICY_FILE.is_symlink() or not POLICY_FILE.is_file():
        raise C7TrustError('trusted_policy_missing_or_symlinked')
    obj = load_json(POLICY_FILE)
    if digest_obj(obj) != TRUST_POLICY_SHA256 or obj.get('policy_version') != '0.3.0':
        raise C7TrustError('trusted_policy_integrity_mismatch')
    return obj


def require_approved(role, obj):
    policy = trusted_policy()
    allowed = policy['approved_inputs'].get(role, {})
    digest = digest_obj(obj)
    if digest not in allowed:
        raise C7TrustError(f'unapproved_synthetic_fixture:{role}')
    # A hash match with an enrolled bundled fixture is a bounded provenance
    # assertion. Re-evaluate the real fixture bytes too; no free-form approval.
    rel = allowed[digest]
    path = ROOT / 'references/fixtures' / rel
    if path.is_symlink() or not path.is_file() or digest_obj(load_json(path)) != digest:
        raise C7TrustError(f'approved_fixture_missing_or_changed:{role}')
    return {'fixture_role': role, 'approved_fixture': rel, 'fixture_sha256': digest}


def require_source_pack(pack, source_root=None):
    trusted = trusted_policy()
    pack_version = pack.get('pack_version')
    if pack_version == '0.5.0':
        policy = trusted['source_pack']
    elif pack_version == '0.6.0':
        policy = trusted['source_pack_0_6']
    elif pack_version == '0.6.1':
        policy = trusted['source_pack_0_6_1']
    else:
        raise C7TrustError('untrusted_source_pack_manifest')
    if (pack.get('pack_name') != policy['pack_name'] or
        pack.get('pack_version') != policy['pack_version'] or
        digest_obj(pack) != policy['manifest_sha256']):
        raise C7TrustError('untrusted_source_pack_manifest')
    reps = {}
    for source in pack['sources']:
        for rep in source['representations']:
            rel = rep['relative_path']
            if rel in reps:
                raise C7TrustError('duplicate_source_representation_path')
            reps[rel] = {
                'sha256': rep['sha256'], 'source_id': source['source_id'],
                'kind': rep['kind'], 'authenticity_state': rep['authenticity_state'],
            }
    if (len(pack['sources']) != policy['logical_source_count'] or
        len(reps) != policy['representation_count'] or
        reps != policy['representation_metadata']):
        raise C7TrustError('untrusted_source_representation_metadata')
    assurance = 'pinned_manifest_and_representation_metadata_only'
    if pack_version in ('0.6.0', '0.6.1'):
        # Release-critical source integrity: the core MUST carry every one of
        # the 47 representations, not just their metadata or Deldwyn.
        # Expected paths and hashes are read from the code-root-pinned policy,
        # while byte lengths come from the manifest whose digest is pinned.
        if pack_version == '0.6.1' and set(policy.get('bundled_verified_relative_paths', {})) != set(reps):
            raise C7TrustError('active_source_policy_incomplete_inventory')
        if (policy.get('bundled_verified_relative_paths') != {
                rel: entry['sha256'] for rel,entry in reps.items()
                if rel in policy.get('bundled_verified_relative_paths', {})}):
            raise C7TrustError('bundled_source_policy_inconsistent')
        sizes = {r['relative_path']: r['bytes']
                 for source in pack['sources'] for r in source['representations']}
        if set(sizes) != set(reps):
            raise C7TrustError('bundled_source_size_index_inconsistent')
        for rel, entry in reps.items():
            parts = PurePosixPath(rel)
            if (parts.is_absolute() or '..' in parts.parts or
                not parts.parts or parts.parts[0] != 'sources' or '\\' in rel):
                raise C7TrustError('unsafe_bundled_source_path:' + rel)
            path = BUNDLED_SOURCE_ROOT.joinpath(*parts.parts)
            if (path.is_symlink() or not path.is_file() or
                not path.resolve().is_relative_to(BUNDLED_SOURCE_ROOT.resolve()) or
                path.stat().st_size != sizes[rel] or
                hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']):
                raise C7TrustError('bundled_source_missing_or_modified:' + rel)
        assurance = 'pinned_metadata_and_verified_bundled_47_representations'
    if source_root is not None:
        base = Path(source_root).resolve(strict=True)
        for rel, entry in reps.items():
            p = PurePosixPath(rel)
            if p.is_absolute() or '..' in p.parts or not p.parts:
                raise C7TrustError('unsafe_source_representation_path')
            candidate = base.joinpath(*p.parts)
            if not candidate.is_file() or candidate.is_symlink() or not candidate.resolve().is_relative_to(base):
                raise C7TrustError(f'source_representation_missing_or_unsafe:{rel}')
            actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if actual != entry['sha256']:
                raise C7TrustError(f'source_representation_bytes_mismatch:{rel}')
        assurance = 'pinned_metadata_and_local_representation_bytes'
    return {
        'policy_sha256': TRUST_POLICY_SHA256,
        'source_manifest_sha256': policy['manifest_sha256'],
        'source_pack_version': pack_version,
        'source_representation_count': len(reps),
        'source_assurance': assurance,
        'official_live_reverification': False,
    }
