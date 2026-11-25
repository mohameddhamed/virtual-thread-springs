# Declaration on the Use of Artificial Intelligence Tools

**MANDATORY ATTACHMENT TO THE THESIS (ANNEX 3 OF DEAN'S DIRECTIVE NO. 1/2026)**  
*Faculty of Informatics, Eötvös Loránd University (ELTE), Budapest*

---

### Student and Thesis Metadata

* **Name of the student:** Hamed Mohamed  
* **Neptun code:** `DG1EWF`  
* **Name of the study program:** Computer Science MSc (Software Architecture Specialization)  
* **Details of the submitted work:**
  * **Title:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*  
  * **Type:** MSc thesis  
* **Supervisory Team:**
  * **Internal Faculty Supervisor:** Dr. habil. Tamás Kozsik (Associate Professor, Head of Department of Programming Languages and Compilers, ELTE)  
  * **External Thesis Advisor / Research Supervisor:** Gregory Reynolds Morse (`morse@inf.elte.hu`, Lecturer and MSc in Computer Science, ELTE)  
* **Request Identifier:** `IK-ZVMSC_EN2_155` (Approved: 2026.10.27)  
* **Final Examination Subjects:** *Project Management*, *Advanced Java programming*, *Scalable enterprise applications*  

---

### Statement on AI Usage

One option must be selected in the declaration below:

- [ ] I did not use any artificial intelligence tools in the preparation of the submitted work.
- [x] **I used artificial intelligence tools in the preparation of the submitted work as detailed below.**

---

### Detailed Table of AI Tool Usage

| For what purpose? <br>*(e.g. outlining, processing literature, AI development)* | How was it used? <br>*(e.g. validating AI outputs, adapting them to the task, revising them, with a description demonstrating critical and creative use)* | Which AI tool was used? <br>*(e.g. ChatGPT 3.0, Copilot, Grok)* | In which part of the thesis? <br>*(e.g. table of contents on page 3, implementation)* |
| :--- | :--- | :--- | :--- |
| **Structural Drafting, Chapter Outlining, and Prose Polish** | Generated initial structural outlines and syntactic drafts for standard framework descriptions; critically revised and rewritten by the author to align with ELTE academic standards and queueing models. | Anthropic Claude (Claude 3.5 Sonnet) | Chapters 1 (§1.2), 3 (§3.1), 4 (§4.1), 5 (§5.1), 7 (§7.1), and 8 |
| **Scaffolding Empirical Recalculation & Verification Scripts** | Generated preliminary Python templates for parsing raw k6 JSON lines streams and JFR binary events; manually audited, refined, and validated against physical data using cryptographic SHA-256 checksums. | Anthropic Claude (Claude 3.5 Sonnet) & GitHub Copilot | [`scripts/normalize_evidence.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/normalize_evidence.py), [`scripts/recalculate_metrics.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/recalculate_metrics.py), [`scripts/validate_normalized_evidence.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/validate_normalized_evidence.py) |
| **Integration Test Template Scaffolding** | Autocompleted boilerplate JUnit 5 integration test fixtures; manually verified and adapted with strict assertions for mutual exclusion across all locking strategies, transactional semantics, ThreadLocal cleanup, and native JNI bindings (`mvn test` 9/9 pass). | GitHub Copilot | Chapter 5 (Implementation) and [`src/test/java/com/thesis/virtualthreadsdemo/`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/test/java/com/thesis/virtualthreadsdemo/) |
| **Pre-Submission Editorial and Formatting Audit** | Automated static editorial audit for layout, cross-document reference consistency, and overfull boxes; all findings independently audited, verified against raw artifacts, and remediated by the author. | Independent Reasoning Model / Editorial Audit | Pre-submission audit across all chapters and appendices |
| **Evidence reconciliation and citation checks** | Codex recomputed table cells from frozen runs, checked references, revised claims and rebuilt the PDF. | OpenAI Codex | Chapters 1–8, abstracts, appendices, bibliography and claim ledger |
| **Editorial revision and LaTeX verification** | Reordered and condensed existing material, moved the annotated literature table, consolidated future work, aligned the matrix name, and rebuilt the PDF. | OpenAI Codex (GPT-6.2 Sol) | Abstract and Kivonat, Chapters 1, 2, 4, 6, 7 and 8, Appendices A, B and D, and the C1–C4 table formatting source |
| **Pre-submission audit, scope alignment, and final polish, 25 November 2026** | Executed adversarial pre-submission audit against Checkpoints 2–4; expanded parameterized lock-mode integration test (`9/9` pass), tightened RQ2 operational closure and Appendix D scope/length alignment, corrected Chapter 5 artifact count (`543`), removed residual wrapper output in `recalculate_metrics.py`, updated `.docx` declaration table, and verified clean 100-page LaTeX compilation (basis of `Declaration_on_the_use_of_AI_tools_DG1EWF_signed.pdf`). | Google Gemini (Antigravity) | Chapters 1 and 5, Appendices A–D, `ApplicationBehaviorTests.java`, `scripts/recalculate_metrics.py`, `run-benchmark.sh`, and Annex 3 declaration files |
| **Pre-submission editorial, structural, and visual polish (current revision)** | Archived Table A.2 to [`docs/evidence-freeze/annotated-literature-inventory.md`](docs/evidence-freeze/annotated-literature-inventory.md) after integrating all 12 stranded references into Chapters 2–3; condensed Abstracts, §3.1, §8.5, and Appendix C (1 page); relocated Symptom Matrix to Table 7.2; built TikZ scheduling diagram (Figure 3.1) and reproducible PGFPlots generator [`scripts/generate_thesis_figure_data.py`](scripts/generate_thesis_figure_data.py) (Figure 6.1) with unit tests; calibrated rhetoric and synchronized Annex 3/audit ledgers (88-page compiled PDF). | Google Gemini (Antigravity) | Abstract, Kivonat, Chapters 1–8, Appendices A–D, `overleaf/figures/`, `scripts/generate_thesis_figure_data.py`, `tests/test_figure_data_generation.py`, unsigned Annex 3 declaration files, and audit ledgers |

---

### Strict Exclusions and Independent Authorship Guarantees

1. **Zero AI Generation of Empirical Data:** No benchmark results, throughput metrics, latency distributions, JFR pinning events, or host CPU telemetry were generated or simulated by AI. All empirical data originates from physical executions on bare-metal hardware.
2. **Independent Theoretical Attribution:** All theoretical conclusions, research question closures (RQ1, RQ2), and architectural taxonomies reflect the author's independent intellectual analysis.
3. **Primary Source Audits:** All cited literature and HotSpot C++ runtime mechanisms (`continuationFreeze.cpp`, `VirtualThread.java`) were verified against primary sources.

---

### Student Declaration

I hereby declare and confirm with my signature that:
* I take full responsibility for the content of the thesis.
* I have reviewed and understood the concept of plagiarism, and the provisions set out in Sections 74/A–E of the Academic Regulations for Students (Eötvös Loránd University Organisational and Operational Regulations – Volume 2) concerning the legal integrity of student work, and Dean’s Instruction No. I/2026 (III. 26.) on the use of artificial intelligence in education, research, and administration.
* I have used only the AI tools listed in the table above in the preparation of the student work.
* I have not incorporated AI-generated text or code without verification and proper citation.

I acknowledge that:
* The direct use of AI-generated content presented as my own work, failure to comply with documentation requirements regarding its use, and making false declarations are considered equivalent to plagiarism.
* The text of my submitted work may be examined using plagiarism detection software after submission.
* In case of suspected plagiarism, the supervisor may verify, orally or in writing, whether the results reflect my own knowledge.
* In the event of plagiarism, my thesis/dissertation cannot be evaluated.
* In case of plagiarism, disciplinary proceedings may be initiated against me.

Budapest, 2026.11.25  
Student Signature: `[Pending physical/electronic signature after author review — Hamed Mohamed (DG1EWF)]`
