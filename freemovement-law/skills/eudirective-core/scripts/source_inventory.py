#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

from contract_validate import ContractError, load_json, validate_obj, digest_obj

class SourceInventoryError(Exception):
    pass

EXPECTED_OWNER = {
    'eu': 'core',
    'member_state': 'member_state',
    'applicant_country': 'applicant_country',
    'local_operational': 'applicant_country',
}

def validate_inventory(obj):
    validate_obj('source-inventory', obj)
    seen_sources=set(); seen_props=set()
    for src in obj['sources']:
        sid=src['source_id']
        if sid in seen_sources:
            raise SourceInventoryError(f'duplicate_source_id:{sid}')
        seen_sources.add(sid)
        expected=EXPECTED_OWNER[src['authority_level']]
        if src['canonical_owner_family'] != expected:
            raise SourceInventoryError(f'wrong_owner:{sid}:expected_{expected}')
        if src['authority_level']=='eu':
            if src['jurisdiction'] not in (None, 'EU'):
                raise SourceInventoryError(f'eu_source_has_national_jurisdiction:{sid}')
        else:
            if not src['jurisdiction']:
                raise SourceInventoryError(f'jurisdiction_required:{sid}')
        if src['migration_state']=='current':
            if not src.get('content_sha256'):
                raise SourceInventoryError(f'current_source_missing_hash:{sid}')
            if not src.get('retrieved_at'):
                raise SourceInventoryError(f'current_source_missing_retrieval_time:{sid}')
        for prop in src['propositions']:
            pid=prop['proposition_id']
            if pid in seen_props:
                raise SourceInventoryError(f'duplicate_proposition_id:{pid}')
            seen_props.add(pid)
    return {
        'status':'valid',
        'inventory_id':obj['inventory_id'],
        'source_count':len(seen_sources),
        'proposition_count':len(seen_props),
        'sha256':digest_obj(obj),
    }

def main():
    ap=argparse.ArgumentParser(description='Validate source ownership and migration inventory for eudirective-core')
    ap.add_argument('path')
    args=ap.parse_args()
    try:
        obj=load_json(Path(args.path))
        out=validate_inventory(obj)
        print(json.dumps(out,sort_keys=True))
        return 0
    except (ContractError,SourceInventoryError,OSError) as e:
        print(json.dumps({'status':'invalid','error':str(e)},sort_keys=True),file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
