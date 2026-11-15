# ELTE IK MSc thesis template

This is a research-first MSc variant of the ELTE IK thesis project. It retains
the MIT-licensed `elteikthesis` class by Máté Cserép and Bálint Bognár, while the
chapter skeleton and evidence guidance are rewritten for MSc research. Current
faculty rules and the approved topic form always take precedence.

## Overleaf quick start

1. In Overleaf choose **New Project > Upload Project**, then select this ZIP.
2. Keep `main.tex` as the main document and use pdfLaTeX.
3. Replace every angle-bracket placeholder in `config.tex` and `chapters/`.
4. Export the approved MSc topic form as `approved-topic-registration.pdf` and
   upload it beside `main.tex`.
5. Select the research-mode evidence that actually applies. Rename or remove the
   optional Background and Research Artifact chapters when they do not apply.
6. Add verified sources actually used to `references.bib`; cite them near the
   claims they support.
7. Before submission, set `\showtemplateguidancefalse`, rebuild, search for `<`,
   inspect every PDF page, and complete Appendix C.

## Research-first structure

- Introduction: programme/specialisation fit, problem and literature gap, exact
  research questions, scope, contributions, responsibility boundaries, roadmap.
- Related Work: verified foundations, closest work, competing approaches,
  baselines, synthesis, and the gap from which each research question follows.
- Background and Preliminaries: optional; keep only material required to inspect
  the method and results.
- Methodology and Research Design: question-to-method traceability, materials and
  provenance, procedure, baselines or proof obligations, validity, ethics, and
  reproducibility.
- Research Artifact or Implementation: optional and research-mode dependent;
  software is not forced into a theoretical or non-software thesis.
- Results: observations and retained evidence before broad interpretation.
- Discussion: explicit research-question answers, comparison with closest work,
  contribution, uncertainty, validity limits, and relevance.
- Conclusion: concise closure of every approved goal and research question.

The supported research modes are theoretical/formal, empirical ML or data,
engineering/system study, human-subject/user study, simulation/numerical, and
qualitative/design. Mixed theses must satisfy every materially relevant branch.

## Official review alignment

The supplied point-by-point review form allocates planning weights of 4/5/9/9/2/1
across six official review areas: research scope and goals; development of the
topic; methods; results and contribution; presentation/language/structure; and
preparation process. These weights are a self-audit aid, not an invented automatic
grade conversion.

## Local build

Run `make`. The Makefile uses `latexmk`, BibTeX, and no shell escape. Use
`make clean` to remove generated files.

## Source and policy references

- Current ELTE IK MSc rules:
  <https://www.inf.elte.hu/en/guidelines-thesis-final-examination-msc>
- Current ELTE IK AI policy:
  <https://www.inf.elte.hu/en/ai-usage-policy>
- Gregory Morse's MSc supervision guidance:
  <https://grm.web.elte.hu/>
- Upstream LaTeX template:
  <https://github.com/mcserep/elteikthesis>

For Gregory Morse's supervisees, the bibliography guidance is at least 30
relevant items and around 50 strongly recommended, predominantly peer reviewed
where appropriate. Quality, authenticity, relevance, and synthesis matter more
than padding.

## License

The LaTeX class remains under its upstream MIT license. See `LICENSE`.
