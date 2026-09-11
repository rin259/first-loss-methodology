# Benchmark 记录

- 冻结 development/test/replay 划分后再运行方法。
- 每行写入 `RESULTS_TEMPLATE.csv`，不覆盖原始探针结果。
- 每个 root-cause case 保存 before/after 配置与输出哈希。
- LLM 基线记录模型版本、prompt 哈希、temperature 和 5 次重复结果。
- `run_experiments.py --samples 5000` reproduces `results/REPORT.md`.
- Ground truth is written into frozen `cases.jsonl` before methods run.
- `INCIDENT_REPLAY.md` is the real incident replay, separate from synthetic metrics.
