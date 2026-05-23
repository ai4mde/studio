import sys, os

system_id   = os.environ.get('PROTOTYPE_SYSTEM', '')
project_name = os.environ.get('PROTOTYPE_NAME', '')

if not system_id or not project_name:
    print(f'ERROR: PROTOTYPE_SYSTEM and PROTOTYPE_NAME must be set', flush=True)
    sys.exit(1)

proto_path  = f'/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}'
print(f'Seeding prototype: {project_name}  path: {proto_path}', flush=True)

if not os.path.isdir(proto_path):
    print(f'ERROR: prototype directory not found: {proto_path}', flush=True)
    sys.exit(1)

if proto_path not in sys.path:
    sys.path.insert(0, proto_path)

os.environ['DJANGO_SETTINGS_MODULE'] = f'{project_name}.settings'

import django
django.setup()

from django.conf import settings as _dj_settings
print(f'Database: {_dj_settings.DATABASES["default"]["NAME"]}', flush=True)

from shared_models.models import (
    User, Category, Seller, Product, ProductImage,
    DeliveryOption, Customer, Review, Cart, CartItem,
    Address, Payment, PaymentMethod, Order, OrderLine, RelatedProduct
)

# Clear
for m in [OrderLine, Order, CartItem, Cart, Review, DeliveryOption,
          ProductImage, RelatedProduct, Product, Seller, Category,
          Customer, Payment, PaymentMethod, Address]:
    m.objects.all().delete()
User.objects.filter(is_superuser=False).delete()
print('Cleared existing data.')

# Categories
cat_phones  = Category.objects.create(category_id='cat-001', name='Smartphones',  slug='smartphones', parent_category_id='', depth=0)
cat_laptops = Category.objects.create(category_id='cat-002', name='Laptops',       slug='laptops',      parent_category_id='', depth=0)
cat_home    = Category.objects.create(category_id='cat-003', name='Home & Garden', slug='home-garden',  parent_category_id='', depth=0)
cat_audio   = Category.objects.create(category_id='cat-004', name='Audio',         slug='audio',        parent_category_id='', depth=0)
print('Created 4 categories.')

# Sellers
_u, _created = User.objects.get_or_create(username='techstore',  defaults=dict(email='techstore@bol.com',  is_Seller=True))
if _created: _u.set_password('demo1234'); _u.save()
_u, _created = User.objects.get_or_create(username='gadgetshop', defaults=dict(email='gadgetshop@bol.com', is_Seller=True))
if _created: _u.set_password('demo1234'); _u.save()
seller1 = Seller.objects.create(seller_id='sel-001', business_name='TechStore NL', rating='4.8', review_count=1240, is_verified=True, ships_from='Amsterdam', response_time='< 1 hour')
seller2 = Seller.objects.create(seller_id='sel-002', business_name='GadgetShop',   rating='4.5', review_count=873,  is_verified=True, ships_from='Rotterdam',  response_time='< 2 hours')
print('Created 2 sellers.')

# Products
p1 = Product.objects.create(
    product_id='prod-001', name='Samsung Galaxy S24 Ultra', brand='Samsung', ean='8806095268835',
    description='Flagship smartphone with 200MP camera and Galaxy AI. 6.8-inch QHD+ AMOLED, S Pen included.',
    price='EUR 1149', original_price='EUR 1299', discount_pct=11, stock_quantity=42,
    rating='4.7', review_count=328, weight_kg='0.23', is_active=True, Category=cat_phones, Seller=seller1)
p2 = Product.objects.create(
    product_id='prod-002', name='Apple iPhone 15 Pro', brand='Apple', ean='0195949038785',
    description='Titanium design with A17 Pro chip, 48MP main camera, and Action Button. 128GB storage.',
    price='EUR 1029', original_price='EUR 1029', discount_pct=0, stock_quantity=28,
    rating='4.8', review_count=512, weight_kg='0.19', is_active=True, Category=cat_phones, Seller=seller1)
