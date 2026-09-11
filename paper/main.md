# First Loss: A Generalizable Software Engineering Method for Evidence-Centric Root-Cause Attribution

Chen KuangYu ^1,2^  
^1^ Veridical Tech, Inc.  
^2^ Xi'an University of Science and Technology Hi-tech College  
Corresponding author: Chen KuangYu <rin@rin.red>

**Preprint v1.0.0.** AI assistants supported writing, code implementation, and experiment organization. The author designed the method, validated the experiments, and approved the final revision.

## Abstract

复杂软件系统里的失败常在下游才显式暴露，但 evidence 可能早已在上游丢失或变形。只看最终症状，工程师会把锅端给一个从未收到证据的组件。FLM 把这条链路改写成 evidence survival pipeline：**First Loss** 记录证据第一次从可消费变成不可消费的位置，**Invariant Loss** 记录证据还在但身份、顺序、范围、时间、来源或权限等语义不变量第一次被破坏的位置。二者不回答同一个问题。First Loss 划定归因边界；Invariant Loss 找更早的语义损坏；Root Cause 则要靠干预确认。

本文的贡献不是某个产品栈里的调试经验，而是一个有明确适用条件的软件工程方法。它要求系统可以分解成有序 evidence transformation，能恢复 lineage identity，能把关键 invariant 写成可检查谓词，并具备最小观测或干预能力。我们在七个抽象领域的 1,200 个冻结测试 case 和 600 个独立窗口 case 上做了受控 replay，验证可重复性和可测量性；再用一个真实 vector-arm ordering incident 做工程可解释性 case study。受控结果里，FLM 把 component-level RCA 的 stage RCA 从 0.420 提到 1.000，把 1-FDAR 从 0.578 提到 1.000；symptom-biased LLM proxy 的两项分别只有 0.407 和 0.436。但我们不声称 FLM 优于 strong LLM proxy：在完整 trace 下，后者同样达到 1.000。FLM 提供的不是模型智能，而是显式、可审计、与模型无关的归因规则和确认协议。

## 1 Introduction

### 1.1 Problem: final failure is not necessarily failure origin

source 产生 evidence，retrieval、selection、processing、assembly 和 output 依次转换或过滤它。最终 failure 只说明结果不可接受，不说明原因在最后一个组件。一条 evidence 可能没到下游，也可能到了，但顺序、identity 或 temporal context 已经不对。只看最终错误的人，会在一个从未收到证据的组件里找缺陷。

考虑一个典型多阶段链路：

```text
Source
  ↓
Retrieval
  ↓
Metadata enrichment
  ↓
Selection / cap
  ↓
Processing / reader
  ↓
Output failure
```

如果 ranked evidence 在 metadata lookup 后失去顺序，又在 `LIMIT N` 处被位置截断，最终症状只是 recall failure。embedding、selector、gate 或 reader 都不是这条 evidence 的失败根源；要解释的是 order invariant 怎么丢的，以及 First Loss 为什么落在 cap。

### 1.2 From debugging heuristic to engineering method

传统 debugging 常以组件为中心提问：“哪个组件出了问题？”组件边界清楚时，这个问法有效。但 evidence 一旦经过复制、合并、重排序和过滤，它就会误导人。FLM 改问：

1. 哪条 evidence 与失败相关？
2. 该 evidence 在每个阶段是否可消费？
3. 若可消费，其下游所需的不变量是否仍然成立？
4. evidence 首次消失或失真的阶段在哪里？
5. 该位置能否通过最小干预重复触发或消除失败？

作为一种软件工程方法，FLM 的边界必须比“一套调试经验”更严格。它至少有四类对象：

1. **Theoretical object**：evidence state、stage transformation、survival function、invariant relation 和 attribution frontier。
2. **Normative rule**：First Loss boundary、upstream exclusion 和 invariant-to-loss chain。
3. **Falsifiable hypotheses**：方法应在可观测系统中提高 First Loss Accuracy、Root Cause Accuracy 和 attribution validity，并降低 False Downstream Attribution Rate。
4. **Repeatable protocol**：探针、干预、数据划分、统计检验和 artifact 发布要求。

因此，FLM 不把故障压缩成组件健康分数，而是沿着 evidence provenance 建立可检查的归因边界。

### 1.3 Research questions

- **RQ1**：First Loss 能否稳定定位 evidence failure 的归因边界？
- **RQ2**：Invariant Loss 能否解释 evidence 尚未消失但语义已经损坏的 failure？
- **RQ3**：在 First Loss 后才显式暴露症状的场景中，FLM 能否降低对下游组件的错误归因？
- **RQ4**：FLM 的实验纪律能否提高 root-cause attribution 的可重复性？

### 1.4 Contributions

1. **Evidence Survival Funnel**：把多阶段系统统一表示为 evidence 转换与过滤流水线。
2. **First Loss**：形式化 evidence 首次消失的位置。
3. **Invariant Loss**：形式化 evidence 存在但关键语义不变量首次被破坏的位置。
4. **Attribution Boundary Rule**：规定在 evidence First Loss 之前不得把该 evidence 的失败归因给下游组件。
5. **Attribution Protocol**：给出 minimal probe、single variable、frozen baseline、fail-before/pass-after 和 independent replay 的确认流程。
6. **Evaluation design**：提出适用性条件、evidence-conservation schema、故障族覆盖、LLM 基线、消融、统计检验和真实 incident replay。
7. **Generalization boundary**：明确 FLM 可由四项抽象条件映射到 retrieval/RAG、agent memory、compiler/build、data pipeline、distributed systems 和 LLM agent，而非绑定某个 retrieval 项目。

