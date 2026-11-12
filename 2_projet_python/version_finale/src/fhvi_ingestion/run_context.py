""" on deifnit le run_id comme identité d'un run
on le retrouve sur chaque ligne de log, dans le nom de chaque fichier écrit, dans la colonne _run_id des données et dans le manifeste json
qd on se demande le matin quel run a donné quel fichier, c est ce id qu'on cherche
un rejeu = un nouveau run (nouveau run_id) qui note dans replay_of le run qu il rejoue
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


# horodatage en tête -> les run_id se trient dans l'ordre chrono (ex: 20261209T143012Z-1a2b3c4d)
def new_run_id(now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    return f"{now:%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"


@dataclass(frozen=True)
class RunContext:
    run_id: str
    load_date: str
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    replay_of: str | None = None

    @classmethod
    def create(cls, load_date: str, replay_of: str | None = None) -> RunContext:
        started_at = datetime.now(UTC)
        return cls(run_id=new_run_id(started_at), load_date=load_date, started_at=started_at,
                   replay_of=replay_of)
