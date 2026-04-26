import sys
import os
import re
import uuid
from datetime import datetime
from flask import Flask, render_template, url_for, request, redirect, session, flash
from functools import wraps

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model.rainModel import db, Product, User, Order, OrderItem, Invoice, InvoiceItem, Role

app = Flask(__name__, 
            template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'view', 'templates')), 
            static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'view', 'static')))

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '../model/rain.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'tu_clave_secreta_aqui'

db.init_app(app)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 1:
            flash("Acceso denegado. Se requieren permisos de administrador. 🌧️")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_cart_total():
    total = 0
    if 'carrito' in session:
        for item in session['carrito']:
            total += float(item['precio']) * item['cantidad']
    return dict(total_carrito=total)

@app.route('/')
def index():
    productos_db = Product.query.all()
    return render_template('Proyecto.html', productos=productos_db)

@app.route('/catalogo')
@app.route('/catalogo/<categoria>')
def catalogo(categoria=None):
    if categoria:
        productos_db = Product.query.filter_by(category=categoria).all()
    else:
        productos_db = Product.query.all()
    
    return render_template('catalogo.html', productos=productos_db, categoria_actual=categoria)

@app.route('/producto/<int:id>')
def detalle_producto(id):
    producto = Product.query.get_or_404(id) 
    return render_template('detalle.html', producto=producto)

