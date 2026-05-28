import os
import sys

system_id = os.environ.get('PROTOTYPE_SYSTEM', '')
project_name = os.environ.get('PROTOTYPE_NAME', '')

if not system_id or not project_name:
    print('ERROR: PROTOTYPE_SYSTEM and PROTOTYPE_NAME must be set', flush=True)
    sys.exit(1)

proto_path = f'/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}'
print(f'Seeding prototype: {project_name}  path: {proto_path}', flush=True)

if not os.path.isdir(proto_path):
    print(f'ERROR: prototype directory not found: {proto_path}', flush=True)
    sys.exit(1)

if proto_path not in sys.path:
    sys.path.insert(0, proto_path)

os.environ['DJANGO_SETTINGS_MODULE'] = f'{project_name}.settings'

import django

django.setup()

from django.apps import apps
from django.conf import settings as _dj_settings
from django.contrib.auth import get_user_model

print(f'Database: {_dj_settings.DATABASES["default"]["NAME"]}', flush=True)

models_by_name = {model.__name__: model for model in apps.get_app_config('shared_models').get_models()}
User = get_user_model()
USER_FIELD_NAMES = {field.name for field in User._meta.get_fields()}


def user_defaults(**defaults):
    return {key: value for key, value in defaults.items() if key in USER_FIELD_NAMES}


def get_or_create_user(username, email, **flags):
    defaults = user_defaults(email=email, **flags)
    user, created = User.objects.get_or_create(username=username, defaults=defaults)
    if created:
        user.set_password('demo1234')
        user.save()
    return user, created


def clear_shared_models():
    for model in models_by_name.values():
        model.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()


def has_ecommerce_models():
    required = [
        'Category', 'Seller', 'Product', 'ProductImage', 'DeliveryOption',
        'Customer', 'Review', 'Cart', 'CartItem', 'Address', 'Payment',
        'Order', 'OrderLine', 'RelatedProduct'
    ]
    return all(name in models_by_name for name in required)


