# 《多空转折一手抓》策略调研记录（首版）

> 说明：你要求“先从网上获取该书信息并阅读策略核心”。我在当前容器中尝试了联网检索，但外网请求被网关 `403` 拦截，因此本文件先给出：
> 1）检索尝试与受限证据；2）可立即用于系统实现的“策略工程化骨架”；3）待你补充书内关键规则后的精确落地位点。

---

## 1. 联网检索尝试与结果

我执行了如下检索命令：

- `curl -L 'https://duckduckgo.com/html/?q=多空转折一手抓'`
- `curl -L 'https://www.bing.com/search?q=多空转折一手抓'`
- `curl -I https://raw.githubusercontent.com`

返回均为：`CONNECT tunnel failed, response 403`。

结论：本运行环境当前无法直接访问外网搜索站点，暂时不能在容器内完成“在线阅读与摘录原文”。

---

## 2. 在无法外网时，先可落地的“策略工程化方案”

为了不阻塞开发，我先把《多空转折一手抓》作为**策略插件**接入框架，做到“规则可替换、参数可配置、结果可回溯”。

### 2.1 策略接口（必须）

```python
class Strategy(Protocol):
    name: str
    def compute_signal(self, snapshot: MarketSnapshot, holding: HoldingState, params: dict) -> StrategyResult:
        ...
```

`StrategyResult` 至少包含：

- `signal_score: int`（0-100）
- `signal_action: Literal['buy','hold','sell']`
- `delta_shares_raw: Decimal`
- `delta_shares_rounded: Decimal`
- `reasons: list[ReasonItem]`

### 2.2 多空转折策略插件占位（v0）

建议先落地 `long_short_reversal_v1`，并在 `strategy_params` 表维护参数：

- `lookback_days`
- `reversal_threshold`
- `trend_filter_weight`
- `volatility_cap`
- `max_position_delta_pct`
- `trade_lot`

这样等你给到书中的明确规则后，只要替换 `compute_signal()` 内部逻辑，不需要改数据库和 API。

### 2.3 输出与执行约束（与你需求对齐）

- 输出必须有“精确份额 + 规整份额”；
- 规整规则以 `trade_lot` 为准（10 或 100 份）；
- 小于最小交易份额自动降为 `hold`；
- 前端展示“信号分、建议份额、关键依据”三元组。

---

## 3. 先验可行的“多空转折”通用指标骨架（待书内规则替换）

> 下述是通用“转折类”策略骨架，目的是保证系统先跑通；不是对该书原文的逐字复现。

可先用 4 组因子拼出 0-100 分：

1. **估值分位因子**：当前估值在近 N 日中的分位；
2. **趋势方向因子**：短中期均线/动量方向；
3. **波动约束因子**：波动过高则降低仓位变化；
4. **回撤保护因子**：当回撤超阈值时限制继续加仓。

分数映射动作：

- `0-30`：减仓
- `31-69`：持有
- `70-100`：加仓

份额换算：

- `delta_shares_raw = risk_budget * f(signal_score) / nav_est`
- `delta_shares_rounded = round_to_lot(delta_shares_raw, trade_lot)`

---

## 4. 与收益模块的耦合点（手续费 + T+n）

策略建议在落地收益计算时要经过“执行模型层”：

- 买入：先扣申购费，再按 T+n 生效份额；
- 卖出：先按持有天数算赎回费，再按 T+n 返还现金；
- 当日收益与月报统一用“生效持仓”口径，不用“下单申请口径”。

---

## 5. 你给我书内信息后，我将立即做的精确化更新

请任选一种方式提供材料（越少越好）：

1. 该书中“多空转折”核心章节目录（拍照/文字都可）；
2. 你最认可的 3-5 条明确入场/减仓规则；
3. 你实际使用的阈值（例如某指标大于/小于多少触发动作）。

拿到后我会输出 `v2.1`：

- 书内规则 -> 参数化表达（可直接入库）
- 每条规则对应的 `reason_code`
- 回测字段与可视化指标清单

---

## 6. 当前阻塞与建议

- 阻塞：容器无法访问外网，无法在本地完成在线检索与原文核验；
- 建议：你可先给我该书核心规则摘要，我这边直接把策略实现与数据结构一次性定版。

