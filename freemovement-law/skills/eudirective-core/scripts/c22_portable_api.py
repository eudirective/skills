#!/usr/bin/env python3
"""C22a: transport-neutral facade over existing, PINNED fictional C18/C21 engines.

No plugin dependency, network, raw document intake, or external sending.
An optional adapter can call invoke_request(); standalone CLI calls invoke().
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from contract_validate import ContractError, load_json, validate_obj
import c18_source_integrity as c18
import c21_privacy as privacy
import c21_cohort as cohort

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'references' / 'fixtures' / 'c21'
INTERFACE_VERSION = '0.1.0'
ALLOWED_PROFILES = frozenset({
    'internal_review_preview', 'public_story_preview', 'feedback_aggregate_preview'
})
OPERATIONS = frozenset({
    'capabilities', 'source_audit', 'privacy_preview', 'privacy_verify',
    'c17_feedback_preview', 'c17_feedback_verify',
    'cohort_preview', 'cohort_verify',
})
FICTIONAL_CASES = frozenset(f'L{i}' for i in range(1, 9))


class InterfaceError(ValueError):
    """Stable fixed reason code; never contain user-supplied text."""


def _result(operation: str, **fields: Any) -> dict[str, Any]:
    return {'interface_version': INTERFACE_VERSION, 'operation': operation,
            'private_data_enabled': False, 'external_disclosure_authorized': False,
            **fields}


def _as_fixture(fixture: str | None, *, c17: bool) -> Path:
    if c17:
        if fixture not in FICTIONAL_CASES:
            raise InterfaceError('unsupported_or_missing_fictional_fixture')
        return FIXTURES / f'fictional-c17-plan-{fixture}.json'
    if fixture != 'c21-demo':
        raise InterfaceError('unsupported_or_missing_fictional_fixture')
    return FIXTURES / 'fictional-private-looking.json'


def _output_dir(path: str | Path | None, *, exists: bool) -> Path:
    if path is None or not isinstance(path, (str, Path)):
        raise InterfaceError('output_dir_required')
    value = Path(path)
    if not value.is_absolute():
        raise InterfaceError('absolute_output_dir_required')
    if '..' in value.parts or '.' in value.parts:
        raise InterfaceError('unsafe_output_path')
    if ROOT == value or ROOT in value.parents:
        raise InterfaceError('output_inside_skill_forbidden')
    if any(p.is_symlink() for p in (value, *value.parents)):
        raise InterfaceError('symlink_output_path_forbidden')
    if exists:
        if not value.is_dir():
            raise InterfaceError('verification_directory_missing')
    else:
        if value.exists():
            raise InterfaceError('output_directory_already_exists')
        if not value.parent.is_dir():
            raise InterfaceError('existing_output_parent_required')
    return value


def _privacy_operation(operation: str, fixture: str, profile: str, outdir: Path,
                       *, c17: bool) -> dict[str, Any]:
    """Reuse existing C21 build/receipt/write functions, not a second policy."""
    pol = privacy.policy()
    fixed = _as_fixture(fixture, c17=c17)
    if c17:
        plan = load_json(fixed)
        inp = privacy.from_c17_plan(plan)  # Validates pinned enrolled plan digest.
        selected = 'c17_feedback_preview'
    else:
        inp = privacy.vetted_input(fixed)
        selected = profile
    view = privacy.build(inp, pol, selected)
    receipt = privacy.receipt_for(view, pol)
    if operation.endswith('verify'):
        prior_view = load_json(outdir / 'minimised-view.json')
        prior_receipt = load_json(outdir / 'privacy-receipt.json')
        validate_obj('c21-privacy-view', prior_view)
        validate_obj('c21-privacy-receipt', prior_receipt)
        if prior_view != view or prior_receipt != receipt:
            raise InterfaceError('engine_rejected_or_failed')
        status = 'verified_synthetic_replay_only'
    else:
        privacy.write_preview(outdir, view, receipt)
        status = 'synthetic_preview_written'
    return {'status': status, 'profile': selected, 'view_sha256': receipt['view_sha256']}


def _cohort_operation(operation: str, outdir: Path) -> dict[str, Any]:
    """Reuse all-eight immutable cohort source, suppression and receipt logic."""
    view = cohort.view_from_enrolled_fixtures()
    receipt = cohort.receipt_for(view)
    if operation.endswith('verify'):
        summary, rec = cohort.output_files(outdir)
        previous = load_json(summary)
        prior_receipt = load_json(rec)
        validate_obj('c21-cohort-view', previous)
        validate_obj('c21-cohort-receipt', prior_receipt)
        if previous != view or prior_receipt != receipt:
            raise InterfaceError('engine_rejected_or_failed')
        status = 'verified_fixed_synthetic_cohort_replay_only'
    else:
        cohort.write_preview(outdir, view, receipt)
        status = 'fixed_synthetic_cohort_preview_written'
    return {'status': status, 'summary_sha256': receipt['summary_sha256']}


def invoke(operation: str, *, fixture: str | None = None,
           profile: str | None = None,
           output_dir: str | Path | None = None) -> dict[str, Any]:
    """Versioned Python execution contract, identical for CLI and future adapters."""
    safe_operation = operation if isinstance(operation, str) and operation in OPERATIONS else 'unknown'
    try:
        if fixture is not None and not isinstance(fixture, str):
            raise InterfaceError('invalid_fixture_type')
        if profile is not None and not isinstance(profile, str):
            raise InterfaceError('invalid_profile_type')
        if safe_operation == 'unknown':
            raise InterfaceError('unknown_operation')
        if operation == 'capabilities':
            if any(v is not None for v in (fixture, profile, output_dir)):
                raise InterfaceError('unexpected_parameter')
            return _result(operation, status='available_synthetic_only',
                           execution_mode='local_python',
                           supported_operations=sorted(OPERATIONS),
                           enrolled_fixture_tokens=['c21-demo', *sorted(FICTIONAL_CASES)],
                           privacy_protection='not_verified_for_real_or_public_person_data',
                           backend='bundled_python_no_mcp_required')
        if operation == 'source_audit':
            if any(v is not None for v in (fixture, profile, output_dir)):
                raise InterfaceError('unexpected_parameter')
            a = c18.audit()  # Reuses the established C18 source verifier.
            return _result(operation, status='verified_local_integrity_with_text_gaps',
                           pack_version=a['pack_version'],
                           representation_count=a['representation_count'],
                           identity_only_gaps=a['identity_only_note_count'],
                           legal_semantic_validation='not_performed')
        if operation in {'privacy_preview', 'privacy_verify'}:
            if profile not in ALLOWED_PROFILES:
                raise InterfaceError('invalid_or_missing_preview_profile')
            if fixture != 'c21-demo':
                raise InterfaceError('unsupported_or_missing_fictional_fixture')
            folder = _output_dir(output_dir, exists=operation.endswith('verify'))
            fields = _privacy_operation(operation, fixture, profile, folder, c17=False)
            return _result(operation, **fields)
        if operation in {'c17_feedback_preview', 'c17_feedback_verify'}:
            if profile is not None:
                raise InterfaceError('c17_profile_is_implicit')
            if fixture not in FICTIONAL_CASES:
                raise InterfaceError('unsupported_or_missing_fictional_fixture')
            folder = _output_dir(output_dir, exists=operation.endswith('verify'))
            fields = _privacy_operation(operation, fixture, 'c17_feedback_preview', folder, c17=True)
            return _result(operation, **fields)
        if operation in {'cohort_preview', 'cohort_verify'}:
            if fixture is not None or profile is not None:
                raise InterfaceError('subset_or_profile_selection_forbidden')
            folder = _output_dir(output_dir, exists=operation.endswith('verify'))
            fields = _cohort_operation(operation, folder)
            return _result(operation, **fields)
        raise InterfaceError('unknown_operation')
    except (InterfaceError, privacy.PrivacyError, c18.C18AuditError,
            ContractError, OSError, ValueError, KeyError) as exc:
        code = str(exc) if isinstance(exc, InterfaceError) else 'engine_rejected_or_failed'
        if not re.fullmatch(r'[a-z0-9_]{1,80}', code):
            code = 'interface_boundary_failure'
        return _result(safe_operation, status='blocked', reason=code)
    except Exception:
        # Fail closed if an engine raises an unexpected runtime exception.
        return _result(safe_operation, status='blocked', reason='engine_unexpected_failure')


def invoke_request(request: object, *, output_dir: str | Path | None = None) -> dict[str, Any]:
    """Reject arbitrary adapter JSON before any engine call or file read."""
    if not isinstance(request, dict) or set(request) - {
        'interface_version', 'operation', 'fixture', 'profile'
    }:
        return _result('unknown', status='blocked', reason='invalid_adapter_request_fields')
    if (request.get('interface_version') != INTERFACE_VERSION or
            not isinstance(request.get('operation'), str)):
        return _result('unknown', status='blocked', reason='unsupported_adapter_contract')
    for name in ('fixture', 'profile'):
        value = request.get(name)
        if name in request and (not isinstance(value, str) or len(value) > 80):
            return _result('unknown', status='blocked', reason='unsafe_adapter_parameter')
    return invoke(request['operation'], fixture=request.get('fixture'),
                  profile=request.get('profile'), output_dir=output_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description='C22a portable fictional-only interface')
    parser.add_argument('operation', help='A fixed operation identifier, not a command')
    parser.add_argument('--fixture')
    parser.add_argument('--profile')
    parser.add_argument('--output-dir')
    args = parser.parse_args()
    result = invoke(args.operation, fixture=args.fixture, profile=args.profile,
                    output_dir=args.output_dir)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 2 if result['status'] == 'blocked' else 0


if __name__ == '__main__':
    raise SystemExit(main())
