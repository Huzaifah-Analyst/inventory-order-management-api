from django.db import models


class Customer(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(max_length=30, blank=True, default="")
    address = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"
