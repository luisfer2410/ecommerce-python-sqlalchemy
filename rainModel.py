from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 1. ROLES
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False) # Admin, Operator, Customer
    status = db.Column(db.String(20), default='Active')

# 2. USERS
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    status = db.Column(db.String(20), default='Active')

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    size = db.Column(db.String(10), nullable=False) 
    category = db.Column(db.String(50), nullable=False) 
    image_url = db.Column(db.String(500)) # <-- Nuevo campo para el link de la foto
    status = db.Column(db.String(20), default='Available')

# 4. ORDERS (Cabecera del pedido)
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Pending')

# 5. ORDER_ITEMS (Detalle del pedido - Tabla Intermedia N:M)
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

# 6. INVOICES (Cabecera de la factura)
class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), unique=True)
    invoice_number = db.Column(db.String(20), unique=True)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_net = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Issued')

# 7. INVOICE_ITEMS (Detalle fiscal - La 7ma tabla para 3FN)
class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price_at_sale = db.Column(db.Float, nullable=False) # Precio congelado al vender