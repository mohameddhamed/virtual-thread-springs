# Spring Boot MVC Rendszerek Migrációja Java 21 Virtuális Szálakra: Architektúra, Kockázatok és Mérnöki Irányelvek

**Szerző:** Hamed Mohamed  
**Képzés / Szakirány:** Okleveles informatikus (MSc) — Szoftverarchitektúra szakirány  
**Intézmény:** Eötvös Loránd Tudományegyetem (ELTE), Informatikai Kar, Budapest  
**Témavezetők:**  
- Dr. habil. Kozsik Tamás (egyetemi docens, tanszékvezető, Programozási Nyelvek és Fordítóprogramok Tanszék, ELTE)  
- Gregory Reynolds Morse (külső konzulens / mesteroktató, ELTE)  
**Esemény:** ELTE IK Kari TDK Konferencia 2026 Ősz / 38. OTDK Informatikatudományi Szekció  
**Nyelv:** Magyar  

---

### Kivonat

A vállalati Java rendszerek terhelésnövekedése miatt a fejlesztők széles körben vezetik be a Java 21 virtuális szálakat (Project Loom, JEP 444), bízva abban, hogy a szálmultiplexelés automatikusan felszámolja a szűk keresztmetszeteket. Ez az iparági Ütemezhetőségi Tévedés (Schedulability Fallacy) azonban elrejti, hogy a virtuális szálak nem oldják fel az alkalmazásszintű sorosítást, a kapcsolatkészlet korlátait és a natív hívások alatti hordozószál-kiéheztetést. Rendszerszintű elemzés nélkül a migrációk diagnosztikai vakfoltokhoz és teljesítményösszeomláshoz vezethetnek.

A jelenségek feltárására egy Spring Boot 3.5.12 MVC demonstrációs rendszert fejlesztettünk, amelyet 125 fizikai mérésnek vetettünk alá nyolc független kísérleti rétegben, 504 hitelesített fájlt (~966 MB) generálva SHA-256 ellenőrzés mellett. A zárt hurkú k6 terhelést egyetlen hordozószálra korlátozott (parallelism=1) és nyolcszálas környezetben vizsgáltuk. A többdimenziós telemetria folyamatos Java Flight Recorder (JFR) eseménykövetést (jdk.VirtualThreadPinned), operációs rendszer szintű folyamatfigyelést és kétablakos tranziens/egyensúlyi kiértékelést alkalmazott.

A szerző önálló kutatása feltárta, hogy a synchronized kiváltása ReentrantLock primitívvel megszüntette a JFR rögzítési eseményeket (108-ról 0-ra), de az átvitel változatlan maradt (1.956 vs. 1.967 req/s), igazolva, hogy a hordozó felszabadítása nem lépi át az Amdahl-féle sorosítási plafont (mu ~ 2.0 req/s). A blokkoló natív Java Native Interface (JNI) hívások némán lefoglalják a hordozószálat Mach várakozásban alacsony processzor-kihasználtság (1.04%) és nulla JFR esemény mellett. A perzisztencia-kísérlet igazolta, hogy a szálak lekapcsolódnak, ám az átvitelt a készletméret köti gúzsba (X = K / T_hold).

A virtuális szálak bevezetése nem egyszerű futtatókörnyezeti beállítás, hanem felelős kapacitástervezést igénylő architekturális migráció. A szerző felállította a Háromszintű Párhuzamossági Taxonómiát, öt kötelező érvényű tervezési szabályt, négy refaktorálási mintát és egy döntési fát. A legfontosabb mérnöki követelmények: a kérések explicit korlátozása (bulkheading), a blokkoló monitorok cseréje, a natív hívások elkülönített platform-szálkészletbe zárása, valamint a kapcsolatkészlet méretezése a háttérkapacitás alapján.

---

**Kulcsszavak:** Project Loom, Szálrögzítés, Hordozó-kiéheztetés, Java Flight Recorder, Kapcsolatkészlet-méretezés
