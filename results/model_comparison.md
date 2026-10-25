| model | split | n_windows | macro_f1 | baseline_random | baseline_none | event_filter | event_f1 | cmds_per_gesture | false_per_min | run |
|---|---|---|---|---|---|---|---|---|---|---|
| rules | val | 11038 | 0.2305 | 0.0796 | 0.1964 | fsm | 0.13 | 0.3704 | 6.821 | results/phase8/evaluate/run_05 |
| rf | val | 11038 | 0.4361 | 0.0796 | 0.1964 | fsm | 0.4046 | 0.3241 | 0.4991 | results/phase8/evaluate/run_06 |
| lstm | val | 11038 | 0.556 | 0.0796 | 0.1964 | fsm | 0.5588 | 0.7685 | 1.464 | results/phase8/evaluate/run_07 |
| hybrid | val | 11038 | 0.5061 | 0.0796 | 0.1964 | fsm | 0.49 | 0.6111 | 1.331 | results/phase8/evaluate/run_08 |
