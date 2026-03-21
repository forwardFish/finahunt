from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
DEFAULT_BENCHMARK_CODE = "000300.SH"


class QuoteSnapshotAdapter:
    def __init__(self, *, timeout_seconds: float = 8.0) -> None:
        self.timeout_seconds = timeout_seconds
        self._cache: dict[tuple[str, str, str], list[dict[str, Any]]] = {}

    def fetch_validation_snapshot(self, *, codes: list[str], event_time: str, benchmark_code: str = DEFAULT_BENCHMARK_CODE) -> dict[str, Any]:
        valid_codes = [str(code or "").strip() for code in codes if str(code or "").strip()]
        if not valid_codes:
            return {"status": "unverifiable", "validation_window": "T1_CLOSE", "company_moves": [], "basket_move": {}, "benchmark_move": {}}

        event_dt = _parse_dt(event_time)
        if not event_dt:
            return {"status": "unverifiable", "validation_window": "T1_CLOSE", "company_moves": [], "basket_move": {}, "benchmark_move": {}}

        local_dt = event_dt.astimezone(SHANGHAI_TZ)
        start_date = (local_dt.date() - timedelta(days=7)).strftime("%Y%m%d")
        end_date = (local_dt.date() + timedelta(days=8)).strftime("%Y%m%d")
        company_moves: list[dict[str, Any]] = []

        for code in valid_codes:
            history = self._fetch_daily_history(code, start_date, end_date)
            if not history:
                continue
            windows = _build_windows(history, local_dt)
            if not windows:
                continue
            company_moves.append(
                {
                    "company_code": code,
                    "windows": windows,
                    "latest_return": windows.get("T1_CLOSE"),
                }
            )

        if not company_moves:
            return {"status": "unverifiable", "validation_window": "T1_CLOSE", "company_moves": [], "basket_move": {}, "benchmark_move": {}}

        benchmark_history = self._fetch_daily_history(benchmark_code, start_date, end_date)
        benchmark_move = _build_windows(benchmark_history, local_dt) if benchmark_history else {}
        basket_move = _mean_windows([item.get("windows", {}) for item in company_moves])
        return {
            "status": "ok",
            "validation_window": "T1_CLOSE" if basket_move.get("T1_CLOSE") is not None else "T0_CLOSE",
            "company_moves": company_moves,
            "basket_move": basket_move,
            "benchmark_move": benchmark_move,
        }

    def _fetch_daily_history(self, code: str, start_date: str, end_date: str) -> list[dict[str, Any]]:
        cache_key = (code, start_date, end_date)
        if cache_key in self._cache:
            return self._cache[cache_key]
        secid = _to_secid(code)
        if not secid:
            self._cache[cache_key] = []
            return []

        try:
            response = requests.get(
                "https://push2his.eastmoney.com/api/qt/stock/kline/get",
                params={
                    "fields1": "f1,f2,f3,f4,f5,f6",
                    "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                    "klt": "101",
                    "fqt": "1",
                    "secid": secid,
                    "beg": start_date,
                    "end": end_date,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            self._cache[cache_key] = []
            return []
        raw_rows = ((payload.get("data") or {}).get("klines") or [])
        rows: list[dict[str, Any]] = []
        for raw in raw_rows:
            parts = str(raw or "").split(",")
            if len(parts) < 3:
                continue
            rows.append({"date": parts[0], "close": _safe_float(parts[2])})
        self._cache[cache_key] = [row for row in rows if row.get("close") is not None]
        return self._cache[cache_key]


def _build_windows(history: list[dict[str, Any]], event_dt: datetime) -> dict[str, float]:
    if len(history) < 2:
        return {}
    local_date = event_dt.date().isoformat()
    trade_dates = [str(item.get("date", "")) for item in history]
    activation_index = next((index for index, trade_date in enumerate(trade_dates) if trade_date >= local_date), -1)
    if activation_index < 0:
        return {}
    if event_dt.hour >= 15 and activation_index + 1 < len(history):
        activation_index += 1
    if activation_index <= 0:
        return {}
    baseline_close = _safe_float(history[activation_index - 1].get("close"))
    if baseline_close in (None, 0):
        return {}
    windows: dict[str, float] = {}
    for label, offset in {"T0_CLOSE": 0, "T1_CLOSE": 1, "T3_CLOSE": 3}.items():
        index = activation_index + offset
        if index >= len(history):
            continue
        close = _safe_float(history[index].get("close"))
        if close is None:
            continue
        windows[label] = round(((close / baseline_close) - 1.0) * 100.0, 2)
    return windows


def _mean_windows(rows: list[dict[str, float]]) -> dict[str, float]:
    outputs: dict[str, float] = {}
    for label in {"T0_CLOSE", "T1_CLOSE", "T3_CLOSE"}:
        values = [row[label] for row in rows if row.get(label) is not None]
        if values:
            outputs[label] = round(sum(values) / len(values), 2)
    return outputs


def _to_secid(code: str) -> str:
    text = str(code or "").strip().upper()
    if "." not in text:
        return ""
    symbol, market = text.split(".", 1)
    if market == "SH":
        return f"1.{symbol}"
    if market in {"SZ", "BJ"}:
        return f"0.{symbol}"
    return ""


def _parse_dt(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
