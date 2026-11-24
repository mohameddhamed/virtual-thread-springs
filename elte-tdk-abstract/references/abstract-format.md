# Abstract text, metadata and layout

Use for final submission copies and checking. The actual event/form instructions govern; separate scientific content, display design and registration metadata.

## Body

For the current 38th OTDK, write four natural paragraphs corresponding to motivation, methods, own achieved results and conclusions. Each must contribute substantive content and meet its 200-character minimum, while the entire body is 800-2,500 characters. Do not pad with boilerplate to satisfy a counter. Keep a margin below the maximum when form counting is unverified.

For an ELTE faculty abstract whose current form/call gives no length rule, a compatible four-paragraph body is a sensible editorial default. Label it a default in abstract-checks.md. Do not refuse a different valid local length, force an OTDK language rule onto an unspecified faculty form, or mistake an absent web-page specification for a confirmed absence of form validation.

The body should read as a polished standalone scientific abstract without numbered section labels. Cite sparingly only if the specific form allows it and a reference is essential; no orphan citation keys. Expand uncommon acronyms. Prefer concrete methods and findings over broad claims about future potential.

## Display metadata

Use only verified fields, normally:

- Exact title.
- Student authors in agreed order, with affiliation markers only if needed.
- Institution/faculty/department and programme/year where relevant and supplied.
- Supervisor(s), with verified names/affiliations where appropriate.
- Event/section and language if useful for the display copy or required by a template.

Do not automatically expose email, Neptun code, education ID, reviewer names/scores or administrative status. Missing mandatory form metadata belongs in the short checks note; never insert fabricated names, inferred credentials or placeholder values into a supposedly finished document.

The current national system generates names/institution/supervisor separately from the body. Its five keywords should not occur in the title and belong in their own field/checklist. Do not import the archived 37th call's ACM category/XML requirement.

## Canonical copies and early submission

Keep abstract.txt as the canonical body: UTF-8, normalized Unicode NFC and LF line endings, no leading/trailing whitespace other than an optional final file newline. Preserve exactly the same words and punctuation in abstract.md/docx/pdf; display wrapping and styling may differ. For the national paper appendix, use this same canonical body after verifying applicable version/cutoff requirements.

A faculty registration abstract can precede the final paper by weeks. Use only current evidence; retain a dated submitted snapshot once supplied or submitted by the user. Later research may warrant a revised abstract, but an update is not an invisible replacement of an earlier submission. When a word-for-word reuse requirement is uncertain, identify the destinations and evidence rather than assuming it.

## Character checking

Examples from the skill root:

~~~text
python scripts/check_abstract.py abstract.txt --profile count-only
python scripts/check_abstract.py abstract.txt --profile otdk38 --title-file title.txt --keywords-file keywords.txt
~~~

The national profile checks the 800-2,500 total, four paragraphs, and 200 characters per paragraph. Keywords.txt has one keyword/phrase per line. It checks five distinct entries and literal, case-insensitive whole-token phrase overlap with the title; a human should also inspect near-duplicates, inflections and relevance.

The counter normalizes line endings and excludes outer whitespace, then reports Unicode code points including internal whitespace, non-whitespace characters and UTF-16 units. It does not silently normalize wording or Unicode. Canonicalize NFC before finalizing the copies if the script flags non-NFC input. The portal's own confirmed counter takes priority if its convention differs; do not claim to have tested the live form from a local count.

If translating, check each language version independently. Do not label the translation as the canonical submitted body unless that is the user's selected/required language. Do not overwrite a Hungarian-required version with English merely because the paper is in English.

## Professional copy

Honor a supplied template. Otherwise use a restrained academic A4 design: a clear title, compact authors/affiliations/supervisor block, a modest gap, and readable body typography with consistent paragraph spacing. Normally one page suffices, but there is no invented mandatory font, logo or page limit. Avoid decorative stock imagery, excessive headers and oversized branding.

Create the editable document, export PDF and visually inspect it. Check correct Hungarian/Unicode names, line breaks, widows/orphans, margins and complete final lines. Extracting text can help check parity but is not a visual inspection. If body content changes after formatting, rerun counts and refresh every copy.
