from django.db import models

from apps.customers.models import Customer
from apps.products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} — {self.customer} [{self.status}]"

    def recalculate_total(self):
        """Recalculate and persist total_amount from order items."""
        from django.db.models import DecimalField, ExpressionWrapper, F, Sum

        total = (
            self.items.aggregate(
                total=Sum(ExpressionWrapper(F("quantity") * F("price_at_purchase"), output_field=DecimalField()))
            )["total"]
            or 0
        )
        self.total_amount = total
        self.save(update_fields=["total_amount"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("order", "product")

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Order #{self.order_id})"

    @property
    def subtotal(self):
        return self.quantity * self.price_at_purchase
