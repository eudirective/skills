#!/usr/bin/env python3
"""C5f: compare and conditionally sequence reviewed C5e options without changing analysis."""
import argparse
import json
from pathlib import Path
import sys

from contract_validate import ContractError, digest_obj, load_json, validate_obj
import suggestion_engine as c5e

ENGINE_VERSION = '0.1.0'
RULESET_VERSION = '0.1.0'
BASELINES = {'direct_compliance', 'direct_cooperation', 'request_clarification', 'waiting', 'no_action'}
RANK_FACTORS = ('urgency','remedy_power','legal_support_strength','evidentiary_value',
                'reversibility','route_compatibility','burden_cost','systemic_value')
GRADE = {'low':1,'medium':2,'high':3,'compatible':3,'not_applicable':None}

class RankingError(Exception):
    pass


def _ensure(test, message):
    if not test:
        raise RankingError(message)


def baseline_kind(candidate):
    if candidate['candidate_kind']=='no_action':
        return 'no_action'
    if candidate['candidate_kind']=='direct_action':
        return candidate.get('baseline_kind')
    return None


def comparable(a,b):
    """Conservative Pareto ordering: N/A vs a rated factor cannot be compared."""
    better=False
    for factor in RANK_FACTORS:
        va=a['ratings'][factor]; vb=b['ratings'][factor]
        if va=='not_applicable' or vb=='not_applicable':
            if va!=vb:
                return False
            continue
        if factor=='burden_cost':
            x,y=4-GRADE[va],4-GRADE[vb]
        else:
            x,y=GRADE[va],GRADE[vb]
        if x<y:
            return False
        if x>y:
            better=True
    return better


def layers(records):
    remaining={x['suggestion_id']:x for x in records}
    tiers=[]
    while remaining:
        front=sorted(k for k,x in remaining.items() if not any(k!=k2 and comparable(y,x) for k2,y in remaining.items()))
        _ensure(bool(front),'ranking_dominance_cycle')
        tiers.append({'tier':len(tiers)+1,'suggestion_ids':front,
                      'reason':'Pareto-nondominated ordinal review factors; equal-tier order is not a claimed preference.'})
        for key in front:
            del remaining[key]
    return tiers


def _check_relations(rels,candidate_ids):
    seen=set(); exclusive={}; precedence={}
    for r in rels:
        a,b=r['first_id'],r['second_id']; kind=r['relationship']
        _ensure(a in candidate_ids and b in candidate_ids, f'relation_unknown_candidate:{a}:{b}')
        _ensure(a!=b,f'relation_self_reference:{a}')
        k=(tuple(sorted([a,b])) if kind in {'conflict','compatible'} else (a,b))
        _ensure((kind,k) not in seen,f'duplicate_relation:{kind}:{a}:{b}'); seen.add((kind,k))
        if kind in {'compatible','conflict'}:
            old=exclusive.get(k)
            _ensure(old is None or old==kind,f'contradictory_pair_relation:{a}:{b}')
            exclusive[k]=kind
        elif kind in {'precedes','response_before'}:
            old=precedence.get((a,b))
            _ensure(old is None or old==kind,f'contradictory_precedence:{a}:{b}')
            precedence[(a,b)]=kind
    for a,b in precedence:
        _ensure(exclusive.get(tuple(sorted([a,b])))!='conflict', f'conflict_and_precedence:{a}:{b}')
    graph={x:set() for x in candidate_ids}
    for a,b in precedence:
        graph[a].add(b)
    visiting=set(); visited=set()
    def dfs(node):
        if node in visiting:
            raise RankingError('precedes_cycle')
        if node in visited:
            return
        visiting.add(node)
        for dest in graph[node]:
            dfs(dest)
        visiting.remove(node); visited.add(node)
    for node in sorted(graph): dfs(node)
    return exclusive,precedence


