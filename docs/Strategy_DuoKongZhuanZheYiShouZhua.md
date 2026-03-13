# 《多空转折一手抓》策略调研记录（网络复核版）

> 目标：按你的要求，优先通过互联网搜集该书公开信息，并沉淀到可用于策略实现的文档。

---

## 1) 在线检索执行记录（本次）

本次在容器中执行了以下命令进行公开信息检索：

1. `curl -L 'https://www.baidu.com/s?wd=多空转折一手抓'`
2. `curl -L 'https://httpbin.org/get'`
3. `curl -L 'http://example.com'`
4. `curl -L 'http://openlibrary.org/search.json?q=多空转折一手抓'`

观测结果：

- 对 HTTPS 站点，返回 `CONNECT tunnel failed, response 403`；
- 对 HTTP 站点，返回 `Domain forbidden`。

结论：当前容器虽然配置了代理环境变量，但外部域名访问仍被策略网关阻断，暂时无法在此环境内直接抓取书籍网页信息。

---

## 2) 已确认不阻塞开发的落地方式

在无法直接在线抓取原书内容时，先按“可替换策略插件”实现，确保后续拿到规则后可无缝替换：

### 2.1 策略接口约定

```python
class Strategy(Protocol):
    name: str

    def compute_signal(
        self,
        snapshot: MarketSnapshot,
        holding: HoldingState,
        params: dict,
    ) -> StrategyResult:
        ...
```

`StrategyResult` 字段：

- `signal_score`（0-100）
- `signal_action`（`buy` / `hold` / `sell`）
- `delta_shares_raw`（原始建议份额）
- `delta_shares_rounded`（按 lot 规整份额）
- `reasons`（关键依据明细）

### 2.2 策略插件占位

- 策略名：`long_short_reversal_v1`
- 参数建议：
  - `lookback_days`
  - `reversal_threshold`
  - `trend_filter_weight`
  - `volatility_cap`
  - `max_position_delta_pct`
  - `trade_lot`

说明：等拿到《多空转折一手抓》的明确规则后，仅替换 `compute_signal()` 逻辑与参数默认值，不改数据库和 API。

---

## 3) 书籍信息采集模板（待联网或你提供线索后补全）

> 为避免再反复改结构，这里先定义采集模板；后续拿到来源即可补齐。

### 3.1 书籍基础信息

- 书名：`多空转折一手抓`
- 作者：`待补充`
- 出版社：`待补充`
- 出版时间：`待补充`
- ISBN：`待补充`

### 3.2 策略核心摘要（待补）

- 核心理念：`待补充`
- 入场条件：`待补充`
- 减仓/离场条件：`待补充`
- 仓位管理规则：`待补充`
- 风险控制规则：`待补充`

### 3.3 参数化映射（可直接工程化）

- 规则 A -> `reason_code_A` -> 参数 `x_threshold`
- 规则 B -> `reason_code_B` -> 参数 `y_window`
- 规则 C -> `reason_code_C` -> 参数 `max_drawdown_limit`

---

## 4) 与你当前系统需求的对齐点

- 支持“候选池 + 当前持有”双池信号输出；
- 输出“精确份额 + 规整份额”（便于手动操作）；
- 信号强度固定 0-100 分；
- 收益计算包含手续费与 T+n 生效逻辑；
- 支持盘前、盘后两次任务更新。

---

## 5) 下一步建议（最短路径）

若你方便提供以下任一内容（截图或文字均可），我可以在下一版直接补齐“书籍信息 + 规则细则 + 参数默认值”：

1. 该书封面页/版权页（用于作者、出版社、ISBN）；
2. 你认可的核心章节目录；
3. 3~5 条你最常用的入场与减仓规则。

拿到后我会输出：

- 完整 `docs/Strategy_DuoKongZhuanZheYiShouZhua.md`（含来源字段）；
- 规则到 API 输出 `reasons[]` 的映射表；
- `strategy_params` 默认参数建议（可直接入库）。

