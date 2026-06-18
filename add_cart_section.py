from metadata.models import Interface

iface = Interface.objects.get(id='ec58bb5b-fb1a-44c4-b9ff-dbc0c2a8944c')
data = iface.data or {}

CORRECT_BODY = (
    "def addCartItem(self, quantity):\n"
    "    cart = Cart.objects.first()\n"
    "    if cart is None:\n"
    "        customer = Customer.objects.first()\n"
    "        if customer is None:\n"
    "            return\n"
    "        cart = Cart.objects.create(Customer=customer)\n"
    "    CartItem.objects.create(Cart=cart, Product=self, quantity=int(quantity))"
)

updated = False
for s in data.get("sections", []):
    if s.get("id") == "product_detail_product_add_to_cart":
        for m in s.get("methods", []):
            if m.get("name") == "addCartItem":
                m["body"] = CORRECT_BODY
                updated = True

if updated:
    iface.data = data
    iface.save()
    print("DSL updated.")
else:
    print("Not found.")
