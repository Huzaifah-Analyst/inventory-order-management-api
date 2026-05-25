from django.db import transaction
from rest_framework import serializers

from apps.products.models import Product

from .models import Order, OrderItem


class OrderItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_name", "product_sku", "quantity", "price_at_purchase", "subtotal")


class OrderItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "customer",
            "customer_name",
            "status",
            "total_amount",
            "items",
            "created_at",
            "updated_at",
        )


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemWriteSerializer(many=True, write_only=True, min_length=1)

    class Meta:
        model = Order
        fields = ("id", "customer", "status", "items", "total_amount", "created_at")
        read_only_fields = ("id", "total_amount", "created_at")

    def validate_items(self, items):
        # Check for duplicate products in request
        product_ids = [item["product"].id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Duplicate products are not allowed in a single order.")

        # Check stock availability
        errors = []
        for item in items:
            product = item["product"]
            if product.stock_quantity < item["quantity"]:
                errors.append(
                    f"Insufficient stock for '{product.name}' (SKU: {product.sku}). "
                    f"Requested: {item['quantity']}, Available: {product.stock_quantity}."
                )
        if errors:
            raise serializers.ValidationError(errors)

        return items

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")

        order = Order.objects.create(**validated_data)

        order_items = []
        for item_data in items_data:
            product = item_data["product"]
            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=item_data["quantity"],
                    price_at_purchase=product.price,
                )
            )
        OrderItem.objects.bulk_create(order_items)
        order.recalculate_total()
        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "status", "updated_at")
        read_only_fields = ("id", "updated_at")

    def validate_status(self, new_status):
        current_status = self.instance.status if self.instance else None
        # Define allowed transitions
        allowed = {
            Order.Status.PENDING: [Order.Status.PROCESSING, Order.Status.CANCELLED],
            Order.Status.PROCESSING: [Order.Status.COMPLETED, Order.Status.CANCELLED],
            Order.Status.COMPLETED: [],
            Order.Status.CANCELLED: [],
        }
        if current_status and new_status not in allowed.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot transition from '{current_status}' to '{new_status}'. "
                f"Allowed: {allowed.get(current_status, [])}."
            )
        return new_status

    @transaction.atomic
    def update(self, instance, validated_data):
        new_status = validated_data.get("status", instance.status)

        if new_status == Order.Status.COMPLETED and instance.status != Order.Status.COMPLETED:
            # Deduct stock for each item — re-check availability inside transaction
            for item in instance.items.select_related("product").select_for_update():
                product = item.product
                if product.stock_quantity < item.quantity:
                    raise serializers.ValidationError(
                        f"Cannot complete order: insufficient stock for '{product.name}'."
                    )
                product.stock_quantity -= item.quantity
                product.save(update_fields=["stock_quantity"])

        return super().update(instance, validated_data)
