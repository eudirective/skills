#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

from contract_validate import ContractError, digest_obj, load_json, validate_obj

ROOT=Path(__file__).resolve().parents[1]
ADAPTED=ROOT/'references'/'stratagems'/'adapted-stratagem-catalog.json'
ORIGINAL=ROOT/'references'/'stratagems'/'original-stratagem-catalog.json'
ENGINE_VERSION="0.2.0"; RULESET_VERSION="0.2.0"

class SuggestionError(Exception): pass

def index_catalog(cat,prefix):
    out={}
    nums=set()
    if cat['layer'] != ('adapted_operational' if prefix=='adapted' else 'original_abstract'):
        raise SuggestionError(f"catalog_layer_mismatch:{prefix}")
    for p in cat['patterns']:
        if p['stratagem_id'] in out: raise SuggestionError(f"duplicate_stratagem_id:{p['stratagem_id']}")
        if p['number'] in nums: raise SuggestionError(f"duplicate_stratagem_number:{prefix}:{p['number']}")
        out[p['stratagem_id']]=p; nums.add(p['number'])
    if nums!=set(range(1,37)): raise SuggestionError(f"catalog_number_set_invalid:{prefix}")
    return out

def build(handoff,context,adapted=None,original=None):
    validate_obj('analysis-handoff',handoff); validate_obj('c5e-context',context)
    if context['case_id']!=handoff['case_id']: raise SuggestionError('case_id_mismatch')
    if handoff['handoff_status']=='blocked': raise SuggestionError('analysis_handoff_blocked')
    adapted=load_json(ADAPTED) if adapted is None else adapted; original=load_json(ORIGINAL) if original is None else original
    validate_obj('stratagem-catalog',adapted); validate_obj('stratagem-catalog',original)
    amap=index_catalog(adapted,'adapted'); omap=index_catalog(original,'original')
    eligible_attacks={x['attack_angle_id'] for x in handoff['eligible_attack_angles']}; eligible_routes={x['route_ref'] for x in handoff['eligible_routes']}
    seen=set(); candidates=[]; blocked=[]; nonapp=[]; returns=[]
    for p in context['proposals']:
        sid=p['suggestion_id']
        if sid in seen: raise SuggestionError(f'duplicate_suggestion_id:{sid}')
        seen.add(sid)
        out=dict(p); out['validation_reasons']=[]; out['recommendation_status']='not_ranked'
        if p['adapted_stratagem_id'] is not None:
            ap=amap.get(p['adapted_stratagem_id'])
            if ap is None: raise SuggestionError(f"unknown_adapted_stratagem:{p['adapted_stratagem_id']}")
            if not ap.get('preferred_for_generation'): raise SuggestionError(f"adapted_stratagem_not_preferred:{p['adapted_stratagem_id']}")
        else: ap=None
        if p['original_stratagem_id'] is not None:
            op=omap.get(p['original_stratagem_id'])
            if op is None: raise SuggestionError(f"unknown_original_stratagem:{p['original_stratagem_id']}")
            if ap is not None and op['number']!=ap['number']: raise SuggestionError(f"stratagem_analogue_number_mismatch:{sid}")
        if not set(p['supporting_attack_angle_refs']).issubset(eligible_attacks):
            out['validation_reasons'].append('unsupported_attack_angle_reference')
        if not set(p['supporting_route_refs']).issubset(eligible_routes):
            out['validation_reasons'].append('unsupported_route_reference')
        if p['candidate_kind']=='action' and not p['supporting_attack_angle_refs'] and not p['supporting_route_refs']:
            out['validation_reasons'].append('action_requires_validated_support')
        if p['candidate_kind']=='action' and p['adapted_stratagem_id'] is None:
            out['validation_reasons'].append('action_requires_adapted_stratagem')
        baseline=p.get('baseline_kind')
        if p['candidate_kind']=='direct_action':
            if context['context_version']!='0.2.0':
                out['validation_reasons'].append('direct_action_requires_c5e_context_0_2')
            if baseline is None:
                out['validation_reasons'].append('direct_action_requires_baseline_kind')
            if p['adapted_stratagem_id'] is not None or p['original_stratagem_id'] is not None:
                out['validation_reasons'].append('direct_action_must_not_use_stratagem')
            if baseline=='direct_compliance' and not p['supporting_attack_angle_refs'] and not p['supporting_route_refs']:
                out['validation_reasons'].append('direct_compliance_requires_validated_support')
            if baseline=='waiting' and not p['inaction_or_delay']:
                out['validation_reasons'].append('waiting_must_flag_inaction')
        elif baseline is not None:
            out['validation_reasons'].append('baseline_kind_reserved_for_direct_action')
        if p['applicability']=='non_applicable':
            out['validation_status']='non_applicable'; nonapp.append(out); continue
        if p['falsification_required']:
            out['validation_reasons'].append('falsification_dependent_tactic_forbidden')
        if p['disclosure_duty_status']=='conflict':
            out['validation_reasons'].append('affirmative_disclosure_duty_conflict')
        if p['disclosure_duty_status']=='unknown':
            out['validation_reasons'].append('disclosure_duty_requires_analysis_return')
        if p['inaction_or_delay'] and p['deadline_waiver_review']!='clear':
            out['validation_reasons'].append('inaction_delay_deadline_waiver_not_cleared')
        if (not p['inaction_or_delay']) and p['deadline_waiver_review'] not in {'not_applicable','clear'}:
            out['validation_reasons'].append('deadline_waiver_review_inconsistent')
        if p['requires_new_determination']:
            if not p['new_question']:
                out['validation_reasons'].append('new_determination_requires_question')
            out['validation_status']='analysis_return'; returns.append(out); continue
        if p['candidate_kind']=='analysis_return':
            if not p['new_question']: out['validation_reasons'].append('analysis_return_requires_question')
            out['validation_status']='analysis_return'; returns.append(out); continue
        if p['candidate_kind']=='no_action':
            if not p['inaction_or_delay'] or p['deadline_waiver_review']!='clear':
                out['validation_reasons'].append('no_action_requires_cleared_inaction_risk')
            if p['adapted_stratagem_id'] is not None and p['adapted_stratagem_id']!='adapted:36':
                out['validation_reasons'].append('no_action_stratagem_must_be_null_or_withdrawal')
            if out['validation_reasons']:
                if any(x in out['validation_reasons'] for x in
                       ('disclosure_duty_requires_analysis_return', 'inaction_delay_deadline_waiver_not_cleared',
                        'no_action_requires_cleared_inaction_risk')):
                    out['validation_status']='analysis_return'; returns.append(out)
                else:
                    out['validation_status']='blocked'; blocked.append(out)
            else:
                out['validation_status']='candidate'; candidates.append(out)
            continue
        if out['validation_reasons']:
            if any(x in out['validation_reasons'] for x in ('disclosure_duty_requires_analysis_return','inaction_delay_deadline_waiver_not_cleared')):
                out['validation_status']='analysis_return'; returns.append(out)
            else:
                out['validation_status']='blocked'; blocked.append(out)
        else:
            out['validation_status']='candidate'; candidates.append(out)
    status='ready' if candidates else ('blocked' if blocked and not returns and not nonapp else 'empty')
    result={
        'engine_version':ENGINE_VERSION,'ruleset_version':RULESET_VERSION,'case_id':handoff['case_id'],
        'bindings':{'handoff_sha256':digest_obj(handoff),'context_sha256':digest_obj(context),'adapted_catalog_version':adapted['catalog_version'],'adapted_catalog_sha256':digest_obj(adapted),'original_catalog_version':original['catalog_version'],'original_catalog_sha256':digest_obj(original)},
        'objective':context['objective'],'generation_status':status,'recommendation_status':'not_ranked',
        'candidates':sorted(candidates,key=lambda x:x['suggestion_id']),'analysis_returns':sorted(returns,key=lambda x:x['suggestion_id']),'non_applicable':sorted(nonapp,key=lambda x:x['suggestion_id']),'blocked':sorted(blocked,key=lambda x:x['suggestion_id']),
        'limitations':[
            'C5e validates and preserves suggestion candidates only; it does not rank, recommend, or surface a preferred tactic. C5f remains the recommendation/ranking boundary.',
            'The adapted/generalized catalogue is the preferred operational layer. The original catalogue is abstract reference only and cannot override adapted constraints or validated case state.',
            'A candidate can reference only attack angles and routes promoted through the digest-bound analysis handoff. It cannot create legal findings, attack angles, source authority, deadlines, or competence.',
            'Falsification-dependent tactics and explicit disclosure-duty conflicts are blocked. Unknown disclosure duties or uncleared inaction/deadline-waiver risk return to analysis rather than becoming action candidates.',
            'Free-text candidate semantics still require later review; deterministic checks validate bindings and declared constraint states but cannot infer truthfulness or legality from prose alone.'
        ]
    }
    validate_obj('c5e-suggestion-candidates',result)
    return result

def main():
    ap=argparse.ArgumentParser(description='Validate C5e stratagem suggestion candidates against a bound analysis handoff')
    ap.add_argument('handoff'); ap.add_argument('context'); ap.add_argument('--adapted-catalog',default=str(ADAPTED)); ap.add_argument('--original-catalog',default=str(ORIGINAL)); ap.add_argument('--output')
    a=ap.parse_args()
    try:
        r=build(load_json(Path(a.handoff)),load_json(Path(a.context)),load_json(Path(a.adapted_catalog)),load_json(Path(a.original_catalog)))
        s=json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
        if a.output: Path(a.output).write_text(s,encoding='utf-8')
        print(s,end=''); return 0
    except (SuggestionError,ContractError,OSError,ValueError) as e:
        print(json.dumps({'status':'invalid','error':str(e)},sort_keys=True),file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