p3 = Product.objects.create(
    product_id='prod-003', name='MacBook Air M3 15-inch', brand='Apple', ean='0195949130403',
    description='M3 chip, 15-inch Liquid Retina display, 8GB RAM, 256GB SSD. All-day battery life.',
    price='EUR 1499', original_price='EUR 1599', discount_pct=6, stock_quantity=15,
    rating='4.9', review_count=187, weight_kg='1.51', is_active=True, Category=cat_laptops, Seller=seller2)
p4 = Product.objects.create(
    product_id='prod-004', name='Dell XPS 15 OLED', brand='Dell', ean='5397184758419',
    description='15.6-inch OLED laptop, Intel Core i7, 16GB RAM, 512GB SSD. InfinityEdge display.',
    price='EUR 1349', original_price='EUR 1549', discount_pct=13, stock_quantity=8,
    rating='4.6', review_count=94, weight_kg='1.86', is_active=True, Category=cat_laptops, Seller=seller2)
p5 = Product.objects.create(
    product_id='prod-005', name='Google Pixel 8 Pro', brand='Google', ean='0840244700522',
    description='Google AI phone with Tensor G3, 50MP camera, Magic Eraser and 7 years of OS updates.',
    price='EUR 799', original_price='EUR 999', discount_pct=20, stock_quantity=33,
    rating='4.5', review_count=201, weight_kg='0.21', is_active=True, Category=cat_phones, Seller=seller2)
p6 = Product.objects.create(
    product_id='prod-006', name='Sony WH-1000XM5', brand='Sony', ean='4548736132412',
    description='Industry-leading noise cancelling headphones. 30-hour battery, multipoint connection.',
    price='EUR 299', original_price='EUR 379', discount_pct=21, stock_quantity=67,
    rating='4.8', review_count=892, weight_kg='0.25', is_active=True, Category=cat_audio, Seller=seller1)
p7 = Product.objects.create(
    product_id='prod-007', name='Philips Hue Starter Kit', brand='Philips', ean='8718699703288',
    description='Smart LED starter kit with Bridge. 16 million colours, voice control, energy saving.',
    price='EUR 79', original_price='EUR 99', discount_pct=20, stock_quantity=120,
    rating='4.4', review_count=445, weight_kg='0.45', is_active=True, Category=cat_home, Seller=seller1)
p8 = Product.objects.create(
    product_id='prod-008', name='Lenovo ThinkPad X1 Carbon', brand='Lenovo', ean='0196380105483',
    description='Ultra-light business laptop, 14-inch IPS, Intel Core i5, 16GB RAM, 512GB SSD.',
    price='EUR 1199', original_price='EUR 1399', discount_pct=14, stock_quantity=20,
    rating='4.7', review_count=156, weight_kg='1.12', is_active=True, Category=cat_laptops, Seller=seller2)
products = [p1, p2, p3, p4, p5, p6, p7, p8]
print(f'Created {len(products)} products.')

# Product Images
image_map = {
    'prod-001': 'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=600',
    'prod-002': 'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600',
    'prod-003': 'https://images.unsplash.com/photo-1611186871525-e07b873d4fc2?w=600',
    'prod-004': 'https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=600',
    'prod-005': 'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=600',
    'prod-006': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600',
    'prod-007': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600',
    'prod-008': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600',
}
for i, prod in enumerate(products):
    ProductImage.objects.create(
        image_id=f'img-{i+1:03d}', product_id=prod.product_id,
        thumb_url=image_map[prod.product_id], alt_text=prod.name,
        is_primary=True, sort_order=1, Product=prod)
print(f'Created {len(products)} product images.')

