import os
import sys
import uuid

sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")

import django

django.setup()

from metadata.models import Classifier, Interface

NAMESPACE = uuid.UUID("77d86611-70f8-4b87-a6d4-112f857dcb37")


def stable_id(*parts):
    return str(uuid.uuid5(NAMESPACE, ":".join(str(part) for part in parts)))


def option(label, value):
    return {"label": label, "value": value}


def attr(name, type_=None):
    spec = ATTRIBUTE_INDEX.get(name, {})
    return {
        "name": name,
        "type": type_ or spec.get("type", "str"),
        "derived": bool(spec.get("derived", False)),
        "enum": spec.get("enum"),
    }


def attrs(*names):
    return [attr(name) for name in names]


def ops(create=False, update=False, delete=False):
    return {"create": create, "update": update, "delete": delete}


def style(
    color,
    density="normal",
    card_style="elevated",
    columns="3",
    radius="xl",
    image_position="top",
    image_size="md",
):
    return {
        "color": color,
        "density": density,
        "card_style": card_style,
        "columns": str(columns),
        "radius": radius,
        "image_position": image_position,
        "image_size": image_size,
    }


def sec(
    actor,
    name,
    class_name,
    layout,
    col_span,
    color,
    attributes,
    operations=None,
    query=None,
    density="normal",
    columns="3",
    card_style="elevated",
    radius="xl",
    text="",
    image_position="top",
    image_size="md",
    view_detail_page=None,
    related_to=None,
    relation_field=None,
    methods=None,
    cta_label=None,
    success_page=None,
    position=None,
):
    s = style(
        color,
        density=density,
        card_style=card_style,
        columns=columns,
        radius=radius,
        image_position=image_position,
        image_size=image_size,
    )
    if cta_label:
        s["cta_label"] = cta_label
    if success_page:
        s["success_page"] = success_page
    out = {
        "id": stable_id(actor, "section", name),
        "name": name,
        "class": CLASS_IDS[class_name],
        "model_name": class_name,
        "layout": layout,
        "col_span": col_span,
        "text": text,
        "style": s,
        "attributes": attributes,
        "operations": operations or ops(),
    }
    if query:
        out["query"] = query
    if view_detail_page:
        out["view_detail_page"] = view_detail_page
    if related_to:
        out["related_to"] = related_to
    if relation_field:
        out["relation_field"] = relation_field
    if methods:
        out["methods"] = methods
    if position:
        out["position"] = position
    return out


def method(name, action, parameters=None, target_model=None, call_name=None):
    out = {
        "name": name,
        "action": action,
        "parameters": parameters or [],
    }
    if target_model:
        out["target_model"] = target_model
    if call_name:
        out["call_name"] = call_name
    return out


ADD_TO_CART_METHOD = method(
    "Add to Cart",
    "cart.add_item",
    parameters=[{"name": "quantity", "type": "int"}],
    target_model="CartItem",
    call_name="add_to_cart",
)


def page(
    actor,
    name,
    sections,
    type_="normal",
    single_record=False,
    layout="vertical",
    gap="normal",
    category=None,
    action=None,
):
    return {
        "id": stable_id(actor, "page", name).replace("-", ""),
        "name": name,
        "type": option(type_.title(), type_),
        "layout": option(layout.title(), layout),
        "gap": option(gap.title(), gap),
        "category": category,
        "action": action,
        "single_record": single_record,
        "sections": [{"label": section["name"], "value": section["id"]} for section in sections],
    }


def category(class_name):
    return {
        "id": stable_id("category", class_name),
        "name": class_name,
    }


def page_category(class_name):
    return {
        "label": class_name,
        "value": {"id": CLASS_IDS[class_name], "name": class_name},
    }


def interface_for_actor(actor_name):
    return Interface.objects.get(actor__data__name=actor_name)


def update_related_product_image_type():
    related_product = Classifier.objects.filter(data__name="RelatedProduct").first()
    if not related_product:
        return
    changed = False
    data = dict(related_product.data)
    for item in data.get("attributes", []):
        if item.get("name") == "image_url" and item.get("type") != "image":
            item["type"] = "image"
            changed = True
    if changed:
        related_product.data = data
        related_product.save(update_fields=["data"])