## 2 Background and related work

### 2.1 Fault localization and first erroneous state

程序分析中的 fault localization 会从 failing test、program state 或 execution trace 里找缺陷；“first erroneous state” 的直觉是：错误状态通常早于最终 failure。FLM 保留这个直觉，但把对象从程序变量换成了 evidence state。它可能是文档、记忆条目、索引结果、metadata，也可能是送进生成请求的上下文片段。FLM 不预测缺陷代码行；它解释 evidence 在系统边界之间如何生存和失真。

### 2.2 Causal debugging and failure propagation

Causal debugging、infection chain 和 failure propagation 看故障如何在程序点之间传播。FLM 看的是另一件事：evidence 在数据流里是否存活。跨服务系统尤其需要后者，因为服务边界和异步队列会把传播链遮住。evidence funnel 逐步记录 `present`、`source_id`、`evidence_id` 和 `reason`，把这条链重新变得可回放。

### 2.3 Provenance and data lineage

Data lineage 回答数据来自哪里、经过了哪些转换。FLM 把 provenance 当作归因骨架，但不停在这里：来源已知不等于 evidence 可消费，更不等于语义完整。一个下游组件可能收到了正确来源的记录，却拿到错误顺序、错误租户、错误生命周期或错误权限。survival 和 invariant 才是归因条件。

### 2.4 Causal testing and counterfactual debugging

反事实调试用干预确认原因：替换输入、修候选缺陷或回滚配置。FLM 把这件事排在边界定位之后。First Loss 先圈定可归因边界，counterfactual intervention 再确认边界内的候选机制。症状消失不是充分证据；要配合 fail-before、pass-after、single variable 和 independent replay，root cause 才能从 candidate 升级成 confirmed。

## 3 First Loss Methodology

### 3.1 Theoretical system

FLM 的理论对象不是组件，而是可观测的 evidence 状态转换。一个软件系统实例由三元组组成：

$$
\mathcal{M}=(\mathcal{E},\mathcal{S},\Omega)
$$

其中：

- $\mathcal{E}$ 是 evidence universe；
- $\mathcal{S}=\{S_1,\ldots,S_n\}$ 是有序阶段集合；
- $\Omega$ 是观测模型，决定每个阶段能记录哪些 evidence 状态、不变量、rejection reason 和干预结果。

可归因性依赖观测模型。$\Omega$ 若看不见某阶段的输入、输出或 rejection reason，FLM 就只能给出有界结论。

### 3.2 Evidence model

一条 evidence $E$ 是带来源和生命周期的可检查实体：

$$
E = (\mathit{id}, c, m, p, a, l)
$$

其中：

- $c$ 是 content；
- $m$ 是 metadata；
- $p$ 是 provenance，包括 source ID、pipeline path 和 transformation history；
- $a$ 是 authority，例如 source trust level、ACL 和 tenant；
- $l$ 是 lifecycle，例如 generation、valid time、revision 和 deletion state。

系统由阶段 $S_1,\ldots,S_n$ 组成，每个阶段是一个部分函数：

$$
S_i: \mathcal{P}(\mathcal{E}) \times \Theta_i \rightarrow \mathcal{P}(\mathcal{E}) \times \Lambda_i
$$

其中 $\mathcal{E}$ 是 evidence universe，$\Theta_i$ 是配置和查询上下文，$\Lambda_i$ 是观测日志。给定输入 evidence 集合，$S_i$ 可以复制、转换、合并、重排序、过滤或拒绝 evidence。

### 3.3 Evidence Survival Funnel

对每条 evidence 和每个阶段，记录最小状态：

```text
present: 0 | 1
source_id
evidence_id
invariants
reason
```

存在性函数定义为：

$$
P_i(E) =
\begin{cases}
1, & \text{if } E \text{ is consumable at the output of } S_i \\
0, & \text{otherwise}
\end{cases}
$$

`present = 1` 不只表示对象在集合中，还要求下游可按其身份和类型消费。一条 evidence 若因 schema、encoding、权限或重复 identity 而不可消费，也视为 absent。

### 3.4 First Loss

对初始存在的 evidence $E$，即 $P_0(E)=1$，其 First Loss 为：

$$
FL(E)=\min\{i \in \{0,\ldots,n-1\} : P_i(E)=1 \land P_{i+1}(E)=0\}
$$

如果 $FL(E)=k$，则 $S_{k+1}$ 是该 evidence 的 First Loss stage，$S_k$ 的输出边界是归因检查边界。

First Loss 是**边界**，不是自动的 root cause。$S_{k+1}$ 可能因为上游错误地交付了非法输入而拒绝 evidence；$S_k$ 的转换也可能违反 invariant，使下游阶段必须丢弃它。因此，First Loss 之后仍需在 $S_k$ 和 $S_{k+1}$ 之间定位 predicate、配置或实现缺陷。

