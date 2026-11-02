#!/usr/bin/env python3
"""Deterministic regression tests; fixtures are synthetic, not student assessments."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import score_topics as s


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.topic_map = s.load_json(s.DEFAULT_MAP)
        s.validate_map(self.topic_map)
        self.data = s.build_template(self.topic_map)
        self.data["project"].update(title="Anonymous research project", stage="Design")
        self.data["artifacts"] = [
            {"id": "D", "kind": "design", "path_or_name": "design.md", "version_or_date": "v1", "status": "current"},
            {"id": "F", "kind": "neptun_form", "path_or_name": "current-form.png", "version_or_date": "2026-10-08", "status": "current"},
        ]
        for a in self.data["topic_assessments"].values():
            a["minimum_work"] = "Do not choose this topic on the present scope."
            for e in a["entries"].values():
                e.update(status="N", justification="Not evidenced by the supplied synthetic design.")

    def set_atom(self, number, atom, status="C"):
        e = self.data["topic_assessments"][str(number)]["entries"][atom]
        e.update(status=status, evidence=["D: Formal model, section 2"], justification="Synthetic substantial relation.")
        if status == "P":
            e.update(work="Complete the named proof obligation", acceptance_evidence=["Checked lemma in model.thy"], feasibility="Approved design task within the stated milestone.")

    def strong(self, number):
        t = self.topic_map["topics"][number-1]
        anchor = t["anchors"][0]
        other = next(a["id"] for a in t["atoms"] if a["id"] != anchor)
        self.set_atom(number, anchor)
        self.set_atom(number, other)

    def result(self, number):
        self.assertEqual(s.validate_assessment(self.data, self.topic_map), [])
        return next(r for r in s.analyze(self.data, self.topic_map) if r["number"] == number)

    def test_complete_map_and_no_links(self):
        ranked = s.analyze(self.data, self.topic_map)
        self.assertEqual(s.validate_assessment(self.data, self.topic_map), [])
        self.assertTrue(all(r["tier"] == "Below cutoff" and r["lower"] == 0 for r in ranked))
        chosen, state = s.recommendation(ranked)
        self.assertEqual(chosen, [])
        self.assertIn("NOT READY", state)
        report = s.make_report(self.data, self.topic_map, ranked)
        self.assertIn(s.CUTOFF, report)
        for t in self.topic_map["topics"]:
            for a in t["atoms"]:
                self.assertIn(a["id"], report)

    def test_strong_and_exact_fraction(self):
        self.strong(4)
        self.set_atom(4, "t04.10", "P")
        r = self.result(4)
        self.assertEqual(r["tier"], "Strong now")
        self.assertEqual(r["lower"], s.Fraction(2, 10))
        self.assertEqual(r["upper"], s.Fraction(3, 10))
        self.assertIn("2/10 to 3/10 (20.0% to 30.0%)", s.range_text(r))

    def test_conditional_and_all_future(self):
        self.set_atom(4, "t04.01")
        self.set_atom(4, "t04.02", "P")
        self.assertEqual(self.result(4)["tier"], "Conditionally defensible")
        self.set_atom(4, "t04.01", "P")
        self.assertEqual(self.result(4)["tier"], "Below cutoff")

    def test_non_anchor_overlap_fails(self):
        for atom in ("t04.01", "t04.05", "t04.07", "t04.09"):
            self.set_atom(4, atom)
        self.assertEqual(self.result(4)["tier"], "Below cutoff")

    def test_appendix_does_not_displace_until_verified(self):
        for n in (4, 6, 16):
            self.strong(n)
        for a in self.topic_map["topics"][19]["atoms"]:
            self.set_atom(20, a["id"])
        ranked = s.analyze(self.data, self.topic_map)
        chosen, state = s.recommendation(ranked)
        self.assertNotIn(20, [r["number"] for r in chosen])
        self.assertEqual(state, "ADMINISTRATIVELY PROVISIONAL")
        self.data["topic_assessments"]["20"]["eligibility"].update(status="verified", evidence=["F: MSc selection dropdown, Advanced Software Technology"], reason="Confirmed by the student's current form.")
        self.assertEqual(s.validate_assessment(self.data, self.topic_map), [])
        chosen, _ = s.recommendation(s.analyze(self.data, self.topic_map))
        self.assertEqual(chosen[0]["number"], 20)
        self.data["selected_topics"] = [20, 4, 16]
        report = s.make_report(self.data, self.topic_map, s.analyze(self.data, self.topic_map))
        self.assertNotIn("20. Advanced Software Technology** — Below cutoff", report)

    def test_unavailable_exclusion_and_ready_human_review(self):
        for n in (4, 6, 16, 19):
            self.strong(n)
            self.data["topic_assessments"][str(n)]["eligibility"].update(status="verified", evidence=[f"F: Subject {n}, current choices"], reason="Confirmed current choice.")
        chosen, state = s.recommendation(s.analyze(self.data, self.topic_map))
        self.assertIn("READY FOR HUMAN REVIEW", state)
        n = chosen[0]["number"]
        self.data["topic_assessments"][str(n)]["eligibility"].update(status="unavailable", reason="Not offered in current form.")
        chosen, _ = s.recommendation(s.analyze(self.data, self.topic_map))
        self.assertNotIn(n, [r["number"] for r in chosen])
        self.assertEqual(len(chosen), 3)

    def test_missing_extra_and_invalid_entries_rejected(self):
        for kind in ("missing", "extra", "fractional", "no_pointer", "unknown_pointer", "vague_p", "map_version"):
            with self.subTest(kind=kind):
                d = copy.deepcopy(self.data)
                es = d["topic_assessments"]["4"]["entries"]
                if kind == "missing":
                    del es["t04.01"]
                elif kind == "extra":
                    es["invented"] = es["t04.01"]
                elif kind == "fractional":
                    es["t04.01"]["status"] = 0.5
                elif kind == "no_pointer":
                    es["t04.01"]["status"] = "C"
                elif kind == "unknown_pointer":
                    es["t04.01"].update(status="C", evidence=["UNLISTED: claim"])
                elif kind == "vague_p":
                    es["t04.01"].update(status="P", evidence=["D: an idea"])
                else:
                    d["map_version"] = "old"
                self.assertTrue(s.validate_assessment(d, self.topic_map))

    def test_admin_cannot_be_verified_by_design(self):
        self.data["topic_assessments"]["20"]["eligibility"].update(status="verified", evidence=["D: name appears in an index"])
        self.assertTrue(s.validate_assessment(self.data, self.topic_map))

    def test_preferred_alternative_and_summary_accounting(self):
        for n in (4, 6, 16, 19):
            self.strong(n)
        ranked = s.analyze(self.data, self.topic_map)
        chosen, _ = s.recommendation(ranked)
        alternative = next(r["number"] for r in ranked if r["candidate"] and r["number"] not in {c["number"] for c in chosen})
        self.data["selected_topics"] = [chosen[0]["number"], chosen[1]["number"], alternative]
        report = s.make_report(self.data, self.topic_map, ranked)
        self.assertIn("Unresolved comparison required against", report)
        summary = s.summary_json(ranked, self.topic_map["map_version"])
        self.assertEqual(len(summary["ranking"]), 19)
        self.assertEqual(len(summary["supplemental"]), 1)
        self.assertEqual(sum(r["counts"]["total"] for r in summary["ranking"]+summary["supplemental"]), 409)

    def test_invalid_input_shapes_return_errors(self):
        for field, value in (("project", []), ("artifacts", {}), ("current_sources", None), ("selected_topics", [1,2,3,4]), ("topic_assessments", [])):
            with self.subTest(field=field):
                d = copy.deepcopy(self.data)
                d[field] = value
                self.assertTrue(s.validate_assessment(d, self.topic_map))

    def test_preferred_partial_and_stop_conditions(self):
        self.strong(20)
        self.data["selected_topics"] = [20]
        report = s.make_report(self.data, self.topic_map, s.analyze(self.data, self.topic_map))
        self.assertIn("Partial preference", report)
        self.assertIn("STOP: 20.", report)
        self.data["selected_topics"] = [True]
        self.assertTrue(s.validate_assessment(self.data, self.topic_map))

    def test_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"assessment.json"
            with patch.object(sys_module := s.sys, "argv", ["score_topics.py", "--template", str(path)]):
                self.assertEqual(s.main(), 0)
            before = path.read_bytes()
            with patch.object(sys_module, "argv", ["score_topics.py", "--template", str(path)]):
                self.assertEqual(s.main(), 2)
            self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
