# models/product.py
from dataclasses import dataclass


@dataclass
class Product:
    id: int
    name: str
    price: float
    stock: int
    currency: str
    vat: int

    @classmethod
    def from_row(cls, row) -> "Product":
        return cls(
            id=row.id,
            name=row.name,
            price=float(row.price),
            stock=row.stock,
            currency=row.currency,
            vat=row.vat,
        )
