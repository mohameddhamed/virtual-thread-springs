# ELTE IK TDK 50-Point Audit

Universal OpenAI/Anthropic distribution

## What is included

- `elte-ik-tdk-50-point-audit.zip` — the installable skill archive.

The installable archive contains one top-level directory named
`elte-ik-tdk-50-point-audit`, with `SKILL.md`, interface metadata, the fixed
50-item rubric, research-mode and evidence protocols, a report contract, and a
deterministic standard-library Python scorer.

## What the skill does

The skill audits the written ELTE Faculty of Informatics TDK paper against the
current seven official criteria:

- novelty and quality of development: 8 one-point checks;
- topic and content: 8;
- verification of results: 8;
- literature review: 6;
- formal presentation and style: 6;
- scientific value: 6;
- summary opinion and overall quality: 8.

Every check is Boolean. A supplied and sufficient item earns one point; a
demonstrated failure earns zero. Missing or pending evidence remains unresolved,
so an incomplete audit reports a defensible score range instead of inventing a
final total. There are no automatic grade bands or award thresholds.

The skill can also compare two complete written reviews, compute their mean, and
flag the current OTDK reconciliation/third-review rule when their totals differ
by strictly more than 15 points. The separate oral-presentation 50 points are
outside the skill.

## Install on OpenAI products

### ChatGPT with personal skills

Enable code execution in **Settings → Capabilities** if your workspace requires
it. Open **Customize → Skills** and upload `elte-ik-tdk-50-point-audit.zip`. Use
the inner installable ZIP, not this outer distribution ZIP.

### Codex

Extract the inner ZIP so the final path is:

```text
${CODEX_HOME:-$HOME/.codex}/skills/elte-ik-tdk-50-point-audit/SKILL.md
```

Restart or begin a new session after installation.

## Install on Anthropic products

### Claude with Skills

Enable code execution if required, then upload
`elte-ik-tdk-50-point-audit.zip` in **Customize → Skills**. Use the inner
installable ZIP.

### Claude Code

Extract the inner ZIP so the final path is:

```text
~/.claude/skills/elte-ik-tdk-50-point-audit/SKILL.md
```

Start a new session after installation.

`agents/openai.yaml` is optional OpenAI interface metadata. Anthropic runtimes
can ignore it; all required cross-platform instructions are in `SKILL.md` and
the bundled references.

## Suggested invocation

```text
Use the ELTE IK TDK 50-Point Audit on the attached final paper, editable source,
abstract, student-result statement, AI declaration, code, data, and result
evidence. Audit all 50 Boolean items, identify blockers, and give me an
evidence-linked correction plan ordered by recoverable points.
```

For a two-reviewer comparison, attach both completed item ledgers or written
reviews and ask the skill to reconcile them. Provide exact versions, hashes, or
dates whenever possible.

## Sources frozen for this release

- ELTE IK TDK Conference, IT Science Section, Spring 2026 (Hungarian):
  <https://www.inf.elte.hu/tdk-konferencia-informatikatudomanyi-szekcio-2026-tavasz>
- ELTE IK TDK Conference, IT Science Section, Spring 2026 (English):
  <https://www.inf.elte.hu/en/tdk-conference-it-science-section-2026-spring>
- 38th OTDK Information and Communication Technology Section call:
  <https://otdk.hu/en/kezdolap/otdk-2027/section-calls/information-and-communication-technology-section/>
- Current Hungarian section supplement:
  <https://otdk.hu/wp-content/uploads/2026/05/38OTDK_Informatikatudomanyi_Szekcio_felhivas_1_sz_melleklet.pdf>

Source retrieval date: 2026-10-05. A newer applicable official rule overrides
this bundle and the conflict must be disclosed.
