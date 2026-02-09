# 模型吞吐性能测试&Inference Benchmarker 实操指南

## 推荐使用GPUStack的[性能测试脚本](https://github.com/gpustack/gpustack/blob/main/benchmarks/benchmark_serving.py)

**11/26日更新：Inference Benchmarker过于复杂，如果只是想简单测试下关键性能指标。**

```bash
python benchmark_serving.py \
  --model openai/gpt-oss-20b \
  --embeddings \
  --num-requests 100 \
  --concurrency 10 \
  --server-url http://127.0.0.1:8080 \
  --api-key gpustack-key-123 \
  --json \
  --result-file emb.json
============ Serving Benchmark Result ============
Successful requests:                     1000
Benchmark duration (s):                  42.03
Total input tokens:                      215312
Total generated tokens:                  194171
Request throughput (req/s):              23.79
Output token throughput (tok/s):         4620.12
Peak output token throughput (tok/s):    7484.00
Peak concurrent requests:                1000.00
Total Token throughput (tok/s):          9743.28
---------------Time to First Token----------------
Mean TTFT (ms):                          13654.59
Median TTFT (ms):                        13063.93
P99 TTFT (ms):                           30306.72
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          48.57
Median TPOT (ms):                        45.15
P99 TPOT (ms):                           110.58
---------------Inter-token Latency----------------
Mean ITL (ms):                           41.95
Median ITL (ms):                         33.96
P99 ITL (ms):                            112.27
==================================================
```

