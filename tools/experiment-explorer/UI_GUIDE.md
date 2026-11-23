# Explorer interface guide

## Review and demonstration cues

| Page | Friction in the earlier interface | What to show |
| --- | --- | --- |
| 01 · Overview | The four run filters followed the hardware tables, artifact ledger, strata catalog and five charts. Readers had to remember which population each count described. | Start at the 504 → 543 snapshot comparison. The donut describes physical files and the admission bars give exact counts. Open **Executions & filters** to query the 126 executions, or **Environment & strata** for the experiment boundaries. |
| 02 · Synchronization | Coincident trial dots obscured repeated observations. Two long callouts preceded the flagship charts. | Hover the three points for one treatment. Horizontal spacing identifies individual trials, while height gives their recorded value. Switch on the diagnostic ceiling to see the change in scale and the methodological caveat. |
| 03 · Runtime comparison | Four abbreviated treatment labels repeated across three small panels. Long titles consumed space, and integer bar labels truncated fractional mean pin counts. | Read throughput, JFR pins and p95 across the same treatment order. Hover for the full JDK and treatment label, units and precision. |
| 04 · Native boundary | The stage shading was implemented separately from the trial view. Migration guidance competed with the selected run’s CPU profile. | Select a blocking JNI run. The shaded bands mark 0–15, 15–45 and 45–55 seconds. Compare its dashed hold mean with the cross-trial CPU figure in the finding above. |
| 05 · Persistence | Long legends competed with the chart titles. Ledger headings omitted units and the size of the waiting queue was easy to miss. | Compare the excluded control and the active-contention treatment, then read the peak-queue bars on the 50-VU scale. The ledger shows exact counts beside the bars. |
| 06 · Individual trial | Eight nested cards squeezed the two measurement windows. An unavailable pin count could look like a measured zero. The ledger discarded most of each SHA-256 string. | Read the full-run and hold values on the same row, then open **Provenance & downloads**. The status distinguishes a verified hash from a present manifest. The complete hashes are available in the cells. |
| 07 · Migration workbench | Eight long tab labels crowded the tool switcher. Several rule panels tried to span independent Markdown elements with HTML. Chart annotations duplicated long legend entries. | Use **Triage** for the six-stage assessment, then **Calculators → HikariCP pool**. Lines show model output, symbols show empirical points at the applicable inputs, and the dashed vertical line marks the hardware bound. **Audit export** uses the current triage inputs. |

## Applying the design system

1. **Set the native theme.** The app-local `.streamlit/config.toml` gives widgets, menus and dataframe canvases the same dark background and readable text. The font stacks resolve locally. Launching from the repository root uses the app’s configuration with the pinned Streamlit version.

2. **Style the shell once.** `app.py` loads `explorer.css` with `st.html(APP_DIR / "explorer.css")`. Glass surfaces use a dark base, a fine border and a restrained highlight. The chart plotting field stays opaque. Use the shared page heading for a numbered page, `.callout-box` for findings and `.callout-warning` for diagnostic caveats. These are representative rules from the stylesheet.

   ```css
   [data-testid="stMetric"], .lab-card, .callout-box, .callout-warning {
       background: var(--lab-glass);
       border: 1px solid var(--lab-line);
       border-radius: .88rem;
   }
   [data-testid="stMetricValue"] {
       font-family: var(--lab-mono);
       font-variant-numeric: tabular-nums;
   }
   .callout-warning { border-inline-start-color: var(--lab-amber); }
   [data-testid="stTab"][aria-selected="true"] {
       background: #203745;
       color: #b6f2ec;
       box-shadow: inset 0 -2px 0 var(--lab-teal);
   }
   ```

   Keep status text beside its colored indicator. Reserve the short pulse for risk status, and honor reduced-motion preferences. Native tabs retain keyboard navigation and horizontal scrolling on narrow screens.

3. **Give each chart its measurement vocabulary.** In `lib/transformations.py`, the shared layout supplies the colorway, monospaced ticks and tooltip numbers, subdued grid and bottom legend. A page supplies the units, formatting and meaning of its traces. Build the figure from the existing series, then style it.

   ```python
   apply_dark_scientific_layout(
       fig, title="Hold-window throughput", height=360,
       hover_value="%{y:,.4f} req/s",
   )
   st.plotly_chart(fig, width="stretch", theme=None)
   ```

   Passing `theme=None` uses the figure’s explicit styling. For trial dots or dual-axis series, attach a trace-specific `hover_card` with the run identity or elapsed time. Apply `shade_workload_stages` after adding telemetry traces. Bind each model and empirical series to its original axis.

4. **Check interactions and the frozen-data contract.** From the repository root, run the focused render and theme checks after editing the presentation. Then run the complete regression suite with the pinned environment.

   ```sh
   pytest tools/experiment-explorer/tests/test_pages_render.py tools/experiment-explorer/tests/test_transformations.py -q
   pytest tools/experiment-explorer/tests/ -v
   ```

   In the running app, check the overview at desktop and phone widths, inspect a trial dot with the diagnostic switch in both positions, select a JNI run, open a trial’s provenance tab, and switch among the workbench calculators. These checks exercise the rendered layout, hover targets, navigation and window labels.
