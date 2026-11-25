# ELTE TDK / 38th OTDK Abstract Verification Report

**Document:** Formal Quality & Compliance Audit for Conference Submission  
**Author / Candidate:** Hamed Mohamed (Neptun: `DG1EWF`)  
**Programme:** Computer Science MSc (Software Architecture Specialisation)  
**Institution:** Faculty of Informatics, Eötvös Loránd University (ELTE), Budapest, Hungary  
**Department:** Department of Programming Languages and Compilers  
**Supervisory Team:**  
- Internal Faculty Supervisor: Dr. habil. Tamás Kozsik (Associate Professor, Head of Department)  
- External Thesis Advisor / Research Supervisor: Gregory Reynolds Morse (`morse@inf.elte.hu`, Lecturer, ELTE)  
**Approved Topic Request ID:** `IK-ZVMSC_EN2_155` (Approved: 2026.10.27)  
**Target Conferences:**  
1. **ELTE Faculty of Informatics Autumn TDK Conference 2026** (Registration Deadline: 16 November 2026; Paper: 3 December 2026; Conference: 17 December 2026)  
2. **38th National Scientific Students' Associations Conference (OTDK)** Information and Communication Technology Section (Spring 2027)  
**Evaluation Date:** 16 November 2026  

---

## 1. Character Count and Structural Verification

