# 智能场外基金系统 v3：开发设计细化（策略接口 + 数据接入）

> 目标：在 v2 的产品规划基础上，补齐“工程可实现”的设计细节，确保可以直接进入后端开发。
>
> 适用范围：单用户、免费优先、仅策略参考（不自动交易）。

---

## 1. 设计目标与原则

1. **策略与数据解耦**：策略引擎不直接依赖任一第三方数据源字段。
2. **结果可追溯**：任一建议都可追到“输入快照 + 参数版本 + 规则版本”。
3. **执行可解释**：输出不仅有分数和动作，还必须有原因与规整偏差。
4. **错误可降级**：当数据不完整或质量不足时，系统自动退化为 `hold` 并标注风险。
5. **迭代可扩展**：先支持评分策略，再支持形态策略组合，不推翻原接口。

---

## 2. 分层架构（实现视角）

```text
Data Source A/B
   ↓
[Data Adapter Layer]   # 抓取、标准化、质量评分
   ↓
[Feature Layer]        # 分位/波动率/偏离等特征
   ↓
[Strategy Layer]       # score/action/reasons
   ↓
[Allocator Layer]      # 风险预算与份额规整
   ↓
[Execution Model]      # 手续费 + T+n 生效模拟
   ↓
API / Reports
```

### 2.1 关键模块职责

- `data_adapters/`
  - 拉取基金估值、指数行情、补充元数据。
  - 统一为内部 DTO（避免上层感知供应商差异）。
- `features/`
  - 计算估值分位、指数方向分、波动率状态、置信度。
- `strategies/`
  - 基于统一上下文输出信号。
  - 通过注册表按 `strategy_name` 动态装载。
- `allocators/`
  - 将信号映射为原始份额，再执行最小份额与 lot 规整。
- `engines/pnl.py`
  - 按 T+n 与手续费形成真实生效收益。

---

## 3. 统一领域模型（建议）

## 3.1 输入模型

```python
@dataclass
class MarketContext:
    trade_date: date
    session_type: Literal["pre_open", "post_close"]
    fund_code: str
    estimated_nav: float | None
    index_change_pct: float | None
    volatility_n: float | None
    quality_score: int
    quality_flags: list[str]
    source: str
```

```python
@dataclass
class HoldingContext:
    fund_code: str
    holding_shares: Decimal
    avg_cost_nav: Decimal
    cash_allocated: Decimal
```

```python
@dataclass
class TradeRule:
    fund_code: str
    buy_fee_rate: Decimal
    sell_fee_rate: Decimal
    redemption_fee_rule_json: dict
    tn_confirm_days: int
    tn_redeem_days: int
    min_trade_shares: Decimal
    trade_lot: Decimal
```

## 3.2 输出模型

```python
@dataclass
class ReasonItem:
    key: str
    value: float | str
    weight: float
    comment: str
```

```python
@dataclass
class StrategySignal:
    strategy_name: str
    signal_score: int       # 0-100
    signal_action: Literal["buy", "hold", "sell"]
    confidence: float       # 0-1
    reasons: list[ReasonItem]
```

```python
@dataclass
class PositionRecommendation:
    fund_code: str
    recommended_delta_shares_raw: Decimal
    recommended_delta_shares_rounded: Decimal
    rounding_lot: Decimal
    action: Literal["buy", "hold", "sell"]
    notes: list[str]
```

---

## 4. 策略接口契约（核心）

## 4.1 抽象接口

```python
class Strategy(Protocol):
    name: str

    def compute_signal(
        self,
        market: MarketContext,
        holding: HoldingContext,
        params: dict,
    ) -> StrategySignal:
        ...
```

## 4.2 注册表接口

```python
class StrategyRegistry:
    def register(self, strategy: Strategy) -> None: ...
    def get(self, name: str) -> Strategy: ...
    def list(self) -> list[str]: ...
```

## 4.3 分配器接口

```python
class Allocator(Protocol):
    def suggest(
        self,
        signal: StrategySignal,
        holding: HoldingContext,
        rule: TradeRule,
        risk_budget: Decimal,
    ) -> PositionRecommendation:
        ...
```

### 4.4 建议的默认实现

- `LongShortReversalV1Strategy`
  - 因子：估值分位、指数方向、波动率抑制。
  - 输出：0-100 分 + buy/hold/sell。
- `ScoreToSharesAllocator`
  - 分段映射（默认）：
    - `0-30`: 减仓
    - `31-69`: 观望
    - `70-100`: 加仓
  - 映射完成后应用：
    1) `min_trade_shares`；
    2) `trade_lot` 规整；
    3) 偏差超阈值提示人工确认。

---

## 5. 数据接入设计（Data Adapter）

## 5.1 适配器规范

