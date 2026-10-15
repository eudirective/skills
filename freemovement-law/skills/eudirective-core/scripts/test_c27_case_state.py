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
        self.assertEqual(len(reg["checks"]), 251)
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
        x["events"].append({"event_id":"E10","proceeding_id":"P1","kind":"procedural_step",
                            "source":"user_reported","step":"receipt_issued"})
        r = c.evaluate(x)["proceedings"][0]
        self.assertEqual(r["lodgement"], "reported_not_documented")

    def test_documented_receipt(self):
        x = load("initial.json")
        x["events"].append({"event_id":"E10","proceeding_id":"P1","kind":"procedural_step",
                            "source":"document_seen","step":"receipt_issued"})
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

if __name__ == "__main__":
    unittest.main()