The canonical text in [`abstract.txt`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/abstract.txt) was verified using the official automated checking tool [`elte-tdk-abstract/scripts/check_abstract.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/elte-tdk-abstract/scripts/check_abstract.py) against both the `count-only` profile and the dated `otdk38` national qualification profile.

### 1.1 Canonical English Abstract (`abstract.txt`)

* **Counting Convention:** Unicode code points; internal whitespace included; LF newlines; outer whitespace excluded.
* **Total Characters:** **2,201** (Compliant: satisfies national 38th OTDK 800–2,500 limit with a safe 300-character safety margin below the ceiling).
* **Characters (without whitespace):** 1,921
* **UTF-16 Code Units:** 2,201
* **Unicode Normalization:** NFC valid (`unicode_nfc: true`)
* **Logical Paragraphs:** **4** (Four mandatory scientific components)
* **Per-Component Paragraph Lengths:**
  1. *Research Justification (Motivation):* **566 characters** (Required: $\ge 200$) — Pass
  2. *Methods:* **569 characters** (Required: $\ge 200$) — Pass
  3. *Student's Own Results:* **563 characters** (Required: $\ge 200$) — Pass
  4. *Main Conclusions:* **497 characters** (Required: $\ge 200$) — Pass
* **Validation Outcome:** **Passed (`passed: true`, 0 errors, 0 warnings)**

```json
{
  "profile": "otdk38",
  "convention": "Unicode code points; internal whitespace included; LF newlines; outer whitespace excluded",
  "characters": 2201,
  "characters_without_whitespace": 1921,
  "utf16_units": 2201,
  "paragraphs": 4,
  "paragraph_characters": [566, 569, 563, 497],
  "unicode_nfc": true,
  "errors": [],
  "passed": true
}
```

---

### 1.2 Companion Hungarian Abstract (`kivonat.txt`)

* **Total Characters:** **2,296** (Compliant: satisfies 800–2,500 range)
* **Characters (without whitespace):** 2,020
* **UTF-16 Code Units:** 2,296
* **Unicode Normalization:** NFC valid (`unicode_nfc: true`)
* **Logical Paragraphs:** **4**
* **Per-Component Paragraph Lengths:**
  1. *Kutatási indoklás:* **577 characters** ($\ge 200$) — Pass
  2. *Módszertan:* **572 characters** ($\ge 200$) — Pass
  3. *A hallgató saját eredményei:* **609 characters** ($\ge 200$) — Pass
  4. *Főbb következtetések:* **532 characters** ($\ge 200$) — Pass
* **Validation Outcome:** **Passed (`passed: true`, 0 errors)**

---

## 2. Title and Keywords Audit

The five keywords were audited for non-overlap with the title to comply with national submission regulations:

### 2.1 English Check
* **Title:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*
* **Keywords File:** [`keywords.txt`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/keywords.txt)
  1. `Project Loom`
  2. `Thread Pinning`
  3. `Carrier Starvation`
  4. `Java Flight Recorder`
  5. `Connection Pooling`
* **Audit Result:** Exactly 5 distinct, highly relevant keywords. Zero token/phrase collisions with the paper title (`title_overlap_entry_numbers: []`).

### 2.2 Hungarian Check
* **Cím:** *Spring Boot MVC Rendszerek Migrációja Java 21 Virtuális Szálakra: Architektúra, Kockázatok és Mérnöki Irányelvek*
* **Kulcsszavak:** [`kulcsszavak.txt`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/kulcsszavak.txt)
  1. `Project Loom`
  2. `Szálrögzítés`
  3. `Hordozó-kiéheztetés`
  4. `Java Flight Recorder`
  5. `Kapcsolatkészlet-méretezés`
* **Audit Result:** 5 distinct keywords, zero collisions with the Hungarian title.

---

## 3. Empirical Grounding & Ownership Verification

All claims in Paragraph 3 (*Student's Own Results*) are grounded in cryptographically verified physical benchmark executions (`docs/evidence-freeze/`):
- **Carrier Unpinning vs. Amdahl's Law:** Replacing `synchronized` with `ReentrantLock` eliminated all qualifying JFR pinning events (108 to 0) while maintaining identical throughput ($1.956$ vs. $1.967\text{ req/s}$), demonstrating that unpinning does not bypass the single-server critical section serialization ceiling ($\mu \approx 2.0\text{ req/s}$).
- **POSIX JNI Silent Starvation:** Blocking `nanosleep()` captured the carrier thread in a Darwin/Mach wait state with low process CPU (approximately $1\%$, measured $1.06\%$) and exactly zero `jdk.VirtualThreadPinned` events.
- **Factorial Persistence Ablation:** Virtual threads unmount cleanly across database operations, but throughput is strictly governed by HikariCP pool size ($X = K / T_{\text{hold}}$), shifting queues downstream.

---

## 4. Governance, Standards & Editorial Defaults

1. **Faculty vs. National Rules:** The current ELTE Autumn Faculty Call establishes a submission date of 16 November 2026, paper deadline of 3 December 2026, and presentation on 17 December 2026. Because the faculty call does not publish rigid font or character-counter constraints, the 38th OTDK ICT Section four-paragraph structure (800–2,500 characters, $\ge 200$ characters per section) is used as an editorial compatibility target.
2. **Language Policy:** The author is enrolled in the English-language Computer Science MSc programme (`IK-ZVMSC_EN2_155`). English is the official language of instruction, thesis authoring, and presentation eligibility under OTDK ICT Section rules. Both English and Hungarian submission packages are provided.
3. **AI Assistance Disclosure:** In compliance with Dean's Directive No. 1/2026 (Annex 3), AI tools were used exclusively for syntactic scaffolding and linguistic drafting. Zero empirical data, benchmark measurements, or theoretical deductions were generated by AI.

---

## 5. Artifact Ledger

| Deliverable | Purpose | Path |
| :--- | :--- | :--- |
| **Submission Text** | Clean plain-text body for portal pasting | [`abstract.txt`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/abstract.txt) |
| **Display Markdown** | Full public record with author/supervisor block | [`abstract.md`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/abstract.md) |
| **Editable Document** | Word DOCX for form upload / archiving | [`abstract.docx`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/abstract.docx) |
| **Printable PDF** | 1-page publication-quality A4 document | [`abstract.pdf`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/abstract.pdf) |
| **Keywords List** | 5 distinct keywords absent from title | [`keywords.txt`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/keywords.txt) |
| **Title Record** | Canonical paper title | [`title.txt`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/title.txt) |
| **Hungarian Submission**| Clean Hungarian plain-text body | [`kivonat.txt`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/kivonat.txt) |
| **Hungarian Display** | Full Hungarian public markdown | [`kivonat.md`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/kivonat.md) |
| **Hungarian DOCX** | Word DOCX Hungarian kivonat | [`kivonat.docx`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/kivonat.docx) |
| **Hungarian PDF** | 1-page publication-quality Hungarian PDF | [`kivonat.pdf`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/kivonat.pdf) |
| **Compliance Audit** | Verification report & script metrics | [`abstract-checks.md`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/abstract-checks.md) |
