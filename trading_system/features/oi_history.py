import json
from pathlib import Path
from statistics import mean, pstdev


class OpenInterestHistory:
    def __init__(self, path: str, window: int = 168):
        self.path = Path(path)
        self.window = window
        self._history: dict[str, list[float]] = {}
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self._history = {
                symbol: [float(value) for value in values][-self.window :]
                for symbol, values in payload.items()
                if isinstance(values, list)
            }
        self._loaded = True

    def snapshot(self) -> dict[str, list[float]]:
        self.load()
        return {symbol: values[:] for symbol, values in self._history.items()}

    def push(self, symbol: str, open_interest: float) -> float:
        self.load()
        series = self._history.setdefault(symbol, [])
        series.append(float(open_interest))
        self._history[symbol] = series[-self.window :]
        self._persist()
        return self.zscore(symbol, open_interest)

    def zscore(self, symbol: str, open_interest: float) -> float:
        self.load()
        series = self._history.get(symbol, [])
        if len(series) < 5:
            return 0.0
        avg = mean(series)
        std = pstdev(series)
        if std == 0:
            return 0.0
        return (open_interest - avg) / std

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._history, indent=2), encoding="utf-8")
