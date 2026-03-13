# best-select

项目规划文档：

- 初版：`docs/initial-planning.md`
- v2（已合并偏好）：`docs/planning-v2.md`
- 策略调研记录：`docs/Strategy_DuoKongZhuanZheYiShouZhua.md`
- v3（开发设计细化）：`docs/planning-v3-architecture.md`
- uv + FastAPI + xalpha 分析：`docs/analysis-uv-fastapi-xalpha.md`
- 后端框架选型评估：`docs/framework-evaluation-fastapi-vs-flask.md`
- 部署规划：`docs/deployment-plan-render-ghpages-supabase.md`

## 后端技术栈（当前）

- Python `3.8`
- 包管理：`uv`
- 后端：`FastAPI`
- 数据源：`xalpha`
- 数据库：`Supabase (Postgres，仅后端访问，不启用 RLS)`

## 当前骨架能力

- 基础服务入口：`GET /`
- 健康检查：`GET /healthz`
- 版本化健康检查：`GET /api/v1/healthz`
- 运行时配置查看：`GET /api/v1/runtime`
- 数据库状态检查：`GET /api/v1/db/healthz`
- 示例业务接口：`GET /market/snapshot?fund_code=000311`（配置 Supabase 后会自动 upsert 到库）

## 本地启动（backend）

```bash
uv python install 3.8
uv sync --extra dev
uv run uvicorn app.main:app --app-dir backend --reload
```

## Docker 启动（用于部署）

```bash
docker compose up --build -d
```

启动后访问：

- `http://localhost:8000/`
- `http://localhost:8000/healthz`
- `http://localhost:8000/docs`

## Render 部署（区分 dev/prod）

`render.yaml` 已定义两个服务：

- `best-select-backend-dev`：跟踪 `develop` 分支，`APP_ENV=dev`
- `best-select-backend-prod`：跟踪 `main` 分支，`APP_ENV=prod`

两个服务都需配置：

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_TABLE_SNAPSHOTS`（可选，默认 `market_snapshots`）

## GitHub Pages 部署前端骨架

- 前端静态文件在 `frontend/`。
- 推送 `main` 后通过 `.github/workflows/deploy-pages.yml` 自动发布。
- 访问域名默认使用仓库对应地址：`https://<username>.github.io/<repo>/`

## 运行测试

```bash
uv run python -m pytest
```