### 3.5 Invariant Loss

Evidence 的语义不变量集合包括：

$$
I(E)=\{\mathit{identity}, \mathit{order}, \mathit{scope}, \mathit{generation}, \mathit{temporal}, \mathit{provenance}, \mathit{authority}, \mathit{lifecycle}\}
$$

设阶段 $i$ 的期望不变量状态为 $I_i^{\mathrm{exp}}(E)$，实际状态为 $I_i^{\mathrm{obs}}(E)$。Invariant Loss 定义为：

$$
IL(E)=\min\{i : \exists j \in I(E),\ I_{i,j}^{\mathrm{obs}}(E) \neq I_{i,j}^{\mathrm{exp}}(E)\}
$$

其中不存在违反时 $IL(E)=\bot$。

Invariant Loss 可以先于、等于或不存在于 First Loss。例如：

1. ranked vector result 经 metadata lookup 变为 unordered result：evidence 仍存在，order invariant 已丢失；
2. unordered result 随后被 `LIMIT N` 截断：evidence 消失，First Loss 发生；
3. query expected generation 与 metadata generation 不一致：identity 或 generation invariant 丢失；
4. evidence 已过期但仍进入上下文：temporal invariant 丢失，后续可能没有显式 First Loss。

因此，**existence 不等于 integrity**。只检查 evidence 是否存在的系统无法发现这类静默损坏。

### 3.6 Invariant-to-loss chain

FLM 用三类事件描述常见失败链：

$$
\text{Invariant Loss} \rightarrow \text{First Loss} \rightarrow \text{Observed Failure}
$$

该链条不是所有故障的必要形式，而是常见且容易被误诊的一类。典型机制如下：

1. 阶段 $S_i$ 使某个 invariant 失效；
2. 阶段 $S_j$ 的正确 predicate 依赖该 invariant；
3. 阶段 $S_j$ 丢弃 evidence，产生 First Loss；
4. 最终 output 因 evidence 不足而失败。

在这个链条中，$S_j$ 是 First Loss stage，$S_i$ 是 Invariant Loss stage，root cause 位于 $S_i$ 的 predicate 或实现中。如果把 $S_j$ 或更下游组件当作故障来源，就会形成 downstream misattribution。但该链条要求局部传播假设：下游之所以失败，是因为它观察到缺失或损坏的 invariant。若上游缺陷通过共享状态、隐式回调或并发副作用使下游在 evidence 完整的情况下仍然失败，必须作为 cross-stage causal exception 显式建模，而不能机械套用 boundary rule。

## 4 Attribution rules

### 4.1 Upstream Attribution Boundary

对单条 evidence $E$，若 $FL(E)=k$，则：

$$
S_{k+1},\ldots,S_n \notin \mathcal{R}(E)
$$

其中 $\mathcal{R}(E)$ 是允许被确认为该 evidence failure 的 root-cause 集合。这条规则禁止在 evidence 未到达的下游位置寻找缺陷。

### 4.2 Existence before selection

归因检查顺序固定为：

```text
Existence
  → Retrieval
  → Cap / Budget
  → Candidate
  → Selector
  → Gate
  → Assembly
  → Reader
```

实际实现中的组件名可以不同，原则不变：只有 evidence 到达某组件后，才能讨论该组件是否造成失败。多个 evidence 同时失败时，必须按 evidence ID 分组计算 First Loss，再聚合形成 attribution frontier；不得把所有 evidence 的失败聚合成单一阶段后直接归因。

### 4.3 Ordering authority

Metadata enrichment 不自动继承 retrieval ordering authority。特别是：

```text
retrieval rank
  ↓
metadata lookup
  ↓
unordered result
  ↓
LIMIT N
```

如果 metadata lookup 返回无序集合，而后续 cap 按位置截断，就会产生 rank invariant loss → positional truncation → recall failure。该模式中，embedding 或 selector 未必有缺陷；必须检查 ordering invariant 是否在 lookup 后保留。

### 4.4 Latent dead-path and precondition failure

有些 evidence 从未显式进入系统输出，但仍会影响最终结果。FLM 把这一组统一为四类 latent dead-path / precondition failure states：

1. **Path Unreachable**：由于路由、索引、租户或 ACL 错误，阶段从未被调用。
2. **Path Returns Empty**：阶段被调用但没有返回该 evidence。
3. **Path Output Rejected**：阶段返回了 evidence，但后续 predicate 拒绝它。
4. **Precondition Identity Mismatch**：identity、tenant、namespace、ACL 或 lifecycle 先验条件不匹配，可能表现为 unreachable、empty 或 rejected。

四类的 root cause 不相同。诊断前必须先验证 identity、tenant、namespace、ACL 和 lifecycle 等先验条件，再检查路由是否可达、路径是否为空、以及 rejection reason。

## 5 Root-cause confirmation protocol

FLM 不允许仅凭观测宣布 root cause。一个 confirmed root cause 必须满足：

