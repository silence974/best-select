from fastapi import FastAPI, Query
from pydantic import BaseModel

from app.core.config import PublicRuntimeConfig, get_settings
from app.db.supabase_client import SupabaseSnapshotRepository
from app.services.market_service import MarketService


class FundSnapshotResponse(BaseModel):
    fund_code: str
    trade_date: str
    latest_nav: float
    latest_nav_date: str
    source: str


class AppInfoResponse(BaseModel):
    name: str
    version: str
    status: str


class DbHealthResponse(BaseModel):
    status: str
    configured: bool


settings = get_settings()
snapshot_repository = SupabaseSnapshotRepository(settings)

app = FastAPI(title=settings.app_name, version=settings.app_version)
service = MarketService(snapshot_repository=snapshot_repository)


@app.get("/", response_model=AppInfoResponse)
def root() -> AppInfoResponse:
    return AppInfoResponse(name=settings.app_name, version=settings.app_version, status="running")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/api/v1/healthz")
def api_healthz() -> dict:
    return {"status": "ok"}


@app.get("/api/v1/runtime", response_model=PublicRuntimeConfig)
def runtime() -> PublicRuntimeConfig:
    return PublicRuntimeConfig(
        app_env=settings.app_env,
        app_version=settings.app_version,
        supabase_enabled=snapshot_repository.enabled,
    )


@app.get("/api/v1/db/healthz", response_model=DbHealthResponse)
def db_healthz() -> DbHealthResponse:
    if not snapshot_repository.enabled:
        return DbHealthResponse(status="not_configured", configured=False)

    return DbHealthResponse(status="ok" if snapshot_repository.check_connection() else "error", configured=True)


@app.get("/market/snapshot", response_model=FundSnapshotResponse)
def get_market_snapshot(
    fund_code: str = Query(..., description="Fund code, e.g. 000311"),
) -> FundSnapshotResponse:
    snapshot = service.get_fund_snapshot(fund_code=fund_code)
    return FundSnapshotResponse(
        fund_code=snapshot.fund_code,
        trade_date=snapshot.trade_date.isoformat(),
        latest_nav=snapshot.latest_nav,
        latest_nav_date=snapshot.latest_nav_date.isoformat(),
        source=snapshot.source,
    )
