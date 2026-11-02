# MSc Computer Science Final Exam — Study Guide (Software Architecture)

**ELTE Faculty of Informatics · Computer Science / Programtervező Informatikus MSc (2022–, English)**  
**Specialization:** Software Architecture (Szoftvertechnológia)  
**Last updated and sources checked:** 2026-10-08

**Official course index:** [ELTE — Software Architecture specialization syllabi, MSc 2022](https://www.inf.elte.hu/th-tematikak-programtervezo-informatikus-msc-2022-szoftvertechnologia-softvare-architecture-specializacio)  
**Programme index:** [ELTE — English Computer Science MSc 2022+ specializations](https://www.inf.elte.hu/th-tematikak-ptimsc-2024)

## Scope and Source Evidence

This guide covers the **19 selectable subjects** in the student-supplied Software Architecture Neptun dropdown, in its original order. The raw HTML supplied on 2026-10-08 contains 21 entries: two placeholders (“Válasszon a listából!” and “Please select”) and 19 distinct subject names. The placeholders are excluded. Dropdown labels are retained exactly in the contents and main chapter headings, including their capitalization and the singular “Design of Distributed System”.

The dropdown is evidence of the selectable subjects in that student's form, not a complete curriculum or proof of how many subjects every student must select. Verify applicability to your curriculum, completed courses, and current examination period. Other MSc specializations have their own course sets; this file is specifically the Software Architecture guide.

Every subject has a direct public ELTE syllabus or course-description link. Where ELTE publishes lecture and practical descriptions separately, both are linked. The **Verified syllabus scope** paragraphs summarize the checked descriptions; the expanded explanations, examples, and oral-practice questions are study aids, not an official question bank or a replacement for lecture materials. Course-responsible names refer to the linked syllabi, not necessarily to the lecturer or examiner in the current semester.

**Two source/version points require attention:**

- **Advanced Java programming:** present in Neptun and the 2022 curriculum, but missing from the public specialization syllabus index. Topic 7 links the available older ELTE description and a curriculum cross-check, and identifies that limitation explicitly.
- **Scalable enterprise applications:** the listed ELTE description contains historical Java EE, applet, and related examples. Topic 19 preserves that scope and distinguishes it from current technology documentation.

The four original chapters are retained: Software quality and testing is now Topic 5, Introduction to Data Science is Topic 8, and Methods and tools for AI applications is Topic 18. **Advanced Software Technology is preserved as Appendix A** because it is an official specialization course but is absent from this 19-subject dropdown. It must not be treated as an additional selectable entry without confirmation from the applicable Neptun form or faculty.

## How to Use the Guide for the MSc Final Exam

The [current public ELTE MSc thesis and final-examination guidance](https://www.inf.elte.hu/en/guidelines-thesis-final-examination-msc) describes registration of **three thesis-related subjects** and an oral examination on those subjects' material and connections, alongside the thesis defense. It does not establish a universal rule that the committee asks only one subject or that the examination lasts exactly 10–20 minutes.

The earlier four-chapter guide stated “register four topics” without a supporting rule. Its four chosen study chapters do not establish the required registration count. Use the applicable current faculty instructions and Neptun form; obtain faculty clarification if they conflict. The dropdown supplied here establishes the available names, not the number of selection fields or the examination procedure.

**Preparation strategy:**

1. Select eligible subjects with a substantive connection to your thesis under the applicable registration instructions.
2. Read each selected subject's official description and current lecture materials. Map every relevant syllabus area to an explanation, example, derivation, or exercise you can perform.
3. For an algorithm or model, state its assumptions, define its terms, explain the mechanism, and justify correctness and limitations.
4. Practice discussing the complete scope of your registered subjects and their connections. Do not prepare only one hoped-for question.
5. Use thesis artifacts as concrete examples where they genuinely fit; they supplement knowledge of the course, rather than substituting for it.

---

## Subjects — Neptun Dropdown Order

1. [Design and analysis of algorithms](#topic-1-design-and-analysis-of-algorithms)
2. [Theory of programming](#topic-2-theory-of-programming)
3. [Project Management](#topic-3-project-management)
4. [Formal semantics](#topic-4-formal-semantics)
5. [Software quality and testing](#topic-5-software-quality-and-testing)
6. [Design of Distributed System](#topic-6-design-of-distributed-system)
7. [Advanced Java programming](#topic-7-advanced-java-programming)
8. [Introduction to Data Science](#topic-8-introduction-to-data-science)
9. [Models of Computation](#topic-9-models-of-computation)
10. [Principles of artificial intelligence](#topic-10-principles-of-artificial-intelligence)
11. [Advanced Algorithms](#topic-11-advanced-algorithms)
12. [Complex information systems](#topic-12-complex-information-systems)
13. [Functional Languages](#topic-13-functional-languages)
14. [Machine Learning](#topic-14-machine-learning)
15. [Service Science](#topic-15-service-science)
16. [Analysis of distributed systems](#topic-16-analysis-of-distributed-systems)
17. [Introduction to Computer Security](#topic-17-introduction-to-computer-security)
18. [Methods and tools for AI applications](#topic-18-methods-and-tools-for-ai-applications)
19. [Scalable enterprise applications](#topic-19-scalable-enterprise-applications)

[Appendix A — Advanced Software Technology (preserved supplementary chapter)](#appendix-a-advanced-software-technology)  
[Exam strategy and cross-subject connections](#exam-strategy-msc-level)  
[Source and maintenance notes](#source-and-maintenance-notes)

---

## Topic 1 — Design and analysis of algorithms

**Course responsible (syllabus):** Dr. Szabó László Ferenc, CSc  
**Official syllabi:** [Lecture](https://www.inf.elte.hu/dstore/document/227897/Design%20and%20Analysis%20of%20Algorithms%20L.pdf) · [Practice](https://www.inf.elte.hu/dstore/document/227898/Design%20and%20Analysis%20of%20Algorithms%20Pr.pdf)

**Verified syllabus scope:** Algorithm-design paradigms, stable matching, recurrence analysis, fast algebraic algorithms, geometric problems, sequence and resource-allocation problems, approximation, and randomized computation. The graph-flow emphasis of Topic 11 is a separate course.

### 1.1 Correctness and Running-Time Arguments

- State the input, required output, and size parameter before presenting an algorithm. A claim of efficiency needs an explicit computation model and cost measure.
- Separate a correctness proof from a complexity proof. An algorithm may be fast and wrong, or correct and impractical.
- Use a loop invariant for iterative algorithms and induction for recursive algorithms. Include initialization, preservation, and the implication of the exit condition.
- Distinguish worst-case, expected, and amortized costs. Expected time needs a probability space; amortized time averages a sequence of operations without assuming random inputs.
- For divide-and-conquer, derive the recurrence from the algorithm. For merge sort, two half-size calls and linear merging give $T(n)=2T(n/2)+\Theta(n)=\Theta(n\log n)$. The Master theorem has hypotheses; it does not apply to every recurrence.

### 1.2 Stable Matching

A matching is stable when no unmatched pair would both prefer each other to their assigned partners. In deferred acceptance, an unassigned proposer approaches the highest-ranked receiver not yet approached; each receiver retains the preferred proposal so far.

- Each proposer–receiver pair is considered at most once, giving $O(n^2)$ proposals for complete lists of equal size.
- To prove stability, consider a supposed blocking pair and the point at which that proposal was rejected. The receiver's retained partner can only improve afterwards.
- Under strict, complete preferences, the result is proposer-optimal among stable matchings. It need not maximize a numerical measure of total happiness, and receiver preferences are not treated symmetrically by the procedure.
- Explain which assumptions change with ties, incomplete preference lists, or unequal population sizes.

### 1.3 Divide-and-Conquer Beyond Sorting

- **Counting inversions:** During a merge, when a right-half element precedes the next left-half element, count all remaining left-half elements. Sorting and counting together avoids enumerating all pairs.
- **Matrix multiplication:** Compare the cubic classical method with Strassen's seven recursive subproducts. Explain asymptotics, constant factors, memory, and numerical considerations separately.
- **Polynomial multiplication:** Coefficient convolution can be computed through evaluation, pointwise multiplication, and interpolation; FFT-based methods exploit roots of unity. Explain why enough evaluation points prevent coefficient aliasing.
- **Closest pair:** Divide sorted points, solve each side, then inspect a narrow strip using geometric packing to bound candidate comparisons. Maintaining the necessary sorted orders is part of the running-time proof.

### 1.4 Dynamic Programming

Specify a state, transition, base cases, evaluation order, and reconstruction procedure. Repeated subproblems alone are not a complete algorithm.

- Matrix-chain optimization chooses parenthesization; it does not reorder matrices. The cost of multiplying an $a\times b$ matrix by a $b\times c$ matrix is proportional to $abc$.
- Sequence alignment defines insertion, deletion, and substitution costs and combines prefix solutions.
- In 0/1 knapsack, a state indexed by item count and integer capacity leads to a pseudo-polynomial algorithm. Polynomial in the numeric capacity is not polynomial in its binary encoding length.
- For subset sum and change-making, distinguish feasibility, counting, and minimization. They have different transitions and sometimes different greedy behavior.

### 1.5 Greedy Choice and Approximation

A greedy rule needs a proof, usually an exchange argument or a stays-ahead argument. Earliest finishing time solves unweighted interval selection; an intuitive scheduling rule need not solve a weighted variant.

For approximation, define the optimization direction and compare the returned objective with the unknown optimum. For makespan scheduling, maximum job size and average load provide lower bounds. For metric center selection, a farthest-first construction gives a useful bound through the triangle inequality; arbitrary distances require separate analysis. A near-optimal result on one dataset is not an approximation guarantee.

### 1.6 Randomized Algorithms

- Random-pivot quicksort has expected $O(n\log n)$ comparisons but quadratic worst-case behavior. Quickselect has expected linear selection time under suitable randomization.
- State the source of randomness and the event being analyzed. A deterministic bad input and a random pivot are different kinds of uncertainty.
- Freivalds' check compares $A(Br)$ and $Cr$ instead of computing the whole matrix product. Over an appropriate field, an incorrect product passes with bounded probability; independent repetition reduces that error. Arithmetic overflow can invalidate a naive implementation.

### 1.7 Oral Practice and Thesis Connections

1. Prove deferred acceptance stable and explain whose preferences it favors.
2. Derive a divide-and-conquer recurrence from pseudocode, including the combine step.
3. Design and reconstruct a dynamic-programming solution; explain why a tempting greedy alternative fails.
4. State a scheduling or clustering approximation guarantee and its assumptions.
5. Distinguish a randomized algorithm's expected running time from its error probability.

In a thesis, identify the actual optimization problem and input scale, then justify the selected algorithm against a baseline and its mathematical assumptions.

### 1.8 Literature

The ELTE syllabi recommend Cormen, Leiserson, Rivest and Stein, *Introduction to Algorithms*, 4th edition, and Kleinberg and Tardos, *Algorithm Design*. Use the relevant proofs and exercises alongside lecture notes.

---

## Topic 2 — Theory of programming

**Course responsible (syllabus):** Dr. Gregorics Tibor, PhD  
**Official syllabi:** [Lecture](https://www.inf.elte.hu/dstore/document/227920/Theory_of_Programming%20L.pdf) · [Practice](https://www.inf.elte.hu/dstore/document/227921/Theory_of_Programming%20Pr.pdf)

**Verified syllabus scope:** Relational descriptions of problems and programs, nondeterministic execution, correctness and preconditions, loop reasoning, sequential program derivation, and Owicki–Gries verification of parallel programs. Topic 4 instead emphasizes defining and comparing language semantics.

### 2.1 States, Relations, and Specifications

A state assigns values to program variables. A problem specification relates permitted initial states to acceptable final states. A deterministic terminating program maps an initial state to one final state; nondeterminism may allow several outcomes.

- A program's input/output relation alone does not tell you whether some execution can diverge. Correctness definitions must account for termination separately.
- Preconditions describe the allowed starting states; postconditions describe the required outcome. Frame conditions state which parts of the state may change.
- For nondeterministic programs, identify whether correctness requires all allowed choices to satisfy the specification. Do not use an existential successful run as evidence of universal correctness.
- A precise specification states edge cases, invalid-input behavior, and the relevant arithmetic model. Mathematical integers and overflowing machine integers are different domains.

### 2.2 Partial and Total Correctness

A Hoare triple $\{P\}\ C\ \{Q\}$ expresses that executions starting in $P$ end in $Q$ whenever they terminate, under the usual partial-correctness interpretation. Total correctness adds termination from every permitted initial state.

For assignment, the precondition needed for a postcondition can be derived by substitution: $wp(x:=E,Q)=Q[E/x]$, subject to the language's rules for expression evaluation. For sequencing, work backwards: $wp(C;D,Q)=wp(C,wp(D,Q))$.

**Worked example:** To establish $x=10$ after `x := x + 1`, the required starting condition is $x=9$. Derive it by substitution instead of guessing from a test run.

For a demonic nondeterministic choice, every enabled alternative must satisfy its proof obligations. In a guarded command, also consider the case when no guard is enabled; the treatment of blocking or aborting is part of the semantic model.

### 2.3 Loop Invariants and Termination

For `while B do C`, a partial-correctness proof establishes:

1. The initial precondition implies invariant $I$.
2. $\{I\land B\}\ C\ \{I\}$ preserves it.
3. $I\land\neg B$ implies the desired postcondition.

A total-correctness proof also supplies a well-founded variant and shows strict decrease on each iteration that continues the loop.

**Worked example:** Assume $n\ge0$. Initialize `i := 0; s := 0`, then repeatedly add `i+1` to `s` and increment `i` while `i<n`. Use $0\le i\le n$ and $s=i(i+1)/2$ as the invariant, with variant $n-i$. At exit, $i=n$ establishes the sum formula. State that the proof uses exact integers; a machine implementation needs an overflow argument.

Common mistakes are choosing an invariant that holds only after completion, forgetting preservation after each assignment, or treating a non-increasing variant as strictly decreasing.

### 2.4 Deriving Programs from Proof Obligations

Start from the postcondition and introduce an invariant describing a partially completed result. Determine the initialization, exit condition, and body from the conditions required to preserve that invariant.

- Strengthening a specification can expose an efficient intermediate representation, but it must remain satisfiable.
- Refinement should preserve the required behavior while making the implementation more explicit.
- A derivation does not end with pseudocode: explain termination, the representation of data, and the correspondence between the mathematical program and implementation.

### 2.5 Parallel Programs and Owicki–Gries

A parallel correctness argument combines local proof outlines with checks that other processes do not invalidate their assertions. Check each relevant atomic action against assertions in the other process, under the action's precondition.

- Two locally correct threads can interfere through shared state. For example, treating `x := x + 1` as a read followed by a write allows lost updates unless atomicity or synchronization is provided.
- Specify the atomic actions and scheduler assumptions before reasoning about interleavings.
- Interference freedom supports the correctness of the combined proof outlines; termination and progress require additional obligations appropriate to the program and scheduling model.
- Deadlock freedom does not imply that each process eventually succeeds. Starvation and fairness are separate issues.

### 2.6 Oral Practice and Thesis Connections

1. Give a relational specification for a search or sorting task, including permitted input states.
2. Derive a weakest precondition for a sequence of assignments.
3. Prove a loop partially correct, then identify the missing termination argument.
4. Show how a second thread can break a locally valid assertion.
5. Explain the difference between interference freedom, deadlock freedom, and starvation freedom.

Use a thesis algorithm or concurrent component to provide a concrete contract, invariant, and proof obligation; tests are useful evidence but do not replace the argument.

### 2.7 Literature

The syllabi point to Apt and Olderog on sequential and concurrent verification, Owicki and Gries on axiomatic parallel proofs, Dijkstra's *A Discipline of Programming*, and Gries' *The Science of Programming*. [Software Foundations — Programming Language Foundations](https://softwarefoundations.cis.upenn.edu/plf-current/toc.html) provides additional mechanized examples of Hoare reasoning.

---

## Topic 3 — Project Management

**Course responsible (syllabus):** Dr. Molnár Bálint, PhD  
**Official syllabus:** [Project Management.pdf](https://www.inf.elte.hu/dstore/document/227912/Project_Management.pdf)

**Verified syllabus scope:** Project-management concepts and frameworks, lifecycle choices, lean and agile approaches, delivery and security practices, activity-network planning, testing, and team organization. This is a distinct dropdown subject from the supplementary Advanced Software Technology course.

### 3.1 Project Definition and Constraints

A project has an intended outcome, a bounded effort, and a delivery context. Distinguish project work from continuing operations and from the wider coordination of a programme or portfolio.

- Define objectives and success measures before making a schedule. Deliverables are produced artifacts; outcomes are the effects those artifacts are supposed to achieve.
- Scope, time, cost/resources, quality, and risk interact. An unchanged deadline with extra scope usually changes another constraint or requires an explicit tradeoff.
- A stakeholder can affect or be affected by the project. Analyze interests, influence, communication needs, and acceptance responsibilities.
- Establish decision authority, escalation paths, and change control. A backlog is not a substitute for agreeing who can change priorities or approve a release.

### 3.2 Selecting a Lifecycle

- **Predictive/waterfall:** Baseline the work and manage deviations. It can fit stable requirements, but discovering a mistaken requirement late is expensive.
- **Iterative/incremental:** Refine knowledge through repeated cycles and deliver usable portions of the result. Iteration and increment are related but not identical.
- **Spiral:** Organize successive cycles around identifying and reducing major risks rather than treating all work as equally predictable.
- **Lean:** Reduce waste and delays in delivering value. Explain what a particular metric measures before optimizing it; activity utilization alone does not measure customer value.
- **Six Sigma:** Address process variation and defects using measurable evidence. It is not another name for agile software development.

The syllabus references PMBOK's seventh edition. Prepare its principles and performance-domain perspective without assuming that one methodology is required for every project.

### 3.3 Agile, Scrum, and Engineering Practices

The [Scrum Guide](https://scrumguides.org/scrum-guide.html) defines accountabilities, events, and artifacts with associated commitments. Understand the purpose of each, not only their names.

- The Product Owner is accountable for product value and effective backlog management; Developers plan and perform the work; the Scrum Master supports effective use of Scrum.
- A Sprint Goal provides a coherent objective. A Sprint Review evaluates the outcome and next steps; a Retrospective improves the way the team works.
- A Definition of Done establishes the quality state required for an Increment. It differs from acceptance criteria for a particular item.
- Explain how XP practices, TDD, BDD, and continuous integration provide technical feedback. A Scrum calendar alone does not guarantee tested or maintainable software.
- Velocity is team- and context-dependent. It should not be used as a universal productivity ranking across teams.

### 3.4 Activity Networks and Critical Paths

In activity-on-node diagrams, nodes are activities and arcs express precedence; activity-on-arrow diagrams represent activities as arcs and may require dummy activities to express dependencies.

For a dependency network with fixed durations, compute earliest starts/finishes with a forward pass and latest starts/finishes with a backward pass. Total float is the difference between latest and earliest permitted starts. A critical path has zero total float under that model.

**Worked example:** A takes 3 days. B takes 4 days and C takes 2 days after A. D takes 1 day after both B and C. The paths A–B–D and A–C–D take 8 and 6 days. The earliest completion is 8 days; C has 2 days of total float. Explain how a shared staff constraint could make this precedence-only plan infeasible.

Crashing trades resources/cost for shorter duration; fast-tracking overlaps work and can increase rework risk. A schedule estimate should state uncertainty and assumptions.

### 3.5 Risk, Quality, and Communication

A risk is uncertain; an issue has occurred. Describe cause, event, consequence, owner, response, and trigger. Likelihood–impact assessment helps prioritize responses but should not disguise uncertain estimates as exact probabilities.

Quality planning establishes acceptance and verification criteria. Test automation, configuration control, and defect reporting contribute evidence. Communicate progress against outcomes, remaining risks, dependencies, and forecast completion rather than only counting completed tasks.

DevOps connects development and operation through collaboration, automation, and feedback. DevSecOps integrates security activities into that lifecycle. Neither means skipping approvals, tests, or separation of responsibilities where required.

### 3.6 Oral Practice and Thesis Connections

1. Choose a lifecycle for a project with uncertain requirements and explain your assumptions.
2. Calculate a critical path and explain what float does and does not guarantee.
3. Distinguish an acceptance criterion, a Definition of Done, and a project success measure.
4. Describe a risk response and how you will know whether it is working.
5. Explain how testing and delivery feedback changed the plan in your thesis.

### 3.7 Literature

Use the syllabus's PMBOK seventh-edition reference and 2020 Scrum Guide, plus Rupp's work on value-stream management. Keep the version of a framework explicit when discussing its terminology.

---

## Topic 4 — Formal semantics

**Course responsible (syllabus):** Horpácsi Dániel, PhD  
**Official syllabi:** [Lecture](https://www.inf.elte.hu/dstore/document/227900/Formal%20semantics%20L.pdf) · [Practice](https://www.inf.elte.hu/dstore/document/227901/Formal%20semantics%20Pr.pdf)

**Verified syllabus scope:** Mathematical meanings for a small imperative language, operational and denotational accounts, fixed points, inductive reasoning, equivalence, and implementation in semantic frameworks or proof assistants.

### 4.1 Syntax, States, and Judgments

Separate the grammar of a language from its meaning. A state $\sigma$ maps variables to values; updating a variable produces a new state $\sigma[x\mapsto v]$. Define expression evaluation and specify whether arithmetic is mathematical or machine-bounded.

A semantic rule consists of premises and a conclusion. An inference rule describes valid derivations, not an informal sequence of implementation steps. Learn to construct a derivation tree for a small program and identify the rule used at each node.

### 4.2 Small-Step Operational Semantics

Small-step semantics describes one computational transition, often written $\langle C,\sigma\rangle\rightarrow\langle C',\sigma'\rangle$.

- An assignment evaluates its expression and updates the state according to the chosen evaluation rules.
- Sequencing first steps the first command; after it finishes, execution proceeds to the second.
- A conditional chooses a branch after testing the guard.
- A loop can be related to a conditional whose true branch executes the body followed by the loop again.

**Example:** For `x := 1; x := x + 2`, show the intermediate state with $x=1$ before reaching $x=3$. The treatment of expression steps may differ between semantic definitions; follow the language specified in the exercise.

Small-step semantics exposes interleavings, nontermination, and stuck configurations. A stuck program and an infinite execution are different phenomena.

### 4.3 Big-Step Operational Semantics

Big-step semantics relates an initial configuration directly to a final result, often $\langle C,\sigma\rangle\Downarrow\sigma'$.

- A sequence derivation includes a state between its two component evaluations.
- A successful loop derivation recursively accounts for each completed iteration.
- A standard inductive terminating big-step relation has no finite derivation for a diverging execution. Absence of a derivation alone does not distinguish divergence from an error unless the model includes the necessary separate notions.

Compare the convenience of big-step proofs about final results with the detail available in small-step traces. Do not claim that either presentation is universally more expressive without specifying its definitions.

### 4.4 Denotational Semantics and Fixed Points

A denotation assigns a mathematical object to each syntactic construct. For a simple deterministic command, a partial state transformation can represent termination with a final state and leave divergence undefined.

Sequential composition corresponds to composition of transformations. A loop's meaning is recursive: execute the body and repeat when the guard holds, otherwise return the state.

- A domain supplies an information order and a least element representing no defined result.
- A monotone function preserves that order; continuity provides the conditions needed for computing a least fixed point through a chain of approximations.
- Under the appropriate domain-theoretic hypotheses, the loop denotation is the least fixed point of its semantic functional. Explain why an arbitrary fixed point would not express the intended least amount of defined behavior.
- Distinguish a fixed-point equation from an algorithm guaranteed to terminate after a finite number of iterations.

### 4.5 Induction and Equivalence

Use structural induction for syntax, induction on derivations for an inductively defined relation, and appropriate reasoning about iteration chains for denotations. State the induction hypothesis precisely.

To establish agreement between terminating small-step and big-step evaluations, show both directions under the assumptions of the chosen language. Agreement with denotational semantics is another theorem; do not substitute a few matching executions for a proof.

Program equivalence depends on what is observable. Equality of final states for terminating programs, preservation of divergence, effects, exceptions, and behavior in surrounding contexts are different possible requirements. A proposed compiler optimization must preserve the relevant observations.

### 4.6 Mechanization and Oral Practice

[Software Foundations — Programming Language Foundations](https://softwarefoundations.cis.upenn.edu/plf-current/toc.html), recommended by the syllabus, gives examples of inductive language definitions and machine-checked proofs.

1. Give small-step and big-step rules for one language construct and derive an example.
2. Explain how your semantic model represents nontermination and errors.
3. Define the functional whose least fixed point gives a loop meaning.
4. Select an induction principle for a proposed equivalence theorem.
5. Evaluate whether replacing a program fragment preserves its observations.

For a thesis involving language tools, connect the model to a transformation, interpreter, compiler, or verification claim. State the proof boundary when the implementation contains features absent from the formal language.

### 4.7 Literature

Consult Nielson and Nielson's semantics text, Winskel's formal-semantics treatment, Reynolds on programming-language theory, and the other readings in the linked syllabi. Their notation differs; define your notation before using a theorem.

---

<a id="topic-3-software-quality-and-testing"></a>

## Topic 5 — Software quality and testing

**Course responsible:** Kovács Attila, DSc
**Official syllabi:** [Lecture](https://www.inf.elte.hu/dstore/document/227917/Software%20Quality%20and%20testing.pdf) · [Practice](https://www.inf.elte.hu/dstore/document/227918/Software%20Quality%20and%20testing.pdf)
**Note:** The exam conforms to the **ISTQB Certified Tester Foundation Level (CTFL)** syllabus.

**Verified syllabus scope:** Testing terminology and principles, development/test lifecycles, planning and risk, test design, structural coverage, reviews, management and tools, and organizational quality frameworks. The syllabus states alignment with ISTQB CTFL but does not specify a CTFL edition.

### 5.1 Overview

This course covers the **principles, processes, and techniques** of software testing and quality assurance. It aligns with the ISTQB CTFL certification — the international standard for software testing knowledge. The course balances theory (definitions, models, principles) with practice (test design techniques, management, tools).

### 5.2 Foundations of Testing

- **Key terminology:**
  - **Error (mistake):** A human action that produces an incorrect result.
  - **Defect (bug, fault):** A flaw in a component or system that can cause it to fail.
  - **Failure:** Deviation of the component or system from its expected delivery, service, or result.
  - **The relationship:** Error → Defect → Failure. Not all defects cause failures; not all failures come from defects in code (environment, configuration).
- **Testing definition:** The process consisting of all lifecycle activities, both static and dynamic, concerned with planning, preparation, and evaluation of software products and related work products to determine that they satisfy specified requirements, to demonstrate that they are fit for purpose, and to detect defects.
- **Test basis:** The body of knowledge used as the basis for test analysis and design (requirements, design specs, code, risk analysis reports).
- **Test condition:** An item or event that could be verified by one or more test cases.
- **Test case:** A set of input values, execution preconditions, expected results, and execution postconditions.

### 5.3 The Seven Testing Principles

1. **Testing shows the presence of defects, not their absence.** Testing reduces probability of undiscovered defects but cannot prove correctness.
2. **Exhaustive testing is impossible.** Except for trivial cases. Use risk analysis and test techniques to focus effort.
3. **Early testing saves time and money.** Find defects early in the lifecycle when they're cheaper to fix (static testing, reviews).
4. **Defect clustering.** A small number of modules contain most defects. Focus testing on complex or changed areas.
5. **Pesticide paradox.** Running the same tests repeatedly stops finding new bugs. Regularly review and update test cases.
6. **Testing is context-dependent.** Safety-critical software is tested differently from an e-commerce site.
7. **Absence-of-errors fallacy.** Finding and fixing defects does not help if the system is unusable or doesn't meet user needs.

### 5.4 Testing in the Software Development Lifecycle

- **Sequential models (Waterfall, V-model):**
  - **V-model:** Each development phase has a corresponding test level.
    - Requirements → Acceptance testing
    - System design → System testing
    - Architecture design → Integration testing
    - Module design → Unit testing
    - Coding ↔ (unit tests execute against code)
  - Strengths: clear mapping, good for regulated environments. Weakness: rigid, late testing.

- **Iterative/incremental models (RAD, Unified Process, Agile):**
  - Testing happens continuously throughout each iteration.
  - **Agile testing:** Testing is integrated into the development process. Testers and developers collaborate closely.
  - **XP (Extreme Programming):** Test-Driven Development (TDD) — write tests before code. Pair programming. Continuous integration.
  - **Scrum:** Testing happens within each sprint. Definition of Done includes testing.
  - **Kanban:** Testing is a column on the board. Work is pulled when capacity exists.

- **Test levels:**
  - **Unit testing:** Individual components/modules. Usually done by developers.
  - **Integration testing:** Interfaces between components. Covers component, system, and system-of-systems integration.
  - **System testing:** The complete, integrated system against specified requirements.
  - **Acceptance testing:** By users/customers to determine if system is ready for deployment. UAT, alpha, beta testing.

### 5.5 Test Process — The Fundamental Test Process

1. **Planning and control:**
   - Test planning: define objectives, scope, approach, resources, schedule.
   - Test control: monitor progress, compare to plan, take corrective actions.
2. **Analysis and design:**
   - Review test basis. Identify test conditions. Design and prioritize test cases.
   - Identify necessary test data. Set up test environment.
3. **Implementation and execution:**
   - Develop and prioritize test procedures. Create test data.
   - Execute test suites. Log outcomes. Compare actual vs. expected results.
4. **Evaluating exit criteria and reporting:**
   - Check test execution against defined exit criteria.
   - Write test summary report for stakeholders.
5. **Test closure activities:**
   - Archive testware. Document lessons learned. Hand over to maintenance.

- **Entry criteria:** Conditions that must be met before testing can begin (e.g., test environment ready, code frozen).
- **Exit criteria:** Conditions that must be met before testing can be declared complete (e.g., 95% pass rate, all critical bugs fixed, coverage targets met).

### 5.6 Human Aspects & Test Management

- **Independence of testing:**
  - Author tests own code → lowest independence.
  - Developer peer tests → some independence.
  - Dedicated test team → higher independence.
  - External organization → highest independence.
  - *Tradeoff:* More independence → more objectivity, but also more communication overhead and less familiarity with code.

- **Test team roles:** Test manager, test analyst, test designer, test automator, test administrator.
- **Risk-based testing:** Prioritize testing based on:
  - **Product risk:** What could go wrong with the product? (Likelihood × Impact)
  - **Project risk:** What could go wrong with the project? (schedule, resources, technical)

### 5.7 Specification-Based (Black-Box) Testing Techniques

These derive test cases from the specification/requirements *without* looking at code.

- **Equivalence Partitioning (EP):** Divide input data into partitions where the system should behave equivalently. Test one value from each partition.
  - *Example:* Age field 1–120. Valid partition: 1–120. Invalid: ≤0, ≥121, non-numeric.
  - **Why:** Dramatically reduces number of test cases while maintaining coverage.

- **Boundary Value Analysis (BVA):** Test values at the edges of equivalence partitions. Defects cluster at boundaries.
  - *Example:* For range 1–120, test: 0, 1, 120, 121.
  - Combine with EP for efficient coverage.

- **Decision Table Testing:** For systems where outputs depend on combinations of inputs. Every combination of conditions → expected action.
  - *Example:* Loan approval: credit score (high/low) × income (sufficient/insufficient) × employment (stable/unstable) → approve/deny/review.
  - **Why:** Systematic. Ensures no combination is missed.

- **State Transition Testing:** Model the system as states and transitions. Test sequences of events.
  - *State transition diagram:* Nodes = states, Edges = transitions labeled with event/action.
  - *State table:* Shows valid and invalid transitions.
  - *Coverage criteria:* Every state, every transition, every path.
  - *Example:* ATM: idle → card inserted → PIN entered → menu → transaction → eject card → idle.

- **Use Case Testing:** Test based on use cases (interactions between actor and system). Covers typical workflows, alternative flows, and exception flows.

- **Combinatorial Testing (Pairwise):** When multiple parameters interact, test all pairs of parameter values (not all combinations). Drastically reduces test cases while catching most interaction defects.

### 5.8 Structure-Based (White-Box) Testing Techniques

These use the internal structure of the code to design tests.

- **Statement coverage:** Percentage of executable statements exercised. Minimum level — 100% statement coverage is weak.
- **Decision (branch) coverage:** Percentage of decision outcomes exercised. Tests each if/else, loop entry/exit. Stronger than statement coverage.
- **Condition coverage:** Each atomic boolean condition evaluated to both true and false.
- **Decision/condition coverage:** Combination of decision and condition coverage.
- **Modified condition/decision coverage (MC/DC):** Each condition independently affects the decision outcome. Required for safety-critical software (DO-178C).
- **Path coverage:** Every possible path through the code. Usually infeasible (loops).
- **Cyclomatic complexity (McCabe):** $M = E - N + 2P$ (edges - nodes + 2×connected components). Measures number of linearly independent paths. Indicates testing difficulty — higher complexity → more tests needed. Can be simplified as: number of decision points + 1.

### 5.9 Static Testing

Testing **without executing** the code:

- **Reviews:**
  - **Informal review:** No formal process. Quick, cheap.
  - **Walkthrough:** Author leads, explains to peers. Learning + defect finding.
  - **Technical review:** Technical experts evaluate. Focus on technical correctness.
  - **Inspection:** Formal, structured process with defined roles (moderator, author, reviewer, scribe). Uses checklists and entry/exit criteria. Most effective but most expensive.

- **Static analysis:** Automated tools analyze code without execution.
  - Detects: unreachable code, uninitialized variables, security vulnerabilities, coding standard violations.
  - Data flow analysis: track how data values propagate.
  - Control flow analysis: check for dead code, infinite loops.

### 5.10 Supporting Processes & Tools

- **Configuration management:** Control changes to testware (test cases, data, scripts, results). Ensures traceability — which test version was run against which code version.
- **Incident (defect) management:** The lifecycle of a defect from discovery to closure.
  - Defect report contents: ID, summary, severity, priority, steps to reproduce, expected vs. actual result, environment, attachments.
  - Defect lifecycle: New → Assigned → Fixed → Retested → Closed (or Reopened).
  - **Severity vs. Priority:** Severity = impact on system. Priority = urgency for business. A cosmetic bug on the homepage might be low severity but high priority.

- **Test tools:**
  - **Categories:** Test management tools, static analysis tools, test design tools, test execution/automation tools, performance/load testing tools.
  - **Selection criteria:** Fit with technology stack, ease of use, integration with existing tools, cost, support.
  - **Benefits:** Faster, more reliable, programmable. **Risks:** Over-reliance, maintenance cost, false sense of security.

### 5.11 Software Quality Frameworks

- **ISO/IEC 25010:2011 product-quality model:** Functional suitability, performance efficiency, compatibility, usability, reliability, security, maintainability, and portability. The [2011 edition](https://www.iso.org/standard/35733.html) has been superseded; the [2023 edition](https://committee.iso.org/standard/78176.html) defines nine product-quality characteristics. Identify the edition used in the lecture rather than presenting the older eight-characteristic model as the current standard.
- **ISO 9000:** Quality management system standard. Process-oriented. "Say what you do, do what you say, prove it."
- **SPICE (ISO 15504 / ISO 33000):** Software Process Improvement and Capability dEtermination. Assesses maturity of software processes on a 6-level scale (0: Incomplete → 5: Optimizing).
- **CMMI (Capability Maturity Model Integration):** Process improvement framework. Maturity levels: 1 (Initial) → 2 (Managed) → 3 (Defined) → 4 (Quantitatively Managed) → 5 (Optimizing).
  - Each level adds more disciplined processes. Moving up is expensive but reduces risk and improves predictability.

### 5.12 Exam Preparation — Key Themes

1. Walk through the 7 testing principles. For each, give a real-world example.
2. Design test cases for a given spec using EP + BVA + decision table. Show your work.
3. Compare black-box vs. white-box techniques — strengths, weaknesses, when to use each.
4. Explain risk-based testing. How do you prioritize?
5. What makes a good defect report? What should it contain and why?
6. Describe the fundamental test process and the V-model. How do they relate?
7. Why is independence in testing important? What are the tradeoffs?

### 5.13 Literature

- Graham, van Veenendaal, Evans, Black: *Foundations of Software Testing*, Thomson, 2007.
- Forgács, Kovács: *Practical Test Design*, BCS, 2019.
- Galin: *Software Quality Assurance: from theory to implementation*, Addison-Wesley, 2004.
- [ISTQB CTFL Syllabus](https://www.istqb.org/certifications/certified-tester-foundation-level)

---

## Topic 6 — Design of Distributed System

**Course responsible (syllabus):** Dr. Horváth Zoltán, PhD  
**Official syllabus:** [Design of Distributed Systems.pdf](https://www.inf.elte.hu/dstore/document/227899/design_of_distributed_systems.pdf)  
**Name match:** Neptun uses the singular “System”; the official syllabus uses “Systems”. This chapter matches that subject, not Topic 16.

**Verified syllabus scope:** Formal reasoning about cooperating programs, resource-sharing problems, safety and progress, verified composition, communication channels, and pipeline networks.

### 6.1 A Distributed Program as a State Machine

Describe the global state as local process states plus communication state. Define the initial predicate and transition relation before stating a property. An execution is a sequence of states connected by allowed actions.

- Local sequential order does not imply a global total order shared by all processes.
- Atomicity is an assumption about an action, not a consequence of writing it on one source-code line.
- Specify whether channels are synchronous or buffered, reliable or lossy, ordered or unordered. A proof relying on ordered delivery does not automatically work on an unordered network.
- Separate scheduling assumptions from protocol behavior. Fairness assumptions restrict admissible executions and must be justified.

### 6.2 Safety, Progress, and Invariants

A safety claim forbids a bad execution prefix; a liveness claim requires a desired event eventually to occur. Mutual exclusion is a safety property. Eventual acquisition after a request is a progress property.

For an invariant $I$, show that every initial state satisfies $I$ and every allowed transition from an $I$-state preserves it. This must include actions of all processes, not only the process whose local code you are explaining.

- Deadlock freedom says the system cannot reach a state with no possible useful continuation under the stated definition.
- Starvation freedom requires an individual request to make progress, not merely that some process keeps working.
- Weak and strong fairness constrain scheduling differently: continuous enabledness and repeated enabledness are distinct conditions.
- An invariant proof alone does not establish eventual service. Add a well-founded progress argument or the appropriate temporal proof under explicit scheduling assumptions.

### 6.3 Dining and Drinking Philosophers

The dining-philosophers example combines exclusive resources and possible circular waiting. If every philosopher holds one fork and waits for the next, each local acquisition rule may be sensible while the complete system deadlocks.

Compare possible remedies by their proof obligations: imposing a global resource order, coordinating acquisition, or using an appropriate distributed protocol. Breaking a circular-wait pattern addresses deadlock; fair access still needs an argument.

The drinking-philosophers problem allows more varied resource needs. Prepare the version used in the lecture: resource ownership, request rules, transfer rules, and the assumptions on changing demands determine the proof. Do not equate it with running the same fixed two-fork algorithm on a renamed resource.

### 6.4 Composition of Verified Components

A component proof usually depends on an environment contract. When components are composed, prove that each component supplies what the others assume.

- Shared-state interference can invalidate a local invariant.
- Hiding internal actions can change which observations are relevant to the external specification.
- A component that always consumes input and one that eventually produces output can still block if their buffering and synchronization conventions do not match.
- Refinement should preserve the required safety and progress behavior under the intended observation model.

**Example:** A bounded producer–consumer buffer should preserve $0\le count\le capacity$. That proves capacity safety. To argue that every produced item is eventually consumed, also state assumptions about consumer progress, scheduling, and failures.

### 6.5 Channels and Pipeline Networks

Model the interface of a stage as a relation or contract on its input and output streams. Check ordering, loss, duplication, termination signals, and blocking behavior when stages are connected.

A pipeline's steady-state throughput is limited by its bottleneck under the assumed resource model. End-to-end latency also includes per-stage and queueing delay; throughput and latency are different metrics. Backpressure may preserve bounded resource use while creating dependencies that must be considered in a deadlock analysis.

### 6.6 Oral Practice and Thesis Connections

1. Specify mutual exclusion and eventual service separately for a shared resource.
2. Prove an invariant under all process actions and identify a fairness assumption.
3. Construct a dining-philosophers deadlock and justify a prevention scheme.
4. Explain why two verified components might fail when combined.
5. Give a correctness argument for a pipeline, including its termination protocol.

For a thesis, use an actual concurrent component or message-processing pipeline. Distinguish measured reliability from properties proved in a formal model.

### 6.7 Literature

Use Chandy and Misra on parallel program design, Misra on multiprogramming, and Lamport's [Specifying Systems](https://lamport.azurewebsites.net/tla/book.html), all identified by the ELTE syllabus. Topic 16 provides the separate Petri-net and algebraic-analysis route.

---

## Topic 7 — Advanced Java programming

**Official ELTE description:** [Advanced Java Programming.pdf](https://www.inf.elte.hu/dstore/document/226045/Advanced_Java_Programming.pdf)  
**Curriculum cross-check:** [Software Architecture MSc 2022 curriculum, March 2026 revision — spring intake](https://www.inf.elte.hu/dstore/document/226809/Elosztott%20szoftverrendszerek%202022%20keresztf%C3%A9l%C3%A9v%20%282026%20m%C3%A1rcius%29.pdf)

**Source limitation:** This course is in the supplied Neptun dropdown and the linked 2022-curriculum document, but it is absent from the public specialization syllabus index checked on 2026-10-08. The available short ELTE description is older, names no course responsible, and cites earlier Java/JPA editions. Confirm the applicable lecturer, syllabus revision, and Java version in current semester materials. The curriculum link confirms the subject, not that every intake has the same schedule.

**Verified description scope:** Java beyond introductory syntax: type abstraction, introspection, concurrency, runtime memory, I/O, persistence, networking, design, failure handling, logging, and testing.

### 7.1 Generics and API Design

- A parameterized type captures a compile-time relationship between values. Java generics are generally invariant: `List<Integer>` is not a subtype of `List<Number>`.
- `? extends T` permits safely reading values as `T`; `? super T` supports adding values of type `T` while restricting what can be assumed when reading. Explain a real API instead of treating PECS as a complete proof.
- Type erasure preserves many compile-time checks without reifying all generic arguments at runtime. Understand raw types, unchecked operations, and heap pollution.
- A generic method can express relationships between arguments and its result more precisely than an API using only `Object`.

**Practice:** Explain why a method copying elements between collections can use a source bounded above by `T` and a destination bounded below by `T`. Identify which operations would be unsafe if the bounds were reversed.

### 7.2 Annotations and Reflection

Annotations carry metadata; their retention policy determines whether it is available in source processing, class files, or runtime reflection. Reflection can inspect types and members and invoke behavior dynamically.

Discuss access restrictions, type-checking boundaries, performance, and failure handling. A reflection-based framework still needs a clear contract. Explain how serialization, dependency injection, or test discovery uses metadata without assuming reflection bypasses every module boundary.

### 7.3 Concurrency and the Memory Model

A data race is not the same as every possible concurrency bug. Atomicity, visibility, and ordering are separate requirements.

- `synchronized` provides mutual exclusion and relevant memory-order guarantees when the same monitor is used correctly.
- `volatile` provides specified visibility/ordering guarantees; it does not make an increment or a multi-variable invariant atomic.
- Locks, atomics, concurrent collections, and executors solve different coordination problems. State cancellation and shutdown behavior.
- Safe publication matters even for objects that will later be read without synchronization.
- Deadlock prevention, bounded queues, thread-pool sizing, and interruption handling require design decisions beyond selecting a concurrency class.

The [Java Language Specification, Chapter 17](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html) is the primary reference for memory-model claims. Use the Java edition applicable to the course when discussing version-dependent features.

### 7.4 Memory, I/O, and Serialization

Explain reachability and garbage collection without promising a particular collection time. Retained references can cause memory growth even in a garbage-collected language. File handles, sockets, and database connections still need deterministic resource management.

Use `try`-with-resources for suitable closeable resources. Distinguish byte streams from character streams, specify encodings, and handle partial I/O and errors. Deserializing untrusted data crosses a security boundary; describe validation and the format's risks rather than assuming object serialization is automatically safe.

### 7.5 JDBC and Persistence

- JDBC provides connection, statement, result-set, and transaction interfaces. A prepared statement separates bound values from SQL syntax; it does not make arbitrary dynamic table names safe.
- Define transaction boundaries and rollback behavior. Connection pooling changes resource lifecycle, not the need to release borrowed connections.
- JPA maps entities and relationships to persistent storage. Explain identity, managed/detached state, lazy loading, cascading, and transaction scope using the assigned provider/version.
- Discuss the difference between the in-memory object model and database constraints, including consistency and query costs.

### 7.6 Networking, Failures, and Testing

TCP offers an ordered byte stream, so applications need framing. UDP preserves datagram boundaries without guaranteeing delivery. HTTP adds application-level semantics; timeouts and retries can create repeated side effects unless the operation handles duplication.

Checked and unchecked exceptions express different API contracts. Assertions should not replace validation of external inputs because their execution is configurable. Log useful context without credentials or sensitive payloads, and distinguish unit tests from integration tests requiring real persistence or network behavior.

### 7.7 Oral Practice and Literature

1. Explain a wildcard signature and show which writes or reads are permitted.
2. Diagnose a visibility or lost-update bug and justify synchronization.
3. Trace an entity and transaction through a failing persistence operation.
4. Design message framing and timeout handling for a TCP-based component.
5. Explain how logging and tests helped resolve a thesis defect.

The historical ELTE bibliography names the Java language specification and JPA specification. Supplement it with [Oracle's official Java SE 25 specification](https://docs.oracle.com/javase/specs/jls/se25/html/index.html) when appropriate; the edition is explicit and is not presented as the course's mandated runtime.

---

<a id="topic-4-introduction-to-data-science"></a>

## Topic 8 — Introduction to Data Science

**Course responsible:** Horváth Tomáš, PhD
**Official syllabus:** [Introduction to Data Science.pdf](https://www.inf.elte.hu/dstore/document/227905/Introduction%20to%20Data%20Science.pdf)

**Verified syllabus scope:** The data-analysis process, data quality and preparation, descriptive mining, predictive-model concepts and validation, and recommendation. The detailed study notes below retain the original chapter.

### 8.1 Overview — The Data Science Pipeline

This course provides a **broad foundation** in data science: the concepts, techniques, and methodology behind extracting knowledge from data. It covers the full pipeline: understanding the business problem → data preparation → modeling → evaluation → deployment. The emphasis is on understanding *what* the techniques do, *why* they work, and *when* to apply them — not just calling library functions.

### 8.2 The CRISP-DM Methodology

**CRoss-Industry Standard Process for Data Mining** — the de facto standard methodology for data science projects. Six phases, highly iterative:

1. **Business Understanding:** Define objectives, success criteria, translate business problem to data science problem.
2. **Data Understanding:** Collect initial data, describe, explore, verify quality.
3. **Data Preparation:** Clean, transform, select features, construct new features. Often 60–80% of project time.
4. **Modeling:** Select technique, build model, tune parameters.
5. **Evaluation:** Does the model meet business objectives? Review process. Decide: deploy or iterate?
6. **Deployment:** Put model into production. Monitor and maintain.

- **Why CRISP-DM?** Provides a common language across teams. Emphasizes iteration — you will go back. Ensures business value, not just technical exercise.

### 8.3 Data Quality & Pre-processing

Real-world data is messy. This is the most time-consuming but critical phase.

- **Data quality issues:**
  - **Noise:** Random error or variance in measured values. *Sources:* sensor errors, human entry, transmission errors.
  - **Missing values:** Data not recorded or unavailable. *Strategies:*
    - Delete rows/columns (only if minimal loss and data is MCAR — Missing Completely At Random).
    - Imputation: mean/median/mode, regression imputation, k-NN imputation, multiple imputation.
    - Indicator variable: add a binary feature marking "was missing."
  - **Outliers:** Data points significantly different from others. *Detection:* IQR method, Z-score, DBSCAN noise points. *Handling:* investigate (might be valuable!), transform, or remove.
  - **Inconsistent data:** Different formats, units, coding schemes.

- **Data transformation:**
  - **Normalization/Standardization:**
    - Min-max scaling: $x' = \frac{x - x_{min}}{x_{max} - x_{min}}$ → range [0,1]. Sensitive to outliers.
    - Z-score standardization: $x' = \frac{x - \mu}{\sigma}$ → mean 0, std 1. Less sensitive to outliers.
    - *Why normalize?* Many ML algorithms (k-means, k-NN, neural networks, SVMs) assume features are on similar scales. Without it, features with larger ranges dominate.
  - **Discretization/Binning:** Convert continuous → categorical. Can improve interpretability and handle non-linearities.
  - **Feature encoding:** One-hot encoding for nominal categories. Label encoding for ordinal.

### 8.4 Descriptive Techniques — Clustering

Find natural groupings in unlabeled data.

- **k-means clustering:**
  - *Algorithm:* (1) Choose k. (2) Initialize k centroids (randomly or k-means++). (3) Assign each point to nearest centroid. (4) Recompute centroids as mean of assigned points. Repeat 3–4 until convergence.
  - *Objective:* Minimize within-cluster sum of squares (WCSS / inertia).
  - *Properties:* An iteration over n points, k centers and d features costs O(n·k·d); i is the number of iterations. The objective does not increase under standard updates, but the result need not be globally optimal. Different densities or cluster sizes can give poor partitions.
  - *k-means++:* Smart initialization — spreads initial centroids. Improves quality and speed.
  - *Choosing k:* Elbow method (plot WCSS vs. k), silhouette score, gap statistic.

- **Agglomerative (Hierarchical) Clustering:**
  - *Algorithm:* (1) Each point is its own cluster. (2) Merge two closest clusters. (3) Repeat until one cluster remains.
  - *Linkage criteria (how to measure cluster distance):*
    - Single-link: distance between closest points. Can produce chain-like clusters.
    - Complete-link: distance between farthest points. Produces compact clusters.
    - Average-link: average distance between all pairs.
    - Ward's method: minimizes increase in total within-cluster variance after merging.
  - *Output:* Dendrogram — can cut at any level to get desired number of clusters. No need to pre-specify k.

- **DBSCAN (Density-Based Spatial Clustering of Applications with Noise):**
  - *Core concept:* A point is a **core point** if ≥ minPts points are within radius ε. Clusters are connected dense regions.
  - *Advantages:* Finds arbitrary-shaped clusters. Handles noise (points not in any cluster = outliers). No need to specify k.
  - *Disadvantages:* Sensitive to ε and minPts. Struggles with varying densities.
  - *Parameters:* ε (neighborhood radius), minPts (minimum points to form dense region).

- **Cluster validation:**
  - **Internal:** Silhouette score, Davies-Bouldin index. Measures compactness + separation using only the data.
  - **External:** Adjusted Rand Index, Normalized Mutual Information. Compares to ground truth labels (if available).
  - **Stability:** Does clustering change significantly with different samples/initializations?

### 8.5 Frequent Pattern Mining

Find interesting associations and patterns in transactional data.

- **Itemset:** A set of items. Support = fraction of transactions containing the itemset.
  - **Frequent itemset:** Support ≥ minimum support threshold.
- **Association rule:** $X \rightarrow Y$ where $X \cap Y = \emptyset$.
  - **Support:** $supp(X \rightarrow Y) = P(X \cup Y)$ — how often the rule applies.
  - **Confidence:** $conf(X \rightarrow Y) = P(Y|X) = supp(X \cup Y)/supp(X)$ — how often Y follows when X occurs.
  - **Lift:** $lift(X \rightarrow Y) = P(Y|X)/P(Y) = conf/supp(Y)$ — how much more likely Y becomes given X.
    - Lift > 1: positive correlation. Lift = 1: independent. Lift < 1: negative correlation.
  - *Why lift?* Confidence alone is misleading. "People who buy milk also buy bread" (high confidence, but bread is common anyway → lift ≈ 1 → not interesting).

- **Quality measures and tradeoffs:**
  - Support: too low → too many spurious rules. Too high → miss interesting rare patterns.
  - Confidence vs. Lift: high confidence ≠ interesting. Always check lift.

- **Applications:** Market basket analysis, recommendation ("customers who bought X also bought Y"), web usage mining, bioinformatics.

### 8.6 Predictive Techniques — The Core Concepts

The course focuses on understanding the *concepts* behind predictive models, not just running algorithms. These concepts apply across all predictive models.

- **Model = function approximator:** $y \approx f(x; \theta)$ where θ are parameters learned from data.
- **Parameters vs. Hyper-parameters:**
  - **Parameters:** Learned from data during training (e.g., weights in linear regression, coefficients).
  - **Hyper-parameters:** Set before training, control the learning process (e.g., k in k-NN, λ in regularization, learning rate). Tuned via cross-validation.

- **Model validation:**
  - **Train/test split:** Train on one portion, evaluate on held-out portion. Simple but high variance.
  - **Cross-validation (k-fold):** Split data into k folds. Train on k-1, test on 1. Repeat k times. Average results.
    - *Why?* More reliable estimate of generalization performance. Uses all data for both training and testing.
    - Typical: k=5 or k=10. Leave-one-out (k=n) for very small datasets.
  - **Stratified sampling:** Preserve class proportions in each fold. Important for imbalanced data.

### 8.7 Overfitting, Underfitting & the Bias-Variance Tradeoff

This is arguably the most important concept in the course. Must understand deeply.

- **Underfitting:** Model too simple. High bias. Doesn't capture patterns in training data. Both training and test error are high.
- **Overfitting:** Model too complex. High variance. Fits noise in training data. Training error low, test error high.
- **The tradeoff:** As model complexity increases:
  - **Bias** (error from wrong assumptions) decreases.
  - **Variance** (error from sensitivity to training data) increases.
  - **Total error = bias² + variance + irreducible error.**
  - Optimal complexity minimizes total error.

- **Detecting overfitting:** Large gap between training and validation performance.
- **Preventing overfitting:**
  - More data (best solution, not always possible).
  - Regularization (L1/L2): add penalty for large parameter values.
  - Early stopping: halt training when validation error starts increasing.
  - Cross-validation for hyperparameter tuning.
  - Simpler models (Occam's razor).

### 8.8 Linear Classification & Regression

- **Linear Regression:** $y = w^Tx + b$. Minimize mean squared error.
  - Closed-form solution (normal equation): $\hat{w} = (X^TX)^{-1}X^Ty$ when X has full column rank. In implementations, use an appropriate linear-system/decomposition solver; rank-deficient cases need a suitable pseudoinverse or regularization.
  - Gradient descent alternative for large datasets.
  - Assumptions: linearity, independence, homoscedasticity (constant variance), normality of errors for inference.

- **Logistic Regression (classification):** $P(y=1|x) = \sigma(w^Tx + b)$ where $\sigma(z) = 1/(1+e^{-z})$.
  - Despite the name, it's for classification (outputs probability).
  - Decision boundary: $w^Tx + b = 0$ — linear.
  - Trained via maximum likelihood (cross-entropy loss).

- **Validation for classifiers:** Confusion matrix, accuracy, precision, recall, F1-score, ROC curve, AUC.
  - Know which metric matters for which problem (e.g., recall for disease detection, precision for spam filtering).

### 8.9 Introduction to Traditional Prediction Techniques

The course covers these as "black-box functions" — understand what they do and when to use them:

- **k-Nearest Neighbors (k-NN):** Instance-based. No training — just store data. Prediction by majority vote of k nearest neighbors. Sensitive to normalization and choice of k.
- **Decision Trees:** Partition space recursively based on feature splits (information gain, Gini impurity). Interpretable but prone to overfitting.
- **Naive Bayes:** Assumes features are conditionally independent given class. Fast, works surprisingly well for text.
- **Support Vector Machines (SVMs):** Find the maximum-margin separating hyperplane. Kernel trick for non-linear separation.

### 8.10 Recommendation Techniques

- **Collaborative Filtering:** "Users who liked what you liked also liked..."
  - User-based: find similar users, recommend what they liked.
  - Item-based: find items similar to ones you liked (more scalable).
  - Matrix factorization (SVD): learn latent factors for users and items.
  - *Cold start problem:* New users/items have no history → need content-based fallback or hybrid.

- **Content-Based:** Recommend items with similar attributes to what user liked. Needs feature representation of items.
- **Hybrid:** Combine collaborative and content-based. Most real-world systems are hybrid.

### 8.11 Exam Preparation — Key Themes

1. Walk through the CRISP-DM phases. For your thesis: map what you did to each phase.
2. Given a dataset with noise, missing values, and different scales — what preprocessing steps? Justify each.
3. Compare k-means, agglomerative clustering, and DBSCAN. When would you choose each?
4. Explain the bias-variance tradeoff intuitively. How does it manifest in model selection?
5. Interpret a confusion matrix. What's the difference between precision and recall? When is one more important?
6. What is an association rule? Why is lift important? Give an example.
7. Explain cross-validation. Why not just use a single train/test split?

### 8.12 Literature

- Peter Flach: *Machine Learning: The Art and Science of Algorithms that Make Sense of Data*, Cambridge University Press, 2012.
- Jiawei Han, Micheline Kamber, Jian Pei: *Data Mining: Concepts and Techniques*, Morgan Kaufmann, 2011.
- Pang-Ning Tan, Michael Steinbach, Vipin Kumar: *Introduction to Data Mining*, Addison Wesley, 2005.

---

## Topic 9 — Models of Computation

**Course responsible (syllabus):** Dr. Lukovszki Tamás, PhD  
**Official syllabi:** [Lecture](https://www.inf.elte.hu/dstore/document/227908/Models%20of%20computation%20L..pdf) · [Practice](https://www.inf.elte.hu/dstore/document/227909/Models%20of%20computation%20Pr..pdf)

**Verified syllabus scope:** Classical and alternative computing devices, parallel and distributed models, neural and natural computation, expressive power, resource efficiency, description size, and applications.

### 9.1 What a Computational Model Specifies

A model identifies allowable states, operations, inputs, outputs, and execution rules. It also needs a cost convention if we intend to compare efficiency.

- Computational power asks what can be computed or recognized in principle.
- Computational complexity asks which resources are needed as input size grows.
- Descriptional complexity asks how large the representation of a machine, grammar, circuit, or other description must be.
- Two models may compute the same class of functions but differ greatly in representation size or simulation overhead.

State what counts as an input symbol, a memory cell, or a single step. Giving arbitrary-precision arithmetic unit cost can change a claimed algorithmic bound.

### 9.2 Automata, Memory, and Language Recognition

- A finite automaton has bounded internal memory and recognizes a regular language. Explain deterministic versus nondeterministic acceptance and the potential state blow-up of determinization.
- A pushdown automaton has a stack. Relate it to context-free structure and explain why a stack is suited to nested matching.
- A Turing machine has an unbounded tape model. Distinguish accepting, rejecting, and failing to halt.
- A recognizer may run forever on some nonmembers; a decider must halt on every input. Undecidability is stronger than saying that an algorithm is too slow.

**Practice:** Compare recognizing strings over `a` and `b` with checking that their counts appear as $a^n b^n$. The latter needs information that cannot be kept by a fixed-size finite-state controller for arbitrary $n$.

### 9.3 Equivalent and Alternative Classical Models

Partial recursive functions describe computation through function-building operations; partiality allows undefined results. Relating them to machines requires an equivalence argument, not a resemblance between programming notation and mathematics.

Random-access machines model addressable memory and operations resembling conventional programming. Their cost depends on permitted word sizes and operations. Multi-tape or other Turing-machine variants may preserve computability while changing simulation cost.

Circuits represent a computation by a finite network of gates. A circuit family is needed for unbounded input lengths; uniformity determines whether those circuits can themselves be generated effectively. Circuit size and depth measure different aspects of resources.

### 9.4 Cellular Automata and Petri Nets

Cellular automata apply local transition rules to a spatial configuration. Explain boundary conditions, synchronous updates, and how local interaction produces global behavior. Universality claims depend on the rule and representation.

Petri nets represent places, transitions, and token markings. Firing changes a marking when input conditions permit it. Their concurrency and resource representation make them useful for workflows and synchronization; see Topic 16 for detailed analysis. A model's computational power is not a guarantee that its useful verification questions are cheap.

### 9.5 Parallel, Distributed, and Neural Models

For parallel computation, distinguish work from time/depth and specify how communication and synchronization are charged. A distributed model must state what participants know, how messages behave, and which failures are allowed.

Neural models use interconnected computational units and parameterized functions. Claims about their theoretical power depend on activation rules, precision, memory, and whether the system is discrete or continuous. A real finite-precision implementation is not automatically equivalent to an idealized real-valued model.

### 9.6 Natural and Unconventional Computation

The syllabus bibliography includes DNA and membrane computing. Explain the modeled operations and how a problem is encoded, where the required resources appear, and how an answer is extracted.

Massive parallelism does not remove costs such as material, number of objects, preparation, or readout. Evaluate a proposed speedup under a complete resource model instead of concluding that unconventional computing solves every difficult problem efficiently.

### 9.7 Oral Practice and Literature

1. Distinguish recognition from decision with a concrete language example.
2. Explain how two models can be equally powerful but differ in complexity.
3. State the RAM cost assumptions behind a running-time claim.
4. Compare sequential, parallel, and distributed resources for the same task.
5. Identify hidden resource costs in an unconventional-computation proposal.

The ELTE bibliography includes Savage, Fernández, Sipser, and work by Păun and collaborators. Savage's [Models of Computation](https://cs.brown.edu/people/jsavage/book/pdfs/ModelsOfComputation.pdf) is linked directly from the official syllabus.

---

## Topic 10 — Principles of artificial intelligence

**Course responsible (syllabus):** Gregorics Tibor, PhD  
**Official syllabus:** [Principles of artificial intelligence — effective from September 2025](https://www.inf.elte.hu/dstore/document/227911/Principles_of_artificial_intelligence%202025%20szept%201.-t%C5%91l.pdf)

**Verified syllabus scope:** Problem representations, general search control, heuristic and evolutionary search, adversarial games, and introductory supervised/unsupervised learning. The detailed statistical-model treatment belongs to Topics 14 and 18.

### 10.1 Representation Comes Before Search

Define states, initial conditions, operators, a goal test, and costs. A search graph is determined by that representation, not just by which algorithm visits its nodes.

- State-space search represents a solution by a path to a goal.
- Problem decomposition may require solutions of several subproblems together; AND/OR representations distinguish joint requirements from alternatives.
- A constraint-satisfaction problem specifies variables, domains, and constraints. Propagation can reduce choices before backtracking explores them.
- A logical representation supports explicit statements and rules; define how a solution is derived from it rather than assuming every logical query is a simple finite graph search.

Representation affects branching, repeated states, and whether a solution can be evaluated incrementally.

### 10.2 Search Properties and Heuristics

Distinguish completeness, optimality, memory use, and time. Their guarantees depend on finite branching, cost assumptions, repeated-state handling, and stopping conditions.

A heuristic estimates the remaining cost. Admissibility gives a lower bound on true remaining cost; consistency requires $h(n)\le c(n,n')+h(n')$ for each relevant edge.

For A*, use $f(n)=g(n)+h(n)$. With the appropriate assumptions, an admissible heuristic supports optimality; a graph-search implementation may need to reopen states when the heuristic is inconsistent. Seeing an optimal result once is not proof that a heuristic is admissible.

The syllabus also names B and EMA* variants. Use the lecturer's definitions and pseudocode for those algorithms; do not expand the initials or transfer A* guarantees to them without establishing the relevant conditions.

### 10.3 Local Search and Backtracking

- Hill climbing improves a candidate locally but can become trapped on local optima or plateaus.
- Tabu search uses memory to discourage cycling and controls when otherwise forbidden moves are allowed.
- Simulated annealing sometimes accepts worsening moves; acceptance depends on the objective change and temperature. Finite-time performance is not the same as an asymptotic convergence theorem under a particular cooling schedule.
- Backtracking systematically extends partial assignments and retracts choices. Explain pruning and why it preserves completeness if that is claimed.
- Evolutionary algorithms specify representation, fitness, selection, variation, and replacement. A fitness value must measure the actual objective rather than reward an unintended shortcut.

**Practice:** Represent a scheduling task both as a constraint problem and as local-search candidates. Explain how hard feasibility constraints are handled in each representation.

### 10.4 Two-Player Games

In a finite, deterministic, perfect-information zero-sum game, minimax models an optimal opponent. Terminal utilities propagate through maximizing and minimizing choices.

Alpha–beta pruning removes branches that cannot affect the minimax decision under the current bounds. It preserves the result at the chosen search depth; move order affects how much work it saves.

A depth cutoff requires an evaluation function. Explain uncertainty in that evaluation, the horizon effect, and why increasing depth does not by itself repair an invalid game model. Games with chance or hidden information require additional modeling choices.

### 10.5 Introductory Learning

- Supervised learning uses labeled examples; discuss how a classifier is evaluated on unseen data. Prepare the principle behind nearest-neighbor methods, trees, forests, and neural networks.
- Unsupervised learning looks for structure without target labels. K-means depends on a distance measure and cluster assumptions.
- PCA selects directions of variance in a centered representation. Variance preservation need not preserve the features most relevant to a classification target.
- Search over model parameters or hyperparameters still requires an objective, validation protocol, and resource budget. Training-set performance is not generalization evidence.

### 10.6 Oral Practice and Thesis Connections

1. Give two representations of one problem and compare their search spaces.
2. Show that a proposed heuristic is admissible, or provide a counterexample.
3. Trace A* or backtracking on a small instance and state the termination rule.
4. Demonstrate minimax and alpha–beta on a small game tree.
5. Explain where local search or learning was appropriate in your thesis and how you evaluated it.

### 10.7 Literature

The syllabus names Russell and Norvig's *Artificial Intelligence: A Modern Approach* and Nilsson's AI texts. Match the lecture's search terminology and definitions when preparing specific algorithm variants.

---

## Topic 11 — Advanced Algorithms

**Course responsible (syllabus):** Dr. Szabó László Ferenc, CSc  
**Official syllabi:** [Lecture](https://www.inf.elte.hu/dstore/document/227887/Advanced%20Algorithms%20L.pdf) · [Practice](https://www.inf.elte.hu/dstore/document/227888/Advanced%20Algorithms%20Pr.pdf)

**Verified syllabus scope:** Network optimization, flow and matching theorems, constrained flows, connectivity and density applications, randomized cuts, approximation, and limits on solvability. Topic 1 is the separate design-paradigms course.

### 11.1 Flow Networks and Residual Graphs

A directed network has capacities, a source, and a sink. A feasible flow respects edge bounds and conservation at intermediate vertices; its value is the net flow leaving the source.

A residual edge records how an existing solution can be changed. Forward residual capacity permits additional flow; reverse residual capacity permits undoing an earlier choice. Forgetting reverse edges can leave an augmenting-path implementation with a suboptimal result.

For an $s$–$t$ cut, partition vertices with $s$ on one side and $t$ on the other. Every feasible flow is bounded above by the cut capacity. A flow whose value equals a cut capacity provides both a solution and an optimality certificate.

### 11.2 Ford–Fulkerson and Edmonds–Karp

The augmenting-path method repeatedly sends the maximum permitted increment along a residual source-to-sink path.

- With integral capacities, integer augmentations give an integral maximum flow. The elementary running-time bound depends on flow value and is therefore not strongly polynomial.
- Arbitrary path choices with irrational capacities can create nontermination behavior in the abstract method. State the assumptions behind a termination claim.
- Edmonds–Karp chooses a shortest residual path in number of edges by BFS. Its $O(VE^2)$ bound is independent of capacity magnitudes.
- The proof of that bound relies on residual distance behavior and how often an edge can be critical, not on pretending that each edge is used once.

**Practice:** Build a small network where an early augmentation must later be partially canceled. Draw the residual graph after each step and end by exhibiting a matching minimum cut.

### 11.3 Matching and Disjoint Paths

Bipartite matching reduces to integral flow by connecting the source to the left partition and the right partition to the sink with unit capacities. Matched edges correspond to unit flow between partitions.

- Hall's condition characterizes a matching covering a specified side: every subset must have at least as many neighbors.
- König's theorem equates maximum matching size and minimum vertex-cover size in bipartite graphs. Neither result should be transferred unchanged to arbitrary graphs.
- Unit-capacity edges support a reduction for edge-disjoint paths between a source and sink. Vertex-disjointness instead needs suitable vertex-capacity modeling.
- Routing several prescribed terminal pairs is a different problem: ordinary maximum flow can connect the wrong pairs. Directedness and the number of pairs affect the relevant complexity results.

### 11.4 Lower Bounds and Other Flow Reductions

For $l_e\le f_e\le u_e$, subtract each lower bound from the edge capacity and account for the resulting imbalance at its endpoints. Add the appropriate demand-balancing construction and check whether every required balancing edge can be satisfied. Derive the signs of the imbalances from conservation instead of memorizing a diagram blindly.

For an $s$–$t$ flow problem, a circulation construction may also need a return edge. Feasibility and maximization are different steps.

Flow and cut reductions can encode connectivity, constrained allocation, and density questions. For densest-subgraph tasks, state the objective precisely: maximizing $|E(S)|/|S|$ differs from finding a maximum clique or requiring a fixed number of vertices.

### 11.5 Global Cuts and Randomization

An $s$–$t$ minimum cut separates prescribed terminals; a global minimum cut selects the partition freely. In the basic undirected Karger contraction method, randomly contract edges until two supervertices remain, avoiding self-loops.

A run can destroy the desired cut. For a fixed minimum cut, the standard lower bound on survival probability is $2/(n(n-1))$. Independent repetition improves the probability of finding a global minimum; do not describe one run as an always-correct minimum-cut algorithm. State how multiedges and weights are handled in the chosen version.

### 11.6 Approximation and Local Search

For nonnegative weighted vertex cover, an LP relaxation requires $x_u+x_v\ge1$ on every edge. Rounding variables at least $1/2$ produces a cover with weight at most twice the relaxation's objective, hence at most twice the optimum.

For nonnegative weighted undirected maximum cut, a locally optimal cut under single-vertex moves has at least half the total edge weight across it: otherwise some vertex could improve the cut. That yields a half-optimum guarantee. Show the inequality and state the assumptions; a local optimum is not necessarily a global optimum.

Distinguish an approximation-ratio proof, exact-solvability restrictions, and an impossibility result. A reduction must preserve the relevant answers or objectives before it supports a complexity conclusion.

### 11.7 Oral Practice and Literature

1. Explain residual reverse edges with a concrete cancellation example.
2. Prove a maximum-flow claim by giving a cut of equal capacity.
3. Construct a matching or disjoint-path reduction and identify its limitations.
4. Transform a lower-bounded network into a feasibility problem.
5. Derive a cut or vertex-cover approximation bound, including its assumptions.

The ELTE syllabi recommend *Introduction to Algorithms* and *Algorithm Design*. In a thesis, show the modeled capacities, constraints, and objective as well as implementation measurements.

---

## Topic 12 — Complex information systems

**Course responsible (syllabus):** Molnár Bálint, PhD, habil.  
**Official syllabi:** [Lecture](https://www.inf.elte.hu/dstore/document/227891/Complex_Information_Systems_en_2022.pdf) · [Practice](https://www.inf.elte.hu/dstore/document/227892/Complex_Information_Systems_en_2022.pdf)

**Verified syllabus scope:** Information-systems analysis and design, requirements and UML, ERP processes and reference models, logistics and planning, workflow and supply chains, organizational functions, controls, and integration.

### 12.1 Requirements and Analysis Models

An information system combines people, processes, data, rules, and technology. Begin by identifying organizational goals and stakeholders rather than treating the task as selecting a database or framework.

- Separate functional requirements from quality requirements and constraints. Give observable acceptance criteria and trace them into design and verification.
- Structured analysis emphasizes processes, data flow, and data stores. Object-oriented analysis emphasizes domain concepts, responsibilities, and collaborations.
- UML diagrams answer different questions: use cases describe actor goals; class diagrams describe structure; sequence diagrams describe interactions; state and activity diagrams describe behavior.
- A diagram is useful when its meaning is clear and it agrees with the requirements and other models. Drawing every available diagram is not a substitute for analysis.

### 12.2 ERP and End-to-End Business Processes

ERP integrates information across organizational functions, often through shared master data and coordinated processes. A department-local optimum can damage the end-to-end process.

**Worked example — procure to pay:** A need leads to a requisition and purchase order, goods receipt changes inventory, an invoice is reconciled, and payment follows authorization. Identify the documents, ownership, state changes, and checks at each step. A goods receipt, supplier invoice, and payment are distinct business events.

Compare this with order-to-cash or production planning. Explain how reference models describe recurring enterprise patterns without guaranteeing that one organization's process can be copied unchanged into another.

### 12.3 Logistics, Forecasting, and Material Planning

- Distinguish inventory position from inventory on hand, and item master data from transactions.
- Demand can be forecast, independently requested, or derived from a production plan. Forecast uncertainty should be reflected in planning decisions.
- Material requirements planning uses the production schedule, bill of materials, inventory records, and lead times to calculate dependent requirements.
- Explain the difference between a requirement, a planned order, a released production order, and an actual receipt or completion.
- Capacity feasibility is separate from material availability. A plan can have all required components and still exceed a resource's available capacity.

For a small bill of materials, work backward through quantities and lead times, showing how stock and scheduled receipts affect net requirements.

### 12.4 Workflows and Organizational Functions

A workflow model specifies tasks, conditions, routing, and responsibility. Prepare sequential, parallel, conditional, and exception paths.

- Workflow engines coordinate task execution but still need application-level rules, permissions, and recovery behavior.
- Supply-chain management crosses organizational boundaries; shared identifiers and timely data do not automatically create shared trust or identical policies.
- Human-resources and maintenance-management systems have their own objects, authorization boundaries, and lifecycle constraints.
- Internal controls, management accounting, and audit evidence need traceability from an action to its actor, authorization, and business effect.

### 12.5 Access Rights, Security, and Auditing

Roles and organizational responsibilities should drive access rules. Least privilege and separation of duties help constrain both mistakes and misuse.

For an approval workflow, identify who can request, approve, record fulfillment, and authorize payment. A log does not prevent an invalid action; it supplies evidence after the fact unless combined with enforcement.

Discuss integrity, availability, privacy, and retention requirements in context. An audit trail must preserve relevant history and support interpretation of changed business records. Actual legal and organizational obligations come from current applicable policy, not from assuming that a textbook model establishes compliance.

### 12.6 Integrating Complex Systems

Compare shared databases, APIs, messaging, and middleware against ownership, coupling, consistency, and recovery needs. Match schemas and business meaning, not only field names.

For an asynchronous inventory update, explain what happens when a message is duplicated, delayed, or delivered after another update. Correlation identifiers, idempotent handling, reconciliation, and explicit error queues may be necessary. Choosing integration software does not settle those semantic requirements.

### 12.7 Oral Practice and Literature

1. Turn a business objective into traceable requirements and complementary models.
2. Walk through an ERP process and identify each document and state transition.
3. Calculate simple material requirements and explain a capacity limitation.
4. Define a permission/control scheme for a multi-step approval process.
5. Compare two integration approaches and explain how failures are reconciled.

Use the syllabus's readings on SSADM, information-system analysis, UML, and integrated ERP processes. A thesis connection should cover business meaning and process correctness as well as application code.

---

## Topic 13 — Functional Languages

**Course responsible (syllabus):** Kaposi Ambrus, PhD  
**Official syllabus:** [Functional Languages.pdf](https://www.inf.elte.hu/dstore/document/227902/Functional_languages.pdf)

**Verified syllabus scope:** Haskell expressions and types, several forms of function definition, comprehensions and recursion, higher-order programming, algebraic and parameterized types, and user-defined type classes and instances.

### 13.1 Functions and Types

A function type describes the inputs and output of a computation. In Haskell, `a -> b -> c` associates to the right: it describes a function returning another function. Application associates to the left.

- Currying represents a multiple-argument function by successive function applications.
- Partial application supplies fewer arguments and returns a function expecting the remainder.
- A polymorphic function uses type variables uniformly; an overloaded function has class constraints expressing which operations are available.
- Lists are homogeneous; tuple positions can have different types. A tuple's arity is part of its type.

**Practice:** Infer the type of `map`, explain the type of `foldr`, and distinguish `(+) 1` from a pair containing a function and a number.

### 13.2 Defining Functions

Pattern matching deconstructs values according to their constructors. Guards test conditions after relevant bindings have been introduced. Conditional expressions select between expressions; lambdas define anonymous functions.

- Check pattern completeness and overlap. An unmatched input can fail even though the function passes a few tests.
- Variable scope matters: pattern variables, local definitions, and lambdas do not all bind names in the same places.
- Operator sections are concise partial applications, but argument order must remain clear.
- Avoid using a partial function such as `head` when the domain includes an empty list; use a result type or a pattern that handles that case.

### 13.3 Comprehensions and Recursion

A list comprehension describes values selected from generators and filtered by guards. Later generators may depend on values bound by earlier generators; order affects enumeration.

For recursion over a list, identify the empty case and how the recursive call reduces the problem. For recursion over several arguments, state which measure ensures progress on the permitted domain.

Laziness allows some results to be produced without evaluating an entire structure. It does not guarantee termination or bounded memory. A function inspecting an entire infinite list cannot finish; a computation retaining unevaluated work may consume unexpectedly much space.

### 13.4 Higher-Order Functions

`map` transforms elements, `filter` selects elements, and folds combine structure according to a supplied operation and initial value.

- `foldr` follows right-associated structure and can sometimes produce results from lazy inputs without inspecting the entire list first.
- A left fold is not automatically a constant-space accumulation in a lazy language. Strictness of the accumulator and retained references matter.
- Function composition connects output of one function to input of another; compare a composition with an explicitly named intermediate value for clarity and type compatibility.
- Equational reasoning can replace a pure expression with an equal one. State any assumptions about termination or partial values when making a general law.

### 13.5 Algebraic and Parameterized Data Types

A type synonym gives another name to an existing type; it does not create a distinct constructor-bearing representation. Algebraic data types describe alternatives and their associated values.

```haskell
data Tree a = Empty | Node (Tree a) a (Tree a)

mapTree :: (a -> b) -> Tree a -> Tree b
mapTree _ Empty = Empty
mapTree f (Node left x right) =
  Node (mapTree f left) (f x) (mapTree f right)
```

Explain how the type variable expresses reusable structure, how pattern matching distinguishes constructors, and how recursive calls follow the tree. Prove a property such as preserving the number of nodes by structural induction.

A `Maybe a` result can make possible absence explicit. The caller must still decide how to handle it; a type representing failure is not an automatic recovery policy.

### 13.6 Type Classes and Instances

A class describes a set of operations available for appropriate types; an instance supplies their implementation for one type. This is not the same concept as an object-oriented class of mutable objects.

Class laws express expected semantic behavior but are generally not enforced merely by type checking. An instance of equality, ordering, or combination can type-check while violating those laws.

Practice defining a small class and instance, deriving a constrained function type, and explaining the difference between parametric and ad-hoc polymorphism. Use extensions only when they are part of the assigned course material.

### 13.7 Oral Practice and Literature

1. Infer and explain a higher-order function's type.
2. Convert a comprehension to equivalent recursive or higher-order code.
3. Handle an empty structure without a partial function.
4. Define a recursive data type and a function over it, then state an induction argument.
5. Explain a type-class constraint and a law an instance should satisfy.

The syllabus recommends Hutton, Lipovača, Allen and Moronuki, and *Real World Haskell*. In a thesis, connect functional structure to correctness, composability, and explicitly modeled failure, while measuring relevant performance properties.

---

## Topic 14 — Machine Learning

**Course responsible (syllabus):** Horváth Tomáš, PhD  
**Official syllabus:** [Machine Learning.pdf](https://www.inf.elte.hu/dstore/document/227906/Machine%20Learning.pdf)

**Verified syllabus scope:** Detailed traditional learners and their tuning, probabilistic and graphical models, neural and factorization methods, learning with limited labels, ensembles, and sequence/text applications.

### 14.1 Learning Objectives and Evaluation

Define the prediction task, training data, hypothesis class, loss, and evaluation protocol. A parameter is fitted by the learning procedure; a hyperparameter controls the model or procedure and must be selected without using final test outcomes.

- Use held-out evaluation appropriate to the data-generating process. Random folds can leak information when records share a subject, time sequence, or near-duplicate content.
- Fit preprocessing within training folds. Scaling, vocabulary building, and feature selection on all data can contaminate validation.
- Compare to a meaningful baseline and report variability, not only the best run.
- Relate the chosen metric to false positives, false negatives, calibration, and decision costs.

Topic 8 introduces the wider data-analysis process; this course requires explaining mechanisms and tuning choices in greater depth.

### 14.2 Decision Trees and Kernel Methods

A decision tree chooses splits according to a criterion such as impurity reduction. Tree depth, leaf size, pruning, and feature handling affect complexity and generalization. A more expressive tree can fit training noise.

An SVM separates classes using a margin-based objective with penalties for violations. Explain the role of regularization and the meaning of support vectors. A kernel evaluates an implicit feature-space inner product; not every similarity function is a valid positive-semidefinite kernel.

For an RBF kernel, kernel width and penalty parameters interact with scaling and data density. Explain how a tuning protocol compares configurations rather than asserting that one parameter choice works across datasets.

### 14.3 Probabilistic and Graphical Models

A graphical model represents relationships in a probability distribution. The graph's edges encode the chosen factorization or independence structure, not necessarily causation.

Distinguish estimating parameters, inferring unobserved variables, and learning structure. A simple conditional-independence assumption can make inference manageable but may be wrong for the application.

**Practice:** State the assumptions of a naive Bayes classifier and derive how it combines class priors with feature likelihoods. Explain why correlated features can affect probability calibration even when classification remains useful.

### 14.4 Neural Networks and Factorization

Neural training combines differentiable parameterized transformations, a loss, and an optimization procedure. Use the chain rule to explain gradient propagation; activation, capacity, initialization, regularization, and learning rate affect behavior.

Factorization methods learn lower-dimensional representations of a data matrix or interactions. Missing observations are not automatically zeros. In a recommender system, explain how the loss is restricted to observed interactions, what regularization does, and how a new user or item is handled.

Do not equate a numerical optimizer reaching a small training loss with a proof of statistical generalization or convergence to a global optimum.

### 14.5 Ensembles and Semi-Supervised Learning

- Bagging combines learners fitted to resampled data and can reduce instability. Random forests also introduce feature randomization.
- Boosting builds learners sequentially to improve a combined objective. Explain how errors or gradients guide the next learner and how overfitting is controlled.
- Stacking learns a combination model; generate its training predictions without training/validation leakage.
- Semi-supervised learning uses unlabeled data in addition to labels. Its usefulness depends on assumptions such as smoothness or cluster structure. Incorrect pseudo-labels can amplify mistakes.

A combined model is not guaranteed to beat its components. Compare with held-out evidence and account for correlated errors and additional complexity.

### 14.6 Time-Series and Text Mining

For time-series prediction, split and evaluate in time order when the task predicts future observations. Features unavailable at prediction time are leakage even if they are present in the recorded dataset. Distinguish trend, seasonality, and temporal dependence.

For text, define tokenization and representation, such as term counts or TF–IDF. Fit vocabulary and statistics on training data, handle unseen terms, and test whether duplicates or source overlap inflate results. Explain why a representation suited to topic classification may fail for order-sensitive meaning.

### 14.7 Oral Practice and Literature

1. Explain a learner's objective, assumptions, and most consequential hyperparameters.
2. Design a leakage-resistant experiment for grouped or temporal observations.
3. Compare a tree ensemble and an SVM for a specified dataset.
4. Derive a probabilistic prediction and identify a questionable independence assumption.
5. Explain when unlabeled data or factorization helps and when it can mislead.

Use the syllabus's Alpaydin, Shalev-Shwartz and Ben-David, and Bishop references. For a thesis, present reproducible comparisons, uncertainty, and failure analysis as well as accuracy.

---

## Topic 15 — Service Science

**Course responsible (syllabus):** Molnár Bálint, PhD, habil.  
**Official syllabi:** [Lecture — effective from September 2025](https://www.inf.elte.hu/dstore/document/227915/Service%20Sciences_2025%20szept%201.-t%C5%91l.pdf) · [Practice](https://www.inf.elte.hu/dstore/document/227916/Service%20Sciences_2025%20szept%201.-t%C5%91l.pdf)

**Verified syllabus scope:** Service systems and electronic delivery, innovation and design, semantics, analytics and optimization, value co-creation, markets and networks, and the opportunities and risks of AI-assisted services. Use the revised syllabus rather than assuming this is only a web-services programming course.

### 15.1 Services and Service Systems

A service involves an activity or interaction that produces value for participants. A service system includes providers, users, resources, information, rules, and relationships; its boundaries must be defined before it can be analyzed.

- Contrast a purchased artifact with the continuing experience and performance of a service. Software may support both.
- Distinguish what the provider produces from what the user achieves. Completing an online form is not the same outcome as receiving the requested benefit.
- Stakeholders may have different objectives: users want useful outcomes, providers manage resources, and partners maintain their own obligations.
- Quality is experienced across a journey, including failures and recovery, not only at one interface or transaction.

### 15.2 Electronic Services, Innovation, and Design

Electronic delivery changes reach, automation, coordination, and the amount of data produced. It also creates dependence on identity, connectivity, accessibility, and operational reliability.

For service innovation, identify the unmet need, a proposed mechanism for delivering value, and evidence that it works. Technological novelty alone is insufficient.

**Worked example:** An appointment service includes discovery, booking, confirmation, attendance, cancellation, and follow-up. A service blueprint can expose visible interactions and backstage processes. Test what happens when a participant cannot use the digital channel, receives duplicate confirmations, or needs to change an appointment.

Map research and design decisions to a measurable user outcome. A prototype, user study, or operational experiment should test a stated hypothesis rather than only demonstrate that a screen can be used.

### 15.3 Service Semantics and Composition

An interface description says how to call an electronic service; a semantic description expresses what the service means and which conditions or effects are intended.

- Shared vocabularies and ontologies can reduce ambiguity, but a syntactically compatible field name does not establish shared meaning.
- State preconditions, outputs, effects, and nonfunctional commitments relevant to composition.
- Distinguish discovery, selection, invocation, and coordination of services.
- A composed service depends on partners' reliability, meaning, authorization, and timing as well as its own implementation.

### 15.4 Analytics and Optimization

Service analytics turns records of demand, interaction, execution, and outcomes into evidence. Examine data quality and missing participants before interpreting average performance.

- Choose metrics for demand, access, wait time, throughput, service quality, and outcomes.
- Segment results when an average hides a group experiencing much poorer service.
- For optimization, define decision variables, an objective, constraints, and uncertainty. Minimizing provider cost can conflict with user waiting time or equitable access.
- Queueing and capacity models must state their assumptions about arrivals, durations, and resources. More utilization can mean more delay rather than better service.

### 15.5 Co-Creation, Markets, and Networks

Value co-creation recognizes that participants contribute information, effort, knowledge, or resources to the outcome. It does not mean transferring all burden to the user.

Explain how service encounters affect perceived quality and productivity. A faster process may generate rework, confuse participants, or reduce successful outcomes.

Service markets and platforms coordinate exchanges among participants. Discuss incentives, pricing or allocation mechanisms, trust, and dependencies. Network effects can increase value while also creating fragility or exclusion. Service-level engineering turns desired performance into operational commitments and measurements.

### 15.6 AI and ML in Services

The revised syllabus explicitly covers AI-supported public-service delivery, including privacy, security, responsibility, and possible harmful enforcement.

Evaluate the task the model performs: retrieving facts, finding patterns, predicting an outcome, or supporting a decision. Those tasks have different error consequences and verification needs.

- Assess who benefits and who bears the cost of mistakes.
- Provide a path for correction, escalation, and human review where the service requires it.
- Check representativeness, data provenance, and access controls.
- Measure service outcomes and reliability in use, rather than only a model's benchmark score.

These are design and evaluation considerations. Determine actual legal obligations from the current applicable authorities and organizational rules.

### 15.7 Oral Practice and Literature

1. Define a service system and identify the value sought by each participant.
2. Draw an appointment-service journey and explain backstage dependencies.
3. Distinguish API compatibility from semantic compatibility.
4. Formulate a capacity or allocation objective and discuss competing constraints.
5. Evaluate an AI-enabled service, including error consequences and recourse.

The revised bibliography covers service-system foundations, service engineering, and AI/ML public-service delivery. For a thesis, connect system behavior to real service outcomes and explicit stakeholder needs.

---

## Topic 16 — Analysis of distributed systems

**Course responsible (syllabus):** Tejfel Máté, PhD, habil.  
**Official syllabus:** [Analysis of distributed systems.pdf](https://www.inf.elte.hu/dstore/document/227890/Analysis%20of%20distributed%20systems.pdf)

**Verified syllabus scope:** Concurrent behavior expressed through nets and algebra, process operations and composition, behavioral/structural properties, reachability and progress, restricted net families, semantics, and analysis tools. This is distinct from Topic 6's distributed-program design and composition proofs.

### 16.1 Ordinary Place/Transition Petri Nets

Places hold tokens; transitions consume and produce tokens according to arc weights. A marking records the number of tokens in each place.

A transition is enabled when its input places contain the required tokens. Firing removes the input amounts and adds the output amounts. Read the net's definition carefully: inhibitor, reset, timed, or colored extensions change the semantics and are not ordinary weighted place/transition nets.

**Worked example:** Two processes share a resource represented by one token. Acquiring the resource moves that token into one process's holding state; release returns it. If all holding states and the free-resource place share a conserved total of one token, simultaneous ownership is excluded in that model.

Concurrency, conflict, and causal dependency are distinct: enabled transitions may compete for the same tokens or be independently executable.

### 16.2 Reachability, Boundedness, and Liveness

- A marking is reachable if a valid firing sequence leads to it from the initial marking.
- A place is bounded if its tokens never exceed a finite bound over reachable markings. A safe net has at most one token in each place under the usual definition.
- A dead marking enables no transition. Absence of a dead marking does not mean every transition remains capable of firing eventually.
- A transition is live when it can eventually be enabled again from every reachable marking, under the standard net-theoretic definition. Distinguish this possibility property from a scheduling guarantee that it actually fires on every execution.

A reachability graph can decide useful properties for a finite-state instance, but state explosion limits feasibility. Unbounded nets require different techniques; a coverability representation is not simply an exact finite reachability graph.

### 16.3 Structural Reasoning and Invariants

Let $C$ be the incidence matrix, $m_0$ the initial marking, and $\sigma$ a vector counting transition firings. A reachable marking must satisfy $m=m_0+C\sigma$ for its firing sequence. This equation is necessary but generally insufficient: it ignores whether the counted transitions could be enabled in a valid order.

- A place invariant $y^T C=0$ preserves $y^T m$. A positive conservation relationship can bound resource counts.
- A transition invariant $Cx=0$ describes a balanced firing-count vector. It does not by itself establish that the corresponding sequence is executable or that the net is live.
- Distinguish properties of the net structure from properties depending on its initial marking.
- Do not conclude global safety or liveness from an invariant that constrains only one subset of places.

### 16.4 Net Classes, Transformations, and Petri Boxes

Restricted net classes can admit stronger analysis methods. Prepare the exact definitions and relationships used in the lecture, including how restrictions on choices and synchronization affect behavior.

A transformation must state which properties it preserves and how old and new executions correspond. Preserving one resource invariant need not preserve timing, observations, or liveness.

Petri boxes provide a compositional approach to representing constructs such as sequence, alternatives, and iteration. Identify entry/exit interfaces and explain the behavior of the composition instead of assuming that joining two drawings proves equivalence.

### 16.5 Process Algebra and Behavioral Equivalence

An algebraic model describes processes through actions and operators, such as sequencing, choice, and parallel composition. Operational semantics can produce a labeled transition system; denotational or axiomatic accounts offer other ways to explain the same constructs.

- State whether parallel components synchronize on shared actions and what happens to internal actions.
- Trace equivalence compares observable action sequences; bisimulation also matches stepwise branching behavior. They are not generally interchangeable.
- Decide whether successful termination, deadlock, divergence, and internal behavior are observable in the chosen model.
- An algebraic equation is meaningful under a particular equivalence and operator semantics. Explain its assumptions before using it as a program transformation.

### 16.6 Tools, Oral Practice, and Thesis Connections

A simulation demonstrates executions; it does not by itself show that every execution satisfies a property. For an analysis result, report the model, initial marking, state-space assumptions, property, and any abstraction.

1. Translate a resource-sharing workflow into a net and trace enabled firings.
2. Distinguish safety, boundedness, deadlock freedom, and net-theoretic liveness.
3. Calculate an invariant and explain what it cannot prove.
4. Show why a state-equation solution might be unreachable.
5. Compare trace equivalence with a branching-sensitive relation.

The syllabus references Murata's Petri-net survey, Best–Devillers–Koutny, Hennessy, and Hoare's CSP. A thesis can use these methods to analyze a protocol, workflow, or synchronization design under explicit abstractions.

---

## Topic 17 — Introduction to Computer Security

**Course responsible (syllabus):** Dr. Burcsi Péter, PhD  
**Official syllabi:** [Lecture](https://www.inf.elte.hu/dstore/document/227903/Introduction%20to%20Computer%20Security%20L.pdf) · [Practice](https://www.inf.elte.hu/dstore/document/227904/Introduction%20to%20Computer%20Security%20Pr.pdf)

**Verified syllabus scope:** Security objectives and risk vocabulary, concrete network and web attack classes, defensive controls, and practical application of that framework.

### 17.1 Objectives and Threat Modeling

Confidentiality protects against unauthorized disclosure; integrity concerns unauthorized or improper change; availability concerns required access to a system or service. State what those objectives mean for the particular asset.

- An asset is something of value; a vulnerability is a weakness; a threat is a potential harmful circumstance or action.
- Risk combines possible consequences and their likelihood in a context. A vulnerability count alone is not a risk assessment.
- A security control can prevent, detect, limit, or support recovery from harm. Explain its mechanism and residual limitations.
- Identify trust boundaries, entry points, data flows, attacker capabilities, and assumptions. Encrypting a transport does not validate business rules at its endpoints.

**Practice:** Model a thesis application's login, data storage, and external API. For each boundary, identify what must be trusted and what is verified.

### 17.2 Identity, Access, and Cryptographic Protection

Authentication establishes an identity or credential claim; authorization determines permitted actions. Perform authorization where the protected operation is enforced, rather than relying solely on a hidden UI control.

Differentiate encryption, hashing, message authentication, and digital signatures. A hash alone does not authenticate a message. Cryptographic guarantees depend on correct keys, protocol use, and endpoint behavior.

Use least privilege and explicit credential lifecycle management. Explain how secrets are provisioned and revoked, and why logs must not become a second disclosure channel.

### 17.3 Man-in-the-Middle and Network Poisoning

A man-in-the-middle attacker can relay or alter traffic when endpoints fail to establish the intended protected peer relationship. Transport encryption without appropriate certificate and hostname validation can leave that relationship unverified.

ARP poisoning can redirect traffic on a relevant local network; DNS poisoning can manipulate name-to-address information. Their prerequisites and boundaries differ. Explain what a network segmentation, validation, monitoring, or cryptographic control actually mitigates.

DNSSEC addresses authenticity/integrity of applicable DNS information; it is not encryption of the application payload. HTTPS protects an authenticated transport relationship under its trust assumptions; it does not make a compromised server trustworthy.

### 17.4 SQL Injection and XSS

SQL injection occurs when untrusted values alter the intended structure of a database command. Prepared statements bind values separately from query structure. Dynamic identifiers need separate constrained handling; blindly concatenating them remains dangerous. See [OWASP's SQL-injection guidance](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html).

Cross-site scripting occurs when untrusted content is interpreted as executable browser content. Defenses depend on the output context: HTML text, attributes, URLs, and JavaScript are not interchangeable encoding targets. Where deliberately authored HTML is accepted, use appropriate sanitization and safe rendering. See [OWASP's XSS-prevention guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).

Do not claim that a single input filter or a content-security policy makes every rendering path safe. Trace a value to its sensitive operation and identify the relevant defensive boundary.

### 17.5 Security Testing and Operational Evidence

Prepare small, authorized lab demonstrations that show an attack precondition, its effect, and how a countermeasure changes the result.

- Negative tests should exercise forbidden accesses, malformed inputs, and failure behavior.
- Distinguish a demonstrated vulnerability from a possible concern and from a verified control.
- A successful test suite cannot establish the absence of every vulnerability.
- Combine secure design, review, dependency awareness, monitoring, and response planning with testing. A control needs maintenance as deployment conditions and threats change.

### 17.6 Oral Practice and Literature

1. Identify an asset, threat, vulnerability, impact, and control in one coherent scenario.
2. Explain authentication and authorization across a service boundary.
3. Compare man-in-the-middle, ARP poisoning, and DNS poisoning prerequisites.
4. Explain why parameterized SQL and context-aware rendering address different problems.
5. Describe what your security tests demonstrate and what remains outside their coverage.

The syllabus recommends Ferguson–Schneier–Kohno, McGraw, and Stallings. A thesis answer should connect threats to concrete safeguards and evidence, rather than merely listing security tools.

---

<a id="topic-2-methods-and-tools-for-ai-applications"></a>

## Topic 18 — Methods and tools for AI applications

**Course responsible:** Csató Lehel, PhD
**Official syllabus:** [Methods and Tools for AI applications.pdf](https://www.inf.elte.hu/dstore/document/227907/Methods%20and%20Tools%20for%20AI%20applications.pdf)

**Verified syllabus scope:** Mathematical/statistical representations, likelihood-based and Bayesian estimation, optimization and approximations, latent-variable learning, clustering, ensemble methods, and autoencoders. This is distinct from the general search-focused Principles of artificial intelligence course.

### 18.1 Overview — The Mathematical Engine of AI

This course covers the **mathematical foundations and algorithmic tools** that power modern AI systems. It goes beyond the BSc-level "what is AI" to the MSc-level "how do AI algorithms actually work mathematically, and how do you choose the right one?" The focus is on probabilistic modelling, optimization, and unsupervised learning methods.

### 18.2 Mathematical Data Models in AI

- **Why mathematical models?** AI systems make predictions/decisions under uncertainty. Mathematical models provide the formal framework to represent data, quantify uncertainty, and optimize decisions.
- **Types of models:**
  - **Deterministic:** fixed input → fixed output (e.g., linear regression without noise).
  - **Probabilistic:** input → distribution over outputs (e.g., logistic regression, Bayesian models). Captures uncertainty.
  - **Generative vs. Discriminative:**
    - Generative: models the joint distribution P(X, Y). Can generate new data. Examples: Naive Bayes, GMMs, autoencoders.
    - Discriminative: models P(Y|X) directly. Better for classification when you don't need to model X. Examples: logistic regression, SVMs, neural networks.

### 18.3 Linear Algebra Foundations

- **Vectors and matrices as data representations:**
  - Data points as vectors in ℝⁿ (feature space).
  - Datasets as matrices (rows = samples, columns = features).
- **Key operations and their AI relevance:**
  - **Dot product:** measures similarity/correlation. Foundation of linear classifiers, attention mechanisms.
  - **Matrix multiplication:** linear transformations, neural network layers.
  - **Eigenvalues/eigenvectors:** PCA, spectral clustering, understanding model behavior.
  - **Matrix decompositions (SVD):** dimensionality reduction, latent factor models, recommender systems.
- **Generalized Linear Models (GLMs):** Extend linear regression to non-normal response distributions via a link function. Includes linear regression (identity link), logistic regression (logit link), Poisson regression (log link).

### 18.4 Probability Theory Essentials

- **Random variables, probability distributions, density functions.**
- **The Normal (Gaussian) distribution:** Central to ML — appears naturally via CLT, used in priors, noise models, variational approximations.
  - PDF: $p(x|\mu,\Sigma) = \frac{1}{(2\pi)^{d/2}|\Sigma|^{1/2}} \exp\left(-\frac{1}{2}(x-\mu)^T\Sigma^{-1}(x-\mu)\right)$
  - **Mahalanobis distance:** $(x-\mu)^T\Sigma^{-1}(x-\mu)$ — distance scaled by covariance. Accounts for correlations between features. Generalizes Euclidean distance. Critical for anomaly detection, clustering with non-spherical clusters.
- **Bayes' theorem:** $P(\theta|D) = \frac{P(D|\theta)P(\theta)}{P(D)}$ — the foundation of all probabilistic ML.
  - Prior $P(\theta)$: beliefs before seeing data.
  - Likelihood $P(D|\theta)$: how probable the data is given parameters.
  - Posterior $P(\theta|D)$: updated beliefs after seeing data.

### 18.5 Likelihood Estimation — From MLE to Bayesian

This is the core optimization framework of the course. Know the progression:

- **Maximum Likelihood Estimation (MLE):** $\hat{\theta}_{MLE} = \arg\max_\theta P(D|\theta)$.
  - Finds parameters that make the observed data most probable.
  - Point estimate. No uncertainty quantification. Can overfit.
  - *Example:* MLE for Gaussian mean = sample mean.

- **Maximum A Posteriori (MAP):** $\hat{\theta}_{MAP} = \arg\max_\theta P(D|\theta)P(\theta)$.
  - Adds a prior — regularization effect.
  - Still a point estimate. Still no full uncertainty.
  - *Example:* MAP with Gaussian prior on weights = L2-regularized regression (ridge).

- **Bayesian Estimation:** Compute the full posterior $P(\theta|D)$, not just the mode.
  - Predictions: $P(y_{new}|D) = \int P(y_{new}|\theta)P(\theta|D)d\theta$ — average over all plausible parameters weighted by their posterior probability.
  - Automatically handles uncertainty. Naturally prevents overfitting.
  - Challenge: the integral is often intractable → need approximations.

- **When to use each:**
  - MLE: large data, simple model, point prediction okay.
  - MAP: want regularization, still want point estimate.
  - Bayesian: need uncertainty quantification, small data, critical decisions.

### 18.6 Likelihood Approximations

- **Why approximate?** Full Bayesian posterior is often computationally intractable (integral over high-dimensional parameter space).
- **Gradient-based optimization:** Use gradient descent/ascent on the log-likelihood. For MLE/MAP with differentiable models.
  - Log-likelihood is easier: turns product into sum, more numerically stable.
- **Conjugate models:** Prior and posterior are in the same distribution family. When available, gives closed-form posterior update.
  - *Example:* Beta prior + Binomial likelihood → Beta posterior.
  - *Example:* Gaussian prior + Gaussian likelihood (known variance) → Gaussian posterior.
  - Elegant but limited — only for simple models with specific distribution pairs.

### 18.7 Unsupervised Methods — EM & Clustering

- **Expectation-Maximization (EM) algorithm:**
  - For models with latent (hidden) variables. Alternates between:
    - **E-step:** Compute expected value of the log-likelihood w.r.t. the current estimate of latent variables.
    - **M-step:** Maximize this expectation to update parameters.
  - Exact EM updates do not decrease the observed-data likelihood under the usual well-defined model assumptions. Convergence can be to a stationary point and need not produce a global maximum.
  - *Applications:* Gaussian Mixture Models (GMMs), HMMs, missing data problems.

- **Clustering methods:**
  - **k-means:** Hard assignment. Minimizes within-cluster squared Euclidean distances. It favors compact clusters under that metric; unequal densities or sizes can yield poor partitions. Sensitive to initialization.
  - **GMM with EM:** Soft assignment (each point has a probability of belonging to each cluster). Handles elliptical clusters of different sizes. More flexible than k-means.
  - **DBSCAN:** Density-based. Finds arbitrary-shaped clusters. Handles noise (outliers). Does not require specifying k. Parameters: ε (neighborhood radius) and minPts.
  - **Hierarchical clustering:** Builds a dendrogram. Agglomerative (bottom-up) vs. divisive (top-down). No need to pre-specify k — can cut dendrogram at desired level.

### 18.8 Ensemble Methods

- **Why ensembles?** Combining models can reduce variance or improve fit, depending on the learning method and error correlations. Improvement over a single model is not guaranteed; evaluate the combined model on held-out data.
- **Bagging (Bootstrap Aggregating):** Train multiple models on bootstrap samples of the data. Average predictions. Reduces variance.
  - *Example:* Random Forest = bagged decision trees + random feature subsets.
- **Boosting:** Sequentially train models, each focusing on errors of the previous. Reduces bias.
  - *Examples:* AdaBoost (reweights samples), Gradient Boosting (fits residuals), XGBoost/LightGBM (optimized implementations).
- **Stacking:** Train a meta-model on the outputs of base models. Learns the optimal way to combine them.

### 18.9 Autoencoder Models

- **Autoencoder:** Neural network trained to reconstruct its input. Architecture: encoder (compress) → bottleneck (latent representation) → decoder (reconstruct).
- **Why autoencoders?** Learn compact, meaningful representations of data without labels (unsupervised).
- **Types:**
  - **Undercomplete:** Bottleneck smaller than input. Forces learning salient features. Classic dimensionality reduction.
  - **Denoising:** Train to reconstruct clean input from corrupted version. Learns robust features.
  - **Variational Autoencoder (VAE):** Latent space is a probability distribution. Can generate new data by sampling from latent space. Combines autoencoders with variational Bayesian methods.
- **Applications:** Dimensionality reduction, anomaly detection (high reconstruction error = anomaly), data generation, pre-training for supervised tasks.

### 18.10 Exam Preparation — Key Themes

1. Walk through the MLE → MAP → Bayesian progression. What changes at each step? When would you choose each?
2. Explain EM intuitively. Why does it work? Give a concrete example (GMM).
3. Compare k-means, GMM, and DBSCAN — when would each fail?
4. Why do ensembles work? Relate to bias-variance tradeoff.
5. How does an autoencoder learn? What does the bottleneck force the network to do?

### 18.11 Literature

- C.M. Bishop: *Pattern Recognition and Machine Learning*, Springer, 2006. ([PDF](https://www.microsoft.com/en-us/research/uploads/prod/2006/01/Bishop-Pattern-Recognition-and-Machine-Learning-2006.pdf))
- M.P. Deisenroth, A.A. Faisal, C.S. Ong: *Mathematics for Machine Learning*, Cambridge University Press, 2020. ([Online](https://mml-book.github.io/))
- Zhang, Lipton, Li, Smola: *Dive into Deep Learning*, 2021. ([Online](https://d2l.ai/))

---

## Topic 19 — Scalable enterprise applications

**Official syllabus:** [Scalable Enterprise Applications.pdf](https://www.inf.elte.hu/dstore/document/227914/Scalable_Enterprise_Applications.pdf)  
**Course responsible:** Not specified in this short public description; consult the applicable semester's course listing.

**Verified syllabus scope:** Distributed application structure, transactional persistence, remote invocation and messaging, web applications/services, discovery, code mobility, grid computation, and cross-cutting behavior.

**Version note:** The syllabus uses historical technology examples, including Java EE, applets, and Jini. Study their architectural purpose and the technologies actually assigned in your course. Applets are obsolete; the [OpenJDK Applet API removal work](https://mail.openjdk.org/pipermail/client-libs-dev/2025-July/030640.html) confirms that this is historical material. [Jakarta EE's official tutorial](https://jakarta.ee/learn/docs/jakartaee-tutorial/current/) supplies a current reference for related enterprise concepts; it is supplementary, not a replacement course syllabus.

### 19.1 Multi-Tier Structure and Scaling

Separate responsibilities and deployment boundaries. A presentation, application, and persistence tier need not imply one machine per tier or one database for the entire enterprise.

- Vertical scaling changes resources of an instance; horizontal scaling adds instances. The application's state and coordination requirements determine whether extra instances help.
- Identify bottlenecks using workload and measurement. Faster application servers will not fix every database, contention, network, or downstream-service limit.
- Availability, throughput, response-time distribution, and resource cost are different objectives.
- A supposedly stateless front end may still depend on centralized sessions, locks, or storage. Explain the remaining shared state.

### 19.2 Persistence and Transactions

JDBC, JPA, and transaction-management mechanisms represent different layers of access and coordination. Define the unit of work and the consistency required by a business operation.

- Atomicity, consistency, isolation, and durability have precise meanings; the application must still encode valid business invariants.
- Isolation levels control which interactions between concurrent transactions are allowed. A transaction annotation alone does not specify every concurrency guarantee.
- Connection pools and caches affect capacity and resource reuse. They also introduce lifecycle and consistency concerns.
- A distributed transaction can couple participants and failure recovery. If an application uses compensating steps instead, define which effects can actually be compensated and what intermediate states are visible.

### 19.3 Remote Calls and Messaging

A remote call can fail after the server has performed its effect but before the response arrives. A retry can duplicate that effect. Explain timeouts, correlation, idempotency, and what the caller can infer from each response or failure.

Messaging decouples participants in time or execution, but delivery, ordering, acknowledgement, persistence, and consumer progress still need explicit contracts.

**Worked example:** Processing an order creates a database change and sends an event. If those actions are not atomically coordinated, a crash can leave the event missing or the state uncommitted. Describe a durable handoff/recovery design and consumer deduplication, then explain the failure cases it covers. Do not claim universal “exactly once” behavior without defining its boundary.

### 19.4 Web Applications and Web Services

The syllabus's servlet, JSP/JSF, and JAX-WS examples illustrate request processing, presentation, and service interfaces. Prepare the lifecycle, session/state management, serialization, and failure semantics relevant to the course implementation.

Distinguish an HTTP API contract from a database schema or internal object interface. Versioning, authorization, validation, and compatibility become important when clients are independently deployed.

Remote-object and message-based approaches may expose different coupling. Compare them against concrete requirements rather than assuming that distributing an object graph provides transparent local semantics.

### 19.5 Discovery, Mobility, Grid Computing, and Aspects

- Component lookup separates a logical service identity from a concrete location or implementation. Naming, discovery, and health information can become stale or unavailable.
- Code mobility transfers executable behavior rather than only data. State its trust, compatibility, and resource-control requirements; browser applets are a historical example, not a modern deployment recommendation.
- Grid computation coordinates resources for demanding workloads. Discuss task partitioning, data placement, scheduling, and partial failures; it is not just another name for every web-service deployment.
- Aspect-oriented techniques isolate cross-cutting behavior through specified join points and advice. Explain how implicit interception affects control flow, testing, and debugging.

### 19.6 Oral Practice and Thesis Connections

1. Diagnose a bottleneck and explain which scaling change addresses it.
2. Trace transaction and recovery behavior across persistence and messaging.
3. Explain why a remote timeout does not prove that an operation was not executed.
4. Compare remote invocation and messaging for a specific business workflow.
5. Explain discovery, cross-cutting behavior, and the limitations of a historical technology example.

### 19.7 Literature

The official description cites the Java EE tutorial and Foster's grid-computing text. Match course examples to their assigned versions, using contemporary documentation to distinguish enduring principles from historical APIs.

---

<a id="topic-1-advanced-software-technology"></a>

## Appendix A — Advanced Software Technology

**Course responsible:** Dévai Gergely, PhD
**Official syllabus:** [Advanced Software Technology.pdf](https://www.inf.elte.hu/dstore/document/227889/Advanced%20software%20technology.pdf)

**Supplementary status:** Preserved from the original guide. ELTE lists this course in the specialization syllabus index, but it is not one of the 19 entries in the supplied Neptun dropdown. Its inclusion here does not establish final-exam selection eligibility.

### A.1 Overview — The Startup-Mindset Course

This course is unusual: it simulates a **startup-like team environment** where you take an idea from concept to execution. You learn a balanced mixture of theoretical knowledge, technical skills, and **soft skills** for running a software development project. The goal is to make you capable of serving as a **manager, architect, or lead developer** in a real software project.

### A.2 Idea Forming & MVP Drafting

- **Minimum Viable Product (MVP):** The smallest version of a product that can be released to early customers to validate core assumptions with minimal effort.
  - *Why MVP?* Avoids building features nobody wants. Tests the riskiest assumptions first.
- **Innovation mindset vs. product mindset:**
  - Innovation: exploring the unknown, validating hypotheses, pivoting when needed.
  - Product: scaling what works, optimizing, maintaining quality.
- **Lean Startup methodology:** Build → Measure → Learn cycle. Every feature is an experiment.
- **Key skill:** Drafting an MVP spec — what is the single core value proposition? What can be cut?

### A.3 Project Execution & Development Methodologies

- **Agile vs. Waterfall:**
  - Waterfall: sequential phases (requirements → design → implementation → testing → deployment). Works when requirements are known and stable. Fails when they change.
  - Agile: iterative, incremental. Embraces change. Delivers working software frequently.
- **Scrum:** Roles (Product Owner, Scrum Master, Development Team), artifacts (Product Backlog, Sprint Backlog, Increment), ceremonies (Sprint Planning, Daily Scrum, Sprint Review, Retrospective).
- **Kanban:** Visual workflow management. Focus on limiting WIP (Work In Progress), continuous delivery, no fixed sprints.
- **Choosing a methodology:** Depends on team size, project uncertainty, stakeholder involvement, regulatory constraints. Know the tradeoffs.
- **Retrospectives:** Regular team reflection on what went well, what didn't, and what to change. *Critical for continuous improvement.*

### A.4 Tools & Techniques for Sustainable Processes

- **Version control:** Git — branching strategies (Git Flow, GitHub Flow, trunk-based development). Why branching strategy matters for team coordination.
- **Continuous Integration / Continuous Delivery (CI/CD):**
  - CI: every commit triggers automated build + test. Catches integration problems early.
  - CD: every passing build is automatically deployable. Reduces release risk.
  - Pipeline stages: build → unit test → integration test → staging deploy → production deploy.
- **Automated testing:** Unit tests, integration tests, end-to-end tests. Test pyramid concept.
- **Code review:** Peer review before merge. Catches defects, spreads knowledge, enforces standards.
- **Documentation:** What to document (architecture decisions, APIs, setup) vs. what not to (obvious code). "Working software over comprehensive documentation" — but not *no* documentation.

### A.5 Creating Maintainable Architecture

- **Software architecture defined:** The set of significant design decisions about the organization of a software system — structural elements, their interfaces, behavior, and composition.
- **Architectural patterns (know when to use each):**
  - **Layered (n-tier):** Presentation → Business Logic → Data Access. Simple, well-understood. Can become rigid.
  - **Microservices:** Independent, loosely coupled services. Scalable, deployable independently. Adds operational complexity.
  - **Event-driven:** Components communicate via events. Decoupled, scalable. Harder to reason about flow.
  - **Hexagonal (Ports & Adapters):** Core business logic isolated from infrastructure. Testable, swappable infrastructure.
- **Design principles:**
  - **SOLID:** Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.
  - **Separation of concerns:** Each module has a single, well-defined responsibility.
  - **Loose coupling, high cohesion:** Modules should depend minimally on each other but be internally focused.
- **Design Patterns (Gamma et al.):** Factory, Singleton, Observer, Strategy, Decorator, Adapter, Facade. Know their intent, structure, and when *not* to use them.
- **Technical debt:** The implied cost of rework caused by choosing an easy solution now instead of a better approach that would take longer. Must be managed consciously — not all debt is bad, but it must be tracked and paid down.
- **Refactoring:** Restructuring existing code without changing its external behavior. Driven by code smells.

### A.6 Achieving Innovation Potential

- **Innovation ≠ invention.** Innovation is creating *value* from new ideas. Invention is creating something new.
- **Disruptive vs. sustaining innovation** (Christensen): Disruptive creates new markets/value networks; sustaining improves existing products for existing customers.
- **Measuring innovation:** Not just features shipped — validated learning, customer adoption, business impact.
- **Team dynamics for innovation:** Psychological safety, diverse perspectives, autonomy with alignment.

### A.7 Exam Preparation — Key Themes

For the oral exam, be prepared to discuss:
1. How would you structure a greenfield project from idea to first release? Justify your methodology choice.
2. Compare at least two architectural patterns — when would you choose one over the other?
3. What makes code "maintainable"? Give concrete examples of good vs. bad practices.
4. How do CI/CD pipelines reduce risk? What would happen without them?
5. Relate to your thesis: what methodology/architecture did you use and why?

### A.8 Literature

- R. C. Martin: *Clean Code: A Handbook of Agile Software Craftsmanship*, Prentice Hall, 2008.
- J. Humble, D. Farley: *Continuous Delivery*, Addison-Wesley, 2010.
- E. Gamma, R. Helm, R. Johnson, J. Vlissides: *Design Patterns: Elements of Reusable Object-Oriented Software*, Addison-Wesley, 1994.
- L. Bass, P. Clements, R. Kazman: *Software Architecture in Practice*, 3rd ed., Addison-Wesley, 2012.

---

## Exam Strategy — MSc Level

### What to Demonstrate

- **Conceptual precision:** Define terms and separate closely related notions. For example, distinguish partial from total correctness, throughput from latency, and deadlock freedom from individual progress.
- **Reasoned choices:** Give the assumptions under which a technique applies, explain alternatives, and identify when the technique fails.
- **Mathematical and technical depth:** Derive an important recurrence, invariant, probability relationship, model objective, or resource argument instead of reciting a formula without interpretation.
- **Evidence:** Support a thesis connection with a design artifact, proof, experiment, test, or measured result. State which claims the evidence can actually establish.
- **Clear oral explanation:** Practice a concise definition, a worked example, and a deeper justification for each important area. The questions in this guide are practice prompts, not predictions of the committee's choices.

### Cross-Subject Connections

| Connection | Prepare to explain |
| --- | --- |
| Design and analysis of algorithms ↔ Advanced Algorithms | General paradigms and performance proofs versus flow/cut/matching reductions, certificates, and approximation bounds. |
| Theory of programming ↔ Formal semantics | Program specification and correctness versus mathematical definitions of language behavior and equivalence. |
| Design of Distributed System ↔ Analysis of distributed systems | Distributed-program safety/progress and verified composition versus Petri-net/process-algebra models and analysis. |
| Advanced Java programming ↔ Scalable enterprise applications | Language/runtime and API contracts versus transaction, persistence, remote-call, and messaging behavior in distributed applications. |
| Introduction to Data Science ↔ Machine Learning ↔ Methods and tools for AI applications | Data/process and evaluation foundations, learner mechanisms/tuning, and statistical/probabilistic model mathematics. |
| Project Management ↔ Software quality and testing | Scope, schedule, risk, and delivery commitments supported by test evidence and quality criteria. |
| Complex information systems ↔ Service Science | Enterprise process/data integration versus service systems, stakeholder value, and measurable outcomes. |
| Functional Languages ↔ Formal semantics ↔ Theory of programming | Typed functional structure, equational/semantic reasoning, and explicit correctness obligations. |
| Introduction to Computer Security ↔ Enterprise and distributed subjects | Trust boundaries, authorization, data integrity, and failure behavior throughout the design. |

### Final Preparation Checklist

- [ ] My chosen subjects match the exact selectable entries and the applicable registration instructions.
- [ ] I have the relevant syllabus and lecture version for each chosen subject.
- [ ] I can cover every relevant syllabus area, not only the examples used in this guide.
- [ ] I can work through at least one nontrivial example and explain its assumptions.
- [ ] I can distinguish a theorem/proof from a measurement, test, or plausible intuition.
- [ ] I can explain how each subject connects to my thesis without forcing an unrelated connection.
- [ ] I have rehearsed questions that change an assumption or ask for a counterexample.
- [ ] I have checked the current semester's examination procedure and timing.

---

## Source and Maintenance Notes

- **Subject names/order:** Student-supplied raw Neptun dropdown, supplied to the supervisor on 2026-10-08; 19 distinct names after removing the two placeholders. No aliasing or deduplication merges the two algorithm subjects or the two distributed-systems subjects.
- **Syllabus authority:** Direct documents linked from the [ELTE Software Architecture MSc 2022 index](https://www.inf.elte.hu/th-tematikak-programtervezo-informatikus-msc-2022-szoftvertechnologia-softvare-architecture-specializacio), plus the explicitly identified older Advanced Java description. The Principles of artificial intelligence and Service Science entries use the revisions effective from September 2025.
- **Course versus final examination:** A syllabus's “Requirements and evaluation” section describes that course's assessment. It should not be silently transferred to the degree's final-examination procedure.
- **Supplementary readings:** Primary technical references linked in the notes help explain concepts; they do not establish additional mandatory ELTE syllabus topics.
- **Preserved chapters:** Their core notes remain in this file. A few overbroad mathematical statements are qualified where needed; the ISO quality-model discussion identifies its edition.
- **Maintenance:** This is a dated guide. Recheck the current faculty sources, the applicable semester's teaching materials, and the student's actual Neptun form before relying on it for registration or examination preparation. A newer applicable official requirement takes precedence.