1. **Reproducible**：在冻结基线上可重复触发。
2. **Clear First Loss**：相关 evidence 的 First Loss 已定位。
3. **Clear invariant**：受影响的 invariant、predicate 或实现被明确描述。
4. **Minimal counterexample**：存在最小输入或配置使失败稳定复现。
5. **Fail-before**：修复前失败可观测。
6. **Pass-after**：只修复候选根因后同一输入通过。
7. **Upstream excluded**：First Loss 之前没有未排除的上游解释。
8. **Independent replay**：不同 seed、时间窗口或进程中归因一致。
9. **No reader guessing**：结论依赖 trace、探针和干预，而不是 reader 对症状的猜测。

确认流程如下：

```text
Hypothesis
  ↓
Minimal probe
  ↓
Single variable
  ↓
Frozen baseline
  ↓
Before / After
  ↓
Regression
  ↓
Independent window
  ↓
Decision
```

未完成全部条件时，只能报告 `candidate root cause`。若 invariant loss 已发生但 evidence 仍存在，应同时报告 `Invariant Loss` 和尚未发生的潜在 First Loss。

## 6 Falsifiable claims and evaluation

### 6.1 Formal claims

为了让 FLM 可被检验而不是只作为工程规范，本节把方法拆成四条命题。设 $D$ 是冻结 test set，$P_i(E)$ 是 stage $i$ 后 evidence $E$ 的可消费性，$I_i(E)$ 是不变量状态。

**Proposition 1: Existence boundary.**  
若 $P_i(E)=0$，则 evidence $E$ 不能作为 stage $i+1,\ldots,n$ 的直接输入。

**Proposition 2: Provenance recoverability.**  
若 $P_i(E)=1$ 且 stage $0$ 到 $i$ 的 observation model 足够完整，则必须存在一条有限的、有序的 lineage chain，把 source evidence ID 映射到它在 stage $i$ 的下游表示。这条 chain 不是“数据结构没变”；它允许复制、enrichment、重排序、split 和 merge。它只要求每次转换后仍能回答“这条下游表示来自哪个上游 evidence”。如果 chain 缺失，不能机械地说 $E$ 没有到达 $S_i$，只能说当前 trace 不足以证明它到达了。此时归因是 bounded，不是 guaranteed。

**Proposition 3: Attribution bound.**  
对一个确认的 failure $F$ 和关键 evidence $E$，若 $FL(E)=k$，则下游阶段 $S_{k+1},\ldots,S_n$ 不属于该 evidence failure 的 confirmed root-cause set。

**Proposition 4: Invariant priority.**  
若 $IL(E)=j<k$ 且 stage $k$ 因缺失或拒绝 invariant $v$ 而产生 $FL(E)=k$，则 root cause 的候选集合必须包含 $S_j$ 中使 $I_{j,v}(E)$ 失效的 predicate、配置或实现。

Proposition 3 是规范性归因规则。它的经验有效性可以被证伪：如果真实失败中 root cause 合法地位于某条关键 evidence 的 First Loss 之后，而 FLM 把它排除，则方法边界必须收窄。

这里的关键是 transformation 和 lineage identity 的区别。一个 stage 可以 copy、enrich、reorder、split、merge 或 reject evidence；lineage identity 不是某个内存对象的地址，而是“从 source evidence 到下游表示仍可恢复的映射”。复制会分叉 lineage，merge 会多对一。两种情况都必须把所有 parent evidence 纳入 attribution frontier，不能只盯一条 ID。

### 6.2 Repetition and attribution validity

单次 before/after 只能确认 $A\rightarrow F$ 的必要条件，排不掉共同原因。FLM 把确认强度分为三级：

1. **Reproduced**：同一 frozen baseline 中失败重复发生，First Loss 位置一致。
2. **Intervened**：单变量修复使同一输入通过，且未引入新的 First Loss。
3. **Confirmed**：在不同 seed、进程或时间窗中归因一致，并且所有关键 evidence 的 upstream exclusion 均被检查。

对非确定性系统，报告以下三个量：

$$
FL\text{-}Consistency=\frac{|\{x:\mathrm{mode}(FL_r(x))=FL_{\mathrm{gt}}(x)\}|}{|D|}
$$

$$
RC\text{-}Consistency=\frac{|\{x:\mathrm{mode}(RC_r(x))=RC_{\mathrm{gt}}(x)\}|}{|D|}
$$

$$
Conflict\ Rate=\frac{|\{x:\text{attributions across }r\text{ disagree}\}|}{|D|}
$$

$r$ 是独立 replay run。只有 $FL\text{-}Consistency$ 和 $RC\text{-}Consistency$ 同时高、Conflict Rate 又低，才能说方法有跨窗口稳定性。

### 6.3 Generalization domains

FLM 的适用条件不是某个产品栈，而是四项抽象条件：

1. 系统可分解为有序 evidence transformation；
2. 每个 evidence 有稳定 ID 或可恢复 identity；
3. 关键 invariant 可以形式化；
4. 存在最小观测或探针能力。

满足这些条件时，同一个协议可映射到七个参考领域：

