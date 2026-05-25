import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User

from apps.products.models import Product
from apps.customers.models import Customer
from apps.orders.models import Order, OrderItem


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "TestPass123!")


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    sku = factory.Sequence(lambda n: f"SKU-{n:04d}")
    description = "Test product description"
    price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    stock_quantity = 100


class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = Customer

    full_name = factory.Faker("name")
    email = factory.Faker("email")
    phone_number = factory.Faker("phone_number")
    address = factory.Faker("address")


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    customer = factory.SubFactory(CustomerFactory)
    status = Order.Status.PENDING
    total_amount = 0


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 2
    price_at_purchase = factory.LazyAttribute(lambda o: o.product.price)
