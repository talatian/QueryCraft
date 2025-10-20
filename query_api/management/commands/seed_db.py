from django.core.management.base import BaseCommand
from faker import Faker
from random import randint, choice
from datetime import datetime, timedelta
import random
from query_api.models import Customer, Product, Order, OrderStatus


class Command(BaseCommand):
    help = 'Seed the database with fake data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--num',
            type=int,
            help='Number of records to create for each table',
            default=1000
        )

    def handle(self, *args, **options):
        num_records = options['num']
        
        fake = Faker()
        
        if Customer.objects.exists() or Product.objects.exists() or Order.objects.exists():
            self.stdout.write('Database is not empty. Seeding canceled...')
            return

        self.stdout.write('Creating customers...')
        customers = []
        for i in range(num_records):
            customer = Customer(
                name=fake.name(),
                email=fake.email(),
                registration_date=fake.date_between(start_date='-2y', end_date='today')
            )
            customers.append(customer)
        
        # Bulk create customers
        Customer.objects.bulk_create(customers, batch_size=1000)
        self.stdout.write(f'Created {len(customers)} customers')
        
        self.stdout.write('Creating products...')
        products = []
        categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Garden', 'Toys', 'Sports', 'Beauty']
        for i in range(num_records // 4):  # Fewer products than customers
            product = Product(
                name=fake.catch_phrase(),
                category=choice(categories),
                price=round(random.uniform(5.0, 500.0), 2)
            )
            products.append(product)
        
        # Bulk create products
        Product.objects.bulk_create(products, batch_size=1000)
        self.stdout.write(f'Created {len(products)} products')
        
        # Get all customer and product IDs for foreign key references
        customer_ids = list(Customer.objects.values_list('id', flat=True))
        product_ids = list(Product.objects.values_list('id', flat=True))
        
        self.stdout.write('Creating orders...')
        orders = []
        statuses = [status[0] for status in OrderStatus.choices]
        
        for i in range(num_records):
            order = Order(
                customer_id=choice(customer_ids),
                product_id=choice(product_ids),
                order_date=fake.date_between(start_date='-1y', end_date='today'),
                quantity=randint(1, 10),
                status=choice(statuses)
            )
            orders.append(order)
        
        # Bulk create orders
        Order.objects.bulk_create(orders, batch_size=1000)
        self.stdout.write(f'Created {len(orders)} orders')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded database with {num_records} records of each type')
        )