def upsert_class_method(class_name, method_def):
    classifier = Classifier.objects.filter(data__name=class_name, data__type="class").first()
    if not classifier:
        return

    data = dict(classifier.data or {})
    methods = list(data.get("methods") or [])
    method_name = method_def["name"]
    method_payload = {
        "name": method_name,
        "type": "bool",
        "abstract": False,
        "parameters": method_def.get("parameters", []),
        "visibility": "public",
        "description": "Adds the product to the current shopping cart.",
        "action": method_def.get("action"),
    }
    if method_def.get("target_model"):
        method_payload["target_model"] = method_def["target_model"]
    if method_def.get("call_name"):
        method_payload["call_name"] = method_def["call_name"]

    for index, existing in enumerate(methods):
        if existing.get("name") == method_name:
            updated = {**existing, **method_payload}
            updated.pop("body", None)
            methods[index] = updated
            break
    else:
        methods.append(method_payload)

    data["methods"] = methods
    classifier.data = data
    classifier.save(update_fields=["data"])


def build_customer_interface():
    actor = "Customer"

    hero = sec(
        actor,
        "Home Hero Search",
        "Product",
        "card",
        12,
        "blue",
        attrs("image_url", "name", "brand", "price", "rating"),
        query={
            "limit": 4,
            "filters": [{"field": "is_active", "operator": "eq", "value": "true"}],
        },
        columns="4",
        text="Find everything for home, school, work, gifts, and daily life.",
        view_detail_page="Product Detail",
    )
    categories = sec(
        actor,
        "Shop Categories",
        "Category",
        "list",
        3,
        "slate",
        attrs("name", "slug", "depth"),
        query={
            "limit": 12,
            "filters": [{"field": "depth", "operator": "lte", "value": "2"}],
            "order_by": [{"field": "name", "direction": "asc"}],
        },
        density="compact",
        card_style="flat",
    )
    featured = sec(
        actor,
        "Featured Products",
        "Product",
        "card",
        9,
        "blue",
        attrs("image_url", "name", "brand", "price", "rating", "review_count"),
        query={
            "limit": 8,
            "filters": [
                {"field": "is_active", "operator": "eq", "value": "true"},
                {"field": "stock_quantity", "operator": "gt", "value": "0"},
            ],
            "order_by": [{"field": "name", "direction": "asc"}],
        },
        columns="4",
        view_detail_page="Product Detail",
    )
    deals = sec(
        actor,
        "Deals For You",
        "Product",
        "card",
        12,
        "orange",
        attrs("image_url", "name", "original_price", "price", "discount_pct"),
        query={
            "limit": 4,
            "filters": [
                {"field": "is_active", "operator": "eq", "value": "true"},
                {"field": "stock_quantity", "operator": "gt", "value": "0"},
            ],
            "order_by": [{"field": "price", "direction": "asc"}],
        },
        columns="4",
        view_detail_page="Product Detail",
    )
    search_results = sec(
        actor,
        "Search Results",
        "Product",
        "card",
        12,
        "blue",
        attrs("image_url", "name", "brand", "price", "rating", "review_count"),
        query={
            "limit": 24,
            "filters": [{"field": "is_active", "operator": "eq", "value": "true"}],
            "order_by": [{"field": "name", "direction": "asc"}],
        },
        columns="4",
        view_detail_page="Product Detail",
    )
    product_info = sec(
        actor,
        "Product Info",
        "Product",
        "detail",
        6,
        "blue",
        attrs(
            "image_url",
            "name",
            "brand",
            "price",
            "original_price",
            "discount_pct",
            "rating",
            "review_count",
            "description",
            "stock_quantity",
            "weight_kg",
        ),
        image_position="top",
        image_size="md",
    )
    gallery = sec(
        actor,
        "Product Gallery",
        "ProductImage",
        "gallery",
        6,
        "slate",
        attrs("image_url", "thumb_url", "alt_text", "is_primary"),
        query={"limit": 6, "order_by": [{"field": "sort_order", "direction": "asc"}]},
        related_to=product_info["id"],
        relation_field="Product",
    )
    add_to_cart = sec(
        actor,
        "Add To Cart",
        "CartItem",
        "form",
        12,
        "orange",
        attrs("quantity"),
        operations=ops(create=True),
        columns="1",
        cta_label="In winkelwagen",
        success_page="Browse_Products",
    )
    delivery = sec(
        actor,
        "Delivery Options",
        "DeliveryOption",
        "list",
        12,
        "green",
        attrs("method", "estimated_days", "cost", "is_free", "cutoff_time", "return_policy_days"),
        query={"limit": 4, "order_by": [{"field": "estimated_days", "direction": "asc"}]},
        related_to=product_info["id"],
        relation_field="Product",
        density="compact",
        card_style="flat",
    )
    seller = sec(
        actor,
        "Seller Info",
        "Seller",
        "card",
        12,
        "slate",
        attrs("business_name", "rating", "review_count", "is_verified", "ships_from", "response_time"),
        columns="2",
        card_style="outlined",
    )
    reviews = sec(
        actor,
        "Customer Reviews",
        "Review",
        "list",
        12,
        "orange",
        attrs("rating", "title", "body", "is_verified_purchase"),
        ops(create=True),
        query={
            "limit": 8,
            "order_by": [{"field": "id", "direction": "desc"}],
        },
        related_to=product_info["id"],
        relation_field="Product",
    )
    related = sec(
        actor,
        "Related Products",
        "RelatedProduct",
        "card",
        12,
        "blue",
        attrs("image_url", "name", "price"),
        query={"limit": 4, "exclude_source": True},
        related_to=product_info["id"],
        columns="4",
        view_detail_page="Product Detail",
    )
    cart_items = sec(
        actor,
        "Cart Items",
        "CartItem",
        "list",
        8,
        "orange",
        attrs("product_id", "quantity", "unit_price", "subtotal"),
        ops(update=True, delete=True),
        query={"limit": 20},
    )
    cart_summary = sec(
        actor,
        "Cart Summary",
        "Cart",
        "detail",
        4,
        "slate",
        attrs("cart_id", "item_count", "total_price"),
        columns="1",
        card_style="outlined",
    )
    address_form = sec(
        actor,
        "Delivery Address",
        "Address",
        "detail",
        8,
        "blue",
        attrs("street", "house_number", "postal_code", "city", "country", "is_default"),
        ops(create=True, update=True),
        query={
            "limit": 3,
            "filters": [{"field": "is_default", "operator": "eq", "value": "true"}],
        },
        columns="1",
    )
    payment_method = sec(
        actor,
        "Payment Method",
        "Payment",
        "card",
        8,
        "purple",
        attrs("method", "amount", "currency", "status"),
        ops(create=True),
        columns="3",
    )
    payment_summary = sec(
        actor,
        "Payment Summary",
        "Payment",
        "detail",
        4,
        "slate",
        attrs("method", "amount", "currency", "status", "transaction_id"),
        query={"limit": 1},
        columns="1",
        card_style="outlined",
    )
    order_confirm = sec(
        actor,
        "Order Confirmed",
        "Order",
        "detail",
        12,
        "green",
        attrs("order_id", "status", "created_at", "total_amount", "shipping_address_id"),
        query={"limit": 1, "order_by": [{"field": "created_at", "direction": "desc"}]},
        density="spacious",
        columns="1",
    )
    order_lines = sec(
        actor,
        "Ordered Items",
        "OrderLine",
        "list",
        12,
        "slate",
        attrs("product_id", "quantity", "unit_price", "subtotal"),
        query={"limit": 20},
        card_style="flat",
    )
    account = sec(
        actor,
        "Account Details",
        "Customer",
        "detail",
        6,
        "blue",
        attrs("email", "first_name", "last_name", "phone", "registered_at", "is_active"),
        ops(update=True),
        columns="1",
    )
    addresses = sec(
        actor,
        "Saved Addresses",
        "Address",
        "list",
        6,
        "green",
        attrs("street", "house_number", "postal_code", "city", "country", "is_default"),
        ops(create=True, update=True, delete=True),
        query={"limit": 5, "order_by": [{"field": "is_default", "direction": "desc"}]},
    )
    orders = sec(
        actor,
        "My Orders",
        "Order",
        "table",
        12,
        "orange",
        attrs("order_id", "status", "created_at", "updated_at", "total_amount"),
        query={"limit": 10, "order_by": [{"field": "created_at", "direction": "desc"}]},
        view_detail_page="Order Detail",
    )
    order_detail = sec(
        actor,
        "Order Detail",
        "Order",
        "detail",
        12,
        "orange",
        attrs("order_id", "status", "created_at", "updated_at", "total_amount", "shipping_address_id"),
        columns="1",
    )

    sections = [
        hero,
        categories,
        featured,
        deals,
        search_results,
        product_info,
        gallery,
        add_to_cart,
        delivery,
        seller,
        reviews,
        related,
        cart_items,
        cart_summary,
        address_form,
        payment_method,
        payment_summary,
        order_confirm,
        order_lines,
        account,
        addresses,
        orders,
        order_detail,
    ]
    pages = [
        page(actor, "Browse Products", [hero, categories, featured, deals]),
        page(actor, "Search Results", [categories, search_results]),
        page(actor, "Product Detail", [product_info, gallery, add_to_cart, delivery, seller, reviews, related], single_record=True, category=page_category("Product")),
        page(actor, "Shopping Cart", [cart_items, cart_summary], type_="activity", action=option("View Cart", "f0000202-0000-5000-8000-000000000000")),
        page(actor, "Checkout Address", [address_form, cart_summary], type_="activity", action=option("Enter Shipping Address", "f0000204-0000-5000-8000-000000000000")),
        page(actor, "Checkout Payment", [payment_method, payment_summary], type_="activity", action=option("Select Payment Method", "f0000205-0000-5000-8000-000000000000")),
        page(actor, "Order Confirmation", [order_confirm, order_lines], type_="activity", action=option("Create Order", "f0000208-0000-5000-8000-000000000000")),
        page(actor, "My Account", [account, addresses]),
        page(actor, "My Orders", [orders]),
        page(actor, "Order Detail", [order_detail, order_lines], single_record=True, category=page_category("Order")),
    ]
    return sections, pages


