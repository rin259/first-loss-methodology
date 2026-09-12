# First Loss Methodology

**First Loss Methodology** is an evidence-boundary method for root-cause attribution in observable multi-stage software systems. This repository contains the paper, two reproducible benchmarks, a real-incident replay, and release artifacts.

## Cite

See `CITATION.cff`, `citation.bib`, or `CITATION.md`. The released `v1.1.0` preprint and reproducibility artifact are archived at DOI [10.5281/zenodo.22709898](https://doi.org/10.5281/zenodo.22709898). The repository also contains a `v1.1.1` manuscript revision with a second, redacted production investigation. An arXiv identifier will be added after submission and moderation.

这个仓库把 FLM 从工程调试笔记提升为可复现的软件工程方法研究：

- `paper/manuscript.tex`：英文投稿稿，收紧理论边界并加入正式相关工作、异构运行时评估和有效性威胁。
- `output/pdf/first-loss-v1.1.0-preprint.pdf`：已归档的 `v1.1.0` 预印本。
- `output/pdf/first-loss-v1.1.1-preprint.pdf`：加入多边界生产案例的当前投稿稿。
- `paper/main.md`：已归档的 `v1.0.0` 中文/英文混合原稿。
- `experiments/PROTOCOL.md`：跨领域可重复实验协议，包含适用性条件、领域适配、指标和统计要求。
- `benchmark/run_experiments.py`：冻结 seed 的受控 replay benchmark。
- `benchmark/runtime_experiments.py`：RAG、ETL 和 build 三个独立可执行参考运行时。
- `benchmark/run_llm_baseline.py`：真实 Responses API 基线，包含冻结 prompt、结构化输出、重复运行和断点续跑。
- `benchmark/conservation_schema.py`：evidence-conservation 数据契约检查。
- `benchmark/results/REPORT.md`：当前 seeded run 的指标与统计检验。
- `benchmark/INCIDENT_REPLAY.md`：真实 vector-arm ordering incident 的结构化回放。
- `experiments/PRODUCTION_CASE_STUDY.md`：第二个生产归因路径的脱敏证据摘要。
- `AUTHORS.md`：作者、 affiliation、贡献和 AI-assistance 声明。
- `CITATION.cff` / `citation.bib`：引用元数据。
- `.github/workflows/ci.yml`：schema 检查与 smoke-test reproduction。

FLM 的适用边界：系统必须可分解为有序 evidence transformation，能恢复 evidence identity，可形式化关键 invariant，并具备最小观测或干预能力。若缺少这些条件，只能报告 bounded evidence attribution。

## Reproduce

Requires Python `>=3.9`; no third-party runtime dependencies.

```bash
python3 benchmark/run_experiments.py --output-dir benchmark/results --samples 5000
python3 benchmark/conservation_schema.py benchmark/results/cases.jsonl --split test
python3 benchmark/conservation_schema.py benchmark/results/cases.jsonl --split replay
python3 benchmark/runtime_experiments.py --output-dir benchmark/runtime_results --repetitions 20
python3 -m unittest discover -s benchmark -p 'test_*.py'
```

Export the frozen 60-case, five-repeat LLM protocol without making API calls:

```bash
python3 benchmark/run_llm_baseline.py --cases 60 --repeats 5
```

The completed `glm-5-3-flash` run is under `benchmark/llm_results/`: 300 raw responses, overall attribution accuracy `0.920`, exact-path RCA `0.973`, overclaim rate `0.047`, and five-run exact agreement `0.200`. The provider endpoint did not enforce strict JSON Schema, so the final run uses validated JSON-object mode; two compatibility pilots are excluded and disclosed.

## License

- Code: MIT, `LICENSE-CODE`
- Benchmark data and results: CC-BY-4.0, `LICENSE-DATA`
- Paper text and prose: CC-BY-4.0, `LICENSE-PAPER`

`CITATION.cff` describes citation metadata only. The repository is intentionally multi-licensed; no single license applies to every file.
