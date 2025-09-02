import yaml
from pathlib import Path
from django.db import transaction
from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter

def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

@transaction.atomic
def import_shop_from_yaml(yaml_path):
    data = load_yaml(yaml_path)

    shop_name = data.get("shop")
    categories = data.get("categories", [])
    goods = data.get("goods", [])

    # 1. Создаём магазин
    shop, _ = Shop.objects.get_or_create(name=shop_name)

    # 2. Создаём категории и связываем с магазином
    for cat_data in categories:
        category, _ = Category.objects.get_or_create(id=cat_data["id"], defaults={"name": cat_data["name"]})
        category.shops.add(shop)

    # 3. Обрабатываем товары
    for item in goods:
        category = Category.objects.get(id=item["category"])

        product, _ = Product.objects.get_or_create(
            name=item["name"],
            category=category
        )

        product_info, created = ProductInfo.objects.update_or_create(
            product=product,
            shop=shop,
            external_id=item["id"],
            defaults={
                "model": item.get("model", ""),
                "quantity": item.get("quantity", 0),
                "price": item["price"],
                "price_rrc": item["price_rrc"]
            }
        )

        # 4. Параметры
        for param_name, param_value in item.get("parameters", {}).items():
            parameter, _ = Parameter.objects.get_or_create(name=param_name)
            ProductParameter.objects.update_or_create(
                product_info=product_info,
                parameter=parameter,
                defaults={"value": str(param_value)}
            )

    print(f"Импорт магазина '{shop.name}' завершён успешно.")