def is_logged_in():
    return 'user_id' in session

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if is_logged_in():
        return redirect(url_for('index'))

    if request.method == 'POST':
        nombre = (request.form.get('full_name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = (request.form.get('password') or '').strip()
        
        if not all([nombre, email, password]):
            flash("Todos los campos son obligatorios para el registro. 🌧️")
            return redirect(url_for('registro'))
            
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", nombre):
            flash("El nombre solo debe contener letras.")
            return redirect(url_for('registro'))

        email_regex = r'^[a-z0-9._%+-]+@gmail\.com$'
        if not re.match(email_regex, email):
            flash("Usa un formato válido de @gmail.com (letras minúsculas).")
            return redirect(url_for('registro'))

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.")
            return redirect(url_for('registro'))

        try:
            user_exists = User.query.filter_by(email=email).first()
            if user_exists:
                flash("Este correo ya está registrado en nuestra base de datos.")
                return redirect(url_for('registro'))

            nuevo_usuario = User(
                full_name=nombre, 
                email=email, 
                password_hash=password,
                role_id=2, 
                status='Active'
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            flash("¡Cuenta creada con éxito! Ya puedes iniciar sesión. 🔥")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f"Error Registro: {e}")
            flash("Error técnico al registrar. Intenta más tarde.")
            return redirect(url_for('registro'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = (request.form.get('password') or '').strip()
        
        if not email or not password:
            flash("Por favor, ingresa tus credenciales.")
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()
        
        if user and user.password_hash == password:
            if user.status != 'Active':
                flash("Tu cuenta está suspendida. Contacta a soporte.")
                return redirect(url_for('login'))

            session.clear()
            session['user_id'] = user.id
            session['user_name'] = user.full_name
            session['user_role'] = user.role_id 
            session.permanent = True
            
            flash(f"¡Bienvenido de nuevo, {user.full_name}! 🌧️")
            return redirect(url_for('index'))
        
        flash("Las credenciales no coinciden con nuestros registros.")
        return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión. ¡Vuelve pronto a Rain! 🌧️")
    return redirect(url_for('index'))

@app.route('/carrito')
def ver_carrito():
    items = session.get('carrito', [])
    total = sum(float(item['precio']) * item['cantidad'] for item in items)
    faltante_envio = max(0, 40 - total)
    porcentaje_progreso = min(100, (total / 40) * 100)
    
    return render_template('carrito.html', items=items, total=total, faltante=faltante_envio, progreso=porcentaje_progreso)

@app.route('/add_to_cart/<int:id>', methods=['POST'])
def add_to_cart(id):
    producto = Product.query.get_or_404(id)
    
    try:
        cantidad_pedida = int(request.form.get('cantidad', 1))
    except (ValueError, TypeError):
        flash("La cantidad ingresada no es válida. 🌧️")
        return redirect(request.referrer or url_for('index'))

    if cantidad_pedida <= 0:
        flash("Debes añadir al menos 1 unidad. 🔥")
        return redirect(request.referrer or url_for('index'))

    if producto.status == 'Agotado' or producto.stock_quantity <= 0:
        flash(f"Lo sentimos, {producto.name} está agotado actualmente. 🌧️")
        return redirect(request.referrer or url_for('index'))

    if 'carrito' not in session:
        session['carrito'] = []
    
    carrito = session['carrito']
    encontrado = False
    
    for item in carrito:
        if item['id'] == id:
            total_potencial = item['cantidad'] + cantidad_pedida
            
            if total_potencial > producto.stock_quantity:
                flash(f"No puedes añadir más. Ya tienes {item['cantidad']} en el carrito y el stock total es de {producto.stock_quantity}. 🌧️")
                return redirect(request.referrer or url_for('index'))
            
            item['cantidad'] = total_potencial
            encontrado = True
            break
            
    if not encontrado:
        if cantidad_pedida > producto.stock_quantity:
            flash(f"Solo quedan {producto.stock_quantity} unidades disponibles.")
            return redirect(request.referrer or url_for('index'))
            
        carrito.append({
            'id': producto.id, 
            'nombre': producto.name,
            'precio': float(producto.price), 
            'imagen': producto.image_url,
            'cantidad': cantidad_pedida,
            'max_stock': producto.stock_quantity
        })
    
    session['carrito'] = carrito
    session.modified = True
    flash(f"¡{producto.name} se añadió correctamente! 🌧️🔥")
    return redirect(request.referrer or url_for('index'))

@app.route('/update_cart/<int:id>/<string:action>')
def update_cart(id, action):
    if 'carrito' in session:
        producto_db = Product.query.get_or_404(id)
        for item in session['carrito']:
            if item['id'] == id:
                if action == 'increment':
                    if item['cantidad'] + 1 > producto_db.stock_quantity:
                        flash(f"No hay más stock disponible de {producto_db.name} 🌧️")
                    else:
                        item['cantidad'] += 1
                elif action == 'decrement' and item['cantidad'] > 1:
                    item['cantidad'] -= 1
                break
        session.modified = True
    return redirect(url_for('ver_carrito'))

@app.route('/remove_from_cart/<int:id>')
def remove_from_cart(id):
    if 'carrito' in session:
        session['carrito'] = [item for item in session['carrito'] if item['id'] != id]
        session.modified = True
    return redirect(url_for('ver_carrito'))

@app.route('/empty_cart')
def empty_cart():
    session.pop('carrito', None)
    return redirect(url_for('ver_carrito'))

@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        flash("Debes iniciar sesión para finalizar tu compra. 🌧️")
        return redirect(url_for('login'))

    if 'carrito' not in session or not session['carrito']:
        flash("Tu carrito está vacío.")
        return redirect(url_for('index'))
    
    carrito_final = []
    total_compra = 0
    
    for item in session['carrito']:
        prod = Product.query.get(item['id'])
        if not prod or prod.stock_quantity < item['cantidad']:
            flash(f"Lo sentimos, el producto {item['nombre']} ya no tiene stock suficiente. Ajusta tu carrito.")
            return redirect(url_for('ver_carrito')) # O como se llame tu ruta del carrito
        
        total_compra += float(item['precio']) * int(item['cantidad'])
        carrito_final.append(item)

    id_referencia = str(uuid.uuid4())[:8].upper()

    try:
        nueva_orden = Order(
            user_id=session['user_id'], 
            total_price=total_compra, 
            status='Pending'
        )
        db.session.add(nueva_orden)
        db.session.flush()

        nueva_factura = Invoice(
            order_id=nueva_orden.id, 
            invoice_number=f"INV-{id_referencia}", 
            total_net=total_compra,
            status='Issued'
        )
        db.session.add(nueva_factura)
        db.session.flush()

        for p in carrito_final:
            db.session.add(OrderItem(
                order_id=nueva_orden.id, 
                product_id=p['id'], 
                quantity=p['cantidad'], 
                subtotal=float(p['precio']) * int(p['cantidad'])
            ))
            db.session.add(InvoiceItem(
                invoice_id=nueva_factura.id, 
                product_id=p['id'], 
                quantity=p['cantidad'], 
                unit_price_at_sale=float(p['precio'])
            ))

        db.session.commit()
        
        datos_para_plantilla = {
            'nro_orden': id_referencia, 
            'fecha_emision': datetime.now().strftime("%d/%m/%Y %H:%M"), 
            'lista_productos': carrito_final, 
            'monto_total': total_compra
        }
        
        session.pop('carrito', None)
        session.modified = True 
        return render_template('factura.html', data=datos_para_plantilla)

    except Exception as e:
        db.session.rollback()
        print(f"Error Crítico Checkout: {e}")
        flash("Ocurrió un error al procesar tu pedido. Intenta de nuevo.")
        return redirect(url_for('index'))

@app.route('/confirmar_pago/<orden_id>', methods=['POST'])
def confirmar_pago(orden_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    factura = Invoice.query.filter_by(invoice_number=f"INV-{orden_id}").first_or_404()
    orden = Order.query.get(factura.order_id)

    # Validación de seguridad: ¿Esta factura le pertenece al que está logueado?
    if orden.user_id != session['user_id']:
        flash("No tienes permiso para procesar esta factura.")
        return redirect(url_for('index'))

    if orden.status == 'Paid' or factura.status == 'Paid':
        flash("Esta orden ya ha sido procesada anteriormente.")
        return redirect(url_for('index'))

    items = OrderItem.query.filter_by(order_id=orden.id).all()
    
    try:
        for item in items:
            producto_db = Product.query.get(item.product_id)
            if not producto_db or producto_db.stock_quantity < item.quantity:
                db.session.rollback()
                flash(f"¡Error de último minuto! El producto {producto_db.name if producto_db else 'desconocido'} se agotó.")
                return redirect(url_for('index'))
            
            producto_db.stock_quantity -= item.quantity

        orden.status = 'Paid'
        factura.status = 'Paid'
        db.session.commit()
        
        flash("¡PAGO CONFIRMADO! Gracias por confiar en Rain. Tu pedido está en camino. 🌧️🔥")
        return redirect(url_for('index'))
    
    except Exception as e:
        db.session.rollback()
        print(f"Error Confirmar Pago: {e}")
        flash("Error al procesar el pago. Por favor contacta a soporte.")
        return redirect(url_for('index'))

@app.route('/admin/productos')
@admin_required
def admin_productos():
    productos = Product.query.all()
    return render_template('admin_productos.html', productos=productos)

@app.route('/admin/panel/<tabla>')
@admin_required
def admin_panel(tabla):
    datos = []
    columnas = []
    
    if tabla == 'products':
        datos = Product.query.all()
        columnas = ['ID', 'Name', 'Price', 'Stock', 'Size', 'Category', 'Status']
    elif tabla == 'users':
        datos = User.query.all()
        columnas = ['ID', 'Full Name', 'Email', 'Role ID', 'Status']
    elif tabla == 'orders':
        datos = Order.query.order_by(Order.order_date.desc()).all()
        columnas = ['ID', 'User ID', 'Date', 'Total Price', 'Status']
    elif tabla == 'order_items':
        datos = OrderItem.query.all()
        columnas = ['ID', 'Order ID', 'Product ID', 'Quantity', 'Subtotal']
    elif tabla == 'invoices':
        datos = Invoice.query.all()
        columnas = ['ID', 'Invoice Number', 'Order ID', 'Issue Date', 'Total Net', 'Status']
    elif tabla == 'invoice_items':
        datos = InvoiceItem.query.all()
        columnas = ['ID', 'Invoice ID', 'Product ID', 'Quantity', 'Unit Price']
    elif tabla == 'roles':
        datos = Role.query.all()
        columnas = ['ID', 'Name', 'Status']

    return render_template('admin_universal.html', tabla_nombre=tabla, datos=datos, columnas=columnas)

@app.route('/admin/eliminar/<tabla>/<int:id>')
@admin_required
def eliminar_registro(tabla, id):
    modelos = {
        'products': Product,
        'users': User,
        'orders': Order,
        'invoices': Invoice,
        'roles': Role
    }
    
    modelo = modelos.get(tabla)
    if not modelo:
        flash("Tabla no encontrada.")
        return redirect(url_for('index'))

    registro = modelo.query.get_or_404(id)
    
    try:
        db.session.delete(registro)
        db.session.commit()
        flash(f"Registro #{id} eliminado de {tabla} con éxito. 🌧️")
    except Exception as e:
        db.session.rollback()
        flash("No se puede eliminar: el registro está vinculado a otra tabla (ej. un producto en una factura).")
        print(f"Error al eliminar: {e}")

    return redirect(url_for('admin_panel', tabla=tabla))

@app.route('/admin/detalle/<tabla>/<int:id>')
@admin_required
def ver_detalle_admin(tabla, id):
    flash(f"Consultando detalles del ID {id} en {tabla}...")
    return redirect(url_for('admin_panel', tabla=tabla))

@app.route('/admin/crear_producto', methods=['GET', 'POST'])
@admin_required
def crear_producto():
    if request.method == 'POST':
        try:
            nuevo_prod = Product(
                name=request.form.get('name'),
                description=request.form.get('description'),
                price=float(request.form.get('price')),
                stock_quantity=int(request.form.get('stock')),
                size=request.form.get('size'),
                category=request.form.get('category'),
                image_url=request.form.get('image_url'),
                status='Available'
            )
            
            db.session.add(nuevo_prod)
            db.session.commit()
            flash("¡Producto añadido exitosamente a Rain! 🌧️🔥")
            return redirect(url_for('admin_panel', tabla='products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear producto: {e}")
            return redirect(url_for('crear_producto'))

    return render_template('form_producto.html')

@app.route('/admin/editar_producto/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_producto(id):
    producto = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            producto.name = request.form.get('name')
            producto.description = request.form.get('description')
            producto.price = float(request.form.get('price'))
            producto.stock_quantity = int(request.form.get('stock'))
            producto.size = request.form.get('size')
            producto.category = request.form.get('category')
            producto.image_url = request.form.get('image_url')
            producto.status = request.form.get('status')
            
            db.session.commit()
            flash(f"Producto '{producto.name}' actualizado correctamente. 🌧️")
            return redirect(url_for('admin_panel', tabla='products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar: {e}")
            return redirect(url_for('editar_producto', id=id))

    return render_template('editar_producto.html', producto=producto)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)