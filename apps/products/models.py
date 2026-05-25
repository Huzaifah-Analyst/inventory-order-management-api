from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0, message="Price cannot be negative.")],
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0, message="Stock quantity cannot be negative.")],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["sku"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0
