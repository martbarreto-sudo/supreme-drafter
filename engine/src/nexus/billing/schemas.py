from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SubscriptionOut(BaseModel):
    plan_code: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    pecas_incluidas: int
    pecas_consumidas_no_periodo: int
    pecas_restantes: int
