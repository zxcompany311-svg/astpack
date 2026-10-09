"""
Sample E-Commerce Payment and Order Processing Service.
Used for testing AstPack context pruning.
"""

from typing import List, Dict, Optional
import time
import math


class OrderItem:
    def __init__(self, item_id: str, price: float, quantity: int):
        self.item_id = item_id
        self.price = price
        self.quantity = quantity

    def subtotal(self) -> float:
        """Calculate line item subtotal."""
        return self.price * self.quantity


class PaymentGateway:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def charge(self, amount: float, card_token: str) -> bool:
        """Charge credit card via external API."""
        print(f"Connecting to banking gateway with key {self.api_key[:4]}...")
        time.sleep(0.01)
        # Complex validation logic
        if amount <= 0:
            raise ValueError("Invalid charge amount")
        if not card_token.startswith("tok_"):
            return False
        return True

    def refund(self, transaction_id: str, amount: float) -> bool:
        """Issue refund to customer."""
        print(f"Refunding transaction {transaction_id} amount {amount}")
        return True


def calculate_shipping(weight_kg: float, distance_km: float) -> float:
    """Calculate shipping cost based on weight and distance tier."""
    base_rate = 5.0
    weight_tier = math.ceil(weight_kg) * 1.5
    distance_tier = (distance_km / 100.0) * 2.0
    return round(base_rate + weight_tier + distance_tier, 2)


def process_order(items: List[OrderItem], card_token: str, gateway: PaymentGateway) -> Dict:
    """
    Main business transaction function:
    Validates cart, calculates total with shipping, charges customer, and logs order.
    """
    total = sum(item.subtotal() for item in items)
    shipping = calculate_shipping(weight_kg=2.5, distance_km=150.0)
    grand_total = total + shipping

    success = gateway.charge(amount=grand_total, card_token=card_token)
    if not success:
        return {"status": "failed", "reason": "Payment declined"}

    return {
        "status": "success",
        "order_id": "ORD-99881",
        "total": grand_total,
        "shipping": shipping,
    }
