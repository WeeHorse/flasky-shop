# models/vat.py
from dataclasses import dataclass


@dataclass
class Vat:
    id: int
    description: str
    amount: float
    region: str

    @classmethod
    def from_row(cls, row) -> "Vat":
        return cls(
            id=row.id,
            description=row.description,
            amount=float(row.amount),
            region=row.region,
        )
