import json
import unittest
from pathlib import Path
import c27_case_state as c

FIX = Path(__file__).resolve().parents[1] / "evaluations/fixtures/c27"

def load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))

class CaseStateTests(unittest.TestCase):
    def test_registry_and_fixture(self):
        reg = c.load_registry()
        self.assertEqual(len(reg["checks"]), 301)
        r = c.evaluate(load("multi-proceeding.json"))
        self.assertEqual(len(r["proceedings"]), 2)
        first = r["proceedings"][0]
        self.assertEqual(first["stage"], "lodgement_disputed")
        self.assertEqual(first["lodgement"], "disputed")
        self.assertEqual(first["disclosures"][0]["delivery_state"], "delivered_not_content_acknowledged")
        self.assertEqual(first["documents"][0]["operations"][0]["action"], "shown")
        self.assertEqual(r["proceedings"][1]["parent_proceeding_id"], "P1")
        self.assertGreater(r["coverage"]["outstanding_total"], 0)

    def test_disclosure_does_not_imply_content_knowledge(self):
        x = load("initial.json")
        disclosure = c.evaluate(x)["proceedings"][0]["disclosures"][0]
        self.assertNotEqual(disclosure["delivery_state"], "content_acknowledged")

    def test_appointment_and_form_not_lodging(self):
        x = load("initial.json")
        x["events"] = x["events"][:2]
        x.pop("responses")
        x["events"].append({"event_id":"E10","proceeding_id":"P1","kind":"procedural_step",
                            "source":"user_reported","step":"online_form_submitted"})
        result = c.evaluate(x)["proceedings"][0]
        self.assertEqual(result["lodgement"], "not_established")
        self.assertEqual(result["stage"], "online_submission_unverified")

    def test_reported_receipt_not_documented(self):
        x = load("initial.json")
        x["events"] = x["events"][:2]
        x.pop("responses")
        x["events"].append({"event_id":"E10","proceeding_id":"P1","kind":"procedural_step",
                            "source":"user_reported","step":"receipt_issued"})
        r = c.evaluate(x)["proceedings"][0]
        self.assertEqual(r["lodgement"], "receipt_purpose_unverified")

    def test_documented_receipt(self):
        x = load("initial.json")
        x["events"].append({"event_id":"E10","proceeding_id":"P1","kind":"procedural_step",
                            "source":"document_seen","step":"receipt_issued",
                            "receipt_kind":"application_lodgement",
                            "issuer_role":"consulate"})
        r = c.evaluate(x)["proceedings"][0]
        self.assertEqual(r["lodgement"], "documented")

    def test_no_fabricated_acknowledgement(self):
        x=load("initial.json")
        x["events"].append({"event_id":"E10","proceeding_id":"P1",
              "kind":"disclosure_observation","source":"model_inference",
              "disclosure_id":"I1","observation":"content_relied_on"})
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_correction_is_audited(self):
        x=load("initial.json")
        x["events"].append({"event_id":"E10","proceeding_id":"P1","kind":"event_correction",
            "source":"user_reported","target_event_id":"E6",
            "replacement":{"event_id":"E11","proceeding_id":"P1","kind":"procedural_step",
                          "source":"user_reported","step":"lodgement_attempted"}})
        x["responses"]=[]
        r=c.evaluate(x)
        self.assertEqual(r["corrections_applied"], 1)
        self.assertEqual(r["proceedings"][0]["lodgement"], "attempted_unconfirmed")

    def test_multi_proceeding_diff(self):
        r=c.compare(load("initial.json"),load("multi-proceeding.json"))
        self.assertIn("new_proceeding",[i.get("kind") for i in r["changes"]])

    def test_no_non_append_only_revisions(self):
        a=load("initial.json")
        b=load("multi-proceeding.json")
        b["events"][0]["procedure_type"]="ordinary_short_stay_visa"
        with self.assertRaises(c.StateError):
            c.compare(a,b)

    def test_not_applicable_requires_scope_reason(self):
        x=load("initial.json")
        x["responses"][0]["checks"][0].update(status="not_applicable",method="none",reason="not_attempted")
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_script_cannot_claim_execution(self):
        x=load("initial.json")
        x["responses"][0]["checks"][0]["method"]="script_execution"
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_source_review_needs_citation(self):
        x=load("initial.json")
        x["responses"][0]["checks"][0]["method"]="source_review"
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_latest_response_assessment_remains_current_if_other_proceeding_changes(self):
        x=load("multi-proceeding.json")
        r=c.evaluate(x,full=True)
        match=[i for i in r["coverage"]["checks"] if i["proceeding_id"]=="P1" and i["check_id"]=="lifecycle.lodgement_disputed"]
        self.assertEqual(match[0]["status"],"assessed")

    def test_unknown_case_keys_fail_closed(self):
        x=load("initial.json")
        x["applicant_full_name"]="Person"
        with self.assertRaises(c.StateError):
            c.evaluate(x)


    def test_correction_preserves_historical_response_and_marks_stale(self):
        x = load("initial.json")
        x["events"].append({
            "event_id":"E10", "proceeding_id":"P1",
            "kind":"event_correction", "source":"user_reported",
            "target_event_id":"E6",
            "replacement":{
                "event_id":"E11", "proceeding_id":"P1",
                "kind":"procedural_step", "step":"lodgement_attempted",
                "source":"user_reported"
            }
        })
        r = c.evaluate(x, full=True)
        self.assertEqual(r["corrections_applied"], 1)
        self.assertEqual(r["proceedings"][0]["lodgement"], "attempted_unconfirmed")
        row = next(q for q in r["coverage"]["checks"]
                   if q["proceeding_id"] == "P1"
                   and q["check_id"] == "lifecycle.lodgement_disputed")
        self.assertEqual(row["status"], "needs_recheck")

    def test_reusing_corrected_old_evidence_in_new_response_fails(self):
        x = load("initial.json")
        x["events"].append({
            "event_id":"E10", "proceeding_id":"P1",
            "kind":"event_correction", "source":"user_reported",
            "target_event_id":"E6",
            "replacement":{
                "event_id":"E11", "proceeding_id":"P1",
                "kind":"procedural_step", "step":"lodgement_attempted",
                "source":"user_reported"
            }
        })
        x["responses"].append({
            "response_id":"R2","through_event_id":"E10","checks":[{
                "check_id":"lifecycle.lodgement_disputed","proceeding_id":"P1",
                "status":"assessed","method":"model_review",
                "reason":"scope_reviewed","evidence_event_ids":["E6"]
            }]
        })
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_new_event_after_last_response_requires_recheck(self):
        x = load("initial.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1",
            "kind":"procedural_step","step":"supplement_requested",
            "source":"user_reported"
        })
        full = c.evaluate(x, full=True)["coverage"]["checks"]
        checked = next(q for q in full if q["check_id"] == "lifecycle.lodgement_disputed")
        self.assertEqual(checked["status"], "needs_recheck")

    def test_previous_appointment_trigger_survives_later_decision(self):
        x = load("initial.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1",
            "kind":"procedural_step","step":"decision_taken",
            "source":"user_reported"
        })
        p = c.evaluate(x)["proceedings"][0]
        self.assertEqual(p["stage"], "decision_taken")
        self.assertIn("appointment", c.feature_tags(p))
        self.assertIn("lodgement", c.feature_tags(p))

    def test_late_discovered_earlier_event_is_flagged(self):
        x = load("initial.json")
        x["events"][1]["occurred_order"] = 17
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1",
            "kind":"procedural_step","step":"inquiry_sent",
            "occurred_order":3,"source":"user_reported"
        })
        p = c.evaluate(x)["proceedings"][0]
        self.assertIn("later_disclosed_earlier_event", p["flags"])
        timeline = p["timeline_by_relative_occurrence"]
        self.assertEqual(timeline[0]["event_id"], "E10")
        self.assertEqual(timeline[1]["event_id"], "E2")

    def test_relative_order_rejects_actual_dates_and_invalid_values(self):
        x = load("initial.json")
        x["events"][0]["occurred_order"] = "2026-10-15"
        with self.assertRaises(c.StateError):
            c.evaluate(x)
        x["events"][0]["occurred_order"] = -1
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_content_acknowledged_not_erased_by_transport_update(self):
        x = load("initial.json")
        x["events"].extend([
            {"event_id":"E10","proceeding_id":"P1","kind":"disclosure_observation",
             "source":"authority_record_seen","disclosure_id":"I1",
             "observation":"content_acknowledged"},
            {"event_id":"E11","proceeding_id":"P1","kind":"disclosure_observation",
             "source":"document_seen","disclosure_id":"I1",
             "observation":"transport_delivered"}
        ])
        d = c.evaluate(x)["proceedings"][0]["disclosures"][0]
        self.assertEqual(d["delivery_state"], "content_acknowledged")
        self.assertTrue(d["transmission_delivered"])
        self.assertTrue(d["content_acknowledged"])

    def test_conflicting_transport_observations_are_not_resolved_by_order(self):
        x = load("initial.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1","kind":"disclosure_observation",
            "source":"document_seen","disclosure_id":"I1",
            "observation":"transmission_failed"
        })
        p = c.evaluate(x)["proceedings"][0]
        self.assertEqual(p["disclosures"][0]["delivery_state"],
                         "conflicting_observations")
        self.assertIn("disclosure_transport_conflict", p["flags"])

    def test_model_cannot_infer_delivery(self):
        x = load("initial.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1","kind":"disclosure_observation",
            "source":"model_inference","disclosure_id":"I1",
            "observation":"transport_delivered"
        })
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_same_document_usable_in_multiple_proceedings(self):
        x = load("multi-proceeding.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P2","kind":"document_event",
            "source":"user_reported","document_id":"D1",
            "document_category":"marriage_record","operation":"shown",
            "recipient_id":"A2"
        })
        p1, p2 = c.evaluate(x)["proceedings"]
        self.assertEqual(p1["documents"][0]["document_id"], "D1")
        self.assertEqual(p2["documents"][0]["document_id"], "D1")
        self.assertNotEqual(p1["documents"][0]["operations"][0]["recipient_id"],
                            p2["documents"][0]["operations"][0]["recipient_id"])

    def test_different_document_category_across_proceedings_is_rejected(self):
        x = load("multi-proceeding.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P2","kind":"document_event",
            "source":"user_reported","document_id":"D1",
            "document_category":"passport","operation":"shown",
            "recipient_id":"A2"
        })
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_untyped_receipt_not_formal_lodgement_even_if_seen(self):
        x = load("initial.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1","kind":"procedural_step",
            "step":"receipt_issued","source":"document_seen",
            "receipt_kind":"provider_check_in","issuer_role":"visa_application_centre"
        })
        p = c.evaluate(x)["proceedings"][0]
        self.assertNotEqual(p["lodgement"], "documented")
        self.assertIn("receipt_does_not_establish_lodgement", p["flags"])

    def test_unqualified_confirmation_does_not_prove_lodgement(self):
        x = load("initial.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1","kind":"procedural_step",
            "step":"lodgement_confirmed","source":"document_seen",
            "record_kind":"file_opened"
        })
        p = c.evaluate(x)["proceedings"][0]
        self.assertNotEqual(p["lodgement"], "documented")

    def test_verified_formal_lodgement_record(self):
        x = load("initial.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1","kind":"procedural_step",
            "step":"lodgement_confirmed","source":"authority_record_seen",
            "record_kind":"formal_lodgement"
        })
        self.assertEqual(c.evaluate(x)["proceedings"][0]["lodgement"],
                         "documented")

    def test_authority_classification_separate_from_claimed_regime(self):
        x = load("initial.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1","kind":"authority_classification",
            "source":"reported_authority_oral",
            "classified_as":"ordinary_short_stay_visa"
        })
        p = c.evaluate(x)["proceedings"][0]
        self.assertEqual(p["claimed_regime"], "directive_2004_38")
        self.assertEqual(p["authority_classifications"][0]["classified_as"],
                         "ordinary_short_stay_visa")

    def test_unimplemented_or_synthetic_check_cannot_be_assessed(self):
        for key in ("stratagems.adapted_36","strategy.known_precedent"):
            x = load("initial.json")
            x["responses"][0]["checks"][0]["check_id"] = key
            with self.assertRaises(c.StateError):
                c.evaluate(x)

    def test_explicit_unavailable_capability_is_reportable(self):
        x = load("initial.json")
        x["responses"][0]["checks"][0] = {
            "check_id":"stratagems.adapted_36","proceeding_id":"P1",
            "status":"unavailable","method":"none","reason":"synthetic_only"
        }
        r = c.evaluate(x, full=True)
        row = next(q for q in r["coverage"]["checks"]
                   if q["check_id"]=="stratagems.adapted_36")
        self.assertEqual(row["status"],"unavailable_for_live_advice")

    def test_assessment_must_have_evidence_or_source_trace(self):
        x = load("initial.json")
        x["responses"][0]["checks"][0].pop("evidence_event_ids")
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_not_applicable_requires_reason_and_trace(self):
        x = load("initial.json")
        check = x["responses"][0]["checks"][0]
        check.update(status="not_applicable",method="none",reason="scope_excluded",
                     scope_exclusion="irrelevant_stage")
        c.evaluate(x)
        check.pop("evidence_event_ids")
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_cross_proceeding_evidence_cannot_verify_unrelated_check(self):
        x = load("multi-proceeding.json")
        x["responses"].append({
            "response_id":"R2","through_event_id":"E9","checks":[{
                "check_id":"proof.burden_of_proof","proceeding_id":"P2",
                "status":"assessed","method":"model_review",
                "reason":"scope_reviewed","evidence_event_ids":["E6"]
            }]
        })
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_future_proceeding_cannot_enter_past_response(self):
        x = load("multi-proceeding.json")
        x["responses"][0]["checks"][0]["proceeding_id"] = "P2"
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_excluded_issue_needs_reason_code(self):
        x = load("initial.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1","kind":"issue_event",
            "source":"user_reported","issue_id":"G1",
            "issue_category":"lodgement","disposition":"excluded_with_reason",
            "from_event_id":"E6"
        })
        with self.assertRaises(c.StateError):
            c.evaluate(x)
        x["events"][-1]["exclusion_reason"]="no_independent_grievance"
        p = c.evaluate(x)["proceedings"][0]
        self.assertEqual(p["issues"][0]["exclusion_reason"],
                         "no_independent_grievance")

    def test_review_history_is_append_only(self):
        old = load("initial.json")
        new = load("multi-proceeding.json")
        new["responses"][0]["checks"][0]["status"]="partial"
        with self.assertRaises(c.StateError):
            c.compare(old,new)

    def test_registry_resolves_catalog_records(self):
        reg = c.load_registry()
        self.assertEqual(len(reg["checks"]), 301)
        self.assertEqual(len(reg["families"]),23)
        self.assertEqual(len([a for a in reg["checks"]
                              if a.get("catalog_entry_id","").startswith("adapted:")]),36)
        self.assertEqual(len([a for a in reg["checks"]
                              if a["family"] == "principle_catalog"]),14)
        for check in reg["checks"]:
            self.assertTrue((c.ROOT / check["reference"]).is_file(),
                            check["check_id"])

    def test_focus_enables_per_stratagem_and_principle_checks(self):
        x=load("initial.json")
        x["requested_focus"]=["stratagem","legal_principle"]
        all_rows=c.evaluate(x,full=True)["coverage"]["checks"]
        patterns=[q for q in all_rows if q["check_id"].startswith("stratagems.pattern_")]
        principles=[q for q in all_rows if q["family"]=="principle_catalog"]
        self.assertEqual(len(patterns),36)
        self.assertEqual(len(principles),14)
        self.assertTrue(all(q["status"] != "not_indicated_not_excluded"
                            for q in patterns+principles))

    def test_priority_sorting_puts_urgent_material_gaps_first(self):
        x=load("initial.json")
        coverage=c.evaluate(x)["coverage"]
        sample=coverage["outstanding_sample"]
        self.assertTrue(sample)
        self.assertEqual(sample[0]["priority"],"urgent")
        self.assertTrue(coverage["outstanding_sample_is_priority_sorted"])


    def test_proceeding_classification_revision_keeps_same_proceeding(self):
        x=load("initial.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1","kind":"event_correction",
            "source":"user_reported","target_event_id":"E1",
            "correction_reason":"classification_revision",
            "replacement":{
                "event_id":"E11","proceeding_id":"P1",
                "kind":"proceeding_opened","source":"user_reported",
                "procedure_type":"ordinary_short_stay_visa",
                "claimed_regime":"visa_code","authority_role":"consulate"
            }
        })
        result=c.evaluate(x,full=True)
        self.assertEqual(len(result["proceedings"]),1)
        self.assertEqual(result["proceedings"][0]["type"],
                         "ordinary_short_stay_visa")
        self.assertEqual(result["correction_log"][0]["supersedes"],"E1")
        self.assertEqual(result["coverage"]["latest_response_id"],"R1")

    def test_reclassification_requires_explicit_reason(self):
        x=load("initial.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1","kind":"event_correction",
            "source":"user_reported","target_event_id":"E1",
            "replacement":{
                "event_id":"E11","proceeding_id":"P1",
                "kind":"proceeding_opened","source":"user_reported",
                "procedure_type":"ordinary_short_stay_visa",
                "claimed_regime":"visa_code","authority_role":"consulate"
            }
        })
        with self.assertRaises(c.StateError):
            c.evaluate(x)

    def test_proceeding_correction_does_not_erase_old_event_ids(self):
        x=load("initial.json")
        x["events"].append({
            "event_id":"E10","proceeding_id":"P1","kind":"event_correction",
            "source":"user_reported","target_event_id":"E6",
            "correction_reason":"user_correction",
            "replacement":{
                "event_id":"E11","proceeding_id":"P1",
                "kind":"procedural_step","step":"lodgement_attempted",
                "source":"user_reported"
            }
        })
        active, all_ids, replaced = c.normalize_events(x)
        self.assertIn("E6",all_ids)
        self.assertIn("E11",all_ids)
        self.assertIn("E6",replaced)
        self.assertEqual(len(active),len(x["events"])-1)

    def test_unsupported_status_cannot_be_claimed_by_model(self):
        x=load("initial.json")
        x["responses"][0]["checks"][0].update(
            check_id="strategy.historical_outcome",status="assessed",
            method="model_review",reason="scope_reviewed"
        )
        with self.assertRaises(c.StateError):
            c.evaluate(x)

if __name__ == "__main__":
    unittest.main()
