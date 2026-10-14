#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

from contract_validate import ContractError, digest_obj, load_json, validate_obj
import element_model as em
import module_conformance as mc
import topology_engine as te

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACK_FILE = ROOT / "references" / "source-pack" / "core-source-pack-manifest-0.6.1.json"
PRINCIPLE_CATALOG_FILE = ROOT / "references" / "principles" / "principle-catalog.json"
ENGINE_VERSION = "0.1.0"
RULESET_VERSION = "0.1.0"
CONTRACT_VERSION = "0.2.0"
ELEMENT_MODEL_VERSION = "0.2.0"

NON_BINDING_STATUSES = {"non_binding_official_guidance", "non_binding_soft_law"}

class C5bError(Exception):
    pass


def index_elements(bundle):
    out = {}
    if bundle is None:
        return out
    for item in bundle["elements"]:
        out.setdefault(item["element_id"], []).append(item)
    return out


def single_value(index, element_id):
    vals = index.get(element_id, [])
    if not vals:
        return None
    if len(vals) != 1:
        raise C5bError(f"multiple_values_for_singleton:{element_id}")
    return vals[0]["value"]


def source_index(pack):
    return {s["source_id"]: s for s in pack["sources"]}


def binding_force(source):
    status = source.get("legal_status")
    if status == "primary_law":
        return "primary_law"
    if status == "binding_secondary_law":
        return "binding_secondary_law"
    if status == "binding_judicial_interpretation":
        return "binding_judicial_interpretation"
    if status == "non_binding_official_guidance":
        return "non_binding_guidance"
    if status == "non_binding_soft_law":
        return "non_binding_soft_law"
    return "unknown"


def hierarchy_note(source):
    bf = binding_force(source)
    if bf == "primary_law":
        return "Primary EU law is identified as a hierarchy-relevant source class; C5b does not infer an issue-specific conflict from metadata alone."
    if bf == "binding_secondary_law":
        return "Binding EU secondary law is identified without assigning automatic priority over another binding secondary-law instrument."
    if bf == "binding_judicial_interpretation":
        return "CJEU authority is preserved as binding judicial interpretation; it is not reduced to a numeric rank against legislation."
    if bf in {"non_binding_guidance", "non_binding_soft_law"}:
        return "The source is non-binding. It may be considered for interpretive relevance but cannot be recoded as binding law by this engine."
    return "Source metadata does not provide a recognized binding-force category; substantive use requires review."


def load_principle_catalog(sources):
    obj = load_json(PRINCIPLE_CATALOG_FILE)
    validate_obj("principle-catalog", obj)
    # C8 additive authority references are source-version-sensitive: historical
    # 0.5.0 source packs cannot claim they already contained Deldwyn.
    # This does not change the principle definitions, their addressee boundary,
    # or the mandatory legal-merits review status.
    if "eu:62024cj0477" in sources:
        for entry in obj["principles"]:
            if entry["principle_id"] in {
                "rights_of_defence", "good_administration_general_principle",
                "effective_judicial_protection", "charter_article_41_direct_reliance"
            }:
                entry["source_refs"].append("eu:62024cj0477")
        validate_obj("principle-catalog", obj)
    seen = set()
    source_ids = set(sources)
    for p in obj["principles"]:
        pid = p["principle_id"]
        if pid in seen:
            raise C5bError(f"duplicate_principle_id:{pid}")
        seen.add(pid)
        missing = sorted(set(p["source_refs"]) - source_ids)
        if missing:
            raise C5bError("principle_source_missing:" + pid + ":" + ",".join(missing))
        nonbinding = [ref for ref in p["source_refs"] if sources[ref].get("legal_status") in NON_BINDING_STATUSES]
        if nonbinding:
            raise C5bError("principle_source_not_binding_authority:" + pid + ":" + ",".join(sorted(nonbinding)))
    return obj, {p["principle_id"]: p for p in obj["principles"]}


def validate_element_bundle(bundle):
    if bundle is None:
        return
    catalog, _, invariants = em.load_model()
    em.check_bundle(bundle, catalog, invariants)


