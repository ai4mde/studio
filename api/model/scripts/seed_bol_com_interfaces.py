import os
import sys
import uuid

sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")

import django

django.setup()

from diagram.models import Diagram, Edge, Node
from metadata.models import Classifier, Interface, Relation

NAMESPACE = uuid.UUID("77d86611-70f8-4b87-a6d4-112f857dcb37")
SHOPPING_FLOW_ACTIVITY_DIAGRAM_ID = "d0000003-0000-5000-8000-000000000000"
VIEW_ORDER_CONFIRMATION_ACTION_ID = "ac000016-0000-5000-8000-000000000000"
SHOPPING_INITIAL_ACTION_ID = "ac000001-0000-5000-8000-000000000000"
VIEW_CART_ACTION_ID = "ac000002-0000-5000-8000-000000000000"
PROCEED_TO_CHECKOUT_ACTION_ID = "ac000003-0000-5000-8000-000000000000"
ENTER_SHIPPING_ADDRESS_ACTION_ID = "ac000004-0000-5000-8000-000000000000"
SELECT_PAYMENT_ACTION_ID = "ac000005-0000-5000-8000-000000000000"
PROCESS_PAYMENT_ACTION_ID = "ac000006-0000-5000-8000-000000000000"
CREATE_ORDER_ACTION_ID = "ac000008-0000-5000-8000-000000000000"
SEND_ORDER_CONFIRMATION_ACTION_ID = "ac000009-0000-5000-8000-000000000000"
UPDATE_INVENTORY_ACTION_ID = "ac000010-0000-5000-8000-000000000000"
BROWSE_PRODUCTS_ACTION_ID = "ac000013-0000-5000-8000-000000000000"
VIEW_PRODUCT_DETAIL_ACTION_ID = "ac000014-0000-5000-8000-000000000000"
ADD_TO_CART_ACTION_ID = "ac000015-0000-5000-8000-000000000000"
SHOPPING_FINAL_ACTION_ID = "ac000012-0000-5000-8000-000000000000"
VIEW_CART_NODE_ID = "f0000202-0000-5000-8000-000000000000"
ENTER_SHIPPING_ADDRESS_NODE_ID = "f0000204-0000-5000-8000-000000000000"
SELECT_PAYMENT_NODE_ID = "f0000205-0000-5000-8000-000000000000"
PROCESS_PAYMENT_NODE_ID = "f0000206-0000-5000-8000-000000000000"
CREATE_ORDER_NODE_ID = "f0000208-0000-5000-8000-000000000000"
SEND_ORDER_CONFIRMATION_NODE_ID = "f0000209-0000-5000-8000-000000000000"
BROWSE_PRODUCTS_NODE_ID = "f0000216-0000-5000-8000-000000000000"
VIEW_ORDER_CONFIRMATION_NODE_ID = "f0000210-0000-5000-8000-000000000000"
UPDATE_INVENTORY_NODE_ID = "f0000213-0000-5000-8000-000000000000"
SHOPPING_INITIAL_NODE_ID = "f0000201-0000-5000-8000-000000000000"
SHOPPING_FINAL_NODE_ID = "f0000212-0000-5000-8000-000000000000"
SHOPPING_FLOW_SWIMLANE_GROUP_CLASSIFIER_ID = "ac000017-0000-5000-8000-000000000000"
SHOPPING_FLOW_SWIMLANE_GROUP_NODE_ID = "f0000217-0000-5000-8000-000000000000"
CREATE_ORDER_TO_CONFIRMATION_RELATION_ID = "10000210-0000-5000-8000-000000000000"
CONFIRMATION_TO_SEND_ORDER_RELATION_ID = "10000216-0000-5000-8000-000000000000"


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


def method(name, action, parameters=None, target_model=None, call_name=None, body=None):
    out = {
        "name": name,
        "action": action,
        "parameters": parameters or [],
    }
    if target_model:
        out["target_model"] = target_model
    if call_name:
        out["call_name"] = call_name
    if body:
        out["body"] = body
    return out


