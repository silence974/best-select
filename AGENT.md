# AGENT 开发指引（阶段性）

## 当前目标对齐（已确认）

1. 后端部署到 Render，且区分环境（dev/prod）。
2. 前端静态页部署到 GitHub Pages，使用仓库默认域名。
3. Supabase 作为后端数据库，不启用 RLS。

## 当前技术落地

- 后端：FastAPI（`backend/app/main.py`）
- 数据落库：`SupabaseSnapshotRepository`（`backend/app/db/supabase_client.py`）
- 部署：
  - Render：`render.yaml`（`develop -> dev`，`main -> prod`）
  - GitHub Pages：`.github/workflows/deploy-pages.yml` + `frontend/index.html`
- CI：`.github/workflows/backend-ci.yml`

## 关键约束

1. **Supabase 不启用 RLS**
   - 数据库仅由后端服务访问。
   - 只在 Render 环境变量中保存 `SUPABASE_SERVICE_ROLE_KEY`。

2. **环境区分**
   - `develop` 分支部署 dev 服务，`APP_ENV=dev`。
   - `main` 分支部署 prod 服务，`APP_ENV=prod`。

3. **API 版本化**
   - 新接口优先放在 `/api/v1/*`。
   - 部署验证必须覆盖 `/api/v1/runtime` 与 `/api/v1/db/healthz`。

## 开发约定

- 不在代码中硬编码密钥。
- 配置集中在 `backend/app/core/config.py`。
- 数据写入保持幂等（`market_snapshots` 使用复合主键 upsert）。
- 前端仅调用后端 API，不直接连接 Supabase。

## 下一步优先级

1. 增加 CORS 白名单（Pages 域名 + 本地域名）。
2. 增加数据库 migration 目录与版本管理。
3. 开始接入第一批策略接口（`/api/v1/strategies/*`）。
