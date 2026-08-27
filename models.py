from pydantic import BaseModel


class TradingResult(BaseModel):

    id: str

    symbol: str

    side: str | None

    price: float

    position: int

    updated_at: int