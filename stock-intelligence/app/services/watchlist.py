"""Watchlist: JSON-file-backed, add/remove/search."""
import json
from pathlib import Path

DEFAULT_WATCHLIST = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
                    "SBIN", "ITC", "LT", "BHARTIARTL", "AXISBANK"]


class Watchlist:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._load()

    def _load(self):
        if self.path.exists():
            self.items = sorted(json.loads(self.path.read_text()))
        else:
            self.items = list(DEFAULT_WATCHLIST)

    def _save(self):
        self.path.write_text(json.dumps(self.items, indent=2))

    def list(self):
        return list(self.items)

    def search(self, q: str):
        q = q.upper()
        return [s for s in self.items if q in s]

    def add(self, symbol: str) -> None:
        s = symbol.upper().strip()
        if not s:
            raise ValueError("empty symbol")
        if s in self.items:
            raise ValueError(f"{s} already in watchlist")
        self.items.append(s)
        self.items.sort()
        self._save()

    def remove(self, symbol: str) -> None:
        s = symbol.upper().strip()
        if s not in self.items:
            raise KeyError(f"{s} not in watchlist")
        self.items.remove(s)
        self._save()
