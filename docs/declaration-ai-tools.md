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
| **Structural Drafting, Chapter Outlining, and Prose Polish** | Generated initial structural outlines and syntactic drafts for standard framework descriptions; critically rewritten and adapted to align with ELTE academic thesis standards, empirical systems methodology, and queueing models. | Anthropic Claude (Claude 3.5 Sonnet) | Chapters 1 (§1.1), 2 (§2.1), 3 (§3.1, §3.15), 4 (§4.1), 7 (§7.1), and 9 (§9.5) |
| **Scaffolding Empirical Recalculation & Verification Scripts** | Generated preliminary Python templates for parsing raw k6 JSON lines streams and JFR binary events; manually audited, refined, and validated against physical data using cryptographic SHA-256 checksums. | Anthropic Claude (Claude 3.5 Sonnet) & GitHub Copilot | [`scripts/normalize_evidence.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/normalize_evidence.py), [`scripts/recalculate_metrics.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/recalculate_metrics.py), [`scripts/validate_normalized_evidence.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/validate_normalized_evidence.py) |
| **Integration Test Template Scaffolding** | Autocompleted boilerplate JUnit 5 integration test fixtures; manually verified and adapted with strict assertions for mutual exclusion, transactional semantics, ThreadLocal cleanup, and native JNI bindings (`mvn test` 8/8 pass). | GitHub Copilot | Chapter 4 (Implementation) and [`src/test/java/com/thesis/virtualthreadsdemo/`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/test/java/com/thesis/virtualthreadsdemo/) |

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

Budapest, 2026.11.14  
Student Signature: **Hamed Mohamed** (`DG1EWF`)
