import sys, os, urllib.request, urllib.parse, http.cookiejar, re
sys.path.insert(0, '/usr/src/prototypes/generated_prototypes/a0000002-0000-5000-8000-000000000000/sync1781202455394')
os.environ['DJANGO_SETTINGS_MODULE'] = 'sync1781202455394.settings'
import django; django.setup()
from shared_models.models import Product, Cart, CartItem

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
opener.open('http://localhost:8020/autologin?as=customer&next=/Customer/render_Customer_Product_Detail')

pk = Product.objects.first().pk

# Add to cart first
CartItem.objects.all().delete()
r = opener.open(
    f'http://localhost:8020/Customer/render_Customer_Product_Detail'
    f'?instance_id_product={pk}&custom_product_addCartItem={pk}&quantity=3'
)
print(f"CartItems after add: {CartItem.objects.count()}")

# Now view the cart page (activity flow step1 requires active_process_node_id)
# Try with node_id=1
r2 = opener.open('http://localhost:8020/Customer/render_Customer_View_Cart/1/')
html = r2.read().decode()
has_qty = 'quantity' in html.lower()
has_item = 'Cart Items' in html or 'cartitem' in html.lower() or 'view_cart_cartitem' in html.lower()
print(f"\nview_cart: HTTP 200  quantity={has_qty}  cart_items_section={has_item}")

# Check for CartItem section specifically
if 'view_cart_cartitem_list' in html:
    idx = html.find('view_cart_cartitem_list')
    print("CartItem section HTML:")
    print(html[idx:idx+400])