| Domain | Evidence | Typical invariants | Attribution question |
|---|---|---|---|
| Retrieval / RAG | document chunk, index result | scope, order, provenance, temporal | evidence 是否被检索、重排或截断 |
| Agent / memory | memory entry, tool result | identity, tenant, lifecycle | 记忆是否到达 prompt 并保持语义 |
| Compilers / build | source artifact, dependency graph | identity, version, dependency order | 输入是否被丢弃或版本替换 |
| Data pipeline | record, partition, checkpoint | schema, key, window, provenance | 记录是否被 filter 或 join 丢失 |
| Distributed systems | request, event, span | causal order, idempotency, retry state | 事件是否丢失、重复或乱序 |
| LLM agents | tool output, plan step, message | schema, authority, ordering | 上下文是否被截断或错误组装 |
| Incident triage | telemetry item, incident record | severity, ownership, time window | 信号是否被过滤、去重或错配 owner |

领域映射必须满足 conservation check：对每条关键 evidence 记录输入 identity、输出 identity、invariant delta 和 rejection reason。记不了，就只给 bounded evidence attribution。

### 6.4 Benchmark design

评估使用可回放多阶段 benchmark。每个 case 包含：

- corpus、query、configuration 和 seed；
- pipeline trace；
- 每 evidence 的 survival 状态；
- invariant 观测；
- ground-truth First Loss、Invariant Loss 和 root cause；
- 下游症状；
- 最小修复；
- independent replay 结果。

语料标注 tenant、namespace、ACL、generation、valid time、revision 和 source authority。故障配置在划分数据集前冻结，避免看到 test trace 后改标注。

故障族覆盖 retrieval、ordering、filtering、budget、selector、gate、metadata、dead path、temporal 和 identity。每个族至少包含多个随机实例，并保留一个真实 incident replay。

### 6.5 Baselines

比较五种方法：

1. **Final-symptom baseline**：把 root cause 设为最后观测失败的组件。
2. **Component-level RCA**：根据组件错误计数和日志选择可疑组件，但不施加 First Loss 边界。
3. **Existence-only provenance**：追踪 evidence 是否存在，但不检查 invariant。
4. **LLM-based RCA**：给模型相同 trace 与错误描述，要求输出 First Loss、Invariant Loss 和 root cause。
5. **FLM**：完整方法。

本节实际跑的是 trace-only LLM proxy，不是公共或私有模型的 live run。`llm_rca_proxy_strong` 明确达到 1.000，所以论文不声称 FLM 优于真实或理想化的 LLM。可检验的说法是：FLM 优于 component-level 和 symptom-biased proxy；strong proxy 在完整 trace 下能学到同一模式。

LLM 基线固定模型版本、prompt、temperature、最大上下文和输出 schema。每个 case 重复 5 次，报告多数投票、同票一致率和 token 成本。

### 6.6 Metrics

对数据集 $D$ 定义：

$$
FLA=\frac{|\{x \in D : FL_{\text{pred}}(x)=FL_{\text{gt}}(x)\}|}{|D|}
$$

$$
ILA=\frac{|\{x \in D : IL_{\text{pred}}(x)=IL_{\text{gt}}(x)\}|}{|D|}
$$

$$
RCA_c=\frac{|\{x \in D : RC_{\text{pred}}(x)=RC_{\text{gt}}(x)\}|}{|D|}
$$

$$
FDAR=\frac{|\{x \in D : A_{\text{pred}}(x) \in D_x \land A_{\text{pred}}(x) \notin R_x\}|}{|D|}
$$

$R_x$ 是 case $x$ 的 acceptable root-cause set，包含 ground-truth root cause 和语义等价的 upstream mechanism；$D_x$ 是 First Loss 之后的下游阶段集合。FDAR 统计“原因被放到下游、且不在可接受 upstream 机制内”的 case，不惩罚位置不同但机制等价的解释。报告时同时给 FDAR 和 1-FDAR，后者只是更直观的补数。重复探针的可重复性定义为：

$$
REP=\frac{|\{x \in D : \text{all repeated attributions are identical}\}|}{|D|}
$$

主指标报告 Wilson 95% CI。方法间差异使用 paired bootstrap；二元正确性使用 McNemar test。所有结果附带 case ID、seed、prompt、代码版本和数据哈希。

### 6.7 E1-E8 results

评估核心压缩为八个实验。E3 和 E4 是主实验，因为它们分别回答“是否减少下游错误归因”和“干预能否确认真实根因”。

| Experiment | Question | Family set | Primary metrics |
|---|---|---|---|
| E1 First-Loss Localization | FLM 能否找到 evidence 首次消失的位置？ | non-dead-path single faults | FLA, attribution-boundary validity |
| E2 Invariant-Loss Detection | FLM 能否发现 evidence 仍在但语义已坏？ | order, scope, authority, provenance, temporal, identity | ILA |
| E3 Downstream Misattribution | FLM 是否显著减少错误甩锅下游？ | invariant-first faults and compounds | FDAR, 1-FDAR |
| E4 Root-Cause Confirmation | 单变量干预是否提高 confirmed RCA？ | non-dead-path single faults | RCA stage, RCA confirmed |
| E5 Compound Failure | 级联故障下是否仍能定位最早机制？ | four two-fault compounds | FLA, ILA, RCA, FDAR |
| E6 Latent Dead Path | 能否区分 path unreachable / path returns empty / path output rejected / precondition identity mismatch？ | four latent dead-path / precondition states | per-class RCA |
| E7 Ablation | Propositions 1-4、invariant checking、boundary、intervention 各贡献多少？ | full test set | per-variant RCA, FDAR |
| E8 Cross-Domain | 七个软件工程领域是否都成立？ | all families over domains | stratified RCA, FDAR |

