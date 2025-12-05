# models/cart_item.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class CartItem:
    id: int
    product_id: int
    product_name: str
    price: Optional[float]
    stock: int
    amount: int
    total_price: Optional[float]

    @classmethod
    def from_row(cls, row) -> "CartItem":
        price = float(row.price) if row.price is not None else None
        total_price = price * row.amount if price is not None else None

        return cls(
            id=row.id,
            product_id=row.product_id,
            product_name=row.product_name,
            price=price,
            stock=row.stock,
            amount=row.amount,
            total_price=total_price,
        )