ADD_TO_CART_METHOD = method(
    "Add to Cart",
    "cart.add_item",
    parameters=[{"name": "quantity", "type": "int"}],
    target_model="CartItem",
    call_name="add_to_cart",
    body="""\
def add_to_cart(self, quantity=1):
    quantity = int(quantity or 1)
    if quantity < 1:
        quantity = 1
    cart = Cart.objects.first()
    if not cart:
        return False
    existing = CartItem.objects.filter(Cart=cart, Product=self).first()
    if existing:
        existing.quantity = (existing.quantity or 0) + quantity
        existing.subtotal = existing.unit_price
        existing.save()
        return True
    CartItem.objects.create(
        cart_item_id=f"ci-{CartItem.objects.count() + 1:03d}",
        cart_id=cart.cart_id,
        product_id=self.product_id,
        quantity=quantity,
        unit_price=self.price,
        subtotal=self.price,
        Cart=cart,
        Product=self,
    )
    return True""",
)

SELECT_PAYMENT_METHOD = method(
    "Select Payment",
    "payment.select",
    parameters=[
        {"name": "amount", "type": "str"},
        {"name": "currency", "type": "str"},
    ],
    target_model="Payment",
    call_name="select_payment",
    body="""\
def select_payment(self, amount=0, currency='EUR', active_process_node_id=None):
    try:
        from workflow_engine.models import ActiveProcessNode
        payment = Payment.objects.create(
            method=self.name,
            amount=float(amount or 0),
            currency=str(currency or 'EUR'),
            status='completed',
        )
        if active_process_node_id:
            apn = ActiveProcessNode.objects.get(id=int(active_process_node_id))
            apn.active_process.add_associated_instance(payment)
        return payment
    except Exception:
        return None""",
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
        "description": method_def.get("description", "Generated custom method."),
        "action": method_def.get("action"),
    }
    if method_def.get("target_model"):
        method_payload["target_model"] = method_def["target_model"]
    if method_def.get("call_name"):
        method_payload["call_name"] = method_def["call_name"]
    if method_def.get("body"):
        method_payload["body"] = method_def["body"]

    for index, existing in enumerate(methods):
        if existing.get("name") == method_name:
            methods[index] = {**existing, **method_payload}
            break
    else:
        methods.append(method_payload)

    data["methods"] = methods
    classifier.data = data
    classifier.save(update_fields=["data"])


def ensure_payment_method_class():
    if "PaymentMethod" in CLASS_IDS:
        return

    payment = Classifier.objects.filter(data__name="Payment", data__type="class").first()
    if not payment:
        return

    classifier = Classifier.objects.create(
        project=payment.project,
        system=payment.system,
        data={
            "name": "PaymentMethod",
            "type": "class",
            "abstract": False,
            "attributes": [
                attr("name"),
                attr("description"),
                attr("provider"),
            ],
            "methods": [],
        },
    )
    CLASS_IDS["PaymentMethod"] = str(classifier.id)


def ensure_activity_swimlane_group():
    diagram = Diagram.objects.filter(id=SHOPPING_FLOW_ACTIVITY_DIAGRAM_ID).first()
    if not diagram:
        return

    swimlanes = []
    for actor_name in ["Customer", "System", "Seller"]:
        actor = Classifier.objects.filter(
            system=diagram.system,
            data__type="actor",
            data__name=actor_name,
        ).first()
        if actor:
            swimlanes.append(
                {"type": "swimlane", "role": "swimlane", "actorNode": str(actor.id), "actorNodeName": actor_name}
            )

    if not swimlanes:
        return

    swimlane_group, _ = Classifier.objects.update_or_create(
        id=SHOPPING_FLOW_SWIMLANE_GROUP_CLASSIFIER_ID,
        defaults={
            "project": diagram.system.project,
            "system": diagram.system,
            "data": {
                "type": "swimlanegroup",
                "height": 1120,
                "width": 320,
                "horizontal": False,
                "swimlanes": swimlanes,
            },
        },
    )
    Node.objects.update_or_create(
        id=SHOPPING_FLOW_SWIMLANE_GROUP_NODE_ID,
        defaults={
            "diagram": diagram,
            "cls": swimlane_group,
            "data": {"position": {"x": -60, "y": -120}},
        },
    )


