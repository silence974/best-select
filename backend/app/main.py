from fastapi import FastAPI, Query
from pydantic import BaseModel

from app.services.market_service import MarketService


class FundSnapshotResponse(BaseModel):
    fund_code: str
    trade_date: str
    latest_nav: float
    latest_nav_date: str
    source: str


app = FastAPI(title="best-select backend", version="0.1.0")
service = MarketService()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


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