三者回答不同问题，不能互相替换：

$$
\boxed{\text{Invariant Loss} \neq \text{First Loss} \neq \text{Root Cause}}
$$

```text
Evidence Flow

E0 ──T1──> E1 ──T2──> E2 ──T3──> E3 ──T4──> E4
             │
             │ Invariant Loss
             ↓
          corrupted
                                  │
                                  │ First Loss
                                  ↓
                              absent

             ↑                         ↑
          semantic                 observable
          corruption               disappearance

                         ↓
                    Root Cause
                  (intervention)
```

Invariant Loss 回答“在哪里第一次违反语义不变量”；First Loss 回答“在哪里第一次不可消费”；Root Cause 回答“哪个可干预因素被改变后故障消除”。这一区分使 FLM 不等同于 first erroneous state 或 first divergence。

有一个读表时必须说清的点：在 E1、E2、E3、E4、E5 和 E6 里，component-level RCA 的 FLA 也是 1.000。找到异常阶段不难，尤其在完整 trace 的封闭 benchmark 里。FLM 的贡献不是“发现某个可疑位置”，而是把这个位置进一步约束成可归因边界：哪些阶段可以成为 root cause，哪些必须排除。区分度来自 RCA、confirmed RCA 和 1-FDAR，不是 FLA 单独撑起来的。

我们用 $R$ 表示 stage-level RCA，$C$ 表示 confirmed RCA，$D^+$ 表示 1-FDAR（越高越好）。E1-E6 的 test-set 结果如下：

| Experiment | n | Component RCA $R/C/D^+$ | Symptom-biased LLM $R/C/D^+$ | FLM $R/C/D^+$ | FLM + blind candidate selection $R/C/D^+$ |
|---|---:|---:|---:|---:|---:|
| E1 First-Loss localization | 720 | 0.483 / 0.483 / 0.674 | 0.418 / 0.418 / 0.467 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 |
| E2 Invariant-Loss detection | 420 | 0.338 / 0.338 / 0.664 | 0.664 / 0.664 / 0.748 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 |
| E3 Downstream misattribution | 660 | 0.358 / 0.358 / 0.644 | 0.648 / 0.648 / 0.702 | 1.000 / 1.000 / 1.000 | 0.980 / 0.980 / 1.000 |
| E4 Root-cause confirmation | 780 | 0.446 / 0.446 / 0.622 | 0.435 / 0.435 / 0.479 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 |
| E5 Compound failure | 240 | 0.392 / 0.392 / 0.608 | 0.621 / 0.621 / 0.621 | 1.000 / 1.000 / 1.000 | 0.946 / 0.946 / 1.000 |
| E6 Latent dead path | 240 | 0.258 / 0.258 / 0.258 | 0.158 / 0.158 / 0.158 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 |

Read E2 down to the invariant level and the pattern holds, though component-level RCA varies a lot:

| E2 family | n | Component RCA | Symptom-biased LLM | FLM |
|---|---:|---:|---:|---:|
| Rank loss → positional truncation | 60 | 0.183 | 0.633 | 1.000 |
| Scope filter mismatch | 60 | 0.217 | 0.733 | 1.000 |
| Authority corruption | 60 | 0.383 | 0.717 | 1.000 |
| Provenance corruption | 60 | 0.233 | 0.600 | 1.000 |
| Temporal invalidity | 60 | 0.350 | 0.700 | 1.000 |
| Identity mismatch | 60 | 0.000 | 0.633 | 1.000 |
| Assembly duplicate identity | 60 | 1.000 | 0.633 | 1.000 |

E5 is the useful stress test. Two things are broken at once, so the question is whether a method stops at the loudest downstream symptom or explains the earliest mechanism:

| Compound family | n | Component RCA | Symptom-biased LLM | FLM | FLM + blind candidate selection |
|---|---:|---:|---:|---:|---:|
| Identity mismatch + empty dead path | 60 | 0.117 | 0.683 | 1.000 | 0.883 |
| Provenance corruption + gate error | 60 | 0.283 | 0.733 | 1.000 | 0.950 |
| Rank loss + scope mismatch | 60 | 0.967 | 0.583 | 1.000 | 1.000 |
| Temporal invalidity + budget off-by-one | 60 | 0.200 | 0.483 | 1.000 | 0.950 |

E7 ablation, on the full 1,200-case test set, shows where the improvement comes from:

| Variant | Stage RCA | Confirmed RCA | 1-FDAR |
|---|---:|---:|---:|
| FLM full | 1.000 | 1.000 | 1.000 |
| No first-loss rule | 0.050 | 0.050 | 0.150 |
| No invariant checking | 0.500 | 0.500 | 1.000 |
| No upstream exclusion | 0.050 | 0.050 | 0.150 |
| No minimal probe | 0.432 | 0.432 | 0.644 |
| No intervention | 1.000 | 1.000 | 1.000 |
| No independent replay | 1.000 | 1.000 | 1.000 |

