from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DailyPrice(Base):
    __tablename__ = "daily_prices"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    ticker: Mapped[str] = mapped_column(Text, primary_key=True, default="KC=F")
    open: Mapped[float] = mapped_column(Numeric)
    high: Mapped[float] = mapped_column(Numeric)
    low: Mapped[float] = mapped_column(Numeric)
    close: Mapped[float] = mapped_column(Numeric)
    volume: Mapped[int | None] = mapped_column(BigInteger)
    source: Mapped[str] = mapped_column(Text, default="yfinance")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    country: Mapped[str] = mapped_column(Text, unique=True)
    region_name: Mapped[str] = mapped_column(Text)
    lat_min: Mapped[float | None] = mapped_column(Numeric)
    lat_max: Mapped[float | None] = mapped_column(Numeric)
    lon_min: Mapped[float | None] = mapped_column(Numeric)
    lon_max: Mapped[float | None] = mapped_column(Numeric)
    production_share: Mapped[float | None] = mapped_column(Numeric)


class WeatherReading(Base):
    __tablename__ = "weather_readings"

    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    temp_max: Mapped[float | None] = mapped_column(Numeric)
    temp_min: Mapped[float | None] = mapped_column(Numeric)
    temp_mean: Mapped[float | None] = mapped_column(Numeric)
    precipitation_sum: Mapped[float | None] = mapped_column(Numeric)
    soil_moisture: Mapped[float | None] = mapped_column(Numeric)
    evapotranspiration: Mapped[float | None] = mapped_column(Numeric)
    source: Mapped[str] = mapped_column(Text, default="open-meteo")


class ShockEvent(Base):
    __tablename__ = "shock_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    event_type: Mapped[str] = mapped_column(Text)
    severity: Mapped[float | None] = mapped_column(Numeric)
    max_temp_anomaly: Mapped[float | None] = mapped_column(Numeric)
    precip_anomaly: Mapped[float | None] = mapped_column(Numeric)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )