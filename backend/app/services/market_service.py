from typing import Optional

from app.data_sources.xalpha_adapter import FundSnapshot, XalphaDataAdapter
from app.db.supabase_client import SupabaseSnapshotRepository


class MarketService:
    def __init__(
        self,
        adapter: Optional[XalphaDataAdapter] = None,
        snapshot_repository: Optional[SupabaseSnapshotRepository] = None,
    ) -> None:
        self.adapter = adapter or XalphaDataAdapter()
        self.snapshot_repository = snapshot_repository

    def get_fund_snapshot(self, fund_code: str) -> FundSnapshot:
        snapshot = self.adapter.fetch_fund_snapshot(fund_code)
        if self.snapshot_repository:
            self.snapshot_repository.save_snapshot(snapshot)
        return snapshot