def build_seller_interface():
    actor = "Seller"

    seller_stats = sec(
        actor,
        "Sales Overview",
        "Seller",
        "card",
        12,
        "green",
        attrs("business_name", "rating", "review_count", "is_verified", "ships_from", "response_time"),
        ops(update=True),
        columns="2",
    )
    products = sec(
        actor,
        "My Products",
        "Product",
        "table",
        12,
        "blue",
        attrs("image_url", "name", "brand", "price", "original_price", "stock_quantity", "is_active"),
        ops(create=True, update=True, delete=True),
        query={"limit": 25, "order_by": [{"field": "name", "direction": "asc"}]},
        view_detail_page="Product Management",
    )
    product_editor = sec(
        actor,
        "Product Editor",
        "Product",
        "detail",
        12,
        "blue",
        attrs("image_url", "name", "brand", "ean", "description", "price", "original_price", "stock_quantity", "weight_kg", "is_active"),
        ops(create=True, update=True),
        columns="1",
        card_style="outlined",
    )
    inventory = sec(
        actor,
        "Inventory",
        "Product",
        "table",
        12,
        "purple",
        attrs("name", "brand", "stock_quantity", "is_active"),
        ops(update=True),
        query={
            "limit": 25,
            "filters": [{"field": "stock_quantity", "operator": "lte", "value": "10"}],
            "order_by": [{"field": "stock_quantity", "direction": "asc"}],
        },
    )
    incoming_orders = sec(
        actor,
        "Incoming Orders",
        "Order",
        "table",
        12,
        "orange",
        attrs("order_id", "customer_id", "status", "created_at", "total_amount", "shipping_address_id"),
        ops(update=True),
        query={
            "limit": 25,
            "filters": [{"field": "status", "operator": "in", "value": "pending,confirmed,shipped"}],
            "order_by": [{"field": "created_at", "direction": "desc"}],
        },
        view_detail_page="Order Management",
    )
    order_detail = sec(
        actor,
        "Order Detail",
        "Order",
        "detail",
        6,
        "orange",
        attrs("order_id", "status", "created_at", "updated_at", "total_amount", "shipping_address_id"),
        ops(update=True),
        columns="1",
    )
    order_items = sec(
        actor,
        "Order Items",
        "OrderLine",
        "list",
        6,
        "slate",
        attrs("product_id", "quantity", "unit_price", "subtotal"),
        query={"limit": 20},
        card_style="flat",
    )
    reviews = sec(
        actor,
        "Product Reviews",
        "Review",
        "table",
        12,
        "orange",
        attrs("product_id", "rating", "title", "body", "is_verified_purchase"),
        query={"limit": 25, "order_by": [{"field": "id", "direction": "desc"}]},
    )
    seller_profile = sec(
        actor,
        "Seller Profile",
        "Seller",
        "detail",
        12,
        "slate",
        attrs("business_name", "is_verified", "ships_from", "response_time", "rating", "review_count"),
        ops(update=True),
        columns="1",
        card_style="outlined",
    )

    sections = [
        seller_stats,
        products,
        product_editor,
        inventory,
        incoming_orders,
        order_detail,
        order_items,
        reviews,
        seller_profile,
    ]
    pages = [
        page(actor, "Seller Dashboard", [seller_stats, products, incoming_orders]),
        page(actor, "Product Management", [product_editor, inventory], single_record=True, category=page_category("Product")),
        page(actor, "Order Management", [order_detail, order_items], type_="activity", action=option("Send Order Confirmation", "f0000209-0000-5000-8000-000000000000")),
        page(actor, "Reviews", [reviews]),
        page(actor, "Seller Settings", [seller_profile]),
    ]
    return sections, pages


