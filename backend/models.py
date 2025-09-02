from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
# Create your models here.

class UserManager(BaseUserManager):
    """Менеджер пользователей с авторазицией по email"""

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Укажите email')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('type', 'shop')
        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Модель пользователя"""

    class Types(models.TextChoices):
        SHOP = 'shop', _('Магазин')
        BUYER = 'buyer', _('Покупатель')
    username = None
    email = models.EmailField(unique=True, verbose_name='Email')
    type = models.CharField(max_length=10, choices=Types.choices, default=Types.BUYER)
    company = models.CharField(max_length=80, blank=True, verbose_name='Компания')
    position = models.CharField(max_length=60, blank=True, verbose_name='Должность')

    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f'{self.email} ({self.get_type_display()})'

    @property
    def is_shop(self):
        return self.type == self.Types.SHOP

    @property
    def is_buyer(self):
        return self.type == self.Types.BUYER

class Shop(models.Model):
    """Магазин-поставщик"""

    name = models.CharField(max_length=100, verbose_name='Название')
    url = models.URLField(blank=True, null=True, verbose_name='Ссылка')
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='shop', null=True, blank=True
    )
    is_active = models.BooleanField(default=True, verbose_name='Прием заказов')

    def __str__(self):
        return self.name

    def toggle(self):
        self.is_active = not self.is_active
        self.save()

class Category(models.Model):
    """Категория товаров"""

    name = models.CharField(max_length=50, verbose_name='Название')
    shops = models.ManyToManyField(Shop, related_name='categories', blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    """Продукт"""

    name = models.CharField(max_length=100, verbose_name='Название')
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE, related_name='products'
    )

    def __str__(self):
        return self.name

class ProductInfo(models.Model):
    """Наличие, цена, остатки продуктов в магазине"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='items')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='items')
    external_id = models.PositiveIntegerField()
    model = models.CharField(max_length=80, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    price = models.DecimalField(max_digits=12, decimal_places=2)
    price_rrc = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop'], name='unique_product_shop'),
        ]

    def __str__(self):
        return f"{self.product} @ {self.shop}"

class Parameter(models.Model):
    """Характеристика продукта"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class ProductParameter(models.Model):
    """Значение характеристики для товара"""

    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, related_name='parameters')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='uniq_param_per_product'),
        ]
    def __str__(self):
        return f"{self.parameter.name} : {self.value}"

class Contact(models.Model):
    """Контактные данные покупателя"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contacts")
    city = models.CharField(max_length=50)
    street = models.CharField(max_length=100)
    house = models.CharField(max_length=15, blank=True)
    apartment = models.CharField(max_length=15, blank=True)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.city}, {self.street}, {self.house}"


class Order(models.Model):
    """Заказ"""

    class States(models.TextChoices):
        CART = "cart", _("Корзина")
        NEW = "new", _("Новый")
        CONFIRMED = "confirmed", _("Подтвержден")
        ASSEMBLED = "assembled", _("Собран")
        SENT = "sent", _("Отправлен")
        DELIVERED = "delivered", _("Доставлен")
        CANCELED = "canceled", _("Отменен")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=15, choices=States.choices, default=States.CART)
    contact = models.ForeignKey(
        Contact, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Order #{self.pk} ({self.get_state_display()})"

    @property
    def total(self):
        return sum(item.total for item in self.items.all())


class OrderItem(models.Model):
    """Строка заказа"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_info = models.ForeignKey(
        ProductInfo, on_delete=models.CASCADE, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product_info"], name="uniq_order_item"
            )
        ]

    @property
    def total(self):
        return self.quantity * self.product_info.price


class ConfirmEmailToken(models.Model):
    """Токен подтверждения email"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tokens")
    key = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = get_token_generator().generate_token()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Token for {self.user.email}"
