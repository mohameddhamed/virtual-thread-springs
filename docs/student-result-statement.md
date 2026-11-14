# Student-Result Statement / Hallgatói Eredménykimutatás

**Governing Call & Regulations:**
- 38th National Scientific Students' Associations Conference (OTDK) Information and Communication Technology Section
- ELTE IK TDK Conference (IT Science Section 2026)
- ELTE IK MSc Thesis Evaluation Standards & Dean's Directive 1/2026

---

### Student and Document Metadata

* **Author / Candidate:** Hamed Mohamed
* **Neptun Code:** `DG1EWF`
* **Academic Programme:** Computer Science MSc — Software Architecture Specialization
* **Document Title:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*
* **Approved Request Identifier:** `IK-ZVMSC_EN2_155` (Approved: 2026.10.27)
* **Supervisory Team:**
  * **Internal Faculty Supervisor:** Dr. habil. Tamás Kozsik (Associate Professor, Head of Department of Programming Languages and Compilers, ELTE)
  * **External Thesis Advisor / Research Supervisor:** Gregory Reynolds Morse (`morse@inf.elte.hu`, Lecturer and MSc in Computer Science, ELTE)
* **Final Examination Subjects:** *Project Management*, *Advanced Java programming*, *Scalable enterprise applications*
* **Submission Date / Term:** Autumn Semester 2026/2027

---

## 1. Magyar Nyelvű Hallgatói Eredménykimutatás (Official Hungarian Statement)

> **Karakterszám-ellenőrzés:** 3 835 karakter (szóközökkel együtt; szigorúan megfelel az OTDK Informatikatudományi Szekció által előírt 2 000–4 000 karakteres terjedelemnek).

A diplomamunka és a kapcsolódó TDK-dolgozat szerzője, Hamed Mohamed (Neptun-kód: DG1EWF) kijelenti, hogy a kutatásban bemutatott elméleti következtetések, szoftveres mérőrendszerek, kísérleti eredmények és mérnöki iránymutatások a saját önálló szellemi és technikai munkájának eredményei, a témavezetők (Dr. habil. Kozsik Tamás és Gregory Reynolds Morse) szakmai irányítása mellett.

A hallgató önálló tudományos és mérnöki eredményei az alábbi pontokban foglalhatók össze:

1. Demonstrációs és mérési infrastruktúra megtervezése és megvalósítása: A hallgató önállóan tervezte és implementálta a Spring Boot 3.5.12 MVC alapú kísérleti rendszert (virtual-threads-demo), beleértve a beágyazott Tomcat 10.1.52 kiszolgálót, a HikariCP 6.3.3 kapcsolatkészletet, a ThreadLocal kontextuskezelést, valamint a C nyelven írt natív dinamikus könyvtárat (libnativeblocking.dylib). A teljes mérési környezetet független JUnit 5 integrációs tesztekkel látta el (8/8 sikeres lefutás).

2. 125 fizikai mérés végrehajtása és 8 kísérleti réteg particionálása: A hallgató nyolc egymástól független kísérleti réteget (strata) alakított ki és hajtott végre zárt hurkú k6 terhelési profillal. A mérések során 504 nyers állományt (~966 MB) rögzített (k6 JSON streams, JFR bináris nyomkövetések, OS folyamattelemetria), amelyeket SHA-256 ellenőrzőösszegekkel fagyasztott be a docs/evidence-freeze/ könyvtárban a nyílt tudomány elvei szerint.

3. Kétablakos kiértékelési szabvány és a sorosítási plafon bizonyítása: A hallgató azonosította a k6 bemelegedési szakaszának torzító hatását, és bevezette a kétablakos (whole-run vs. steady-state hold) elemzési módszertant. Bizonyította, hogy a Java 21 alatt a synchronized blokk ReentrantLock-ra cserélése megszünteti a hordozószál-rögzítést (108-ról 0-ra), de az átvitel változatlan marad (1.956 vs. 1.967 req/s), igazolva az Amdahl-törvény érvényesülését (mu ~ 2.0 req/s).

4. OpenJDK HotSpot forráskód-audit: A hallgató önállóan elemezte a HotSpot C++ forráskódját (continuationFreeze.cpp, continuation.cpp, VirtualThread.java), feltárva a freeze_result állapotgépet és az ObjectMonitor általi szálrögzítés alacsony szintű mechanizmusát, valamint annak feloldását a JDK 24 JEP 491 tervezetében.

5. A JNI natív hordozó-kiéheztetés és diagnosztikai vakfolt felfedezése: A hallgató kimutatta, hogy a blokkoló natív rendszerhívások (POSIX nanosleep) a hordozószálat operációs rendszer szintű Darwin/Mach várakozási állapotba kényszerítik, miközben a CPU-kihasználtság minimális (~1.04%), és a Java Flight Recorder egyetlen jdk.VirtualThreadPinned eseményt sem rögzít, rejtett skálázódási kockázatot képezve.

6. Faktoriális perzisztencia-abláció (Stratum 8) és a Lefelé Tolódó Szűk Keresztmetszet Törvénye: A hallgató feltárta az /orders korábbi konstrukciós hibáját, és megtervezte a kétkezeléses faktoriális kísérletet. Igazolta, hogy a kapcsolatot blokkoló hívás alatt tartó virtuális szálak rögzítés nélkül lekapcsolódnak a hordozóról, ám a szűk keresztmetszet teljes egészében a HikariCP kapcsolatkészletbe tolódik át, ahol az átvitelt szigorúan a Little-törvény diktálta kapacitás határozza meg (X = K / T_hold).