def patch_interface(actor_name, build):
    interface = interface_for_actor(actor_name)
    current = interface.data or {}
    sections, pages = build()
    current.update(
        {
            "sections": sections,
            "pages": pages,
            "categories": [category(name) for name in ["Product", "Category", "Cart", "Order", "Customer", "Seller"]],
            "styling": {
                "radius": 8,
                "textColor": "#111827",
                "accentColor": "#0A66C2",
                "selectedStyle": "modern",
                "backgroundColor": "#F7FAFC",
            },
            "tokens": {
                "region.header.bg": "bg-blue-700",
                "page.body.bg": "bg-slate-50",
                "page.body.text": "text-slate-900",
                "page.container.max_width": "max-w-7xl",
                "element.button.primary": "bg-yellow-400 text-blue-950",
                "element.text.accent": "text-blue-700",
            },
        }
    )
    interface.data = current
    interface.save(update_fields=["data"])
    print(f"{actor_name}: {len(pages)} pages, {len(sections)} sections")
    for item in pages:
        print(f"  PAGE {item['name']}")
    for item in sections:
        print(f"  SECTION {item['name']} query={bool(item.get('query'))}")


CLASSIFIERS = list(Classifier.objects.filter(data__type="class"))
CLASS_IDS = {item.data.get("name"): str(item.id) for item in CLASSIFIERS}
ATTRIBUTE_INDEX = {
    attribute.get("name"): attribute
    for item in CLASSIFIERS
    for attribute in item.data.get("attributes", [])
}

required_classes = {
    "Customer",
    "Product",
    "Category",
    "Seller",
    "Cart",
    "CartItem",
    "Order",
    "OrderLine",
    "Payment",
    "Review",
    "ProductImage",
    "DeliveryOption",
    "Address",
    "RelatedProduct",
}
missing = sorted(required_classes - set(CLASS_IDS))
if missing:
    raise RuntimeError(f"Missing required bol.com classes: {', '.join(missing)}")

update_related_product_image_type()
upsert_class_method("Product", ADD_TO_CART_METHOD)
patch_interface("Customer", build_customer_interface)
patch_interface("Seller", build_seller_interface)
print("Done.")
