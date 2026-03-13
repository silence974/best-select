# best-select

项目规划文档：

- 初版：`docs/initial-planning.md`
- v2（已合并偏好）：`docs/planning-v2.md`
- 策略调研记录：`docs/Strategy_DuoKongZhuanZheYiShouZhua.md`
- v3（开发设计细化）：`docs/planning-v3-architecture.md`
- uv + FastAPI + xalpha 分析：`docs/analysis-uv-fastapi-xalpha.md`
- 后端框架选型评估：`docs/framework-evaluation-fastapi-vs-flask.md`

## 后端技术栈（当前）

- Python `3.8`
- 包管理：`uv`
- 后端：`FastAPI`
- 数据源：`xalpha`

## 本地启动（backend）

```bash
uv python install 3.8
uv sync
uv run uvicorn app.main:app --app-dir backend --reload
```

## 运行测试

```bash
uv run pytest
```