# Delivery Options
for prod in products:
    DeliveryOption.objects.create(
        option_id=f'del-{prod.product_id}-1', product_id=prod.product_id,
        method='Standard Delivery', estimated_days=2, cost='EUR 0.00',
        is_free=True, cutoff_time='23:59', return_policy_days=30, Product=prod)
    DeliveryOption.objects.create(
        option_id=f'del-{prod.product_id}-2', product_id=prod.product_id,
        method='Same Day Delivery', estimated_days=0, cost='EUR 6.95',
        is_free=False, cutoff_time='15:00', return_policy_days=30, Product=prod)
print(f'Created {len(products) * 2} delivery options.')

# Related Products
for prod in products:
    others = [p for p in products if p != prod][:3]
    for op in others:
        RelatedProduct.objects.create(
            product_id=op.product_id, name=op.name,
            price=int(op.price.replace('EUR ', '').replace(',', '')),
            Product=prod)
print('Created related products.')

# Customers
_u, _created = User.objects.get_or_create(username='jan_devries',  defaults=dict(email='jan@example.com',  first_name='Jan',  last_name='de Vries', is_Customer=True))
if _created: _u.set_password('demo1234'); _u.save()
_u, _created = User.objects.get_or_create(username='emma_bakker', defaults=dict(email='emma@example.com', first_name='Emma', last_name='Bakker',   is_Customer=True))
if _created: _u.set_password('demo1234'); _u.save()
cust1 = Customer.objects.create(customer_id='cust-001', email='jan@example.com',  first_name='Jan',  last_name='de Vries', phone='+31 6 1234 5678', is_active=True)
cust2 = Customer.objects.create(customer_id='cust-002', email='emma@example.com', first_name='Emma', last_name='Bakker',   phone='+31 6 9876 5432', is_active=True)
print('Created 2 customers.')

# Reviews
Review.objects.create(review_id='rev-001', product_id='prod-001', customer_id='cust-001', rating=5,
    title='Incredible camera and AI features',
    body='The 200MP camera is stunning. Galaxy AI makes everything easier. Battery lasts all day.',
    is_verified_purchase=True, Customer=cust1, Product=p1)
Review.objects.create(review_id='rev-002', product_id='prod-001', customer_id='cust-002', rating=4,
    title='Great phone, pricey but worth it',
    body='Performance is top notch. S Pen is a bonus I did not expect to use so much.',
    is_verified_purchase=True, Customer=cust2, Product=p1)
Review.objects.create(review_id='rev-003', product_id='prod-002', customer_id='cust-001', rating=5,
    title='Best iPhone ever made',
    body='A17 Pro is lightning fast. Camera quality phenomenal. Titanium build feels premium.',
    is_verified_purchase=True, Customer=cust1, Product=p2)
Review.objects.create(review_id='rev-004', product_id='prod-003', customer_id='cust-002', rating=5,
    title='Perfect laptop for everyday use',
    body='M3 chip handles everything effortlessly. Battery 12+ hours easily. Silent and fast.',
    is_verified_purchase=True, Customer=cust2, Product=p3)
Review.objects.create(review_id='rev-005', product_id='prod-006', customer_id='cust-001', rating=5,
    title='Best noise-cancelling headphones',
    body='Noise cancelling is on another level. Comfortable for long sessions. Sound quality superb.',
    is_verified_purchase=True, Customer=cust1, Product=p6)
print('Created 5 reviews.')

# Addresses
addr1 = Address.objects.create(address_id='addr-001', customer_id='cust-001',
    street='Damrak', house_number='1', city='Amsterdam',
    postal_code='1012 LG', country='Netherlands', is_default=True, Customer=cust1)
addr2 = Address.objects.create(address_id='addr-002', customer_id='cust-002',
    street='Coolsingel', house_number='42', city='Rotterdam',
    postal_code='3011 AD', country='Netherlands', is_default=True, Customer=cust2)
print('Created 2 addresses.')

