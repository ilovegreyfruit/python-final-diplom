"""
URL configuration for orders project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic.base import RedirectView
from backend.views import RegisterView, LoginView, ProductListView, BasketView, BasketAddView, BasketRemoveView, ContactView, ContactAddView, ContactRemoveView, ConfirmOrderView, OrderListView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('basket/', BasketView.as_view(), name='basket'),
    path('basket/add/', BasketAddView.as_view(), name='basket-add'),
    path('basket/remove/', BasketRemoveView.as_view(), name='basket-remove'),
    path('contacts/', ContactView.as_view(), name='contacts'),
    path('contacts/add/', ContactAddView.as_view(), name='contacts-add'),
    path('contacts/remove/<int:pk>/', ContactRemoveView.as_view(), name='contacts-remove'),
    path('order/confirm/', ConfirmOrderView.as_view(), name='confirm-order'),
    path('orders/', OrderListView.as_view(), name='order-list'),
    path("", RedirectView.as_view(url="/products/", permanent=False)),

]
