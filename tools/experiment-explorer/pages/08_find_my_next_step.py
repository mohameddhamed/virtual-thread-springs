"""A short, goal-first route into Chapter 7's migration guidance."""
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st

from lib.presentation import page_heading

from lib.migration_data import CORE_RULES


# Each answer gives one next action, a verification check, and a chapter reference.
PATHS = {
    "Free up carriers": ("Where does the request wait?", {
        "Inside a Java monitor": (1, "Inspect the lock scope", "Check for blocking I/O and carrier starvation affecting unrelated requests. On Java 21, consider Pattern 1 when both are present. Preserve mutual exclusion. On Java 24+, check residual stalls after JEP 491."),
        "Inside a native call": (2, "Bound the native work", "Inspect the native implementation. Offload materially blocking or unpredictable calls to a bounded platform-thread pool. Validate duration and concurrency before keeping a call inline."),
        "I can’t tell yet": (4, "Capture the wait", "Pair JFR stacks with OS thread and CPU telemetry during the same interval. Native blocking can leave the pin-event count at zero."),
    }),
    "Reduce database waits": ("What does the pool show?", {
        "Pending requests climb": (3, "Limit concurrent database work", "Measure connection hold time, active and pending connections, and database headroom. Set pool size and acquisition timeout against database capacity and the service latency target."),
        "The pool is mostly idle": (3, "Locate the delay", "Trace when the request checks out its connection. A delay before checkout can leave the pool idle. Inspect query time and the surrounding request path before resizing."),
    }),
    "Reduce request memory": ("Which runtime carries your request context?", {
        "Java 21 LTS": (5, "Clean up request context", "Pair ThreadLocal.set() with remove() in a finally block. Inspect a heap profile under representative concurrency for retained request payloads."),
        "Java 25 or newer": (5, "Evaluate Scoped Values", "Try Scoped Values for immutable, lexically scoped request context. Audit remaining ThreadLocal lifecycles and verify retention with a heap profile."),
    }),
    "Find a starting point": ("What have you already checked?", {
        "Dependency versions are unknown": (0, "Inventory the dependencies", "Run mvn dependency:tree and compare resolved driver and library versions with Table 7.1. Inspect the affected call paths before choosing an upgrade."),
        "Versions are known, telemetry is missing": (4, "Establish an observable baseline", "Enable continuous JFR and companion OS metrics. Compare full-run and hold-window measurements under the same workload."),
        "I have versions and telemetry": (0, "Walk the request path", "Open Triage and follow one request through all six checks. A single request can encounter a driver, a lock and a connection pool."),
    }),
}


def open_triage() -> None:
    st.session_state.migration_section = "Triage"
    st.switch_page("pages/07_migration_guidelines.py")


def render_interview() -> None:
    page_heading("08", "Find My Next Step")
    st.caption("Pick one concern for one request path. You can change either answer.")
    st.subheader("What do you want to do?")
    goal = st.pills("Choose a goal", list(PATHS), label_visibility="collapsed")
    if not goal:
        return
    question, answers = PATHS[goal]
    st.subheader(question)
    answer = st.pills("Choose what fits", list(answers), key=f"interview_{goal}", label_visibility="collapsed")
    if not answer:
        return
    rule_id, title, action = answers[answer]
    with st.container(border=True):
        st.caption(f"{goal} → {answer}")
        st.subheader(title)
        st.write(action)
        if rule_id:
            rule = CORE_RULES[rule_id]
            st.caption(f"Chapter 7 · Rule {rule_id} · {rule.name} · {rule.claim_id}")
        else:
            st.caption("Chapter 7 · Table 7.1" if answer.startswith("Dependency") else "Chapter 7 · §7.6.2")
        st.button("Continue to the full triage", icon=":material/arrow_forward:", on_click=open_triage)


render_interview()
