"""CR du run (statut par table + global), sérialisé en JSON pour le manifeste"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum

from fhvi_ingestion.run_context import RunContext


class Status(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


@dataclass
class TableResult:
    source: str
    table: str
    status: Status
    rows: int = 0
    uri: str | None = None
    duration_s: float = 0.0
    error: str | None = None


@dataclass
class RunReport:
    run: RunContext
    results: list[TableResult] = field(default_factory=list)
    finished_at: datetime | None = None

    def add(self, result: TableResult) -> None:
        self.results.append(result)

    def finish(self) -> None:
        self.finished_at = datetime.now(UTC)

    @property
    def failed(self) -> list[TableResult]:
        return [r for r in self.results if r.status is Status.FAILED]

    @property
    def status(self) -> Status:
        if not self.failed:
            return Status.SUCCESS
        return Status.FAILED if len(self.failed) == len(self.results) else Status.PARTIAL

    @property
    def duration_s(self) -> float:
        end = self.finished_at or datetime.now(UTC)
        return round((end - self.run.started_at).total_seconds(), 3)

    @property
    def exit_code(self) -> int:
        # PARTIAL compte comme un échec, on veut que l'ordonnanceur alrete
        return 0 if self.status is Status.SUCCESS else 1

    def to_dict(self) -> dict:
        return {
            "run_id": self.run.run_id,
            "load_date": self.run.load_date,
            "replay_of": self.run.replay_of,
            "started_at": self.run.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_s": self.duration_s,
            "status": self.status.value,
            "tables_total": len(self.results),
            "tables_failed": len(self.failed),
            "rows_total": sum(r.rows for r in self.results),
            "results": [{**asdict(r), "status": r.status.value} for r in self.results],
        }

    def to_json(self) -> bytes:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2).encode("utf-8")