def build(handoff,c5e_context,c5e_output,rank_context,adapted=None,original=None):
    validate_obj('analysis-handoff',handoff)
    validate_obj('c5e-context',c5e_context)
    validate_obj('c5e-suggestion-candidates',c5e_output)
    validate_obj('c5f-context',rank_context)
    _ensure(handoff['handoff_status']!='blocked','analysis_handoff_blocked')
    _ensure(handoff['case_id']==c5e_output['case_id']==c5e_context['case_id']==rank_context['case_id'], 'case_id_mismatch')
    _ensure(c5e_context['objective']['objective_id']==rank_context['objective_id'], 'objective_id_mismatch')
    for k,expected in [('handoff_sha256',digest_obj(handoff)),('c5e_context_sha256',digest_obj(c5e_context)),
                       ('c5e_candidates_sha256',digest_obj(c5e_output))]:
        _ensure(rank_context['bindings'][k]==expected, f'ranking_review_binding_mismatch:{k}')
    # Replay the C5e validator instead of trusting mutable caller-supplied candidate labels.
    replay=c5e.build(handoff,c5e_context,adapted,original)
    _ensure(digest_obj(replay)==digest_obj(c5e_output),'c5e_replay_mismatch')
    _ensure(c5e_output['bindings']['handoff_sha256']==digest_obj(handoff),'c5e_handoff_binding_mismatch')
    ids={x['suggestion_id']:x for x in c5e_output['candidates']}
    _ensure(len(ids)==len(c5e_output['candidates']),'duplicate_c5e_candidate_id')
    reviews={}
    for x in rank_context['candidate_assessments']:
        sid=x['suggestion_id']; _ensure(sid not in reviews,f'duplicate_ranking_review:{sid}')
        _ensure(sid in ids,f'ranking_review_not_c5e_candidate:{sid}')
        reviews[sid]=x
    _ensure(set(reviews)==set(ids),'all_c5e_candidates_must_be_assessed')
    baseline_entries={}
    for b in rank_context['baseline_comparison']:
        kind=b['baseline_kind']
        _ensure(kind not in baseline_entries,f'duplicate_baseline_kind:{kind}')
        baseline_entries[kind]=b
        sid=b['suggestion_id']
        if b['review_status']=='represented':
            _ensure(sid in ids,f'baseline_reference_not_c5e_candidate:{kind}')
            _ensure(baseline_kind(ids[sid])==kind, f'baseline_kind_candidate_mismatch:{kind}')
        else:
            _ensure(sid is None,f'nonrepresented_baseline_has_candidate:{kind}')
    _ensure(set(baseline_entries)==BASELINES,'incomplete_baseline_comparison')
    exclusive,precedence=_check_relations(rank_context['relations'],set(ids))
    source_refs=set(); valid_refs=set()
    candidate_support={}
    for angle in handoff['eligible_attack_angles']:
        valid_refs.add(angle['attack_angle_id']); source_refs.update(angle['source_refs'])
    for route in handoff['eligible_routes']:
        valid_refs.add(route['route_ref']); source_refs.update(route['source_refs'])
    valid_refs|=source_refs
    for sid,c in ids.items():
        candidate_support[sid]=set(c['supporting_attack_angle_refs']+c['supporting_route_refs'])
        for a in handoff['eligible_attack_angles']:
            if a['attack_angle_id'] in candidate_support[sid]: candidate_support[sid].update(a['source_refs'])
        for r in handoff['eligible_routes']:
            if r['route_ref'] in candidate_support[sid]: candidate_support[sid].update(r['source_refs'])
    reviews_ok=[]; deferred=[]; excluded=[]; questions=[]
    for sid in sorted(ids):
        c=ids[sid]; rev=reviews[sid]; ratings=rev['ratings']; reasons=[]
        _ensure(set(rev['rating_basis_refs']) <= valid_refs, f'rating_reference_outside_handoff:{sid}')
        _ensure(set(rev['rating_basis_refs']) <= candidate_support[sid], f'rating_reference_outside_candidate_support:{sid}')
        if rev['disposition']!='include': reasons.append('review_disposition_'+rev['disposition'])
        if rev['basis_classification']=='exploratory_possibility': reasons.append('exploratory_possibility_not_rankable')
        if rev['assumptions_state']=='changed': reasons.append('assumptions_changed_requires_reanalysis')
        if rev['assumptions_state']=='unknown': reasons.append('assumptions_currentness_unknown')
        if rev['factual_basis_state']!='reviewed': reasons.append('facts_'+rev['factual_basis_state'])
        if rev['counterevidence_state']!='reviewed_no_material_conflict': reasons.append('counterevidence_'+rev['counterevidence_state'])
        if rev['prerequisites_state']!='satisfied': reasons.append('prerequisites_'+rev['prerequisites_state'])
        if rev['adverse_effects_state']!='clear': reasons.append('adverse_effects_'+rev['adverse_effects_state'])
        for factor in RANK_FACTORS:
            if ratings[factor]=='unknown': reasons.append('unknown_factor_'+factor)
        for factor,c5e_key in [('reversibility','reversibility'),('evidentiary_value','information_value'),('burden_cost','burden_cost')]:
            if c[c5e_key]!='unknown' and ratings[factor]!=c[c5e_key]:
                reasons.append('c5e_rating_mismatch_'+factor)
        if ratings['route_compatibility']=='incompatible': reasons.append('route_compatibility_incompatible')
        if len(c['supporting_route_refs'])>1 and ratings['route_compatibility']!='compatible':
            reasons.append('multiple_routes_without_compatibility_review')
        if not c['supporting_route_refs'] and ratings['route_compatibility']!='not_applicable':
            reasons.append('route_compatibility_without_route')
        if not candidate_support[sid]:
            if ratings['legal_support_strength']!='not_applicable': reasons.append('unbound_legal_support_rating')
            if ratings['remedy_power']!='not_applicable': reasons.append('unbound_remedy_power_rating')
        else:
            if ratings['legal_support_strength']=='not_applicable' and c['candidate_kind']=='action':
                reasons.append('action_legal_support_review_missing')
            if ratings['legal_support_strength'] in {'high','medium'} and not (set(rev['rating_basis_refs']) & candidate_support[sid]):
                reasons.append('legal_support_rating_without_bounded_basis')
        if ratings['remedy_power'] in {'high','medium'} and not c['supporting_route_refs']:
            reasons.append('remedy_power_without_validated_route')
        if reasons:
            entry={'suggestion_id':sid,'reasons':sorted(set(reasons)),'action_summary':c['action_summary']}
            resolved_rejection=rev['disposition']=='reject' or (rev['disposition']=='include' and (
                rev['factual_basis_state']=='contradicted' or rev['counterevidence_state']=='material_conflict' or
                rev['adverse_effects_state']=='risk_present'))
            (excluded if resolved_rejection else deferred).append(entry)
            if (not resolved_rejection) or rev['assumptions_state']=='changed':
                questions.append({'suggestion_id':sid,'question':'Re-enter analysis or obtain a new reviewed assessment for: '+', '.join(sorted(set(reasons)))})
        else:
            reviews_ok.append({'suggestion_id':sid,'candidate_kind':c['candidate_kind'],
                               'adapted_stratagem_id':c['adapted_stratagem_id'],
                               'ratings':ratings,'rating_basis_refs':rev['rating_basis_refs'],
                               'review_rationale':rev['review_rationale'],'basis_classification':rev['basis_classification'],'priority_tier':1})
    tiers=layers(reviews_ok)
    tier_index={sid:t['tier'] for t in tiers for sid in t['suggestion_ids']}
    for r in reviews_ok: r['priority_tier']=tier_index[r['suggestion_id']]
    ready_ids=set(tier_index)
    conflicts=sorted((r for r in rank_context['relations'] if r['relationship']=='conflict'),
                     key=lambda x:(x['first_id'],x['second_id']))
    seq_ids=set(); sequences=[]
    for s in rank_context['sequences']:
        sk=s['sequence_id']; _ensure(sk not in seq_ids,f'duplicate_sequence_id:{sk}'); seq_ids.add(sk)
        ids_seq=s['steps']; _ensure(set(ids_seq)<=set(ids),f'sequence_unknown_candidate:{sk}')
        blockers=[]
        for sid in ids_seq:
            if sid not in ready_ids: blockers.append(f'step_not_rankable:{sid}')
            if ids[sid]['candidate_kind']=='no_action' and len(ids_seq)>1:
                blockers.append(f'no_action_cannot_be_chained:{sid}')
        for i,a in enumerate(ids_seq):
            for b in ids_seq[i+1:]:
                if exclusive.get(tuple(sorted([a,b])))=='conflict': blockers.append(f'sequence_conflict:{a}:{b}')
        for a,b in zip(ids_seq,ids_seq[1:]):
            if (a,b) not in precedence and exclusive.get(tuple(sorted([a,b])))!='compatible':
                blockers.append(f'unspecified_adjacent_relation:{a}:{b}')
            if (b,a) in precedence: blockers.append(f'reverse_precedence:{a}:{b}')
        sequences.append({'sequence_id':sk,'steps':ids_seq,'sequence_status':'deferred' if blockers else 'conditional_for_review',
                          'reassessment_trigger':s['reassessment_trigger'],'blockers':sorted(set(blockers))})
    for c in c5e_output['analysis_returns']:
        questions.append({'suggestion_id':c['suggestion_id'],'question':c['new_question'] or 'C5e requested analysis return: '+', '.join(c.get('validation_reasons',[]))})
    incomplete_baselines=[k for k,v in baseline_entries.items() if v['review_status']=='unresolved']
    # A represented baseline cannot be hidden as 'not applicable' when a matching C5e option is present.
    for kind in BASELINES:
        if any(baseline_kind(x)==kind for x in ids.values()):
            _ensure(baseline_entries[kind]['review_status']=='represented',f'existing_baseline_not_represented:{kind}')
    complete=not (deferred or questions or incomplete_baselines)
    if not reviews_ok:
        status='no_eligible_options'; rec_status='no_safe_option_for_review'
    else:
        status='ready_for_review' if complete else 'incomplete'
        if not complete:
            rec_status='insufficient_for_ranking'
        elif len(tiers[0]['suggestion_ids'])==1:
            rec_status='single_preferred_for_review'
        else:
            rec_status='alternatives_for_review'
    preferred=tiers[0]['suggestion_ids'][0] if rec_status=='single_preferred_for_review' else None
    top_pairs=[]
    top=tiers[0]['suggestion_ids'] if tiers else []
    review_by_id={x['suggestion_id']:x for x in reviews_ok}
    for i,a in enumerate(top):
        for b in top[i+1:]:
            if len(top_pairs)>=50: break
            first=[]; second=[]; noncomparable=[]
            for f in RANK_FACTORS:
                x=review_by_id[a]['ratings'][f]; y=review_by_id[b]['ratings'][f]
                if x=='not_applicable' or y=='not_applicable':
                    if x!=y: noncomparable.append(f)
                    continue
                vx=4-GRADE[x] if f=='burden_cost' else GRADE[x]
                vy=4-GRADE[y] if f=='burden_cost' else GRADE[y]
                if vx>vy: first.append(f)
                if vy>vx: second.append(f)
            top_pairs.append({'first_id':a,'second_id':b,'first_advantages':first,
                              'second_advantages':second,'noncomparable_factors':noncomparable})
        if len(top_pairs)>=50: break
    tradeoffs_truncated=(len(top)*(len(top)-1)//2)>50
    out={
        'engine_version':ENGINE_VERSION,'ruleset_version':RULESET_VERSION,'case_id':handoff['case_id'],
        'bindings':{
          'handoff_sha256':digest_obj(handoff),'c5e_context_sha256':digest_obj(c5e_context),
          'c5e_candidates_sha256':digest_obj(c5e_output),'c5f_context_sha256':digest_obj(rank_context),
          'adapted_catalog_sha256':c5e_output['bindings']['adapted_catalog_sha256'],
          'original_catalog_sha256':c5e_output['bindings']['original_catalog_sha256']
        },
        'objective':c5e_output['objective'],'ranking_status':status,'recommendation_status':rec_status,
        'legal_conclusion_status':'not_determined','review_identity_assurance':'unverified_local',
        'priority_tiers':tiers,'preferred_suggestion_id':preferred,
        'reviewed_options':sorted(reviews_ok,key=lambda x:(x['priority_tier'],x['suggestion_id'])),
        'deferred_options':sorted(deferred,key=lambda x:x['suggestion_id']),
        'excluded_options':sorted(excluded,key=lambda x:x['suggestion_id']),
        'top_tier_tradeoffs':top_pairs,'tradeoffs_truncated':tradeoffs_truncated,
        'baseline_comparison':sorted(rank_context['baseline_comparison'],key=lambda x:x['baseline_kind']),
        'conflicts':conflicts,'conditional_sequences':sorted(sequences,key=lambda x:x['sequence_id']),
        'analysis_returns':sorted(questions,key=lambda x:(x['suggestion_id'],x['question'])),
        'limitations':[
          'Priority tiers use transparent Pareto comparisons of reviewer-provided ordinal assessments; they are not measurements of legal rights, probabilities, remedy entitlement, or effectiveness.',
          'This is a development-stage ranking FOR REVIEW, not an approved action plan or verified legal conclusion. Reviewer identity is unverified_local.',
          'C5f replays the exact C5e inputs and binds the original handoff and catalogue digests. It cannot add attack angles, legal findings, routes or source authority.',
          'Incompatible suggestions remain mutually exclusive; chains are conditional and require reassessment after a material response or change of assumptions.',
          'An unsettled baseline, changed assumption or unknown factor prevents a unique preference; a separately rejected unsafe/contradicted option is excluded from the comparison, not treated as pending.',
          'The underlying truth, completeness and legal meaning of reviewer assessments and free-text rationales are not proved mechanically; private-data handling remains disabled upstream.'
        ]
    }
    validate_obj('c5f-ranked-suggestions',out)
    return out


def main():
    ap=argparse.ArgumentParser(description='C5f: reviewer-gated priority tiers and conditional sequences for C5e suggestions')
    ap.add_argument('handoff'); ap.add_argument('c5e_context'); ap.add_argument('c5e_candidates'); ap.add_argument('c5f_context')
    ap.add_argument('--output'); a=ap.parse_args()
    try:
        out=build(load_json(Path(a.handoff)),load_json(Path(a.c5e_context)),load_json(Path(a.c5e_candidates)),load_json(Path(a.c5f_context)))
        output=json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
        if a.output: Path(a.output).write_text(output,encoding='utf-8')
        print(output,end=''); return 0
    except (RankingError,c5e.SuggestionError,ContractError,OSError,ValueError) as e:
        print(json.dumps({'status':'invalid','error':str(e)},sort_keys=True),file=sys.stderr)
        return 2

if __name__=='__main__': raise SystemExit(main())
