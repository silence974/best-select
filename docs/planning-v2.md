# 智能支付宝场外基金策略系统（v2 细化方案）

> 本文基于你已确认的 8 条偏好，给出可直接落地的 MVP/迭代方案。目标依然是：
> **FastAPI + Render（后端） + GitHub Pages（前端） + Supabase（数据库）**，免费优先，单人使用，仅做策略参考，不自动交易。

## 1. 已确认需求（冻结）

1. 维护两部分基金池：
   - **候选池**：约 10-20 只
   - **当前持有**：约 20 只
2. 输出结果要给出**精确份额增减**，并尽量“规整化”便于下单。
3. 信号强度统一为 **0-100 分**。
4. 策略框架要可扩展；初期策略采用《多空转折一手抓》思路。
5. 更新频率改为**两次**：盘前一次 + 盘后一次（降低请求成本）。
6. 前端优先使用 **React + Vite**，并走 GitHub Pages 官方推荐部署。
7. 单用户鉴权：使用 **Supabase 存储简单口令**，不做账号系统。
8. 需要：
   - **按月复盘图表**
   - **当天收益汇总**
   - 收益计算自动考虑**交易手续费**与**T+n 到账/确认规则**。

---

## 2. MVP 架构（按确认需求收敛）

```text
          [基金估值/指数数据源 A/B]
                     |
                     v
            [FastAPI on Render]
             |   策略引擎（可插拔）
             |   收益引擎（手续费 + T+n）
             v
          [Supabase Postgres]
             ^
             |
 [React+Vite on GitHub Pages]  ->  展示今日建议、当日收益、月度复盘
```

### 2.1 模块边界

- **Pool 模块**：管理候选池与持有池。
- **Signal 模块**：输出 0-100 分强度 + 买卖方向 + 建议份额。
- **Execution-Model 模块**：按手续费与 T+n 模拟资金/份额变化。
- **PnL 模块**：输出当日收益、月度收益、回撤。
- **Auth 模块（轻量）**：口令校验。

---

## 3. 数据库设计（Supabase）

> 以下为推荐表，不是最终 SQL；下一步可直接给建表脚本。

### 3.1 基金池与持仓

1. `fund_candidates`
   - `fund_code` (pk)
   - `fund_name`
   - `track_index`
   - `enabled` (bool)
   - `created_at`

2. `fund_holdings`
   - `id` (pk)
   - `fund_code`
   - `holding_shares`（当前持有份额）
   - `avg_cost_nav`（平均成本净值）
   - `cash_allocated`
   - `updated_at`

### 3.2 行情与估值

3. `market_snapshots`
   - `id` (pk)
   - `trade_date`
   - `session_type`（`pre_open` / `post_close`）
   - `fund_code`
   - `estimated_nav`
   - `index_change_pct`
   - `volatility_n`
   - `source`
   - `fetched_at`
   - `is_valid`

### 3.3 策略信号与建议操作

4. `strategy_signals`
   - `id` (pk)
   - `trade_date`
   - `fund_code`
   - `strategy_name`（初期固定：`long_short_reversal_v1`）
   - `signal_score`（0-100）
   - `signal_action`（`buy` / `hold` / `sell`）
   - `reason_json`（关键依据明细）
   - `generated_at`

5. `position_recommendations`
   - `id` (pk)
   - `trade_date`
   - `fund_code`
   - `recommended_delta_shares_raw`（算法原始份额）
   - `recommended_delta_shares_rounded`（规整后份额）
   - `rounding_lot`（规整粒度，如 10/100 份）
   - `action`
   - `notes`

### 3.4 交易规则与收益

6. `fund_trade_rules`
   - `fund_code` (pk)
   - `buy_fee_rate`
   - `sell_fee_rate`
   - `redemption_fee_rule_json`（按持有天数分段）
   - `tn_confirm_days`（申购确认 T+n）
   - `tn_redeem_days`（赎回到账 T+n）
   - `min_trade_shares`
   - `trade_lot`

7. `daily_pnl`
   - `id` (pk)
   - `trade_date`
   - `fund_code`
   - `holding_shares_effective`（考虑 T+n 后生效份额）
   - `daily_pnl_amount`
   - `daily_pnl_pct`
   - `fee_cost_amount`
   - `nav_used`
   - `created_at`

8. `monthly_reports`
   - `month` (pk, `YYYY-MM`)
   - `total_pnl_amount`
   - `total_pnl_pct`
   - `max_drawdown_pct`
   - `turnover_ratio`
   - `report_json`

### 3.5 单用户口令

9. `app_secrets`
   - `key` (pk)
   - `value_hash`（口令 hash）
   - `updated_at`

---

