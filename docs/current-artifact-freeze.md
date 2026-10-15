# Current Artifact Freeze Record

**Recorded:** 2026-10-15  
**Repository HEAD at recording:** `1ccb617b6beecb250e534d758d4f0eb1ea67e2d2`  
**Working tree:** dirty; the documentation and experimental changes listed by
`git status` are not committed

This is a working freeze record for the Checkpoint 4 package. It identifies
the state that was inspected; it is not a claim that the repository has
already been published or that every historical artifact belongs to this
revision.

## Runtime and application identity

| Item | Current value |
|---|---|
| Java | OpenJDK 21.0.8, Azul Zulu21.44+17-CA |
| Java target | 21 |
| Spring Boot | 3.5.12 |
| Application version | `0.0.1-SNAPSHOT` |
| Primary OS | macOS, Apple Silicon, 8 logical CPUs |
| Primary database | H2 for local primary runs |
| Extension database | PostgreSQL 15 Alpine in Docker |
| Load generator | k6, captured in run manifests for orchestrated runs |
| Evidence dataset | 76 trial-level records after normalization |

## Completed validation

```text
./mvnw test                                      PASS
python3 scripts/normalize_evidence.py           PASS
python3 scripts/validate_normalized_evidence.py PASS (validated 76 records)
git diff --check                                 PASS
docker compose config                            PASS previously
docker compose down                              PASS after PostgreSQL runs
```

## Current raw PostgreSQL artifacts

The six valid PostgreSQL pool-sensitivity artifacts were checked for zero
failed HTTP points:

| Artifact | SHA-256 |
|---|---|
| `results/docker-pg-orders-pool1-trial1.json` | `69a4bb99299c2560ea4bcdce29a481e9f9dfc7da9896bfad2dcd7fef3fc2bae3` |
| `results/docker-pg-orders-pool1-trial2.json` | `955598b319c5026e08d39e7af729b38d24c424aca355a45ee58766fabb541a2f` |
| `results/docker-pg-orders-pool1-trial3.json` | `0f98be430b27e9d9679c590c8133073eca5fb041ab75a42b44217c8e34ea7653` |
| `results/docker-pg-orders-pool10-trial1.json` | `03f4658f44b8dfb905159e9b700be7295ada35e1859cbbaa3a889391bfb5ac04` |
| `results/docker-pg-orders-pool10-trial2.json` | `f04dacc6dcd9864bd5b350e20718ed1842cb1b096c9c3e7d4fe067045b920ad8` |
| `results/docker-pg-orders-pool10-trial3.json` | `d7a721e9c68ab0fd4982c822a1e1fe667406c709d6c9fdb665d667be44659a5f` |

These files contain valid k6 runs with zero HTTP failures. They are separate
from the H2 and Java 21 primary synchronization evidence and do not carry
PostgreSQL-specific JFR conclusions.

## Freeze actions still required

1. Commit or otherwise record the exact source revision used for the final
   thesis evidence package.
2. Map every retained Java 21/JNI/JDK-boundary JFR and k6 artifact to its
   manifest, source revision, configuration, and extraction output.
3. Remove or label any superseded narrative table that is not traceable to the
   frozen package.
4. Rebuild the thesis tables and presentation from the frozen evidence only.
5. Store the final signed AI declaration and required interaction-log evidence
   outside the code/results claim chain, with appropriate privacy handling.
