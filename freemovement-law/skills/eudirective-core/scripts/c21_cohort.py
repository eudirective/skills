#!/usr/bin/env python3
"""C21: fixed-eight-fictional-plan, non-send C17 remedy category cohort preview.

This is not evidence of statistical anonymity, misconduct, host protection or
legal merits. A caller cannot select a subset of the enrolled plans.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from contract_validate import ContractError, digest_obj, load_json, validate_obj
from c21_privacy import PrivacyError, atomic_new, from_c17_plan

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'references/fixtures/c21'
CASES = tuple('L' + str(i) for i in range(1, 9))
C21_COHORT_VERSION = '0.1.0'
K_THRESHOLD = 3
ALLOWED_CATEGORIES = frozenset({
    'administrative_appeal_then_judicial_referral',
    'administrative_clarification',
    'operational_contact',
    'informal_problem_solving',
    'supervisory_complaint',
    'eu_law_enforcement_complaint',
    'evidence_acquisition',
})


def view_from_enrolled_fixtures():
    """All eight pinned synthetic plans, fixed denominator, no subset queries."""
    counts = Counter()
    for case in CASES:
        path = FIXTURES / f'fictional-c17-plan-{case}.json'
        try:
            plan = load_json(path)
        except (ContractError, OSError, ValueError):
            raise PrivacyError('missing_or_invalid_enrolled_cohort_fixture') from None
        from_c17_plan(plan)  # Schema, review gate and independent enrolled digest.
        if plan['case_id'] != case:
            raise PrivacyError('enrolled_cohort_case_mismatch')
        categories = set()
        for candidate in plan['remedy_candidates']:
            category = candidate['category']
            if category not in ALLOWED_CATEGORIES:
                raise PrivacyError('unsupported_cohort_category')
            categories.add(category)
        counts.update(categories)  # One contribution maximum per case/category.

    visible = {c: counts[c] for c in sorted(counts) if counts[c] >= K_THRESHOLD}
    if not visible:
        raise PrivacyError('no_cohort_category_above_threshold')
    view = {
        'c21_cohort_version': C21_COHORT_VERSION,
        'status': 'fixed_fictional_cohort_preview_only',
        'cohort_size': len(CASES),
        'count_method': 'case_presence_once_per_category',
        'minimum_visible_cell': K_THRESHOLD,
        'remedy_category_case_counts': visible,
        'suppression': 'all categories below threshold omitted; no subgroup or remainder queries',
        'risk_flags': [
            'fictional_only_not_compliance_incidence',
            'synthetic_cohort_not_reidentification_tested',
            'small_cells_suppressed_not_anonymity_proof',
            'external_disclosure_prohibited',
            'no_differencing_assurance_beyond_fixed_input_set',
        ],
        'external_disclosure_authorized': False,
        'human_review_required': True,
        'private_data_enabled': False,
    }
    validate_obj('c21-cohort-view', view)
    return view


def receipt_for(view):
    receipt = {
        'c21_cohort_version': C21_COHORT_VERSION,
        'summary_sha256': digest_obj(view),
        'verification': 'pinned_local_fictional_fixture_replay_only_not_authenticated_provenance',
        'external_disclosure_authorized': False,
        'private_data_enabled': False,
    }
    validate_obj('c21-cohort-receipt', receipt)
    return receipt


def output_files(outdir):
    return outdir / 'cohort-summary.json', outdir / 'cohort-receipt.json'


def write_preview(outdir, view, receipt):
    if outdir.exists() or outdir.is_symlink() or outdir.parent.is_symlink():
        raise PrivacyError('output_directory_must_be_new')
    outdir.mkdir(mode=0o700, parents=True, exist_ok=False)
    summary_path, receipt_path = output_files(outdir)
    try:
        atomic_new(summary_path, view)
        atomic_new(receipt_path, receipt)
    except Exception:
        for p in (summary_path, receipt_path):
            if p.is_file() and not p.is_symlink():
                p.unlink()
        outdir.rmdir()
        raise


def main():
    ap = argparse.ArgumentParser(description='Non-send pinned eight-case C17 cohort rehearsal')
    ap.add_argument('operation', choices=['preview', 'verify'])
    ap.add_argument('--output-dir', type=Path, required=True)
    args = ap.parse_args()
    try:
        view = view_from_enrolled_fixtures()
        receipt = receipt_for(view)
        if args.operation == 'preview':
            write_preview(args.output_dir, view, receipt)
            status = 'fixed_synthetic_cohort_preview_written'
        else:
            sp, rp = output_files(args.output_dir)
            try:
                prev_view = load_json(sp)
                prev_receipt = load_json(rp)
                validate_obj('c21-cohort-view', prev_view)
                validate_obj('c21-cohort-receipt', prev_receipt)
            except (ContractError, OSError, ValueError):
                raise PrivacyError('missing_or_invalid_cohort_preview') from None
            if prev_view != view or prev_receipt != receipt:
                raise PrivacyError('cohort_replay_or_digest_mismatch')
            status = 'verified_fixed_synthetic_cohort_replay_only'
        print(json.dumps({'status': status, 'summary_sha256': receipt['summary_sha256'],
                          'external_disclosure_authorized': False,
                          'private_data_enabled': False}, sort_keys=True))
        return 0
    except (PrivacyError, ContractError, OSError, ValueError):
        # Fixed code avoids returning arbitrary plan contents, paths or codes.
        print(json.dumps({'status': 'blocked', 'reason': 'synthetic_cohort_boundary_failure'}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