def load_module_pairs(module_pairs, case_obj):
    bindings = []
    national_rules = {}
    if not module_pairs:
        return bindings, national_rules
    for manifest_path, export_path in module_pairs:
        manifest = load_json(Path(manifest_path))
        export = load_json(Path(export_path))
        try:
            mc.validate_pair(manifest, export)
        except mc.ConformanceError as e:
            raise C5bError(f"module_pair_nonconformant:{e}")
        if export.get("module_family") != "member_state":
            raise C5bError(f"c5b_national_hierarchy_requires_member_state_module:{export.get('module_id')}")
        relevant = False
        for req in case_obj.get("module_requests", []):
            if req.get("family") != "member_state":
                continue
            if te.same_jurisdiction(req.get("jurisdiction"), export.get("jurisdiction")) and req.get("role") in manifest.get("supported_roles", []):
                relevant = True
                break
        if not relevant:
            raise C5bError(f"member_state_module_not_requested_for_case:{export.get('jurisdiction')}")
        bindings.append({
            "module_id": export["module_id"],
            "jurisdiction": export["jurisdiction"],
            "manifest_sha256": digest_obj(manifest),
            "export_sha256": digest_obj(export),
        })
        for rule in export.get("rule_records", []):
            rid = rule["rule_id"]
            if rid in national_rules:
                raise C5bError(f"duplicate_bound_national_rule_id:{rid}")
            if rule.get("normative_layer") != "national":
                continue
            national_rules[rid] = {"module_id": export["module_id"], "rule": rule}
    return sorted(bindings, key=lambda x: x["module_id"]), national_rules


def classify_source_record(source):
    return {
        "source_ref": source["source_id"],
        "legal_status": source.get("legal_status", "unknown"),
        "source_type": source.get("source_type", "unknown"),
        "binding_force": binding_force(source),
        "hierarchy_note": hierarchy_note(source),
    }


def regime_map(regimes):
    return {x["element_id"]: x for x in regimes["candidates"]}


def build_lex_specialis_relationship(regimes, sources, used_sources):
    cmap = regime_map(regimes)
    d = cmap.get("legal_regime.directive_2004_38")
    v = cmap.get("legal_regime.visa_code")
    refs = ["eu:32004l0038", "eu:32009r0810"]
    for ref in refs:
        if ref not in sources:
            raise C5bError(f"required_hierarchy_source_missing:{ref}")
        used_sources.add(ref)
    if d is None or v is None:
        return {
            "relationship_id": "directive_visa_code_lex_specialis",
            "kind": "lex_specialis_overlap",
            "status": "blocked",
            "participant_refs": ["legal_regime.directive_2004_38", "legal_regime.visa_code"],
            "source_refs": refs,
            "principle_ids": [],
            "rationale_codes": ["required_regime_candidate_missing"],
            "review_required": True,
            "detail": "C5b cannot examine the Directive/Visa Code interaction because one or both required C5a candidate records are missing."
        }
    participants = [d["element_id"], v["element_id"]]
    if d["disposition"] == "candidate" and v["disposition"] == "candidate":
        return {
            "relationship_id": "directive_visa_code_lex_specialis",
            "kind": "lex_specialis_overlap",
            "status": "unresolved",
            "participant_refs": participants,
            "source_refs": refs,
            "principle_ids": [],
            "rationale_codes": ["coexisting_binding_secondary_law_candidates", "metadata_does_not_resolve_lex_specialis"],
            "review_required": True,
            "detail": "Both regimes remain candidates and both source instruments are binding secondary EU law. C5b preserves the lex-specialis question for issue-specific legal review rather than assigning priority from source class alone."
        }
    if d["disposition"] == "blocked" or v["disposition"] == "blocked":
        return {
            "relationship_id": "directive_visa_code_lex_specialis",
            "kind": "lex_specialis_overlap",
            "status": "blocked",
            "participant_refs": participants,
            "source_refs": refs,
            "principle_ids": [],
            "rationale_codes": ["underlying_regime_candidate_blocked"],
            "review_required": True,
            "detail": "At least one underlying regime candidate is blocked. Resolve the C5a gap before attempting hierarchy or lex-specialis analysis."
        }
    return {
        "relationship_id": "directive_visa_code_lex_specialis",
        "kind": "lex_specialis_overlap",
        "status": "not_indicated",
        "participant_refs": participants,
        "source_refs": refs,
        "principle_ids": [],
        "rationale_codes": ["coexisting_regime_candidates_not_present"],
        "review_required": False,
        "detail": "The bound C5a output does not contain simultaneous Directive and Visa Code candidates, so this overlap is not indicated in the current scope."
    }