```python
class DataAdapter(Protocol):
    source_name: str

    async def fetch_fund_snapshot(self, fund_code: str, trade_date: date) -> dict: ...
    async def fetch_index_snapshot(self, index_code: str, trade_date: date) -> dict: ...
    def normalize(self, payload: dict) -> MarketContext: ...
```

## 5.2 多源合并流程

1. 主源拉取；失败则备源补齐。
2. 同字段冲突时按可信度优先级决策。
3. 计算 `quality_score`（0-100）：
   - 字段完整性（40）
   - 时间新鲜度（30）
   - 主备一致性（20）
   - 历史偏离合理性（10）
4. `quality_score < 60`：策略层仅允许输出 `hold`。

## 5.3 快照落库建议

建议在既有 `market_snapshots` 上新增（可后续 migration）：

- `quality_score` int
- `quality_flags` jsonb
- `source_priority` int
- `ingest_run_id` uuid
- `raw_payload_ref` text

---

## 6. 调度与任务编排

## 6.1 两次任务职责

- `pre_open`（09:20）
  - 读取前日收盘+当日盘前估算。
  - 生成“预案建议”（可执行上限低）。
- `post_close`（15:10）
  - 读取收盘确认数据。
  - 生成“正式建议 + 当日收益 + 月度聚合增量”。

## 6.2 任务流水（每个 fund）

1. 数据抓取与质量评估。
2. 构建 `MarketContext`。
3. 调用策略 `compute_signal`。
4. 调用分配器生成份额建议。
5. 调用收益引擎刷新 `daily_pnl`。
6. 写入 `strategy_signals` 与 `position_recommendations`。

## 6.3 错误策略

- 数据缺失：记录错误 + `hold` 建议。
- 单基金失败：不中断整批任务，继续下一个。
- 全局失败：标记 job 为 failed 并保留 trace。

---

## 7. 收益引擎（手续费 + T+n）接口

```python
class PnLEngine(Protocol):
    def apply_trade(self, trade_event: dict, rule: TradeRule) -> dict: ...
    def effective_position(self, as_of: date, fund_code: str) -> Decimal: ...
    def daily_pnl(self, as_of: date, fund_code: str, nav: Decimal) -> dict: ...
```

### 7.1 处理顺序（固定）

1. 先更新申赎待确认队列。
2. 计算当日生效份额。
3. 按生效份额计算毛收益。
4. 扣除当日应计手续费。
5. 输出净收益与拆解明细。

---

## 8. API 扩展建议（在 v2 基础上）

保留现有接口，同时补充可运维性接口：

- `GET /jobs/runs?date=YYYY-MM-DD`
- `GET /market/snapshots/latest?fund_code=...`
- `GET /strategies`
- `GET /strategies/{name}/params`
- `PUT /strategies/{name}/params`

建议统一响应 envelope：

```json
{
  "code": 0,
  "message": "ok",
  "trace_id": "...",
  "data": {}
}
```

---

## 9. 参数治理与版本管理

## 9.1 参数表建议

`strategy_params`

- `strategy_name`
- `param_key`
- `param_value`
- `version`
- `effective_from`
- `updated_at`

## 9.2 版本冻结策略

- 每日盘后任务运行时，锁定一份参数快照写入 `reason_json.meta`：
  - `param_version`
  - `strategy_version`
  - `allocator_version`

这样可保证后续复盘时结果可重现。

---

## 10. 里程碑拆解（可直接分任务）

### M1（1-2 天）

- 建立项目目录骨架（adapters / strategies / allocators / engines）。
- 完成接口定义与注册表。
- 打通单基金 mock 数据到信号输出。

### M2（2-3 天）

- 接入主备数据源。
- 完成质量评分与降级规则。
- 快照落库 + 任务日志。

### M3（2-3 天）

- 完成 allocator 规整逻辑。
- 完成手续费与 T+n 的 PnL 引擎。
- 打通今日建议 + 当日收益 API。

### M4（1-2 天）

- 增加策略参数管理接口。
- 增加 jobs/snapshots 运维接口。
- 补充回放脚本（指定交易日重算）。

---

## 11. 推荐默认值（先落地，再迭代）

- `trade_lot`: `10`
- `min_trade_shares`: `100`
- `score_buy_threshold`: `70`
- `score_sell_threshold`: `30`
- `quality_min_to_trade`: `60`
- `pre_action_cap`: `0.10`
- `stop_loss_pct`: `0.06`

> 以上均放入参数表，不在代码写死。

---

## 12. 下一步可直接开始的开发清单

1. 先做 `Strategy` + `Allocator` 协议与默认实现。
2. 做 `DataAdapter` 的 mock 版本，先打通链路。
3. 接入真实数据源并上质量评分。
4. 完成 `post_close` 全流程任务。
5. 最后补 `pre_open` 预案任务与前端展示字段。

