# models/user.py
from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    email: str

    @classmethod
    def from_row(cls, row) -> "User":
        return cls(
            id=row.id,
            name=row.name,
            email=row.email,
        )