def ensure_usecase_activity_links():
    links = {
        "Browse and Search Products": {
            "actions": [BROWSE_PRODUCTS_ACTION_ID],
            "classes": ["Product", "Category"],
        },
        "View Product Detail Page": {
            "actions": [VIEW_PRODUCT_DETAIL_ACTION_ID],
            "classes": ["Product", "ProductImage", "Seller", "Review"],
        },
        "Add Product to Cart": {
            "actions": [ADD_TO_CART_ACTION_ID],
            "classes": ["Cart", "CartItem", "Product"],
        },
        "Purchase Product": {
            "actions": [
                VIEW_CART_ACTION_ID,
                ENTER_SHIPPING_ADDRESS_ACTION_ID,
                SELECT_PAYMENT_ACTION_ID,
                PROCESS_PAYMENT_ACTION_ID,
                CREATE_ORDER_ACTION_ID,
                VIEW_ORDER_CONFIRMATION_ACTION_ID,
            ],
            "activities": [SHOPPING_FLOW_ACTIVITY_DIAGRAM_ID],
            "classes": ["Cart", "CartItem", "Product", "Order", "OrderLine", "Payment", "Address"],
        },
        "Track Order": {
            "classes": ["Order"],
        },
        "Write Product Review": {
            "classes": ["Review", "Product"],
        },
        "Manage Account": {
            "classes": ["Customer", "Address"],
        },
        "Manage Product Listings": {
            "classes": ["Product", "DeliveryOption"],
        },
        "Process Payment": {
            "actions": [PROCESS_PAYMENT_ACTION_ID],
            "activities": [SHOPPING_FLOW_ACTIVITY_DIAGRAM_ID],
            "classes": ["Payment"],
        },
        "Send Order Confirmation": {
            "actions": [SEND_ORDER_CONFIRMATION_ACTION_ID],
            "activities": [SHOPPING_FLOW_ACTIVITY_DIAGRAM_ID],
            "classes": ["Order"],
        },
    }
    for usecase_name, spec in links.items():
        classifier = Classifier.objects.filter(data__type="usecase", data__name=usecase_name).first()
        if not classifier:
            continue
        data = dict(classifier.data)
        data["actions"] = spec.get("actions", [])
        data["activities"] = spec.get("activities", [])
        data["classes"] = [
            CLASS_IDS[class_name]
            for class_name in spec.get("classes", [])
            if class_name in CLASS_IDS
        ]
        classifier.data = data
        classifier.save(update_fields=["data"])


