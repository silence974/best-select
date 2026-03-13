from typing import Optional

from app.data_sources.xalpha_adapter import FundSnapshot, XalphaDataAdapter


class MarketService:
    def __init__(self, adapter: Optional[XalphaDataAdapter] = None) -> None:
        self.adapter = adapter or XalphaDataAdapter()

    def get_fund_snapshot(self, fund_code: str) -> FundSnapshot:
        return self.adapter.fetch_fund_snapshot(fund_code)
