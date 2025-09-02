from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, F
from rest_framework.decorators import api_view, permission_classes
from .models import (
    User, Shop, Category, Product, ProductInfo, Parameter,
    ProductParameter, Contact, Order, OrderItem, ConfirmEmailToken
)
from rest_framework.authtoken.models import Token



User = get_user_model()

class RegisterView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        type = request.data.get("type", User.Types.BUYER)

        if not email or not password:
            return Response({"error": "Email и пароль обязательны"}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Пользователь уже существует"}, status=400)

        user = User.objects.create_user(email=email, password=password, type=type)
        return Response({"message": "Пользователь зарегистрирован"})

class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({"error": "Неверные учетные данные"}, status=400)

        token, created = Token.objects.get_or_create(user=user)

        return Response({
            "message": "Вход выполнен",
            "user_id": user.id,
            "token": token.key
        })

class ProductListView(APIView):
    def get(self, request):
        products = ProductInfo.objects.select_related('product', 'shop').all()
        data = [
            {
                "id": p.id,
                "name": p.product.name,
                "shop": p.shop.name,
                "price": p.price,
                "quantity": p.quantity,
                "model": p.model,
                "parameters": {
                    param.parameter.name: param.value
                    for param in p.parameters.all()
                }
            }
            for p in products
        ]
        return Response(data)

class BasketView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        order = Order.objects.filter(user=request.user, state=Order.States.CART).first()
        if not order:
            return Response({"items": [], "total": 0})

        items = order.items.select_related('product_info__product', 'product_info__shop')
        data = [
            {
                "product": item.product_info.product.name,
                "shop": item.product_info.shop.name,
                "quantity": item.quantity,
                "price": item.product_info.price,
                "total": item.total
            }
            for item in items
        ]
        return Response({"items": data, "total": order.total})

class BasketAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        product_info_id = request.data.get("product_info")
        quantity = int(request.data.get("quantity", 1))

        if not product_info_id:
            return Response({"error": "Не указан product_info"}, status=400)

        try:
            product_info = ProductInfo.objects.get(id=product_info_id)
        except ProductInfo.DoesNotExist:
            return Response({"error": f"Товар с id={product_info_id} не найден"}, status=404)

        order, _ = Order.objects.get_or_create(user=request.user, state=Order.States.CART)
        product_info = ProductInfo.objects.get(id=product_info_id)

        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            product_info=product_info,
            defaults={"quantity": quantity}
        )
        if not created:
            order_item.quantity += quantity
            order_item.save()

        return Response({"message": "Товар добавлен в корзину"})

class BasketRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        item_id = request.data.get("order_item_id")
        OrderItem.objects.filter(id=item_id, order__user=request.user).delete()
        return Response({"message": "Товар удален из корзины"})

class ContactView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contacts = Contact.objects.filter(user=request.user)
        data = [
            {
                "id": c.id,
                "city": c.city,
                "street": c.street,
                "house": c.house,
                "apartment": c.apartment,
                "phone": c.phone
            } for c in contacts
        ]
        return Response(data)

class ContactAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        contact = Contact.objects.create(user=request.user, **data)
        return Response({"message": "Контакт добавлен", "id": contact.id})

class ContactRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        Contact.objects.filter(id=pk, user=request.user).delete()
        return Response({"message": "Контакт удалён"})

class ConfirmOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        contact_id = request.data.get("contact_id")
        contact = Contact.objects.get(id=contact_id, user=request.user)
        order = Order.objects.filter(user=request.user, state=Order.States.CART).first()
        if not order:
            return Response({"error": "Корзина пуста"}, status=400)

        order.contact = contact
        order.state = Order.States.NEW
        order.save()

        return Response({"message": "Заказ подтвержден", "order_id": order.id})

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).exclude(state=Order.States.CART)
        data = []
        for order in orders:
            items = [
                {
                    "product": item.product_info.product.name,
                    "shop": item.product_info.shop.name,
                    "quantity": item.quantity,
                    "price": item.product_info.price,
                    "total": item.total
                }
                for item in order.items.all()
            ]
            data.append({
                "id": order.id,
                "created": order.created_at,
                "state": order.get_state_display(),
                "total": order.total,
                "items": items
            })

        return Response(data)



    class RegisterView(APIView):
        def post(self, request):
            email = request.data.get("email")
            password = request.data.get("password")
            type = request.data.get("type", User.Types.BUYER)

            if not email or not password:
                return Response({"error": "Email и пароль обязательны"}, status=400)

            if User.objects.filter(email=email).exists():
                return Response({"error": "Пользователь уже существует"}, status=400)

            user = User.objects.create_user(email=email, password=password, type=type)
            token = ConfirmEmailToken.objects.create(user=user)

            # Отправляем email (тестовый)
            send_mail(
                subject="Подтверждение регистрации",
                message=f"Ваш токен подтверждения: {token.key}",
                from_email="no-reply@shop.com",
                recipient_list=[email],
            )

            return Response({"message": "Пользователь зарегистрирован. Проверьте email."})
