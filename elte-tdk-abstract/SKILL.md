---
name: elte-tdk-abstract
description: Create an ELTE Informatics TDK or ICT OTDK abstract with submission-ready text, professional layout and checked length/metadata. Use before the paper deadline or to revise an existing abstract.
---

# ELTE TDK abstract

Produce the abstract itself and its clean submission text, independently of the later paper review or presentation. Work for BSc/MSc students and collaborative, theoretical, empirical or software research; do not impose degree-specific feature quotas.

## Read context and ask once

Extract the target event/year, title, author order, affiliations, supervisors, language, research question, methods, own contributions and achieved evidence from the conversation, draft/source files, code/results or prior abstract. A completed paper, code repository, reviewer reports and committee are not prerequisites for this early deliverable.

If essential information is absent, request all consequential gaps together, omitting known items:

> Please send your current draft/notes or a concise description of the problem, method, your own contribution, and results actually obtained so far, including any measured values and their limits. Include the target TDK/OTDK event or form instructions, author order/affiliations/supervisors if not already in the files, and the required language. Identify planned work separately. An unfinished paper is fine.

Ask a later targeted question only if a newly discovered ambiguity changes authorship, claims, language eligibility or compliance. Do not ask for Neptun code, personal emails, a defense panel or both source and PDF merely to draft the abstract. If only optional display metadata is absent, finish the body and list missing submission fields separately.

Read [references/tdk-authorities.md](references/tdk-authorities.md) to identify applicable current requirements. The supplied ELTE autumn call establishes a faculty event; an archived OTDK link does not make the old national rules current. Check the actual abstract/form requirements and language, not an assumed universal template.

## Draft from supported research

Tell a compact scientific story: why the question matters -> how it was addressed -> the student's own achieved result -> what the evidence means and where it stops. State the contribution relative to existing work only as strongly as the supplied/verified literature supports.

Keep authorship boundaries explicit in group work: distinguish student-developed methods, implementation, study/proof and analysis from advisor ideas, shared infrastructure, reused models and collaborators' findings. For joint authors, preserve agreed order and do not invent who performed which work.

Include quantitative results with comparator, metric, units and experimental scope when available; use an equally precise theorem, counterexample, validated design or qualitative result for other research modes. Preserve negative/mixed outcomes. Do not turn a plan, intended experiment, unrun code or preliminary observation into a completed study or claim universal novelty.

When achieved results are insufficient, produce an honest provisional draft and one concise evidence gap note, not a fabricated submission-ready success story. A future-work sentence may be useful, but does not satisfy an applicable requirement for achieved results. For national OTDK, apply the qualifying-conference cutoff from the current call.

An editable source ZIP can be newer than its bundled PDF. Use the current editable source for a revision draft, building/rendering it if needed; an old PDF alone is not evidence the source remains unfixed. Keep the registered/submitted abstract snapshot and any frozen paper distinct from a later draft. Do not imply changed prose verifies changed application behavior.

## Submission text and professional layout

Read [references/abstract-format.md](references/abstract-format.md) before finalizing. Follow an actual official template when supplied. Without a local specification, use the current national abstract structure/length as a labelled compatibility-oriented editorial target, not a claimed ELTE faculty rule.

Maintain one canonical body. Provide abstract.txt containing only the exact text to paste, without title, author block, Markdown labels, commentary or counts. Use four logical paragraphs when applying the current national format. Reuse the same wording in the editable/print copy and, when applicable, the paper appendix; do not silently generate a different polished version for each destination.

Create abstract.md, a professional editable abstract.docx and a clean abstract.pdf when file tools are available. The display copy places the verified title, authors in order, affiliation(s), supervisor(s) and event/language metadata as appropriate above the body. Default to a restrained readable A4 layout, normally one page. These design defaults are not official format rules. Keep private registration identifiers out of the public abstract unless explicitly required.

Also provide abstract-checks.md with exact character counts, counting convention and per-component counts where applicable; keyword/title checks; verified rules versus defaults; source dates; material missing metadata/evidence; and the factual AI-assistance description if required. Keep this note outside the paste-ready body.

Run [scripts/check_abstract.py](scripts/check_abstract.py) on the actual final text when Python is available: count-only for unspecified local rules; the otdk38 profile when those requirements apply or when explicitly checking that editorial compatibility target. The script also accepts a title and keyword file for the five-keyword check. Report the profile's applicability, not just "passed". If Python is unavailable, perform equivalent exact counts with available tools; do not estimate a character-limit pass.

## Validate and hand over

Check that every result and ownership claim is grounded, all four scientific components are present, and metadata are accurate. At national submission include five distinct keywords absent from the title as a separate metadata list, not hidden inside the character-limited body. Avoid unsupported citations, undefined acronyms, dense equations or a miniature literature review.

Render and inspect the professional copy, checking accents, hierarchy, whitespace, page count, clipping and body parity. Preserve readable type rather than squeezing to an invented one-page requirement. If document/PDF tooling is unavailable, deliver the complete text and layout specification and state which files could not be produced.

If revising a previously submitted abstract, preserve its snapshot and identify material changes; do not claim the local and later national abstracts must always be verbatim identical unless the applicable rules establish that. Identify readiness and unresolved items briefly. Do not register, upload, email or submit anything without the user's instruction to do so.