The pattern is clean: the attribution boundary prevents downstream blame; invariant checking finds the earlier corruption; minimal probes stop heuristic distractors from winning. The last two ablations do not hurt in this deterministic replay because independent replay is simulated by another seeded run and intervention is an oracle-supported confirmation, not a human decision process.

E8 uses the same families over seven domain-named instances. In the current generator, domains differ by role names and labels, not by heterogeneous runtimes. FLM is 1.000 on stage RCA, confirmed RCA and 1-FDAR in each of the two windows. That is protocol transfer, not proof of production generality.

### 6.8 Controlled replay

在正式报告真实系统结果前，我们实现了一个冻结 seed 的合成 replay benchmark，用来检查归因规则本身。benchmark 覆盖七个抽象领域——knowledge assistant、agent memory、incident triage、commerce search、compiler/build、data pipeline 和 distributed request——并共享同一 9 阶段 evidence funnel。故障集包括 16 类 single fault 和 4 类 two-fault compound failure。冻结 test set 有 1,200 个 case；independent replay window 用不同 seed stream，有 600 个 case。case、schema、指标、模型卡、数据卡、协议和统计结果都随仓库发布。

全量 test set 的结果如下：

| Method | FLA | ILA | RCA stage | RCA confirmed | 1-FDAR |
|---|---:|---:|---:|---:|---:|
| Final symptom | 0.150 | 0.450 | 0.050 | 0.050 | 0.150 |
| Component-level RCA | 1.000 | 1.000 | 0.420 | 0.420 | 0.578 |
| Existence-only provenance | 1.000 | 0.450 | 0.500 | 0.500 | 1.000 |
| Pattern RCA proxy | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Strong LLM proxy | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Symptom-biased LLM proxy | 0.150 | 1.000 | 0.407 | 0.407 | 0.436 |
| FLM | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| FLM + blind candidate selection | 1.000 | 1.000 | 0.987 | 0.987 | 1.000 |

FLM 在两个窗口都保持 stage RCA、confirmed RCA 和 1-FDAR 为 1.000。相对 symptom-biased LLM proxy，stage RCA 在 test window 提高 0.593（95% CI $[0.566,0.621]$），在 replay window 提高 0.575（95% CI $[0.537,0.615]$）。相对 component-level RCA，stage RCA 和 confirmed RCA 提高 0.580（95% CI $[0.552,0.608]$；McNemar exact $p<10^{-209}$），1-FDAR 提高 0.422（95% CI $[0.394,0.452]$）。这些数字与上一节的 E1-E8 分层结果一致，但不要把它读成对 strong LLM proxy 的胜利；strong proxy 在完整 trace 下同样是 1.000。

Blind candidate selection 测的是干预目标不确定时的鲁棒性。规则很简单：每个 case 从 `blind_intervention_candidates` 随机选一个干预点，选到失败的主组件才算 confirmed，选到其他相关 component 就失败。冻结 generator 把候选分布设为 85% primary root-cause stage、15% 其他相关 component。这是 synthetic candidate-selection control，不是人类被试实验。

这些结果支持一个受限但重要的结论：在 trace 完整可观测、ground truth 由冻结注入配置生成的受控环境里，FLM 的边界规则能稳定防止 downstream misattribution，并在两个 seed window 里复现优势。它不能外推到 trace 不完整、非局部因果、真实 LLM 推理或人类干预选择。

## 7 Real-world case study: vector-arm ordering incident

### 7.1 Symptom

This incident occurred in the production recall pipeline of SPM-Polaris; the methodology is stated independently of that system instance.

真实链路中的预期行为是 vector arm 返回 ranked evidence，metadata lookup 补充字段，cap 保留 top-$N$，最终 reader 消费结果。实际表现为预期 evidence 在最终上下文中缺失，症状类似 recall failure。

### 7.2 Evidence funnel

相关 evidence 的状态如下：

| 阶段 | Evidence | Invariant | 结果 |
|---|---|---|---|
| Vector retrieval | present | order present | ranked evidence 产生 |
| Metadata lookup | present | **rank lost** | 返回 unordered result |
| Cap | present → absent | order already lost | unordered result 被位置截断 |
| Selector | absent | — | evidence 未到达 |
| Gate | absent | — | evidence 未到达 |
| Reader | absent | — | evidence 未到达 |

因此：

```text
Invariant Loss = metadata lookup: order invariant lost
First Loss     = cap: unordered evidence positionally truncated
Root Cause     = metadata lookup result did not preserve retrieval rank
```

### 7.3 Excluded downstream causes

根据 First Loss boundary，embedding、selector、gate、Echo 和 reader 不满足该 evidence 的归因条件。它们可能是后续查询中的独立缺陷，但不能解释本条 evidence 在 cap 前后的消失。

### 7.4 Confirmation

确认流程如下：

1. **Fail-before**：原始配置中 ranked evidence 进入 metadata lookup，lookup 输出无序，随后 cap 截断。
2. **Minimal probe**：在 lookup 输出与 cap 输入处记录 rank 和 key，确认 order invariant 在 lookup 后丢失。
3. **Single variable**：冻结 corpus、query、embedding、retrieval 和 cap；只修改 lookup 输出以保留 retrieval rank。
4. **Pass-after**：同一查询和窗口中目标 evidence 通过 cap 并进入后续阶段。
5. **Independent replay**：独立进程和时间窗口得到一致 First Loss 与 root cause。

