# ELTE IK TDK / MSc Thesis 50-Point Audit Kit for Reviewers
**Candidate:** Hamed Mohamed (Neptun: DG1EWF)  
**Title:** Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines  
**External Advisor:** Gregory Reynolds Morse  

---

## Quickstart: Running the Scorer Locally

The audit tool is zero-dependency standard Python 3.

### 1. View Author Baseline Score (50/50)
```bash
python3 score_tdk.py review-author-baseline.json
```

### 2. Enter Your Independent Scores
Edit `review-morse-template.json`. For each of the 50 items (N01-N08, T01-T08, V01-V08, L01-L06, F01-F06, S01-S06, Q01-Q08):
- Change `"status"` to `"awarded"` (1 point) or `"not_awarded"` (0 points) — or `"pending"` / `"unverified"` if unresolved.
- Record your notes / critique in `"evidence"`.
- Refer to `rubric.md` for the exact definitions of all 50 items.

Run the scorer on your review:
```bash
python3 score_tdk.py review-morse-template.json
```

### 3. Reconcile / Compare Two Reviews
To run a two-reviewer comparison between the Author baseline and your review (computing delta, mean, and OTDK >15pt reconciliation check):
```bash
python3 score_tdk.py review-author-baseline.json --second review-morse-template.json
```

---

## Optional: Using AI Assistants (ChatGPT / Claude)
If you prefer an LLM to assist in brutally reviewing the thesis against the rubric:
- Upload `elte-ik-tdk-50-point-audit.zip` as a custom skill in **ChatGPT (Customize -> Skills)** or **Claude (Skills)**.
- Prompt:
  > "Use the ELTE IK TDK 50-Point Audit on the attached thesis PDF. Audit all 50 Boolean items brutally, identify blockers, and score each item."
