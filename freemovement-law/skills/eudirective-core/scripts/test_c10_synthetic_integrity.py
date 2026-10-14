#!/usr/bin/env python3
"""C10 scoped fixture and typed-internal-code regression checks; synthetic only."""
import tempfile, pathlib, sys, json, copy
from contract_validate import load_json, ContractError
import c7_trust_gate as trust
import module_conformance as mod
from source_library_paths import compatibility_root

ROOT=pathlib.Path(__file__).resolve().parents[1]
checked=[]
def accept(name,fn):
 fn();checked.append(name)
def denies(fn,contains):
 try:fn()
 except Exception as e:
  assert contains in str(e),(str(e),contains)
 else:raise AssertionError(f'accepted forbidden input: {contains}')

def fixture_guard():
 for i in range(1,9):
  f=ROOT/f'references/fixtures/c10/L{i}'
  for role,suffix in [('case','case'),('elements','elements'),('actors','actors')]:
   trust.require_approved(role,load_json(f/f'{suffix}.json'))
  if (f/'c5c-context.json').exists():trust.require_approved('c5c_context',load_json(f/'c5c-context.json'))
 checked.append('24_exact_case_element_actor_fixture_hashes')
 accept('reject_rebound_case',lambda:denies(lambda:trust.require_approved('case',{'case_id':'UNAPPROVED'}),'unapproved_synthetic_fixture'))
 for slug in ('sweden','turkiye'):
  m=load_json(ROOT/f'references/fixtures/c10/{slug}-module-manifest.json')
  x=load_json(ROOT/f'references/fixtures/c10/{slug}-module-export.json')
  mod.validate_pair(m,x)
  trust.require_approved('module_manifest',m)
  trust.require_approved('module_export',x)
 checked.append('country_module_pair_exact_conformance_and_enrolment')

def metadata_guard():
 accept('reject_private_identifier_run_id',lambda:denies(lambda:trust.require_synthetic_run_metadata('RUN-PERSON-test','2026-10-10T00:00:00Z'),'unapproved_synthetic_run_id'))
 accept('reject_2099_source_as_of',lambda:denies(lambda:trust.require_source_as_of(load_json(compatibility_root()/'core-source-pack-manifest-0.6.1.json'),'2099-01-01T00:00:00Z'),'source_freshness_as_of_blocked'))

def internal_issue_code_guard():
 with tempfile.TemporaryDirectory() as td:
  p=pathlib.Path(td)/'input.json'
  p.write_text(json.dumps({'unresolved':[{'code':'actor_scope_ambiguous','scope':'case','detail':'test'}]}))
  accept('default_external_code_key_rejected',lambda:denies(lambda:load_json(p),'forbidden executable-style key: code'))
  assert load_json(p,allow_internal_issue_code=True)['unresolved'][0]['code']=='actor_scope_ambiguous';checked.append('typed_internal_unresolved_code_accepted')
  for val in [{'nested':{'code':'anything'}},{'issues':[{'value':{'code':{'exec':'x'}}}]},{'issues':[{'value':{'code':'exec()'}}]},{'unresolved':[{'code':'id;rm -rf /'}]}]:
   p.write_text(json.dumps(val))
   denies(lambda:load_json(p,allow_internal_issue_code=True),'forbidden executable-style key: code')
  checked.append('four_internal_code_smuggling_shapes_rejected')
  p.write_text(json.dumps({'issues':[{'value':{'code':'actor_scope_ambiguous'}}]}))
  assert load_json(p,allow_internal_issue_code=True)['issues'][0]['value']['code']=='actor_scope_ambiguous';checked.append('typed_issue_index_code_accepted')

if __name__=='__main__':
 fixture_guard();metadata_guard();internal_issue_code_guard()
 print(json.dumps({'suite':'C10 synthetic and typed issue-code boundaries','status':'passed','checks':len(checked),'names':checked},indent=2))
