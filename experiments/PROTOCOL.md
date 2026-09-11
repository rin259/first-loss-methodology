# FLM 实验方案

## 目标

本实验验证 First Loss Methodology (FLM) 是否能够：

1. 稳定定位 evidence 从可消费状态变为不可消费状态的阶段；
2. 识别 evidence 仍然存在但语义不变量首次被破坏的位置；
3. 降低把上游 evidence 丢失错误归因给下游组件的概率；
4. 在重复探针和独立回放窗口下产生一致归因。

## 核心假设

- H1：在可控多阶段系统中，FLM 的 First Loss Accuracy 高于不使用 evidence funnel 的组件级 RCA。
- H2：对 rank、identity、temporal、scope、provenance 等不变量损坏，FLM 的 Invariant Loss Accuracy 高于只检查 existence 的基线。
- H3：当上游发生 First Loss 时，FLM 的 False Downstream Attribution Rate 低于最终症状定位和普通组件级 RCA。
- H4：移除 First Loss rule、invariant checking、upstream exclusion 或 minimal-probe discipline 会降低归因质量和可重复性。

## Propositions under test

- **P1 Existence boundary**：若 $P_i(E)=0$，$E$ 不能直接成为 $S_{i+1}$ 的输入。
- **P2 Provenance recoverability**：若 $P_i(E)=1$ 且 observation model 完整，必须存在有限、有序的 lineage chain，把 source evidence ID 映射到 $S_i$ 的下游表示。chain 允许 copy、enrich、reorder、split 和 merge；每次转换后仍要能回答“这条下游表示来自哪个上游 evidence”。若 chain 缺失，结论是 bounded，不是断言 evidence 未到达。
- **P3 Attribution bound**：若 $FL(E)=k$，则 $S_{k+1},\ldots,S_n$ 不得成为该 evidence failure 的 confirmed root cause。
- **P4 Invariant priority**：若 Invariant Loss $j$ 先于 First Loss $k$，root-cause 候选必须包含使 invariant 失效的 predicate、配置或实现。

P3/P4 可被非局部因果反例证伪；遇到共享状态、并发副作用或隐式协议时，必须收窄为 direct-path exclusion 并记录 cross-stage exception。

## 数据与故障注入

构建可回放的 pipeline benchmark，统一包含以下阶段：

1. Source
2. Retrieval
3. Metadata enrichment
4. Ordering
5. Cap / Budget
6. Candidate selection
7. Gate / Filter
8. Assembly
9. Reader

每个 case 包含确定性 seed、语料、查询、流水线配置、trace、ground-truth 标注和预期观测。语料按 tenant、namespace、ACL、generation、valid-time 和 source authority 标注。

除上述规则一致性 benchmark 外，`runtime_experiments.py` 必须执行三个不同实现，而不是只替换阶段名称：

1. RAG：ranked retrieval、metadata enrichment、fallback、context cap 和 answer；
2. ETL：parse、key mapping、dead-letter replay、join 和 window commit；
3. Build：dependency resolution、cache、vendored fallback、link 和 test。

每个实现覆盖 local invariant-first fault、direct loss、partial observability、noisy probes、nonlocal side effect 和 evidence reacquisition。partial case 必须输出 bounded interval；nonlocal case 必须降级为 cross-stage exception；reacquisition 必须开启新的 lineage segment。

故障族包括：

| 族                     | 注入点                            | 预期检查                              |
| --------------------- | ------------------------------ | --------------------------------- |
| Retrieval miss        | 向量或索引查询                        | evidence 是否离开 retrieval           |
| Rank loss             | ordering 后 metadata lookup     | order invariant 是否丢失              |
| Positional truncation | unordered result 后 cap         | First Loss 是否发生在 cap              |
| Filter mismatch       | gate                           | scope / namespace / ACL invariant |
| Budget miss           | candidate / budget             | evidence 是否到达 budget              |
| Selector error        | selector                       | evidence 是否进入 selector            |
| Metadata corruption   | enrichment                     | provenance / authority invariant  |
| Dead path             | identity or namespace mismatch | path unreachable / path returns empty / path output rejected / precondition identity mismatch |
| Temporal invalidity   | reader 或 lifecycle             | temporal invariant                |
| Duplicate identity    | assembly                       | identity invariant                |

实验集划分为：

- Development set：用于调试探针，不得用于报告最终指标。
- Test set：冻结配置后一次性评估。
- Independent replay set：与 test set 同分布但采用不同 seed 和时间窗口。

## 基线

