# First Loss Methodology

**First Loss Methodology** is a generalizable software engineering method for evidence-centric root-cause attribution. This repository contains the preprint, reproducible benchmark, conservation schema, statistical results, real-incident case study, and open artifacts.

## Cite

See `CITATION.cff` or `citation.bib`. Current artifact version is `v1.0.0`; DOI is `10.5281/zenodo.22704463`.

这个仓库把 FLM 从工程调试笔记提升为可复现的软件工程方法研究：

- `paper/main.md`：论文主体，包含理论对象、形式化定义、可证伪命题、评估协议、受控 replay 和案例研究。
- `experiments/PROTOCOL.md`：跨领域可重复实验协议，包含适用性条件、领域适配、指标和统计要求。
- `benchmark/run_experiments.py`：冻结 seed 的受控 replay benchmark。
- `benchmark/conservation_schema.py`：evidence-conservation 数据契约检查。
- `benchmark/results/REPORT.md`：当前 seeded run 的指标与统计检验。
- `benchmark/INCIDENT_REPLAY.md`：真实 vector-arm ordering incident 的结构化回放。
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
```

## License

- Code: MIT, `LICENSE-CODE`
- Benchmark data and results: CC-BY-4.0, `LICENSE-DATA`
- Paper text and prose: CC-BY-4.0, `LICENSE-PAPER`
