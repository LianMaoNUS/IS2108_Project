import os
import sys
import django
import csv
from decimal import Decimal
import random
import string

# Add the project root to Python path
sys.path.append('C:\\Users\\yomao\\Desktop\\HOOTHOOT\\IS2108\\Pair Project\\IS2108_PairProject\\AuroraMart')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AuroraMart.settings')
django.setup()

# Import models after Django setup
from customer_website.models import Customer
from admin_panel.models import Product, Category

def generate_random_username():
    """Generate a random username"""
    # Random username patterns
    patterns = [
        lambda: f"user_{random.randint(1000, 9999)}",
        lambda: f"customer_{random.randint(100, 999)}",
        lambda: f"{''.join(random.choices(string.ascii_lowercase, k=6))}{random.randint(10, 99)}",
        lambda: f"{''.join(random.choices(string.ascii_lowercase, k=4))}_{random.randint(1000, 9999)}",
        lambda: f"guest{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}",
    ]
    
    # Pick a random pattern and generate username
    pattern = random.choice(patterns)
    username = pattern()
    
    # Ensure uniqueness by checking if it already exists
    while Customer.objects.filter(username=username).exists():
        username = pattern()
        if len(username) > 20:  # Ensure username length does not exceed 20 characters
            username = username[:20]
    
    return username

def populate_customers():
    Customer.objects.all().delete()
    """Populate Customer model from customers.csv"""
    csv_path = os.path.join(os.path.dirname(__file__), 'b2c_customers_100.csv')
    
    if not os.path.exists(csv_path):
        print(f"Customer CSV file not found: {csv_path}")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        customers_created = 0
        
        for row in reader:
            try:
                customer = Customer.objects.create(
                    username=generate_random_username(),
                    password='Customer12345@',  # Default password for all customers
                    age=int(row.get('age', 0)) if row.get('age') else None,
                    gender=row.get('gender', ''),
                    employment_status=row.get('employment_status', ''),
                    occupation=row.get('occupation', ''),
                    education=row.get('education', ''),
                    household_size=int(row.get('household_size', 1)) if row.get('household_size') else 1,
                    number_of_children=int(row.get('number_of_children', 0)) if row.get('number_of_children') else 0,
                    monthly_income_sgd=Decimal(row.get('monthly_income_sgd', '0')) if row.get('monthly_income_sgd') else Decimal('0'),
                    preferred_category=row.get('preferred_category', ''),
                )
                if customer:
                    customers_created += 1
                    print(f"Created customer: {customer.username}")
                else:
                    print(f"Customer already exists: {customer.username}")
                    
            except Exception as e:
                print(f"Error creating customer from row {row}: {e}")
        
        print(f"\nCustomers populated: {customers_created} new customers created")

def populate_products():
    Product.objects.all().delete()
    Category.objects.all().delete()
    """Populate Product model from products.csv"""
    csv_path = os.path.join(os.path.dirname(__file__), 'b2c_products_500.csv')
    
    if not os.path.exists(csv_path):
        print(f"Product CSV file not found: {csv_path}")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        products_created = 0
        
        for row in reader:
            print(row.get('\ufeffsku'))
            try:
                category = None
                subcategory = None
                
                # Handle main category
                if row.get('Product Category'):
                    category_name = row.get('Product Category').strip()
                    # Check if main category exists, if not create it
                    category, created = Category.objects.get_or_create(
                        name=category_name,
                        defaults={'parent_category': None}  # Main category has no parent
                    )
                    if created:
                        print(f"Created main category: {category.name}")
                    else:
                        print(f"Using existing main category: {category.name}")
                
                # Handle subcategory
                if row.get('Product Subcategory') and category:
                    subcategory_name = row.get('Product Subcategory').strip()
                    # Check if subcategory exists, if not create it
                    subcategory, created = Category.objects.get_or_create(
                        name=subcategory_name,
                        defaults={'parent_category': category}  # Subcategory has parent
                    )
                    if created:
                        print(f"Created subcategory: {subcategory.name} under {category.name}")
                    else:
                        print(f"Using existing subcategory: {subcategory.name}")

                # Use subcategory if available, otherwise use main category
                product_category = category

                product = Product.objects.create(
                    sku=row.get('\ufeffsku'),
                    product_name=row.get('Product name', ''),
                    category=product_category,  # Single category field now
                    subcategory=subcategory,
                    unit_price=Decimal(row.get('Unit price', '0')) if row.get('Unit price') else Decimal('0'),
                    quantity_on_hand=int(row.get('Quantity on hand', 0)) if row.get('Quantity on hand') else 0,
                    reorder_quantity=int(row.get('Reorder Quantity', 10)) if row.get('Reorder Quantity') else 10,
                    description=row.get('Product description', ''),
                    product_rating=float(row.get('Product rating', 0.0)) if row.get('Product rating') else 0.0,
                )
                if product:
                    products_created += 1
                    print(f"Created product: {product.product_name} in category: {product_category}")
                else:
                    print(f"Product already exists: {product.product_name}")
                    
            except Exception as e:
                print(f"Error creating product from row {row}: {e}")
        
        print(f"\nProducts populated: {products_created} new products created")

def main():
    """Main function to populate all models"""
    print("Starting data population...")
    print("=" * 50)

    
    print("\n2. Populating Products...")
    populate_products()
    
    print("\n3. Populating Customers...")
    #populate_customers()
    
    print("\n" + "=" * 50)
    print("Data population completed!")

if __name__ == "__main__":
    main()