def build_charter_scope(element_index, regimes, sources, used_sources):
    refs = ["eu:12012p", "eu:62010cj0617"]
    for ref in refs:
        if ref not in sources:
            raise C5bError(f"required_charter_source_missing:{ref}")
        used_sources.add(ref)
    val = single_value(element_index, "legal_regime.eu_law_scope_established")
    if regimes["resolution_status"] == "blocked":
        return {
            "disposition": "blocked",
            "eu_law_scope_state": "missing" if val is None else ("established" if val is True else "not_established"),
            "source_refs": refs,
            "rationale_codes": ["c5a_resolution_blocked"],
            "review_required": True,
            "detail": "C5a is blocked, so C5b does not promote Charter-scope analysis beyond a blocked review state."
        }
    if val is True:
        return {
            "disposition": "candidate",
            "eu_law_scope_state": "established",
            "source_refs": refs,
            "rationale_codes": ["eu_law_scope_established", "charter_scope_review_candidate"],
            "review_required": True,
            "detail": "The bound element state establishes EU-law scope for the scoped question. C5b therefore emits a Charter-scope review candidate, not a final finding that any particular Charter right is applicable or infringed."
        }
    if val is False:
        return {
            "disposition": "not_indicated",
            "eu_law_scope_state": "not_established",
            "source_refs": refs,
            "rationale_codes": ["eu_law_scope_not_established"],
            "review_required": False,
            "detail": "The bound element state says EU-law scope is not established for the scoped question. C5b does not emit a Charter applicability candidate from that state."
        }
    return {
        "disposition": "blocked",
        "eu_law_scope_state": "missing",
        "source_refs": refs,
        "rationale_codes": ["eu_law_scope_missing"],
        "review_required": True,
        "detail": "A scoped EU-law-scope determination is missing. Charter applicability cannot be promoted from regime candidacy alone."
    }


def principle_candidate(req, definition, scope_state, used_sources, regimes, sources, c5a_blocked=False):
    refs = list(definition["source_refs"])
    used_sources.update(refs)
    rationale = []
    limitations = ["Principle candidate status does not establish that the principle's substantive conditions are met in the facts of the case."]
    if "eu:62024cj0477" in refs:
        limitations.append("Deldwyn C-477/24 concerns retained residence-card status and decisive inaccessible former-spouse evidence; do not generalize its pre-decision file-access conclusion to every visa procedure or override Charter Article 41 addressee limits.")
    disposition = "candidate"
    review = True
    cmap = regime_map(regimes)
    for ref in req["basis_refs"]:
        if ref in cmap:
            if cmap[ref]["disposition"] != "candidate":
                disposition = "blocked"
                rationale.append("basis_regime_not_candidate")
        elif ref in sources:
            used_sources.add(ref)
        else:
            raise C5bError(f"unknown_principle_basis_ref:{ref}")
    if c5a_blocked:
        disposition = "blocked"
        rationale.append("c5a_resolution_blocked")

    if definition["requires_eu_law_scope"]:
        if scope_state == "missing":
            disposition = "blocked"
            rationale.append("eu_law_scope_missing")
        elif scope_state == "not_established":
            disposition = "not_indicated"
            rationale.append("eu_law_scope_not_established")
            review = False
        else:
            rationale.append("eu_law_scope_established")

    if definition["article_41_direct_addressee_boundary"] and disposition == "candidate":
        level = req["authority_level"]
        if level in {"member_state_authority", "national_court"}:
            disposition = "blocked"
            rationale.append("article_41_direct_addressee_boundary")
            limitations.append("Direct Article 41 reliance against a Member-State authority is kept distinct from general rights-of-defence/good-administration principles; request those separately where relevant.")
        elif level not in {"eu_institution", "eu_body"}:
            disposition = "blocked"
            rationale.append("article_41_addressee_not_scoped")
            limitations.append("The authority level must be scoped before direct Article 41 reliance can be considered.")
        else:
            rationale.append("article_41_eu_addressee_candidate")

    if disposition == "candidate":
        rationale.append("source_supported_principle_review")

    return {
        "request_id": req["request_id"],
        "principle_id": definition["principle_id"],
        "disposition": disposition,
        "scope": req["scope"],
        "authority_level": req["authority_level"],
        "basis_refs": req["basis_refs"],
        "requested_use": req["requested_use"],
        "source_refs": refs,
        "rationale_codes": sorted(set(rationale)),
        "review_required": review,
        "limitations": limitations,
    }