1. **Final-symptom baseline**：把 failure 归因到最后一个观测失败或输出异常的组件。
2. **Component-level RCA**：允许查看 trace，按组件错误计数选择最可疑组件，但不施加 First Loss 边界。
3. **Existence-only provenance**：追踪 evidence 是否存在，但不检查语义不变量。
4. **LLM-based RCA**：给模型相同 trace 和错误描述，不提供 FLM 归因规则；模型输出 First Loss、Invariant Loss 和 root cause。真实模型实验固定 60 个分层 case、5 次重复、prompt、JSON schema、temperature 和 exact model ID。deterministic proxy 只能用于开发，不得作为真实模型证据。
5. **FLM**：完整方法，包括 evidence survival funnel、invariant check、attribution boundary 和 confirmation protocol。

LLM 基线必须固定模型版本、提示词、温度和上下文长度。若系统允许随机性，则每个 case 重复 5 次并报告多数投票与一致性。当前 synthetic run 只含 trace-only LLM proxy；strong proxy 得到 1.000，因此不声称 FLM 优于真实或理想化 LLM。

## 指标

对每个 case 判断：

- `FL_pred` 是否等于 ground-truth First Loss；
- `IL_pred` 是否等于 ground-truth Invariant Loss，不存在时是否正确输出 `none`；
- `RC_pred` 是否等于 ground-truth root cause；
- `DA` 是否发生错误下游归因。

定义：

```text
First Loss Accuracy, FLA = correct FL / |D|
Invariant Loss Accuracy, ILA = correct IL / |D|
Root Cause Accuracy, RCAc = correct root cause / |D|
False Downstream Attribution Rate, FDAR =
  predicted downstream AND not in acceptable root-cause set / |D|
Reproducibility = identical attribution across repeated probes / |D|
```

补充报告：

- 每个故障族的分项 accuracy；
- 探针数量和 token / time 成本；
- Wilson 95% confidence interval；
- 方法与最强基线的 paired bootstrap difference 和 McNemar test。

## 确认流程

每个 root-cause hypothesis 必须依次通过：

1. Minimal probe：只检查一个候选阶段的输入、输出和不变量。
2. Single variable：除候选机制外，baseline、seed、语料和其他配置保持冻结。
3. Fail-before：在原始配置下重复触发失败，并记录 First Loss。
4. Pass-after：只修复候选根因后，同一查询和窗口必须恢复。
5. Upstream exclusion：确认 First Loss 之前不存在可解释失败的未被排除上游条件。
6. Independent replay：在不同 seed、时间窗口或进程中重放，归因必须一致。

只有同时满足以上条件的 root cause 才能标记为 confirmed。未完成确认流程时只能报告 candidate root cause。

## 消融

完整 FLM 与以下变体比较：

1. `FLM - First Loss rule`：仍记录 trace，但不禁止下游归因。
2. `FLM - invariant checking`：只检查 existence。
3. `FLM - upstream exclusion`：不执行 attribution boundary。
4. `FLM - minimal probe`：允许一次性修改多个变量。
5. `FLM - independent replay`：只做 before / after，不做独立窗口。

## 统计与有效性

- 主指标按 test set 计算；按故障族报告分层 bootstrap 95% CI。
- 使用 paired bootstrap 估计方法间差异；对二元正确性使用 McNemar test。
- 所有 case 的 seed、prompt、代码版本和数据哈希必须随结果发布。
- Ground truth 由故障注入配置自动生成，实验者不得在看到 test trace 后修改标注。
- 为避免探针信息泄漏，每轮探针只能消费前一阶段的 evidence 状态和不变量结果。
- paired bootstrap 必须对两个方法使用同一组 resampled case indices；不得分别独立抽样。
- 极小 McNemar exact p-value 若发生浮点下溢，应报告为数值上界（例如 `<1e-300`），不得写成 `0`。
- 多基线比较属于次要分析；主结论优先报告 effect size 与 confidence interval。

## 有效性威胁

1. 合成 case 可能低估真实系统复杂性，因此另设真实 incident replay。
2. LLM 基线表现可能受提示词影响，因此发布提示词并进行提示词扰动测试。
3. 部分真实系统无法记录中间状态；论文不声称 FLM 可在不可观测边界内保证定位。
4. 多个 evidence 同时丢失时，First Loss 需按 evidence ID 展开，不能聚合成单一阶段后草率归因。
5. evidence 在 fallback 或 side input 中重新出现时，presence 不再单调；必须按 lineage segment 报告 loss 与 reacquisition。
6. 明示的 nonlocal side-effect 标记只验证 exception handling，不代表系统能够自动发现隐藏的非局部原因。