def ensure_shopping_activity_diagram():
    diagram = Diagram.objects.filter(id=SHOPPING_FLOW_ACTIVITY_DIAGRAM_ID).first()
    if not diagram:
        return

    actors = {
        name: Classifier.objects.filter(
            system=diagram.system,
            data__type="actor",
            data__name=name,
        ).first()
        for name in ["Customer", "System", "Seller"]
    }
    if any(actor is None for actor in actors.values()):
        return

    def base_action(name, actor_name, classes, precondition, postcondition, automatic=False):
        actor = actors[actor_name]
        return {
            "body": "",
            "name": name,
            "page": None,
            "role": "action",
            "type": "action",
            "classes": classes,
            "publish": None,
            "actorNode": str(actor.id),
            "namespace": "",
            "operation": None,
            "subscribe": None,
            "customCode": None,
            "isAutomatic": automatic,
            "actorNodeName": actor_name,
            "localPrecondition": precondition,
            "application_models": None,
            "localPostcondition": postcondition,
        }

    classifiers = {}

    classifiers["initial"], _ = Classifier.objects.update_or_create(
        id=SHOPPING_INITIAL_ACTION_ID,
        defaults={
            "project": diagram.system.project,
            "system": diagram.system,
            "data": {
                "name": None,
                "type": "initial",
                "role": "control",
                "activity_scope": "activity",
                "scheduled": False,
                "schedule": "",
            },
        },
    )
    classifiers["final"], _ = Classifier.objects.update_or_create(
        id=SHOPPING_FINAL_ACTION_ID,
        defaults={
            "project": diagram.system.project,
            "system": diagram.system,
            "data": {"name": None, "type": "final", "role": "control", "activity_scope": "activity"},
        },
    )

    action_specs = [
        (
            "view_cart",
            VIEW_CART_ACTION_ID,
            "View Cart",
            "Customer",
            ["Cart", "CartItem"],
            "Customer has items in the cart or wants to review the cart",
            "Customer has reviewed the cart and can continue checkout",
            False,
        ),
        (
            "enter_address",
            ENTER_SHIPPING_ADDRESS_ACTION_ID,
            "Enter Shipping Address",
            "Customer",
            ["Address", "Cart"],
            "Customer proceeds from the cart",
            "A shipping address is selected or entered",
            False,
        ),
        (
            "select_payment",
            SELECT_PAYMENT_ACTION_ID,
            "Select Payment Method",
            "Customer",
            ["Payment", "PaymentMethod", "Cart"],
            "Shipping address is known",
            "Customer has selected a payment method",
            False,
        ),
        (
            "process_payment",
            PROCESS_PAYMENT_ACTION_ID,
            "Process Payment",
            "System",
            ["Payment"],
            "Customer submitted a payment method",
            "Payment is authorised or rejected",
            True,
        ),
        (
            "create_order",
            CREATE_ORDER_ACTION_ID,
            "Create Order",
            "System",
            ["Order", "OrderLine", "Cart"],
            "Payment is authorised",
            "Order and order lines are created from the cart",
            True,
        ),
        (
            "seller_confirmation",
            SEND_ORDER_CONFIRMATION_ACTION_ID,
            "Send Order Confirmation",
            "Seller",
            ["Order", "OrderLine"],
            "A paid order is ready for seller confirmation",
            "Seller confirms the order for fulfilment",
            False,
        ),
        (
            "update_inventory",
            UPDATE_INVENTORY_ACTION_ID,
            "Update Inventory",
            "System",
            ["Product", "OrderLine"],
            "Seller confirmed the order",
            "Purchased product stock is reduced",
            True,
        ),
        (
            "view_confirmation",
            VIEW_ORDER_CONFIRMATION_ACTION_ID,
            "View Order Confirmation",
            "Customer",
            ["Order", "OrderLine"],
            "Order has been confirmed and inventory updated",
            "Customer sees the order confirmation",
            False,
        ),
    ]

    for key, classifier_id, name, actor_name, classes, pre, post, automatic in action_specs:
        classifiers[key], _ = Classifier.objects.update_or_create(
            id=classifier_id,
            defaults={
                "project": diagram.system.project,
                "system": diagram.system,
                "data": base_action(name, actor_name, classes, pre, post, automatic),
            },
        )

    node_specs = [
        ("initial", SHOPPING_INITIAL_NODE_ID, 100, -40),
        ("view_cart", VIEW_CART_NODE_ID, 100, 100),
        ("enter_address", ENTER_SHIPPING_ADDRESS_NODE_ID, 100, 240),
        ("select_payment", SELECT_PAYMENT_NODE_ID, 100, 380),
        ("process_payment", PROCESS_PAYMENT_NODE_ID, 420, 380),
        ("create_order", CREATE_ORDER_NODE_ID, 420, 520),
        ("seller_confirmation", SEND_ORDER_CONFIRMATION_NODE_ID, 740, 520),
        ("update_inventory", UPDATE_INVENTORY_NODE_ID, 420, 660),
        ("view_confirmation", VIEW_ORDER_CONFIRMATION_NODE_ID, 100, 800),
        ("final", SHOPPING_FINAL_NODE_ID, 100, 940),
    ]
    for key, node_id, x, y in node_specs:
        Node.objects.update_or_create(
            id=node_id,
            defaults={
                "diagram": diagram,
                "cls": classifiers[key],
                "data": {"position": {"x": x, "y": y}},
            },
        )

    Node.objects.filter(diagram=diagram).exclude(
        id__in=[SHOPPING_FLOW_SWIMLANE_GROUP_NODE_ID] + [node_id for _, node_id, _, _ in node_specs]
    ).delete()

    controlflow_data = {
        "type": "controlflow",
        "guard": "",
        "weight": "",
        "condition": None,
        "is_directed": True,
        "position_handlers": [],
    }

    workflow_classifiers = list(classifiers.values())
    Edge.objects.filter(diagram=diagram).delete()
    Relation.objects.filter(system=diagram.system, source__in=workflow_classifiers).delete()
    Relation.objects.filter(system=diagram.system, target__in=workflow_classifiers).delete()

    edge_specs = [
        ("initial_to_cart", "initial", "view_cart"),
        ("cart_to_address", "view_cart", "enter_address"),
        ("address_to_payment", "enter_address", "select_payment"),
        ("payment_to_process", "select_payment", "process_payment"),
        ("process_to_order", "process_payment", "create_order"),
        ("order_to_seller", "create_order", "seller_confirmation"),
        ("seller_to_inventory", "seller_confirmation", "update_inventory"),
        ("inventory_to_confirmation", "update_inventory", "view_confirmation"),
        ("confirmation_to_final", "view_confirmation", "final"),
    ]
    for edge_key, source_key, target_key in edge_specs:
        relation, _ = Relation.objects.update_or_create(
            id=stable_id("shopping-workflow", edge_key),
            defaults={
                "system": diagram.system,
                "source": classifiers[source_key],
                "target": classifiers[target_key],
                "data": controlflow_data,
            },
        )
        Edge.objects.update_or_create(
            rel=relation,
            defaults={"diagram": diagram, "data": {}},
        )

    # Keep these deterministic IDs available for older references in generated interfaces.
    Relation.objects.update_or_create(
        id=CREATE_ORDER_TO_CONFIRMATION_RELATION_ID,
        defaults={
            "system": diagram.system,
            "source": classifiers["update_inventory"],
            "target": classifiers["view_confirmation"],
            "data": controlflow_data,
        },
    )
    Relation.objects.update_or_create(
        id=CONFIRMATION_TO_SEND_ORDER_RELATION_ID,
        defaults={
            "system": diagram.system,
            "source": classifiers["create_order"],
            "target": classifiers["seller_confirmation"],
            "data": controlflow_data,
        },
    )


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
        attrs("Product.name", "Product.brand", "quantity", "unit_price", "subtotal"),
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
        "PaymentMethod",
        "card",
        8,
        "purple",
        attrs("name", "description", "provider"),
        query={"limit": 4, "order_by": [{"field": "name", "direction": "asc"}]},
        methods=[SELECT_PAYMENT_METHOD],
        columns="2",
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
        page(actor, "Order Confirmation", [order_confirm, order_lines], type_="activity", action=option("View Order Confirmation", VIEW_ORDER_CONFIRMATION_NODE_ID)),
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

ensure_payment_method_class()
ensure_shopping_activity_diagram()
ensure_activity_swimlane_group()

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
    "PaymentMethod",
    "Review",
    "ProductImage",
    "DeliveryOption",
    "Address",
    "RelatedProduct",
}
missing = sorted(required_classes - set(CLASS_IDS))
if missing:
    raise RuntimeError(f"Missing required bol.com classes: {', '.join(missing)}")

ensure_usecase_activity_links()
update_related_product_image_type()
upsert_class_method("Product", ADD_TO_CART_METHOD)
upsert_class_method("PaymentMethod", SELECT_PAYMENT_METHOD)
patch_interface("Customer", build_customer_interface)
patch_interface("Seller", build_seller_interface)
print("Done.")