## 4. 策略输出格式（按你的偏好）

### 4.1 每只基金输出

- `fund_code`
- `signal_score`（0-100）
- `signal_action`（买/持/卖）
- `delta_shares`（精确份额）
- `delta_shares_rounded`（规整份额）
- `reasons[]`（关键依据）

### 4.2 规整份额规则（建议）

为提升可执行性：

- 默认按 `trade_lot` 规整（如 10 份或 100 份）；
- 小于最小交易份额时改为 `hold`；
- 规整后偏差超过阈值（如 20%）时，提示“需人工确认”。

---

## 5. 《多空转折一手抓》策略的工程化落地（v1）

> 为避免策略被写死，采用“策略注册表 + 参数表”方式实现。

### 5.1 可扩展设计

- `Strategy` 抽象接口：
  - `compute_signal(snapshot, holding, params) -> score/action/reasons`
- `strategy_registry`：按 `strategy_name` 注册实例
- `strategy_params` 表：策略参数可在数据库维护

### 5.2 v1 输出逻辑（示意）

- 根据估值分位、指数方向、波动率状态合成 `0-100` 分；
- 分数映射动作：
  - `0-30`: 偏减仓
  - `31-69`: 观望
  - `70-100`: 偏加仓
- 目标份额 = 风险预算 * 分数权重 * 基金规则约束；
- 最终份额通过 `trade_lot` 规整并应用上下限。

---

## 6. 调度频率（两次更新）

你已确认降低频率，建议：

- **盘前**：09:20（生成当日开盘前参考）
- **盘后**：15:10（按收盘后数据修正并生成复盘）

这样可以显著降低免费额度压力，同时满足“日内参考 + 日终复盘”。

---

## 7. 鉴权方案（单人、口令制）

- Supabase 仅存口令哈希（如 Argon2/Bcrypt）；
- FastAPI 提供 `POST /auth/token`：口令正确后签发短期 JWT；
- 前端本地存储 token，过期后重新输入口令。

> 不做注册/找回密码，减少复杂度与安全暴露面。

---

## 8. 前端方案（React + Vite + GitHub Pages）

### 8.1 页面清单

1. **今日信号页**
   - 基金列表（候选池/持有池切换）
   - 0-100 信号分
   - 增减份额（规整值）
   - 关键依据

2. **当日收益页**
   - 持仓总收益
   - 分基金收益
   - 手续费影响拆解

3. **月度复盘页**
   - 月收益曲线
   - 月回撤
   - 换手率与费用统计

### 8.2 Pages 推荐工作流

- 使用 GitHub Actions：
  - `npm ci`
  - `npm run build`
  - `actions/upload-pages-artifact`
  - `actions/deploy-pages`
- Pages Source 设置为 `GitHub Actions`。

---

## 9. 收益计算：手续费与 T+n 的处理要点

### 9.1 手续费

- 申购费：买入时从投入金额扣减；
- 赎回费：卖出时按持有天数分段计算；
- 每日收益展示分“毛收益/净收益（扣费后）”。

### 9.2 T+n

- 买入份额在 `tn_confirm_days` 后进入可计收益持仓；
- 卖出资金在 `tn_redeem_days` 后回到可用现金；
- `daily_pnl` 使用“生效持仓”而非“提交申请份额”。

---

## 10. API 草案（v2）

- `POST /auth/token`：口令换 token
- `GET /funds?pool=candidate|holding`：基金池查询
- `GET /signals/today?pool=holding`：今日信号
- `GET /recommendations/today`：今日建议份额（含规整值）
- `GET /pnl/daily?date=YYYY-MM-DD`：当日收益
- `GET /reports/monthly?month=YYYY-MM`：月度复盘
- `POST /jobs/run?session=pre_open|post_close`：手动触发任务

---

## 11. 下一步落地清单（开发顺序）

1. 建表与初始化数据（基金池、交易规则、口令）。
2. 搭建 FastAPI 项目骨架（uv 管理）与口令鉴权。
3. 接入两类数据源并写入 `market_snapshots`。
4. 实现策略引擎 v1（多空转折）与建议份额规整。
5. 实现收益引擎（手续费 + T+n）与日报/月报接口。
6. React + Vite 前端页面与 GitHub Pages Action。
7. Render 部署 + 定时任务 + 失败重试。

---

## 12. 仍需你拍板的 4 个参数（小范围）

1. `trade_lot` 默认值设为多少？（10 / 100 份）
2. 信号分到仓位变化的映射曲线：线性还是分段阶梯？
3. 《多空转折一手抓》里你最看重的 3 个因子优先级？
4. 月报里是否需要“策略建议 vs 实际手动执行”的偏差分析？

