from dataclasses import dataclass
from datetime import date

import pandas as pd
import xalpha as xa


@dataclass
class FundSnapshot:
    fund_code: str
    trade_date: date
    latest_nav: float
    latest_nav_date: date
    source: str = "xalpha"


class XalphaDataAdapter:
    """Use xalpha as the fund data adapter for off-exchange funds."""

    source_name = "xalpha"

    def fetch_fund_snapshot(self, fund_code: str) -> FundSnapshot:
        info = xa.fundinfo(fund_code)
        price_table: pd.DataFrame = info.price
        if price_table.empty:
            raise ValueError(f"no price data for fund {fund_code}")

        latest = price_table.iloc[-1]
        nav_date = latest["date"]
        return FundSnapshot(
            fund_code=fund_code,
            trade_date=date.today(),
            latest_nav=float(latest["netvalue"]),
            latest_nav_date=nav_date.date() if hasattr(nav_date, "date") else nav_date,
        )
