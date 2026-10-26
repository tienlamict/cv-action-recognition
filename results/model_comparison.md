| model | split | n_windows | macro_f1 | baseline_random | baseline_none | event_filter | event_f1 | cmds_per_gesture | false_per_min | run |
|---|---|---|---|---|---|---|---|---|---|---|
| rules | val | 11038 | 0.2305 | 0.0796 | 0.1964 | fsm | 0.1276 | 0.2315 | 4.309 | results/phase8/evaluate/run_09 |
| rf | val | 11038 | 0.4361 | 0.0796 | 0.1964 | fsm | 0.2537 | 0.1574 | 0.1497 | results/phase8/evaluate/run_10 |
| lstm | val | 11038 | 0.4893 | 0.0796 | 0.1964 | fsm | 0.6 | 0.6296 | 0.7653 | results/phase8/evaluate/run_11 |
| hybrid | val | 11038 | 0.5366 | 0.0796 | 0.1964 | fsm | 0.5714 | 0.4722 | 0.2828 | results/phase8/evaluate/run_12 |