这个 real-world case study 的价值是解释方法和机制，不是统计证据。它显示 First Loss 与 Invariant Loss 的分工：First Loss 指出 evidence 在哪里消失，Invariant Loss 指出更上游的语义损坏；root cause 位于违反 ordering invariant 的 lookup predicate。受控 benchmark 验证可重复性和可测量性；这里验证工程可解释性。一个 incident 不能说明 FLM 在真实世界普遍有效。

## 8 Discussion

### 8.1 First Loss is not automatically the root cause

First Loss 是归因边界。它排除了从未收到 evidence 的下游组件，但不自动指定根因。必须继续区分：

1. 阶段本身错误地丢弃合法 evidence；
2. 上游 invariant loss 使下游 predicate 正确拒绝 evidence；
3. 配置、查询或数据本身导致合法 rejection。

因此，root cause 可能在 Invariant Loss、First Loss 或其间的 predicate 中。

First Loss boundary 还依赖局部传播假设。常见安全场景是 predicate 检查同一 evidence 的 invariant；危险场景是上游通过共享配置、缓存、并发副作用或隐式协议改变下游行为，而 evidence 本身看起来完整。遇到这类非局部机制时，FLM 必须把 boundary 从“组件排除”降级为“该 evidence 的直接路径排除”，并新增 cross-stage causal probe。这个限制说明方法可证伪，也说明边界规则不能脱离 observation model 使用。

### 8.2 Multiple first losses

多个 evidence 可能在同一或不同阶段丢失。FLM 不做单一全局 First Loss 断言，而是对每个 evidence ID 计算 First Loss，然后构建阶段级的 attribution frontier。若一个失败由多条 evidence 共同引起，root-cause 解释必须覆盖所有关键 evidence 的 frontier。

### 8.3 Unobservable systems

如果服务或库不记录中间 evidence 状态，FLM 只能给出有界结论。插入探针、结构化日志或回放代理是必要前置条件。论文不声称在不可观测边界内保证找到真实 First Loss。

### 8.4 Non-deterministic systems

异步调度、并发写入和模型生成都可能使 trace 变化。FLM 要求固定 seed、重复探针和独立窗口。若归因不稳定，应把 First Loss 表述为分布而不是单点。

### 8.5 Counterfactual extension

FLM 目前以归因规则和确认协议为主。未来可把 First Loss 状态纳入 causal graph，用干预估计“恢复 invariant”“保留 evidence”或“绕过候选 predicate”对最终输出的影响。这会把 attribution boundary 从可检验规则进一步形式化为因果模型。

## 9 Conclusion

复杂系统中的 root-cause attribution 不应从最终症状开始，也不应从组件错误计数开始。FLM 主张沿 evidence provenance 找到 evidence 首次失去或失真的位置：First Loss 划定可归因边界，Invariant Loss 揭示存在但已损坏的 evidence，最小干预和独立回放确认因果解释。其核心纪律可以概括为：不要把失败归因给从未接收到必要 evidence 的组件；先找到 evidence 第一次丢失或失真的地方，再归因下游。

## Author contributions

Using CRediT terminology: **Chen KuangYu**: conceptualization, methodology, software, investigation, validation, data curation, writing - original draft, writing - review & editing, supervision, project administration. AI assistants supported prose drafting, code implementation, and experiment organization under the author's direction.

## Funding and acknowledgements

This work was independently conducted at Veridical Tech, Inc. and Xi'an University of Science and Technology Hi-tech College. No external funding is reported.

## Conflicts of interest

The author reports affiliation with Veridical Tech, Inc. and Xi'an University of Science and Technology Hi-tech College, and no other competing financial interests related to this work.

## Data and code availability

The synthetic benchmark, generator, conservation schema, frozen cases, per-case metrics, statistical summaries, protocol, data card, and model card are released in the accompanying repository. The real SPM-Polaris vector-arm incident is published only as a structured qualitative replay. Code is licensed under MIT; benchmark data are licensed under CC-BY-4.0; the paper text is licensed under CC-BY-4.0. A permanent artifact DOI is available at [https://doi.org/10.5281/zenodo.22704463](https://doi.org/10.5281/zenodo.22704463).

## Reproducibility statement

The benchmark uses a frozen master seed and separate test/replay seed streams. The full run can be reproduced with:

```bash
python3 benchmark/run_experiments.py --output-dir benchmark/results --samples 5000
python3 benchmark/conservation_schema.py benchmark/results/cases.jsonl --split test
python3 benchmark/conservation_schema.py benchmark/results/cases.jsonl --split replay
```

CI runs a smoke test with reduced bootstrap samples. Published results use 5,000 paired bootstrap samples and require Python 3.9 or later. No third-party packages are required.

## Ethics statement

No human-subject experiments were performed. The blind intervention condition is a synthetic candidate-selection control, not a human study. The real incident replay contains no confidential query, tenant, prompt, payload, or production artifact.
