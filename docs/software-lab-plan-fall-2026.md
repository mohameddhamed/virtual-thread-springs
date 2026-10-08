# Software Lab Plan

## Spring Boot MVC and Java 21 Virtual Threads

**Student:** Mohamed Hamed (DG1EWF)
**Semester:** Fall 2026
**Subject:** Software Lab / Practical Software Engineering Work
**Related thesis:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*

## 1. Purpose

This plan defines the practical software work to be completed during the semester. The thesis consultation subject is the priority and contains the formal research-plan, bibliography, and thesis-methodology work. This parallel software-lab subject will document tangible engineering progress from the same project without duplicating the full thesis process.

The objective is to maintain a clear, verifiable record of implementation, measurement, analysis, and documentation. Each progress item will produce a small inspectable artifact: source-code changes, tests, benchmark data, JFR output, analysis notes, or a revised project document.

## 2. Existing project foundation

The project already contains:

- A Spring Boot MVC demonstration application targeting Java 21.
- Three workload paths: `/orders`, `/payments`, and `/products`.
- Deliberately controlled blocking, synchronization, request-context, and database-resource scenarios.
- Platform-thread, naive Virtual-Thread, and refactored Virtual-Thread configurations.
- k6 load-test scripts and Java Flight Recorder integration.
- Docker and Docker Compose configuration.
- Historical benchmark outputs and JFR recordings.
- Documentation describing the software architecture, migration risks, and preliminary results.

The historical benchmark documents are treated as pilot material until each result is mapped to a source commit, exact configuration, raw k6 output, and JFR recording. This keeps the software-lab progress record honest while the thesis evidence is being validated.

## 3. Work objectives

During the semester I will:

1. Maintain and improve the Java 21 Spring Boot demonstration application.
2. Add or improve tests for endpoint behavior and synchronization correctness.
3. Make benchmark execution and configuration reproducible.
4. Re-examine Virtual Thread pinning and blocking-resource behavior using JFR and k6.
5. Record measurements and observations in short progress documents.
6. Produce a final software-lab package that can support the later thesis.

The work is a controlled software-engineering case study, not a claim that the application represents every production Spring system.

## 4. Progress schedule

Progress meetings are expected on Thursdays, approximately every second week. Dates may be adjusted by the instructor; the artifact for each period remains the important requirement.

| Meeting / target date | Practical activity | Tangible evidence |
|---|---|---|
| 24 September 2026 | Reconfirm the application architecture and freeze the current baseline | Updated architecture note, repository status, runtime/dependency inventory |
| 8 October 2026 | Improve reproducibility and test coverage | Run-manifest template, endpoint smoke tests, synchronization/mutual-exclusion test |
| 22 October 2026 | Execute or re-execute controlled baseline measurements | Raw k6 output, selected JFR recording, benchmark-run note |
| 5 November 2026 | Analyse Java 21 Virtual Thread pinning and blocking behavior | JFR extraction output, stack-trace classification, short findings memo |
| 19 November 2026 | Compare legacy and refactored synchronization behavior | Refactoring diff, correctness-test result, comparison table |
| 3 December 2026 | Examine request context and finite database-resource risks | `ThreadLocal` lifecycle note, pool/configuration observation, limitation note |
| 17 December 2026 | Consolidate software results and migration guidance | Updated results document, migration checklist, reproducibility instructions |
| Final submission period | Prepare the software-lab submission package | This plan, progress notes, selected code/results links, and final summary |

If a measurement cannot be reproduced because of an environment or tooling problem, the progress artifact will document the attempted procedure, the observed limitation, and the next corrective action rather than presenting an unsupported result.

## 5. Measurement and documentation approach

The main software configurations are:

1. Platform threads with the legacy synchronized payment path.
2. Java 21 Virtual Threads with the same legacy synchronized path.
3. Java 21 Virtual Threads after replacing the intrinsic synchronization with a compatible lock.

The main measurements are:

- request throughput;
- p50, p95, and p99 latency where available;
- HTTP errors, timeouts, and completed requests;
- JFR `jdk.VirtualThreadPinned` events and stack traces;
- selected CPU, memory, database-pool, and application observations;
- correctness and mutual-exclusion behavior after refactoring.

The existing mixed endpoint workload will be useful for observing whole-application interference. Endpoint-isolated runs will be preferred when the purpose is to identify the cause of a specific behavior. A result will be labelled preliminary when it is based on an unmapped historical run or insufficient repetitions.

## 6. Expected final outputs

By the end of the semester, the software-lab work should provide:

- a maintained and runnable Java 21 Spring Boot project;
- a documented benchmark command and configuration;
- selected raw k6 and JFR evidence;
- short progress notes showing what was implemented, measured, researched, or learned;
- a comparison of platform, naive Virtual-Thread, and refactored Virtual-Thread behavior;
- a practical migration checklist;
- a reproducibility note explaining how another student can run the application and benchmark;
- a final summary suitable for submission in the software-lab subject.

These outputs will also provide implementation and measurement material for the thesis consultation subject, while the two subjects remain administratively separate.

## 7. Scope control

The minimum successful scope is the maintained demonstration application, reproducible execution, documented measurements, and a final software-engineering summary. PostgreSQL sensitivity tests, a complete factorial experiment, and testing on later JDK versions are optional extensions. They will not be allowed to prevent the regular bi-weekly progress submissions.

The thesis consultation remains the higher-priority activity. Software-lab documents will therefore be concise and evidence-based: each submission will state what changed, what was run or researched, what artifact was produced, and what remains uncertain.
