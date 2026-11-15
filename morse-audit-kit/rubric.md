# Fixed 50-item written-paper rubric

Each item is worth exactly one point when `awarded`. The IDs and seven
subtotals are immutable.

## N — Novelty and quality of development (8)

| ID | Boolean item |
|---|---|
| N01 | The paper grounds a concrete research or technical problem and an evidence-based gap. |
| N02 | It states the exact delta from the closest prior work rather than asserting novelty by omission. |
| N03 | The contribution contains a new informatics result or insight, not merely the use of information technology as a tool. |
| N04 | The student's own contribution is explicit and separable from prior, supervisor, collaborator, research-group, reused, and AI-assisted work. |
| N05 | The development or derivation includes non-trivial choices justified against credible alternatives. |
| N06 | The claimed contribution type—new result, method, system, application, study, dataset, formalization, replication, or negative result—is credible and supported. |
| N07 | Boundaries, assumptions, failure cases, and limits of the novelty claim are explicit. |
| N08 | Originality claims are calibrated to verified literature and artifact evidence without overclaiming. |

## T — Topic and content (8)

| ID | Boolean item |
|---|---|
| T01 | Title, abstract, registered topic, paper body, and claimed contribution are materially aligned. |
| T02 | Objectives and research questions or formal goals are precise, answerable, and technically meaningful. |
| T03 | Scope, assumptions, dependencies, constraints, and exclusions are defined. |
| T04 | The work has appropriate informatics depth for the stated topic and intended expert audience. |
| T05 | The structure preserves a coherent problem → gap → question → method → evidence → result → answer → contribution chain. |
| T06 | Methods and results cover every research question or formal goal, including partial or negative outcomes. |
| T07 | Concepts, terminology, notation, models, and units are correct and consistent. |
| T08 | Conclusions directly answer the research questions and introduce no unsupported new claims. |

## V — Verification of results (8)

| ID | Boolean item |
|---|---|
| V01 | The method is described sufficiently for an expert to reproduce, recompute, or independently check the central work. |
| V02 | Inputs, data, cases, instruments, proof sources, software, models, and artifact versions have adequate provenance. |
| V03 | Baselines, controls, comparison conditions, counterfactuals, or proof obligations are appropriate and fair for the research mode. |
| V04 | Metrics, statistical procedures, analyses, coding procedures, derivations, or proof steps are appropriate and correctly applied. |
| V05 | Every central result traces to fixed inputs, a named method, raw evidence, and an analysis or proof path. |
| V06 | Uncertainty, robustness, sensitivity, failure behavior, negative results, and boundary cases receive mode-appropriate treatment. |
| V07 | Code, data, proofs, models, logs, notebooks, certificates, or equivalent retained evidence support representative independent checks. |
| V08 | The validation design supports each central claim without material leakage, cherry-picking, confounding, circularity, or unsupported generalization. |

## L — Literature review (6)

| ID | Boolean item |
|---|---|
| L01 | Foundational claims rely on authentic, relevant, preferably primary scholarly or authoritative sources. |
| L02 | The review covers current closest work that materially defines the frontier. |
| L03 | Competing approaches, standard baselines, and relevant contrary or limiting evidence are covered. |
| L04 | Sources are critically synthesized and compared rather than listed as isolated summaries. |
| L05 | Borrowed claims, data, methods, figures, definitions, and reused material are cited accurately at the point of use. |
| L06 | The bibliography is authentic, complete for cited work, internally consistent, and includes relevant prior work by the student when reused. |

## F — Formal presentation and style (6)

| ID | Boolean item |
|---|---|
| F01 | The submission includes the cover, title-page metadata, abstract, result statement, AI declaration, and other components required by the governing call. |
| F02 | Hierarchy, navigation, cross-references, numbering, and chapter or section flow are coherent. |
| F03 | Figures, tables, equations, algorithms, and code excerpts are legible, captioned, cited, and interpretable without guesswork. |
| F04 | Language is precise, professional, grammatically controlled, and consistent with scientific writing. |
| F05 | Citation and reference style, links, symbols, terminology, abbreviations, and formatting are consistent. |
| F06 | The final PDF and editable source are polished, version-consistent, free of placeholders and layout defects, and appropriately anonymized for the requested workflow. |

## S — Scientific value (6)

| ID | Boolean item |
|---|---|
| S01 | The work addresses a relevant problem whose importance is supported rather than merely asserted. |
| S02 | The results are substantive relative to the field, closest work, or a defensible research need. |
| S03 | Generality, transfer, reuse, explanatory power, or bounded utility is demonstrated or carefully delimited. |
| S04 | The contribution can support further research, verification, adoption, or cumulative knowledge beyond the submitted narrative. |
| S05 | Publication status or publication potential is described realistically and supported by evidence where claimed. |
| S06 | The scientific value claim is calibrated to uncertainty, limitations, negative results, and authorship boundaries. |

## Q — Summary opinion and overall quality (8)

| ID | Boolean item |
|---|---|
| Q01 | The end-to-end research argument is coherent and mutually consistent across abstract, body, conclusions, and appendices. |
| Q02 | The paper's strongest claim is independently supportable from the supplied method and evidence. |
| Q03 | Student ownership of the central intellectual and technical contribution is credible and consistently documented. |
| Q04 | Ethical, legal, privacy, licensing, data-access, safety, and AI-use responsibilities are handled where applicable. |
| Q05 | The paper has identifiable, evidence-backed strengths that are material to the contribution. |
| Q06 | Material weaknesses and limitations are disclosed, analyzed, and reflected in the conclusions. |
| Q07 | The paper stands alone for expert written review, with essential evidence available or transparently bounded. |
| Q08 | Taken as a whole, the written work demonstrates competitive TDK-level research quality without relying on the oral presentation to repair central gaps. |

## Invariants

- N = 8, T = 8, V = 8, L = 6, F = 6, S = 6, Q = 8.
- Total = 50.
- No partial points and no N/A.
- The oral-presentation score is excluded.