def source_use_assessment(req, source, sources, used_sources):
    used_sources.add(source["source_id"])
    bf = binding_force(source)
    legal_status = source.get("legal_status")
    support = []
    rationale = []
    review = True
    if req["proposed_use"] == "binding_rule" and legal_status in NON_BINDING_STATUSES:
        disposition = "blocked"
        rationale.append("non_binding_source_cannot_be_recoded_as_binding")
        detail = "The source metadata marks this material as non-binding. C5b rejects using it as a binding rule while preserving possible interpretive relevance for separate review."
        if source.get("source_type") == "commission_recommendation" or legal_status == "non_binding_soft_law":
            if "eu:61988cj0322" in sources:
                support.append("eu:61988cj0322")
                used_sources.add("eu:61988cj0322")
    elif req["proposed_use"] == "interpretive_support":
        disposition = "candidate"
        if legal_status in NON_BINDING_STATUSES:
            rationale.append("non_binding_interpretive_use_candidate")
            detail = "The source remains non-binding but may be considered as interpretive support. C5b does not convert relevance into binding force."
            if source.get("source_type") == "commission_recommendation" or legal_status == "non_binding_soft_law":
                if "eu:61988cj0322" in sources:
                    support.append("eu:61988cj0322")
                    used_sources.add("eu:61988cj0322")
        else:
            rationale.append("binding_source_interpretive_use_candidate")
            detail = "The source may be considered in interpretation, but proposition-specific legal meaning remains a review question."
    else:
        disposition = "candidate"
        review = False
        rationale.append("background_use_only")
        detail = "The source is requested only as background. No binding-force or proposition-level conclusion is inferred from that use."
    return {
        "request_id": req["request_id"],
        "source_ref": req["source_ref"],
        "proposed_use": req["proposed_use"],
        "disposition": disposition,
        "binding_force": bf,
        "supporting_source_refs": sorted(set(support)),
        "rationale_codes": sorted(set(rationale)),
        "review_required": review,
        "detail": detail,
    }


def national_conflict_relationship(q, national_rules, sources, principle_defs, used_sources):
    missing = sorted(set(q["national_rule_refs"]) - set(national_rules))
    if missing:
        raise C5bError("unknown_bound_national_rule_ref:" + ",".join(missing))
    missing_eu = sorted(set(q["eu_source_refs"]) - set(sources))
    if missing_eu:
        raise C5bError("unknown_eu_source_ref:" + ",".join(missing_eu))
    used_sources.update(q["eu_source_refs"])
    nonbinding = [ref for ref in q["eu_source_refs"] if binding_force(sources[ref]) not in {"primary_law", "binding_secondary_law", "binding_judicial_interpretation"}]
    participant_refs = sorted(set(q["eu_source_refs"] + q["national_rule_refs"]))
    if nonbinding:
        return {
            "relationship_id": q["question_id"],
            "kind": "eu_vs_national",
            "status": "blocked",
            "participant_refs": participant_refs,
            "source_refs": sorted(set(q["eu_source_refs"])),
            "principle_ids": [],
            "rationale_codes": ["non_binding_eu_source_cannot_ground_primacy_conflict"],
            "review_required": True,
            "detail": "At least one EU source presented as the hierarchy basis is non-binding. C5b will not construct a primacy/disapplication path from a non-binding source."
        }
    if q["assertion_status"] == "unknown":
        return {
            "relationship_id": q["question_id"],
            "kind": "eu_vs_national",
            "status": "blocked",
            "participant_refs": participant_refs,
            "source_refs": sorted(set(q["eu_source_refs"])),
            "principle_ids": [],
            "rationale_codes": ["conflict_assertion_unknown"],
            "review_required": True,
            "detail": "The possible EU/national conflict itself is not sufficiently asserted. C5b does not infer conflict from the existence of two rules."
        }
    principles = ["primacy", "disapplication", "consistent_interpretation"]
    rule_domains = {national_rules[r]["rule"].get("domain") for r in q["national_rule_refs"]}
    if "procedure" in rule_domains:
        principles += ["equivalence", "effectiveness"]
    principle_sources = []
    for pid in principles:
        if pid not in principle_defs:
            raise C5bError(f"required_principle_missing:{pid}")
        principle_sources.extend(principle_defs[pid]["source_refs"])
    used_sources.update(principle_sources)
    return {
        "relationship_id": q["question_id"],
        "kind": "eu_vs_national",
        "status": "unresolved",
        "participant_refs": participant_refs,
        "source_refs": sorted(set(q["eu_source_refs"] + principle_sources)),
        "principle_ids": sorted(set(principles)),
        "rationale_codes": ["bound_national_rule_present", "eu_national_conflict_requires_substantive_review", "no_automatic_disapplication"],
        "review_required": True,
        "detail": "A conformant Member-State rule and binding EU source are bound to a possible conflict question. C5b identifies relevant hierarchy/interpretive principles but does not establish the conflict, choose an interpretation, or order disapplication."
    }