def seed_ecommerce_models():
    Category = models_by_name['Category']
    Seller = models_by_name['Seller']
    Product = models_by_name['Product']
    ProductImage = models_by_name['ProductImage']
    DeliveryOption = models_by_name['DeliveryOption']
    Customer = models_by_name['Customer']
    Review = models_by_name['Review']
    Cart = models_by_name['Cart']
    CartItem = models_by_name['CartItem']
    Address = models_by_name['Address']
    Payment = models_by_name['Payment']
    Order = models_by_name['Order']
    OrderLine = models_by_name['OrderLine']
    RelatedProduct = models_by_name['RelatedProduct']

    cat_phones = Category.objects.create(category_id='cat-001', name='Smartphones', slug='smartphones', parent_category_id='', depth=0)
    cat_laptops = Category.objects.create(category_id='cat-002', name='Laptops', slug='laptops', parent_category_id='', depth=0)
    cat_home = Category.objects.create(category_id='cat-003', name='Home & Garden', slug='home-garden', parent_category_id='', depth=0)
    cat_audio = Category.objects.create(category_id='cat-004', name='Audio', slug='audio', parent_category_id='', depth=0)
    print('Created 4 categories.')

    _u, _c = get_or_create_user('techstore', 'techstore@bol.com', is_Seller=True)
    _u, _c = get_or_create_user('gadgetshop', 'gadgetshop@bol.com', is_Seller=True)
    seller1 = Seller.objects.create(seller_id='sel-001', business_name='TechStore NL', rating='4.8', review_count=1240, is_verified=True, ships_from='Amsterdam', response_time='< 1 hour')
    seller2 = Seller.objects.create(seller_id='sel-002', business_name='GadgetShop', rating='4.5', review_count=873, is_verified=True, ships_from='Rotterdam', response_time='< 2 hours')
    print('Created 2 sellers.')

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

    PRODUCT_IMAGES = {
        'prod-001': [('img-001-1', 'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=800&fit=crop', 'Samsung Galaxy S24 Ultra – front', True, 1), ('img-001-2', 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=800&fit=crop', 'Samsung Galaxy S24 Ultra – back', False, 2), ('img-001-3', 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&fit=crop', 'Samsung Galaxy S24 Ultra – S Pen', False, 3), ('img-001-4', 'https://images.unsplash.com/photo-1567581935884-3349723552ca?w=800&fit=crop', 'Samsung Galaxy S24 Ultra – in hand', False, 4)],
        'prod-002': [('img-002-1', 'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=800&fit=crop', 'iPhone 15 Pro – front', True, 1), ('img-002-2', 'https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=800&fit=crop', 'iPhone 15 Pro – back titanium', False, 2), ('img-002-3', 'https://images.unsplash.com/photo-1574751139207-cdb78ddbb739?w=800&fit=crop', 'iPhone 15 Pro – side profile', False, 3), ('img-002-4', 'https://images.unsplash.com/photo-1580910051074-3eb694886505?w=800&fit=crop', 'iPhone 15 Pro – box & cables', False, 4)],
        'prod-003': [('img-003-1', 'https://images.unsplash.com/photo-1611186871525-e07b873d4fc2?w=800&fit=crop', 'MacBook Air M3 – open angled', True, 1), ('img-003-2', 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&fit=crop', 'MacBook Air M3 – closed on desk', False, 2), ('img-003-3', 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=800&fit=crop', 'MacBook Air M3 – keyboard close', False, 3), ('img-003-4', 'https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=800&fit=crop', 'MacBook Air M3 – workspace', False, 4)],
        'prod-004': [('img-004-1', 'https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=800&fit=crop', 'Dell XPS 15 – open front', True, 1), ('img-004-2', 'https://images.unsplash.com/photo-1588702547919-26089e690ecc?w=800&fit=crop', 'Dell XPS 15 – side view', False, 2), ('img-004-3', 'https://images.unsplash.com/photo-1593642634524-b40b5baae6bb?w=800&fit=crop', 'Dell XPS 15 – OLED display', False, 3), ('img-004-4', 'https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?w=800&fit=crop', 'Dell XPS 15 – on desk', False, 4)],
        'prod-005': [('img-005-1', 'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=800&fit=crop', 'Google Pixel 8 Pro – front', True, 1), ('img-005-2', 'https://images.unsplash.com/photo-1565849904461-04a58ad377e0?w=800&fit=crop', 'Google Pixel 8 Pro – back', False, 2), ('img-005-3', 'https://images.unsplash.com/photo-1533228876829-65c94e7b5025?w=800&fit=crop', 'Google Pixel 8 Pro – camera bar', False, 3)],
        'prod-006': [('img-006-1', 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&fit=crop', 'Sony WH-1000XM5 – side profile', True, 1), ('img-006-2', 'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=800&fit=crop', 'Sony WH-1000XM5 – on ears', False, 2), ('img-006-3', 'https://images.unsplash.com/photo-1484704849700-f032a568e944?w=800&fit=crop', 'Sony WH-1000XM5 – flat lay', False, 3), ('img-006-4', 'https://images.unsplash.com/photo-1613040809024-b4ef7ba99bc3?w=800&fit=crop', 'Sony WH-1000XM5 – with case', False, 4)],
        'prod-007': [('img-007-1', 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&fit=crop', 'Philips Hue – kit contents', True, 1), ('img-007-2', 'https://images.unsplash.com/photo-1565814329452-e1efa11c5b89?w=800&fit=crop', 'Philips Hue – smart bulb', False, 2), ('img-007-3', 'https://images.unsplash.com/photo-1558002038-1055907df827?w=800&fit=crop', 'Philips Hue – living room scene', False, 3)],
        'prod-008': [('img-008-1', 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&fit=crop', 'ThinkPad X1 Carbon – open', True, 1), ('img-008-2', 'https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=800&fit=crop', 'ThinkPad X1 Carbon – keyboard', False, 2), ('img-008-3', 'https://images.unsplash.com/photo-1484788984921-03950022c38b?w=800&fit=crop', 'ThinkPad X1 Carbon – on desk', False, 3), ('img-008-4', 'https://images.unsplash.com/photo-1587613759197-3c3f5d4c6c68?w=800&fit=crop', 'ThinkPad X1 Carbon – closed', False, 4)],
    }

    prod_map = {p.product_id: p for p in products}
    total_images = 0
    for pid, imgs in PRODUCT_IMAGES.items():
        prod = prod_map[pid]
        for image_id, url, alt, primary, order in imgs:
            ProductImage.objects.create(image_id=image_id, product_id=pid, thumb_url=url, alt_text=alt, is_primary=primary, sort_order=order, Product=prod)
            total_images += 1
    print(f'Created {total_images} product images ({total_images // len(products):.1f} avg per product).')

    for prod in products:
        DeliveryOption.objects.create(option_id=f'del-{prod.product_id}-1', product_id=prod.product_id, method='Standard Delivery', estimated_days=2, cost='EUR 0.00', is_free=True, cutoff_time='23:59', return_policy_days=30, Product=prod)
        DeliveryOption.objects.create(option_id=f'del-{prod.product_id}-2', product_id=prod.product_id, method='Same Day Delivery', estimated_days=0, cost='EUR 6.95', is_free=False, cutoff_time='15:00', return_policy_days=30, Product=prod)
    print(f'Created {len(products) * 2} delivery options.')

    RELATED_MAP = {
        'prod-001': ['prod-002', 'prod-005', 'prod-006'],
        'prod-002': ['prod-001', 'prod-005', 'prod-006'],
        'prod-003': ['prod-004', 'prod-008', 'prod-006'],
        'prod-004': ['prod-003', 'prod-008', 'prod-006'],
        'prod-005': ['prod-001', 'prod-002', 'prod-006'],
        'prod-006': ['prod-002', 'prod-003', 'prod-001'],
        'prod-007': ['prod-001', 'prod-006', 'prod-003'],
        'prod-008': ['prod-003', 'prod-004', 'prod-006'],
    }

    for source_pid, related_pids in RELATED_MAP.items():
        source = prod_map[source_pid]
        for rel_pid in related_pids:
            rel = prod_map[rel_pid]
            RelatedProduct.objects.create(product_id=rel.product_id, name=rel.name, price=int(rel.price.replace('EUR ', '').replace(',', '')), Product=source)
    print(f'Created {sum(len(v) for v in RELATED_MAP.values())} related product links.')

    _u, _c = get_or_create_user('jan_devries', 'jan@example.com', first_name='Jan', last_name='de Vries', is_Customer=True)
    _u, _c = get_or_create_user('emma_bakker', 'emma@example.com', first_name='Emma', last_name='Bakker', is_Customer=True)
    cust1 = Customer.objects.create(customer_id='cust-001', email='jan@example.com', first_name='Jan', last_name='de Vries', phone='+31 6 1234 5678', is_active=True)
    cust2 = Customer.objects.create(customer_id='cust-002', email='emma@example.com', first_name='Emma', last_name='Bakker', phone='+31 6 9876 5432', is_active=True)
    print('Created 2 customers.')

    Review.objects.create(review_id='rev-001', product_id='prod-001', customer_id='cust-001', rating=5, title='Incredible camera and AI features', body='The 200MP camera is stunning. Galaxy AI makes everything easier. Battery lasts all day.', is_verified_purchase=True, Customer=cust1, Product=p1)
    Review.objects.create(review_id='rev-002', product_id='prod-001', customer_id='cust-002', rating=4, title='Great phone, pricey but worth it', body='Performance is top notch. S Pen is a bonus I did not expect to use so much.', is_verified_purchase=True, Customer=cust2, Product=p1)
    Review.objects.create(review_id='rev-003', product_id='prod-002', customer_id='cust-001', rating=5, title='Best iPhone ever made', body='A17 Pro is lightning fast. Camera quality phenomenal. Titanium build feels premium.', is_verified_purchase=True, Customer=cust1, Product=p2)
    Review.objects.create(review_id='rev-004', product_id='prod-003', customer_id='cust-002', rating=5, title='Perfect laptop for everyday use', body='M3 chip handles everything effortlessly. Battery 12+ hours easily. Silent and fast.', is_verified_purchase=True, Customer=cust2, Product=p3)
    Review.objects.create(review_id='rev-005', product_id='prod-006', customer_id='cust-001', rating=5, title='Best noise-cancelling headphones', body='Noise cancelling is on another level. Comfortable for long sessions. Sound quality superb.', is_verified_purchase=True, Customer=cust1, Product=p6)
    Review.objects.create(review_id='rev-006', product_id='prod-004', customer_id='cust-002', rating=4, title='Stunning OLED display', body='Colors are vivid and deep blacks make a real difference for creative work. A bit heavy though.', is_verified_purchase=True, Customer=cust2, Product=p4)
    Review.objects.create(review_id='rev-007', product_id='prod-008', customer_id='cust-001', rating=5, title='Best business laptop I have owned', body='Ultra-light and the keyboard is class-leading. Battery easily gets me through a full work day.', is_verified_purchase=True, Customer=cust1, Product=p8)
    print('Created 7 reviews.')

    addr1 = Address.objects.create(address_id='addr-001', customer_id='cust-001', street='Damrak', house_number='1', city='Amsterdam', postal_code='1012 LG', country='Netherlands', is_default=True, Customer=cust1)
    addr2 = Address.objects.create(address_id='addr-002', customer_id='cust-002', street='Coolsingel', house_number='42', city='Rotterdam', postal_code='3011 AD', country='Netherlands', is_default=True, Customer=cust2)
    print('Created 2 addresses.')

    cart1 = Cart.objects.create(cart_id='cart-001', customer_id=cust1.customer_id, total_price='EUR 1448', item_count=2, Customer=cust1)
    cart2 = Cart.objects.create(cart_id='cart-002', customer_id=cust2.customer_id, total_price='EUR 379', item_count=1, Customer=cust2)
    CartItem.objects.create(cart_item_id='ci-001', cart_id=cart1.cart_id, product_id=p1.product_id, quantity=1, unit_price=p1.price, subtotal=p1.price, Cart=cart1, Product=p1)
    CartItem.objects.create(cart_item_id='ci-002', cart_id=cart1.cart_id, product_id=p6.product_id, quantity=1, unit_price=p6.price, subtotal=p6.price, Cart=cart1, Product=p6)
    CartItem.objects.create(cart_item_id='ci-003', cart_id=cart2.cart_id, product_id=p6.product_id, quantity=1, unit_price=p6.price, subtotal=p6.price, Cart=cart2, Product=p6)
    print('Created 2 carts and 3 cart items.')

    pay1 = Payment.objects.create(payment_id='pay-001', order_id='ord-001', method='ideal', amount='EUR 1448', currency='EUR', status='completed', transaction_id='txn-001')
    pay2 = Payment.objects.create(payment_id='pay-002', order_id='ord-002', method='credit_card', amount='EUR 379', currency='EUR', status='completed', transaction_id='txn-002')
    order1 = Order.objects.create(order_id='ord-001', customer_id=cust1.customer_id, status='confirmed', total_amount='EUR 1448', shipping_address_id=addr1.address_id, Payment=pay1, Address=addr1, Customer=cust1)
    order2 = Order.objects.create(order_id='ord-002', customer_id=cust2.customer_id, status='shipped', total_amount='EUR 379', shipping_address_id=addr2.address_id, Payment=pay2, Address=addr2, Customer=cust2)
    OrderLine.objects.create(line_id='line-001', order_id=order1.order_id, product_id=p1.product_id, quantity=1, unit_price=p1.price, subtotal=p1.price, Product=p1, Order=order1)
    OrderLine.objects.create(line_id='line-002', order_id=order1.order_id, product_id=p6.product_id, quantity=1, unit_price=p6.price, subtotal=p6.price, Product=p6, Order=order1)
    OrderLine.objects.create(line_id='line-003', order_id=order2.order_id, product_id=p6.product_id, quantity=1, unit_price=p6.price, subtotal=p6.price, Product=p6, Order=order2)
    print('Created 2 payments, 2 orders, and 3 order lines.')

    get_or_create_user('system', 'system@bol.com', is_System=True)
    print('Created system user.')


def seed_loan_app_models():
    Applicant = models_by_name.get('Applicant')
    LoanApplication = models_by_name.get('LoanApplication')
    Document = models_by_name.get('Document')
    ApplicationNote = models_by_name.get('ApplicationNote')

    if Applicant is None or LoanApplication is None:
        print('Skipping fallback seed: Applicant/LoanApplication models are unavailable.')
        return

    get_or_create_user('demo-applicant', 'demo-applicant@example.com', is_Applicant=True)
    get_or_create_user('demo-loan-officer', 'demo-loan-officer@example.com', is_Loan_officer=True)

    def fields_for(model):
        return {field.name for field in model._meta.fields}

    def create_supported(model, **values):
        model_fields = fields_for(model)
        return model.objects.create(**{key: value for key, value in values.items() if key in model_fields})

    applicant1 = create_supported(
        Applicant,
        applicant_id='app-001', first_name='Amina', last_name='Khan', date_of_birth='1992-01-14',
        credit_score=742, address='72 Orchard Lane', email='amina.khan@example.com',
        phone='+31 20 555 0101', employment_status='Employed', annual_income=72000)
    applicant2 = create_supported(
        Applicant,
        applicant_id='app-002', first_name='Luca', last_name='Ferrari', date_of_birth='1988-08-02',
        credit_score=689, address='21 River Road', email='luca.ferrari@example.com',
        phone='+31 20 555 0102', employment_status='Self-employed', annual_income=58000)

    loan_fields = fields_for(LoanApplication)
    loan1_values = dict(
        application_id='loan-001', loan_amount=25000, amount=25000,
        requires_additional_documents=False, approved=False,
        reason='Home renovation', status='Submitted', risk='Low', submitted_date='2026-05-10')
    loan2_values = dict(
        application_id='loan-002', loan_amount=12000, amount=12000,
        requires_additional_documents=True, approved=False,
        reason='Vehicle purchase', status='Needs documents', risk='Medium', submitted_date='2026-05-12')
    if 'Applicant' in loan_fields:
        loan1_values['Applicant'] = applicant1
        loan2_values['Applicant'] = applicant2
    loan1 = create_supported(LoanApplication, **loan1_values)
    loan2 = create_supported(LoanApplication, **loan2_values)

    if Document is not None:
        doc_fields = fields_for(Document)
        doc1_values = dict(document_id='doc-001', file_conent='Proof_of_income.pdf', file_content='Proof_of_income.pdf', upload_date='2026-05-10', valid=True, document_type='PDF')
        doc2_values = dict(document_id='doc-002', file_conent='Bank_statement.pdf', file_content='Bank_statement.pdf', upload_date='2026-05-12', valid=True, document_type='PDF')
        if 'LoanApplication' in doc_fields:
            doc1_values['LoanApplication'] = loan1
            doc2_values['LoanApplication'] = loan2
        create_supported(Document, **doc1_values)
        create_supported(Document, **doc2_values)

    if ApplicationNote is not None:
        note_fields = fields_for(ApplicationNote)
        note1_values = dict(note_id='note-001', comment='Applicant qualifies for standard review.', created_at='2026-05-10', author_role='Loan officer')
        note2_values = dict(note_id='note-002', comment='Additional documents requested for verification.', created_at='2026-05-12', author_role='Document analyst')
        if 'LoanApplication' in note_fields:
            note1_values['LoanApplication'] = loan1
            note2_values['LoanApplication'] = loan2
        create_supported(ApplicationNote, **note1_values)
        create_supported(ApplicationNote, **note2_values)

    print(f'Created {Applicant.objects.count()} applicants, {LoanApplication.objects.count()} loan applications, and fallback demo records.')


GENERIC_NAMES = ['Alpha Record', 'Beta Record', 'Gamma Record']
PERSON_NAMES = [('Amina', 'Khan'), ('Luca', 'Ferrari'), ('Maya', 'Chen')]
DOCUMENT_NAMES = ['Proof of income', 'Bank statement', 'Identity document']
STATUSES = ['active', 'pending', 'completed']
DATES = ['2026-05-10', '2026-05-12', '2026-05-15']
EMAILS = ['amina.khan@example.com', 'luca.ferrari@example.com', 'maya.chen@example.com']


def _generic_value(field, row):
    name = field.name.lower()
    internal = field.get_internal_type()
    if internal in ('AutoField', 'BigAutoField'):
        return None
    if internal == 'BooleanField':
        return row % 2 == 0
    if internal in ('IntegerField', 'PositiveIntegerField', 'SmallIntegerField', 'PositiveSmallIntegerField'):
        if 'score' in name:
            return [742, 689, 715][row]
        if 'count' in name or 'quantity' in name or 'stock' in name:
            return [12, 47, 8][row]
        return [100, 250, 500][row]
    if internal in ('FloatField', 'DecimalField'):
        return [49.99, 119.00, 199.00][row]
    if internal in ('DateField', 'DateTimeField'):
        return DATES[row]
    if internal == 'EmailField':
        return EMAILS[row]
    if internal in ('CharField', 'TextField', 'URLField', 'SlugField'):
        if 'email' in name:
            return EMAILS[row]
        if 'first' in name:
            return PERSON_NAMES[row][0]
        if 'last' in name:
            return PERSON_NAMES[row][1]
        if 'full' in name or name == 'name' or 'title' in name or 'label' in name:
            return GENERIC_NAMES[row]
        if 'status' in name or 'state' in name or 'phase' in name:
            return STATUSES[row]
        if 'date' in name or 'time' in name:
            return DATES[row]
        if 'amount' in name or 'price' in name or 'cost' in name or 'total' in name:
            return ['EUR 49.99', 'EUR 119.00', 'EUR 199.00'][row]
        if 'file' in name or 'document' in name:
            return DOCUMENT_NAMES[row]
        if 'description' in name or 'summary' in name or 'body' in name or 'reason' in name:
            return f'Deterministic sample description {row + 1}'
        if name.endswith('_id') or name == 'id':
            return f'{field.model.__name__.lower()}-{row + 1:03d}'
        return f'{field.name}_{row + 1}'
    return None


def seed_generic_models():
    seeded = set()
    models = [m for name, m in models_by_name.items() if name != User.__name__]
    for _pass in range(len(models) + 1):
        progressed = False
        for model in models:
            if model in seeded or model.objects.exists():
                seeded.add(model)
                continue
            rows = []
            blocked = False
            for row in range(3):
                values = {}
                for field in model._meta.fields:
                    if field.primary_key and field.get_internal_type() in ('AutoField', 'BigAutoField'):
                        continue
                    if field.is_relation and getattr(field, 'remote_field', None):
                        related = field.remote_field.model.objects.first()
                        if related is None and not field.null:
                            blocked = True
                            break
                        values[field.name] = related
                        continue
                    value = _generic_value(field, row)
                    if value is not None:
                        values[field.name] = value
                if blocked:
                    break
                rows.append(values)
            if blocked:
                continue
            for values in rows:
                model.objects.create(**values)
            seeded.add(model)
            progressed = True
            print(f'Created {len(rows)} generic {model.__name__} records.')
        if not progressed:
            break


def shared_model_record_count():
    return sum(model.objects.count() for name, model in models_by_name.items() if name != User.__name__)


clear_shared_models()
print('Cleared existing data.')

if has_ecommerce_models():
    seed_ecommerce_models()
else:
    seed_loan_app_models()

if shared_model_record_count() == 0:
    print('No domain-specific seed data was created; using generic deterministic seed data.')
    seed_generic_models()

print()
print('=== Seed complete ===')
if has_ecommerce_models():
    print(f'Categories:    {models_by_name["Category"].objects.count()}')
    print(f'Sellers:       {models_by_name["Seller"].objects.count()}')
    print(f'Products:      {models_by_name["Product"].objects.count()}')
    print(f'Images:        {models_by_name["ProductImage"].objects.count()}')
    print(f'Delivery opts: {models_by_name["DeliveryOption"].objects.count()}')
    print(f'Customers:     {models_by_name["Customer"].objects.count()}')
    print(f'Reviews:       {models_by_name["Review"].objects.count()}')
    print(f'Addresses:     {models_by_name["Address"].objects.count()}')
    print(f'Carts:         {models_by_name["Cart"].objects.count()}')
    print(f'Cart items:    {models_by_name["CartItem"].objects.count()}')
    print(f'Payments:      {models_by_name["Payment"].objects.count()}')
    print(f'Orders:        {models_by_name["Order"].objects.count()}')
    print(f'Order lines:   {models_by_name["OrderLine"].objects.count()}')
else:
    applicant_model = models_by_name.get('Applicant')
    loan_model = models_by_name.get('LoanApplication')
    print(f'Applicants:     {applicant_model.objects.count() if applicant_model else 0}')
    print(f'Loan applications: {loan_model.objects.count() if loan_model else 0}')
    if 'Document' in models_by_name:
        print(f'Documents:      {models_by_name["Document"].objects.count()}')
    if 'ApplicationNote' in models_by_name:
        print(f'Application notes: {models_by_name["ApplicationNote"].objects.count()}')
print(f'Users:         {User.objects.count()}')
