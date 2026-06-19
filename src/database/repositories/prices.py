import pandas as pd

from src.database.engine import Session
from src.database.models import DailyPrice


def save_prices(df: pd.DataFrame) -> None:
    with Session() as session:
        for row in df.itertuples():
            price = DailyPrice(
                date=row.Index.date(),
                ticker="KC=F",
                open=row.Open,
                high=row.High,
                low=row.Low,
                close=row.Close,
                volume=row.Volume if hasattr(row, "Volume") else None,
            )
            session.merge(price)
        session.commit()


def get_prices_in_range(start: str, end: str) -> pd.DataFrame:
    with Session() as session:
        rows = (
            session.query(DailyPrice)
            .filter(DailyPrice.date.between(start, end))
            .order_by(DailyPrice.date)
            .all()
        )
    records = [
        {
            "Date": r.date,
            "Open": float(r.open),
            "High": float(r.high),
            "Low": float(r.low),
            "Close": float(r.close),
            "Volume": r.volume or 0,
        }
        for r in rows
    ]
    df = pd.DataFrame(records)
    if not df.empty:
        df.set_index("Date", inplace=True)
        df.index = pd.to_datetime(df.index)
    return df.sort_index()