# Carts and orders
cart1 = Cart.objects.create(cart_id='cart-001', customer_id=cust1.customer_id, total_price='EUR 1448', item_count=2, Customer=cust1)
cart2 = Cart.objects.create(cart_id='cart-002', customer_id=cust2.customer_id, total_price='EUR 379', item_count=1, Customer=cust2)
CartItem.objects.create(cart_item_id='ci-001', cart_id=cart1.cart_id, product_id=p1.product_id, quantity=1, unit_price=p1.price, subtotal=p1.price, Cart=cart1, Product=p1)
CartItem.objects.create(cart_item_id='ci-002', cart_id=cart1.cart_id, product_id=p6.product_id, quantity=1, unit_price=p6.price, subtotal=p6.price, Cart=cart1, Product=p6)
CartItem.objects.create(cart_item_id='ci-003', cart_id=cart2.cart_id, product_id=p6.product_id, quantity=1, unit_price=p6.price, subtotal=p6.price, Cart=cart2, Product=p6)
print('Created 2 carts and 3 cart items.')

pay1 = Payment.objects.create(payment_id='pay-001', order_id='ord-001', method='ideal', amount='EUR 1448', currency='EUR', status='completed', transaction_id='txn-001')
pay2 = Payment.objects.create(payment_id='pay-002', order_id='ord-002', method='credit_card', amount='EUR 379', currency='EUR', status='completed', transaction_id='txn-002')
PaymentMethod.objects.create(name='ideal', description='Dutch online bank payment', provider='iDEAL')
PaymentMethod.objects.create(name='credit_card', description='Credit card payment', provider='Visa / Mastercard')
PaymentMethod.objects.create(name='paypal', description='PayPal wallet payment', provider='PayPal')
print('Created 3 payment methods.')
order1 = Order.objects.create(order_id='ord-001', customer_id=cust1.customer_id, status='confirmed', total_amount='EUR 1448', shipping_address_id=addr1.address_id, Payment=pay1, Address=addr1, Customer=cust1)
order2 = Order.objects.create(order_id='ord-002', customer_id=cust2.customer_id, status='shipped', total_amount='EUR 379', shipping_address_id=addr2.address_id, Payment=pay2, Address=addr2, Customer=cust2)
OrderLine.objects.create(line_id='line-001', order_id=order1.order_id, product_id=p1.product_id, quantity=1, unit_price=p1.price, subtotal=p1.price, Product=p1, Order=order1)
OrderLine.objects.create(line_id='line-002', order_id=order1.order_id, product_id=p6.product_id, quantity=1, unit_price=p6.price, subtotal=p6.price, Product=p6, Order=order1)
OrderLine.objects.create(line_id='line-003', order_id=order2.order_id, product_id=p6.product_id, quantity=1, unit_price=p6.price, subtotal=p6.price, Product=p6, Order=order2)
print('Created 2 payments, 2 orders, and 3 order lines.')

# System user
_u, _created = User.objects.get_or_create(username='system', defaults=dict(email='system@bol.com', is_System=True))
if _created: _u.set_password('demo1234'); _u.save()
print('Created system user.')

print()
print('=== Seed complete ===')
print(f'Categories:    {Category.objects.count()}')
print(f'Sellers:       {Seller.objects.count()}')
print(f'Products:      {Product.objects.count()}')
print(f'Images:        {ProductImage.objects.count()}')
print(f'Delivery opts: {DeliveryOption.objects.count()}')
print(f'Customers:     {Customer.objects.count()}')
print(f'Reviews:       {Review.objects.count()}')
print(f'Addresses:     {Address.objects.count()}')
print(f'Carts:         {Cart.objects.count()}')
print(f'Cart items:    {CartItem.objects.count()}')
print(f'Payments:      {Payment.objects.count()}')
print(f'Pay methods:   {PaymentMethod.objects.count()}')
print(f'Orders:        {Order.objects.count()}')
print(f'Order lines:   {OrderLine.objects.count()}')
print(f'Users:         {User.objects.count()}')