def build(case_obj, regimes, element_bundle=None, context=None, module_pairs=None, source_pack=None):
    validate_obj("case-input", case_obj)
    if case_obj.get("privacy_classification") == "private":
        raise C5bError("private_data_disabled")
    validate_obj("legal-regime-candidates", regimes)
    if case_obj["case_id"] != regimes["case_id"]:
        raise C5bError("case_id_mismatch")
    if digest_obj(case_obj) != regimes["bound_case_sha256"]:
        raise C5bError("regime_case_binding_mismatch")

    if element_bundle is not None:
        validate_element_bundle(element_bundle)
        element_digest = digest_obj(element_bundle)
    else:
        element_digest = None
    if regimes["bound_element_bundle_sha256"] is not None:
        if element_bundle is None:
            raise C5bError("element_bundle_required_for_bound_regimes")
        if element_digest != regimes["bound_element_bundle_sha256"]:
            raise C5bError("regime_element_bundle_binding_mismatch")
    elif element_bundle is not None:
        raise C5bError("unexpected_element_bundle_for_unbound_regimes")

    if source_pack is None:
        source_pack = load_json(SOURCE_PACK_FILE)
    validate_obj("core-source-pack", source_pack)
    if digest_obj(source_pack) != regimes["source_pack_sha256"]:
        raise C5bError("regime_source_pack_binding_mismatch")
    sources = source_index(source_pack)

    principle_catalog, principle_defs = load_principle_catalog(sources)

    if context is not None:
        validate_obj("c5b-context", context)
        if context["case_id"] != case_obj["case_id"]:
            raise C5bError("context_case_id_mismatch")
        context_digest = digest_obj(context)
    else:
        context = {
            "context_version": "0.1.0",
            "case_id": case_obj["case_id"],
            "hierarchy_questions": [],
            "principle_requests": [],
            "source_use_requests": [],
        }
        context_digest = None

    module_bindings, national_rules = load_module_pairs(module_pairs, case_obj)
    if context["hierarchy_questions"] and not module_bindings:
        raise C5bError("member_state_module_required_for_hierarchy_question")

    idx = index_elements(element_bundle)
    used_sources = set()
    unresolved = []
    relationships = [build_lex_specialis_relationship(regimes, sources, used_sources)]

    charter = build_charter_scope(idx, regimes, sources, used_sources)
    if charter["disposition"] == "blocked":
        unresolved.append({
            "code": charter["rationale_codes"][0],
            "scope": "legal_regime.charter",
            "detail": charter["detail"],
        })

    principle_candidates = []
    scope_state = charter["eu_law_scope_state"]
    seen_requests = set()
    for req in context["principle_requests"]:
        if req["request_id"] in seen_requests:
            raise C5bError(f"duplicate_context_request_id:{req['request_id']}")
        seen_requests.add(req["request_id"])
        definition = principle_defs.get(req["principle_id"])
        if definition is None:
            raise C5bError(f"unknown_principle_id:{req['principle_id']}")
        cand = principle_candidate(req, definition, scope_state, used_sources, regimes, sources, regimes["resolution_status"] == "blocked")
        principle_candidates.append(cand)
        if cand["disposition"] == "blocked":
            unresolved.append({
                "code": cand["rationale_codes"][0] if cand["rationale_codes"] else "principle_blocked",
                "scope": req["request_id"],
                "detail": "; ".join(cand["limitations"]),
            })

    source_use_assessments = []
    for req in context["source_use_requests"]:
        if req["request_id"] in seen_requests:
            raise C5bError(f"duplicate_context_request_id:{req['request_id']}")
        seen_requests.add(req["request_id"])
        source = sources.get(req["source_ref"])
        if source is None:
            raise C5bError(f"unknown_source_use_ref:{req['source_ref']}")
        assessment = source_use_assessment(req, source, sources, used_sources)
        source_use_assessments.append(assessment)
        if assessment["disposition"] == "blocked":
            unresolved.append({
                "code": assessment["rationale_codes"][0],
                "scope": req["request_id"],
                "detail": assessment["detail"],
            })

    for q in context["hierarchy_questions"]:
        if q["question_id"] in seen_requests:
            raise C5bError(f"duplicate_context_request_id:{q['question_id']}")
        seen_requests.add(q["question_id"])
        rel = national_conflict_relationship(q, national_rules, sources, principle_defs, used_sources)
        relationships.append(rel)
        if rel["status"] == "blocked":
            unresolved.append({"code": rel["rationale_codes"][0], "scope": q["question_id"], "detail": rel["detail"]})

    classifications = [classify_source_record(sources[ref]) for ref in sorted(used_sources)]
    result = {
        "engine_version": ENGINE_VERSION,
        "ruleset_version": RULESET_VERSION,
        "contract_version": CONTRACT_VERSION,
        "element_model_version": ELEMENT_MODEL_VERSION,
        "case_id": case_obj["case_id"],
        "bindings": {
            "case_sha256": digest_obj(case_obj),
            "regime_candidates_sha256": digest_obj(regimes),
            "element_bundle_sha256": element_digest,
            "context_sha256": context_digest,
            "source_pack_version": source_pack["pack_version"],
            "source_pack_sha256": digest_obj(source_pack),
            "principle_catalog_version": principle_catalog["catalog_version"],
            "principle_catalog_sha256": digest_obj(principle_catalog),
            "module_bindings": module_bindings,
        },
        "resolution_status": "blocked" if regimes["resolution_status"] == "blocked" else "ready",
        "final_hierarchy_resolution": "not_determined",
        "source_classifications": classifications,
        "hierarchy_relationships": relationships,
        "charter_scope": charter,
        "principle_candidates": principle_candidates,
        "source_use_assessments": source_use_assessments,
        "unresolved": unresolved,
        "limitations": [
            "C5b emits hierarchy, Charter-scope, source-use and legal-principle review candidates only; it does not issue a final hierarchy resolution or final legal conclusion.",
            "Source legal-status metadata classifies binding force but does not by itself resolve lex-specialis, direct-effect, conflict, disapplication, proportionality, effectiveness or other substantive conditions.",
            "CJEU judgments are preserved as binding judicial interpretation and are not reduced to a numeric hierarchy rank against legislation.",
            "National rules are considered only when supplied through conformant Member-State module exports; C5b never invents national-law content.",
            "A non-binding source may have interpretive relevance but cannot be recoded as binding law by this engine.",
            "Charter and EU general-principle candidates require scoped EU-law context where the catalogue says so; missing scope remains explicit rather than inferred from regime candidacy."
        ],
    }
    validate_obj("c5b-hierarchy-principles", result)
    return result


def main():
    ap = argparse.ArgumentParser(description="Build C5b hierarchy/Charter/general-principle review candidates")
    ap.add_argument("case")
    ap.add_argument("regimes")
    ap.add_argument("--elements")
    ap.add_argument("--context")
    ap.add_argument("--module-pair", nargs=2, action="append", metavar=("MANIFEST", "EXPORT"))
    ap.add_argument("--source-pack", default=str(SOURCE_PACK_FILE))
    ap.add_argument("--output")
    args = ap.parse_args()
    try:
        case_obj = load_json(Path(args.case))
        regimes = load_json(Path(args.regimes))
        elements = load_json(Path(args.elements)) if args.elements else None
        context = load_json(Path(args.context)) if args.context else None
        source_pack = load_json(Path(args.source_pack))
        result = build(case_obj, regimes, elements, context, args.module_pair, source_pack)
        rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (C5bError, ContractError, OSError, ValueError) as e:
        print(json.dumps({"status": "invalid", "error": str(e)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
