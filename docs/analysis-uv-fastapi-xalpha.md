# uv + Python3.8 + FastAPI + xalpha 方案分析

## 1. 目标与结论

你要求的技术栈是：

- 包管理：`uv`
- Python 版本：`3.8`
- 后端框架：`FastAPI`
- 数据源：`xalpha`

该组合可行，建议先以“**日频快照 + 两次任务**”模式落地，再扩展多策略与收益引擎。

---

## 2. 可行性评估

## 2.1 Python3.8 与依赖兼容性

为了保证 Python3.8 稳定运行，依赖应明确 pin 版本：

- `fastapi==0.110.3`
- `uvicorn[standard]==0.30.6`
- `xalpha==0.12.3`（最新版）
- `pandas==1.5.3`（固定）
- `pydantic==2.10.6`

`pyproject.toml` 已设置：`requires-python = ">=3.8,<3.9"`。

## 2.2 xalpha 在本项目中的定位

xalpha 更适合作为：

1. 基金历史净值/价格数据读取源；
2. 策略输入（估值与历史序列）生成源；
3. 数据接入层的实现之一（Data Adapter）。

不建议策略层直接调用 xalpha，应经由 adapter/service 统一封装。

---

## 3. 接入设计建议

## 3.1 数据接入分层

- `app/data_sources/xalpha_adapter.py`
  - 负责 xalpha API 调用与字段标准化。
- `app/services/market_service.py`
  - 聚合适配器输出，供 API 层使用。
- `app/main.py`
  - 仅处理请求、响应、参数校验，不做业务计算。

## 3.2 最小可用接口（MVP）

- `GET /healthz`
- `GET /market/snapshot?fund_code=000311`

返回字段示例：

- `fund_code`
- `trade_date`
- `latest_nav`
- `latest_nav_date`
- `source`

---

## 4. uv 工作流建议

## 4.1 初始化与安装

```bash
uv python install 3.8
uv sync
```

## 4.2 本地运行

```bash
uv run uvicorn app.main:app --app-dir backend --reload
```

## 4.3 测试

```bash
uv run pytest
```

---

## 5. 风险与对策

1. **xalpha 数据波动或字段变化**
   - 对策：adapter 层做字段兜底和异常提示。
2. **免费环境网络波动**
   - 对策：任务层重试 + 单基金失败不阻断全局。
3. **Python3.8 生命周期较旧**
   - 对策：先固定版本，后续规划升级到 3.10+。

---

## 6. 下一步建议

1. 增加 `index` 数据适配器（补指数方向因子）。
2. 加入 `quality_score` 和降级为 `hold` 规则。
3. 增加盘前/盘后任务入口（`/jobs/run?session=...`）。
4. 接入 Supabase 落库，打通 `market_snapshots` 表。
