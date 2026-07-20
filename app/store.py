from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from uuid import uuid4

from app.models import Order, OrderCreate, OrderStatus, Product


class ProductNotFoundError(Exception):
    pass


class OutOfStockError(Exception):
    pass


@dataclass
class ShopStore:
    products: dict[str, Product] = field(default_factory=dict)
    orders: dict[str, Order] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    @classmethod
    def with_seed_data(cls) -> "ShopStore":
        return cls(
            products={
                "coffee-001": Product(
                    sku="coffee-001",
                    name="Deployment Coffee",
                    price=9.5,
                    in_stock=42,
                ),
                "mug-001": Product(
                    sku="mug-001",
                    name="On-call Mug",
                    price=14.0,
                    in_stock=12,
                ),
                "sticker-001": Product(
                    sku="sticker-001",
                    name="Ship It Sticker Pack",
                    price=4.5,
                    in_stock=100,
                ),
            }
        )

    def list_products(self) -> list[Product]:
        return list(self.products.values())

    def get_product(self, sku: str) -> Product:
        product = self.products.get(sku)
        if product is None:
            raise ProductNotFoundError(sku)
        return product

    def create_order(self, data: OrderCreate) -> Order:
        with self._lock:
            product = self.get_product(data.sku)
            if product.in_stock < data.quantity:
                raise OutOfStockError(data.sku)

            updated_product = product.model_copy(update={"in_stock": product.in_stock - data.quantity})
            self.products[data.sku] = updated_product

            order = Order(
                id=str(uuid4()),
                sku=data.sku,
                quantity=data.quantity,
                total=round(product.price * data.quantity, 2),
                status=OrderStatus.pending,
            )
            self.orders[order.id] = order
            return order

    def list_orders(self) -> list[Order]:
        return list(self.orders.values())

    def mark_order_paid(self, order_id: str) -> Order:
        with self._lock:
            order = self.orders.get(order_id)
            if order is None:
                raise KeyError(order_id)

            paid_order = order.model_copy(update={"status": OrderStatus.paid})
            self.orders[order_id] = paid_order
            return paid_order

