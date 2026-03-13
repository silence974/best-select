# 部署规划（Render + GitHub Pages + Supabase）

## 1. 目标

- 后端 API 部署到 Render（FastAPI + Docker）。
- 前端静态页面部署到 GitHub Pages（使用默认仓库域名）。
- 数据库存储使用 Supabase（Postgres），作为后端专用数据库。

## 2. 当前实现状态

- 已新增 Render Blueprint：`render.yaml`，区分 `develop`（dev）和 `main`（prod）两个服务。
- 已新增 GitHub Pages workflow：`.github/workflows/deploy-pages.yml`。
- 已新增后端 CI workflow：`.github/workflows/backend-ci.yml`。
- 已在后端加入 Supabase Repository：读取 `SUPABASE_URL`、`SUPABASE_SERVICE_ROLE_KEY`，并在获取快照后自动 upsert。
- 已新增 `/api/v1/runtime` 与 `/api/v1/db/healthz` 用于远程验证运行环境和数据库状态。

## 3. 环境变量清单

后端（Render dev/prod 都需要）：

- `APP_ENV`（dev 服务为 `dev`，prod 服务为 `prod`）
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_TABLE_SNAPSHOTS=market_snapshots`

前端（GitHub Pages）：

- 使用 GitHub Pages 默认域名：`https://<username>.github.io/<repo>/`
- 前端 API 地址建议通过 `window.BEST_SELECT_API_BASE` 指向 Render prod 域名。

## 4. Supabase 数据库策略

- 不启用 RLS（按当前需求：数据库仅服务于后端）。
- 不向前端暴露 `SUPABASE_SERVICE_ROLE_KEY`。

### 推荐初始化 SQL（无 RLS）

```sql
create table if not exists public.market_snapshots (
  fund_code text not null,
  trade_date date not null,
  latest_nav numeric not null,
  latest_nav_date date not null,
  source text not null,
  created_at timestamptz not null default now(),
  primary key (fund_code, trade_date)
);

alter table public.market_snapshots disable row level security;
```

## 5. 发布顺序

1. 在 Supabase 执行建表 SQL（确认 RLS 关闭）。
2. 在 Render 按 `render.yaml` 创建 dev/prod 两个服务。
3. 配置 Render 两个服务的 Supabase 环境变量。
4. 验证 Render：`/api/v1/runtime`、`/api/v1/db/healthz`、`/healthz`。
5. 推送前端到 `main`，由 GitHub Actions 发布到 GitHub Pages。

## 6. 验证清单

- dev 分支发布后，dev 服务 `APP_ENV=dev`。
- main 分支发布后，prod 服务 `APP_ENV=prod`。
- `/api/v1/runtime` 中 `supabase_enabled=true`。
- `/api/v1/db/healthz` 返回 `status=ok`。
- 调用 `/market/snapshot?fund_code=000311` 后，Supabase 表中可见对应记录。
- GitHub Pages 页面可访问并显示后端连接结果。

## 7. 下一步迭代建议

- 增加 CORS 白名单（GitHub Pages 域名 + 本地开发域名）。
- 增加 migration 管理（SQL 版本目录或 Alembic）。
- 将前端 API 地址改成构建时注入，避免静态文件硬编码。