部署完模型后，建议使用[inference-benchmarker](https://github.com/huggingface/inference-benchmarker)测试下性能上限，便于控制并发预期。

![架构图](/images/img_14_NTA5YTNmNGQ2OGN.jpg)

![配置示例](/images/img_15_NTMxMjk2MTRhMWQ.jpg)

![测试结果](/images/img_27_YWUxNzIyNGU0MDg.jpg)

## Inference Benchmarker

### 1. 合并后的维度/指标表

| 指标类别            | 具体项（合并后）                                             | 说明                                          |
| ------------------- | ------------------------------------------------------------ | --------------------------------------------- |
| **吞吐量**          | `requests/sec` (RPS), `tokens/sec`                           | 每秒成功请求数；每秒生成 token 数             |
| **延迟（分位数）**  | `p50`, `p90`, `p95`, `p99`                                   | 端到端延迟（ms），反映典型与尾部延迟          |
| **延迟（流/首包）** | `TTFT`, `Inter-Token latency`, `Time per token`              | 首个 token 返回时间、token 间延时             |
| **成功率 / 错误率** | `success_rate`, `error_rate`, `timeout_count`                | 成功率、失败或超时比例                        |
| **资源/稳定性信号** | GPU 利用率、显存、CPU、内存、重试次数                        | 需外部监控（如 `nvidia-smi`、Prometheus）     |
| **配置上下文**      | prompt 长度、decode 参数、batch size、并发 VUs、请求率、profile | 测试输入与行为参数，影响结果可比性            |
| **测试阶段指标**    | `warmup` 时间、`step duration`、`detected_max_throughput`    | warmup 是否充分、单步耗时、自动探测的最大吞吐 |
| **输出统计**        | 平均值、标准差、原始请求时间线（JSON）                       | 用于后续分析（延迟分布、时间序列图）          |
| **其它**            | `latencies histogram`, `tail latency trends`, `percentile over time` | 排查突发延迟或资源退化                        |

> **提示：** JSON 字段名示例：`requests_per_second`, `tokens_per_second`, `p50_latency_ms`, `p99_latency_ms`, `error_rate`

### 2. 三种模式的可运行命令

> **注意：** `--benchmark-kind` 与 `--profile` 互斥，不能同时使用。

#### A) 显式指定模式（推荐用于可控测试）

**Sweep（自动扫 QPS）**

```bash
RUST_LOG=warn ./target/release/inference-benchmarker \
  --tokenizer-name Qwen/Qwen3-VL-8B-Instruct \
  --model-name qwen3-vl-8b-instruct \
  --url http://localhost:8001 \
  --api-key <YOUR_API_KEY> \
  --benchmark-kind sweep \
  --num-rates 10 \
  --duration 120s \
  --warmup 30s \
  --dataset-file data.json \
  --decode-options "num_tokens=80,max_tokens=100,min_tokens=60,variance=10"
```

**Rate（固定请求率）**

```bash
RUST_LOG=warn ./target/release/inference-benchmarker \
  --tokenizer-name Qwen/Qwen3-VL-8B-Instruct \
  --model-name qwen3-vl-8b-instruct \
  --url http://localhost:8001 \
  --api-key <YOUR_API_KEY> \
  --benchmark-kind rate \
  --rates "5,10,25,50" \
  --duration 120s \
  --warmup 30s \
  --dataset-file data.json \
  --decode-options "num_tokens=80,max_tokens=100,min_tokens=60,variance=10"
```

**Throughput（固定并发 VUs）**

```bash
RUST_LOG=warn ./target/release/inference-benchmarker \
  --tokenizer-name Qwen/Qwen3-VL-8B-Instruct \
  --model-name qwen3-vl-8b-instruct \
  --url http://localhost:8001 \
  --api-key <YOUR_API_KEY> \
  --benchmark-kind throughput \
  --max-vus 64 \
  --duration 120s \
  --warmup 30s \
  --dataset-file data.json \
  --decode-options "num_tokens=80,max_tokens=100,min_tokens=60,variance=10"
```

#### B) 使用预设 Profile（适合快速验证）

```bash
RUST_LOG=warn ./target/release/inference-benchmarker \
  --tokenizer-name Qwen/Qwen3-VL-8B-Instruct \
  --model-name qwen3-vl-8b-instruct \
  --url http://localhost:8001 \
  --api-key <YOUR_API_KEY> \
  --profile chat \
  --duration 120s \
  --warmup 30s
```

> **注意：** Profile 内部已定义测试逻辑（可能是 rate/sweep/throughput 中的一种），无法再指定 `--benchmark-kind`。

### 3. 关键机制说明

#### Sweep 的 QPS 范围如何决定？

- **最低 QPS：** 通常为 1 RPS 或 `detected_max / 10`，代表轻载。
- **最高 QPS：** 通过递增负载直到出现大量错误/超时/延迟飙升，取前一个稳定点作为上限。

**控制建议：**

- 若需精确控制范围，先用 `rate` 模式手动探测上限；
- 或修改源码/配置强制设置 `min_rate` / `max_rate`（若支持）。

#### Rate vs Throughput 的本质区别

| 模式           | 控制变量         | 行为                  | 适用场景                      |
| -------------- | ---------------- | --------------------- | ----------------------------- |
| **Rate**       | 固定 RPS         | 恒定请求到达率        | 模拟真实 API QPS，测延迟/错误 |
| **Throughput** | 固定 VUs（并发） | 每个 VU 循环发请求    | 测并发容量、资源占用          |
| **Sweep**      | 自动探测 max     | 扫描 min→max QPS 曲线 | 快速评估系统极限              |

> **选型口诀：**
>
> - "我要知道 100 RPS 下 p99 是多少" → 用 `rate`
> - "我要知道 32 并发下 GPU 是否打满" → 用 `throughput`
> - "我想自动找出最大吞吐" → 用 `sweep`

### 4. 推荐压力测试流程（实操步骤）

#### Step 1: 准备

- 固定 `prompt` 和 `decode` 长度（如 `num_tokens=80`）
- 开启系统监控：`nvidia-smi -l 1`, `htop`, Prometheus 等
- 确保后端日志级别为 `INFO` 或 `WARN`

#### Step 2: Sanity Check（功能验证）

```bash
--benchmark-kind rate --rates "1" --duration 30s --warmup 10s
```

**预期：** error_rate ≈ 0%，TTFT 正常

#### Step 3: 粗略探测上限

```bash
for vus in 4 8 16 32; do
  ./bench ... --benchmark-kind throughput --max-vus $vus --duration 60s
done
```

**目标：** 找到第一个出现 error 或延迟突增的 VU 数

#### Step 4: Sweep 扫描完整曲线

```bash
--benchmark-kind sweep --num-rates 10 --duration 120s --warmup 30s
```

**分析输出：** 定位 `detected_max_throughput` 和 p99 拐点

#### Step 5: 关键点细测（Rate 模式）

```bash
# 假设 detected_max = 100 RPS
--benchmark-kind rate --rates "10,25,50,75,90" --duration 300s --warmup 30s
```

**重点记录：** p95/p99、error_rate、tokens/sec

#### Step 6: 并发验证（Throughput）

```bash
--benchmark-kind throughput --max-vus 32 --duration 600s
```

**观察：** GPU 显存是否稳定？有无 OOM？延迟是否漂移？

#### Step 7: 长稳测试（可选）

- 在 75% max 吞吐下跑 1–4 小时
- **监控：** 内存泄漏、错误累积、延迟趋势

#### Step 8: 结果归档

- 保存所有 `.json` 输出
- 绘制三张核心图：
  1. 吞吐 vs p99 延迟
  2. QPS vs error_rate
  3. GPU 利用率/显存 vs 时间

### 5. 常见错误处理

#### 错误：`--benchmark-kind cannot be used with --profile`

**原因：** CLI 设计为互斥。

**解决方案：**

- **方案 A（推荐）：** 不用 `--profile`，改用 `--dataset-file` + `--decode-options` 显式控制
- **方案 B：** 只用 `--profile`，接受其内置行为（查看 `profiles/` 目录了解细节）

> **最佳实践：** 生产级压测一律使用显式参数（方案 A），确保可复现、可对比。Profile 仅用于快速 demo。

#### LLM 压测与 vLLM 调度常见误区

**误区 1：RPS = 模型处理速度**

RPS 是施加的压力，不是模型的实际处理能力。模型吞吐受限于 GPU decode 速度、批处理能力和 KV cache 容量。超限会导致排队、超时或拒绝。

**误区 2：decode-options 强制输出长度**

min_tokens / max_tokens 是生成目标，非硬性限制。若 prompt 要求更多内容，模型仍会生成更长响应，压测工具不会干预。

**误区 3：vLLM 不会排队或容量无限**

vLLM 内部基于队列 + scheduler + continuous batching。高负载下会持续接收请求并排队，但延迟和显存消耗将急剧上升。

**误区 4：不设置 max_num_seqs / max_model_len / kv_cache_size 无影响**

默认配置倾向于最大化吞吐，易导致 OOM 或延迟雪崩。必须根据硬件显存和预期负载显式限制。

**误区 5：RPS 与 QPS 本质不同**

二者语义略有差异，但常可互换：

- **RPS：** 客户端每秒发送请求数（输入压力）
- **QPS：** 服务端每秒成功处理请求数（实际产能）

**误区 6：fixed RPS 与 fixed VUs 等效**

- **Fixed VUs（固定虚拟用户）：** 用户循环发请求，实际 RPS 随延迟波动
- **Fixed RPS：** 严格控制每秒请求数，更稳定可控

两者压测结果差异显著。

**误区 7：warmup 仅用于"预热几秒"**

Warmup 的核心作用是消除 JIT 编译、模型加载、KV cache 冷启动等一次性开销，确保压测数据反映稳态性能。

#### LLM 压测核心 Mental Model（5 句）

1. RPS 是施压，QPS 是产能。
2. 超出产能就排队，排队则延迟上升。
3. KV cache 决定显存上限，撑满即 OOM。
4. decode-options 影响 token 数，但不强制截断。
5. vLLM 本质是"请求排队 + token 调度"的吞吐引擎。

## 模型部署相关

### 模型加速方案

**扩展 KV 缓存**

集成扩展 KV 缓存方案，显著降低首 Token 延迟（TTFT），在 vLLM 中使用 LMCache，在 SGLang 中使用Hicache。特别适用于长上下文和多轮对话推理。

**推测解码配置**

支持前沿推测解码算法（EAGLE3、MTP、N-gram），提供草稿模型下载与管理，降低用户使用负担。

![推测解码配置](/images/img_30_YzgxNDRlZjk1NDQ.png)

### 模型推荐列表

| 类型                                              | 型号                                        | 推荐理由                                                     | 显存（vLLM、KV Cache）                                    | 备注                                                         |
| ------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------- | ------------------------------------------------------------ |
| LLM                                               | Qwen/Qwen3-30B-A3B-Instruct（上下文开多少） | 速度快，资源占用少，能力强，没有烦人的思考模式               | 72 GB （基于vllm运行，自动压缩后48G）                      | --enable-auto-tool-choice  --tool-call-parser=hermes         |
| GPT-OSS-20B                                       | 速度极快                                    | 20GB                                                         | 速度极快                                                  |                                                              |
| VLM                                               | Qwen/Qwen3-VL-8B-Instruct（图片语意理解）   | 资源占用较少少，模型能力强                                   | 36 GB                                                     | --enable-auto-tool-choice  --tool-call-parser=hermes         |
| MinerU2.5-2509-1.2B（仅OCR）PaddleOCR-VL（仅OCR） | 速度超快，资源占用少，OCR效果稳定           | 6GB                                                          | 优先考虑PaddleOCR-VL，更加稳定                            |                                                              |
| Embedding                                         | BAAI/bge-m3                                 | 老牌模型，资源占用少。Embedding一般确定好了后面就不会换了。这种模型还是得稳定，一些刚出的Embedding没有经过社区验证精度容易出问题 | 8 GB                                                      | 维度1024                                                     |
| Rerank                                            | BAAI/bge-reranker-v2-m3                     | 同上                                                         | 4 GB                                                      |                                                              |
| 文档解析                                          | 自研文档解析服务                            |                                                              | 一般一张4090就可以了                                      | 大纲解析只有一个worker，多任务走队列；视觉解析有多个worker，并发上限取决于VLM上限。知识库文档同步会触发长期大量文档解析任务，需要做兜底机制确保服务稳定运行 |

### 常见问题

在使用张量并行（Tensor Parallelism, TP）部署大模型时，**注意力头数必须能被使用的 GPU 数量整除**，这是主流框架（如 vLLM、Megatron、DeepSpeed）的硬性要求。原因和应对方式如下：

**为什么必须整除？**

- 多头注意力机制中，每个注意力头是独立计算的。
- 张量并行会把同一层的 Q、K、V 权重按"头"切分到不同 GPU 上，每张卡负责处理完整且数量相等的一组头。
- 如果头数不能被 GPU 数整除，就无法均匀分配，会导致：
  - 某些 GPU 需要处理"半个头"或拼接不同头的数据；
  - 通信模式变得复杂且不均衡；
  - 框架直接报错，拒绝启动。

**举例：** 32 个头的模型，只能用 1、2、4、8、16、32 张卡做张量并行；不能用 3、5、6、7 等卡数。