7. Háromszintű Párhuzamossági Taxonómia és migrációs keretrendszer: A hallgató rendszerezte az eredményeket a Háromszintű Taxonómiába (I. szint: Virtuális Szál Ütemezhetőség; II. szint: Alkalmazás Kölcsönös Kizárás; III. szint: Háttér Kapacitáskorlát), formalizált 5 kötelező architekturális szabályt, 4 helyességmegőrző refaktorálási mintát és egy determinisztikus döntési fát a mérnökök számára.

A hallgató igazolja a Dékáni Utasítás 1/2026 előírásainak teljes körű betartását: mesterséges intelligencia eszközöket kizárólag nyelvi stilizálásra és kódvázlatok gyorsítására vett igénybe pontszerű közzététel mellett, az összes kísérleti adat, kód és tudományos konklúzió saját önálló munkája.

---

## 2. English Student-Result Statement

> **Character Count Verification:** 3,858 characters (including spaces; strictly compliant with the official 2,000–4,000 character requirement).

The author of this MSc thesis and accompanying TDK paper, Hamed Mohamed (Neptun: DG1EWF), declares that the theoretical formulations, experimental testbeds, benchmark executions, empirical discoveries, and engineering guidelines presented in this work represent his own independent intellectual and technical contributions, conducted under the academic guidance of his supervisors (Dr. habil. Tamás Kozsik and Gregory Reynolds Morse).

The student's independent scientific and engineering contributions comprise seven verified areas:

1. Design and Implementation of the Empirical Testbed: The student independently designed and implemented the full Spring Boot 3.5.12 MVC benchmarking application (virtual-threads-demo), including Tomcat 10.1.52 virtual thread integration, HikariCP 6.3.3 connection pooling, ThreadLocal request context propagation, and a custom native POSIX C shared library (libnativeblocking.dylib). The system is validated by an automated JUnit 5 test suite executing with 8/8 passing assertions across all boundaries.

2. Execution and Forensic Auditing of 125 Benchmark Trials across 8 Strata: The student structured and executed 125 physical benchmark trials across eight non-overlapping experimental strata under closed-loop k6 load profiles. He captured and cataloged 504 raw artifacts totaling ~966 MB (k6 JSON streams, JFR binary recordings, and OS process telemetry), freezing the normalized corpus in docs/evidence-freeze/ with cryptographic SHA-256 checksums under open-science reproducibility standards.

3. Formulation of Dual-Window Analysis and Proof of the Serialization Ceiling: The student identified the distorting effects of benchmark warm-up ramps and instituted the dual-window analysis standard (whole-run vs. steady-state hold). He proved that under Java 21, refactoring from synchronized to ReentrantLock eliminates carrier pinning events (108 to 0) while producing identical throughput (1.956 vs. 1.967 req/s), demonstrating that carrier unpinning cannot overcome Amdahl's serialization ceiling (mu ~ 2.0 req/s).

4. Low-Level HotSpot C++ Source Audit: The student conducted an independent source audit of OpenJDK HotSpot (continuationFreeze.cpp, continuation.cpp, VirtualThread.java), identifying the freeze_result state machine and the exact low-level pinning mechanisms of ObjectMonitor, contrasting them with the unpinning architecture introduced in JDK 24 JEP 491.

5. Discovery of Silent JNI Carrier Starvation and Diagnostic Blind Spots: The student proved that blocking native system calls (POSIX nanosleep) capture carrier threads in Darwin/Mach OS wait states while CPU utilization remains minimal (~1.04%), with Java Flight Recorder emitting zero jdk.VirtualThreadPinned events, demonstrating an observability gap in enterprise monitoring.

6. Factorial Persistence Ablation (Stratum 8) and the Bottleneck Shift Law: The student uncovered the pre-acquisition delay flaw in the legacy /orders baseline and designed the Two-Treatment Factorial Persistence experiment. He demonstrated that virtual threads holding connections unmount cleanly without carrier pinning, but queue formation shifts into the HikariCP pool, where throughput is strictly constrained by Little's Law (X = K / T_hold).

7. The Three-Tier Concurrency Taxonomy and Migration Framework: The student synthesized the research findings into the Three-Tier Concurrency Taxonomy (Tier I: Schedulability; Tier II: Mutual Exclusion; Tier III: Backend Capacity), formalizing 5 mandatory architectural rules, 4 correctness-preserving refactorings, and a migration decision tree.

Compliance with Dean's Directive 1/2026 is fully observed: generative AI was used solely for prose polishing and script templates with point-of-use disclosure, while all empirical data, source code, and scientific conclusions are the student's independent work.

---

### Authorship and Integrity Declaration

I hereby confirm that the above statement reflects the verifiable reality of my research and thesis development. All reused concepts, libraries, and prior publications have been attributed in the bibliography, and point-of-use disclosures have been embedded in each chapter in strict compliance with ELTE regulations.

Budapest, 2026.11.14  
Student Signature: **Hamed Mohamed** (`DG1EWF`)
