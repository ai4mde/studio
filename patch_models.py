MODELS_PATH = "/usr/src/prototypes/generated_prototypes/a0000002-0000-5000-8000-000000000000/sync1781202455394/shared_models/models.py"

with open(MODELS_PATH, "r") as f:
    content = f.read()

OLD = (
    "    def addCartItem(self, quantity):\n"
    "        cart = Cart.objects.first()\n"
    "        if cart is None:\n"
    "            cart = Cart.objects.create()\n"
    "        CartItem.objects.create(Cart=cart, Product=self, quantity=int(quantity))"
)

NEW = (
    "    def addCartItem(self, quantity):\n"
    "        cart = Cart.objects.first()\n"
    "        if cart is None:\n"
    "            customer = Customer.objects.first()\n"
    "            if customer is None:\n"
    "                return\n"
    "            cart = Cart.objects.create(Customer=customer)\n"
    "        CartItem.objects.create(Cart=cart, Product=self, quantity=int(quantity))"
)

if OLD in content:
    with open(MODELS_PATH, "w") as f:
        f.write(content.replace(OLD, NEW))
    print("Fixed models.py")
elif NEW in content:
    print("Already correct.")
else:
    # Show current method
    idx = content.find("def addCartItem")
    print("Current:", content[idx:idx+250] if idx >= 0 else "Not found")
