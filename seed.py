import sys
import os

# Permitir que reconozca la carpeta model
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from controller.main import app
from model.rainModel import db, Role, User, Product, Order, OrderItem, Invoice, InvoiceItem

with app.app_context():
    print("Insertando datos de prueba...")

    """# 1. ROLES
    admin_role = Role(name="Admin", status="Active")
    customer_role = Role(name="Customer", status="Active")
    db.session.add_all([admin_role, customer_role])
    db.session.commit() # Guardamos para obtener los IDs

    # 2. USERS
    new_user = User(
        full_name="Luisfer Prueba", 
        email="test@email.com", 
        password_hash="12345", 
        role_id=admin_role.id
    )
    db.session.add(new_user)
    db.session.commit()

    # 3. PRODUCTS
    p1 = Product(
        name="Oversized Black Tee", 
        price=25.0, 
        stock_quantity=50, 
        size="XL", 
        category="T-Shirts",
        image_url="https://basicoclothes.com/wp-content/uploads/2025/09/ChatGPT-Image-12-sept-2025-11_06_49.png" # Link real
    )
    db.session.add(p1)
    db.session.commit()

    # 4. ORDERS
    order1 = Order(user_id=new_user.id, total_price=25.0, status="Paid")
    db.session.add(order1)
    db.session.commit()

    # 5. ORDER_ITEMS (Relación Pedido-Producto)
    item1 = OrderItem(order_id=order1.id, product_id=p1.id, quantity=1, subtotal=25.0)
    db.session.add(item1)

    # 6. INVOICES
    inv1 = Invoice(
        order_id=order1.id, 
        invoice_number="INV-001", 
        total_net=25.0, 
        status="Issued"
    )
    db.session.add(inv1)
    db.session.commit()

    # 7. INVOICE_ITEMS (Detalle fiscal)
    inv_item1 = InvoiceItem(
        invoice_id=inv1.id, 
        product_id=p1.id, 
        quantity=1, 
        unit_price_at_sale=25.0
    )
    db.session.add(inv_item1)"""

    p2 = Product(
    name="Trackpant Negro con Costuras Contrastantes", 
    price=12.99, 
    stock_quantity=30, 
    size="M", 
    category="Pants",
    status="Oferta",
    image_url="https://basicoclothes.com/wp-content/uploads/2025/08/Trackpant-Negro.png" # Ajusta al link real si lo tienes
    )

    # p3: El Hoodie gris
    p3 = Product(
        name="Hoodie Gris Plomo 'Basico Star'", 
        price=37.99, 
        stock_quantity=20, 
        size="L", 
        category="Hoodies",
        status="Oferta",
        image_url="https://basicoclothes.com/wp-content/uploads/2025/08/Hoodie-Gris.png"
    )

    # p4: El Jersey de Soccer
    p4 = Product(
        name="Basico Club Jersey Soccer", 
        price=37.99, 
        stock_quantity=15, 
        size="XL", 
        category="T-Shirts",
        status="Oferta",
        image_url="https://basicoclothes.com/wp-content/uploads/2025/08/Jersey-Soccer.png"
    )

    # Agregamos todos a la sesión
    db.session.add_all([p2, p3, p4])
    db.session.commit()

    # GUARDAR TODO
    db.session.commit()
    print("¡Todo correcto! Datos insertados en las 7 tablas sin errores.")