from typing import Optional

from supabase import Client, create_client

from app.core.config import Settings
from app.data_sources.xalpha_adapter import FundSnapshot


class SupabaseSnapshotRepository:
    def __init__(self, settings: Settings) -> None:
        self.table_name = settings.supabase_table_snapshots
        self.client: Optional[Client] = None

        if settings.supabase_url and settings.supabase_service_role_key:
            self.client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def check_connection(self) -> bool:
        if not self.client:
            return False

        try:
            self.client.table(self.table_name).select("fund_code").limit(1).execute()
            return True
        except Exception:
            return False

    def save_snapshot(self, snapshot: FundSnapshot) -> None:
        if not self.client:
            return

        payload = {
            "fund_code": snapshot.fund_code,
            "trade_date": snapshot.trade_date.isoformat(),
            "latest_nav": snapshot.latest_nav,
            "latest_nav_date": snapshot.latest_nav_date.isoformat(),
            "source": snapshot.source,
        }
        self.client.table(self.table_name).upsert(payload).execute()
