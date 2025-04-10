from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database helper
def get_db_connection():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/products')
def products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/order/<int:product_id>', methods=['GET', 'POST'])
def order(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        quantity = int(request.form['quantity'])

        conn.execute('INSERT INTO orders (name, phone, product, quantity, address) VALUES (?, ?, ?, ?, ?)',
                     (name, phone, product['name'], quantity, address))
        conn.commit()
        conn.close()

        return redirect(url_for('order_success'))

    conn.close()
    return render_template('order.html', product=product)

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials!', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/products', methods=['GET', 'POST'])
def admin_products():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image = request.files.get('image')
        filename = ''

        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn.execute('INSERT INTO products (name, description, price, image) VALUES (?, ?, ?, ?)', 
                     (name, description, price, filename))
        conn.commit()

    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('admin_products.html', products=products)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image = request.files.get('image')
        filename = product['image']  # Default to old image

        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn.execute('UPDATE products SET name = ?, description = ?, price = ?, image = ? WHERE id = ?',
                     (name, description, price, filename, product_id))
        conn.commit()
        conn.close()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))

    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/admin/products/delete/<int:id>')
def delete_product(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
def view_orders():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders').fetchall()
    conn.close()
    return render_template('view_orders.html', orders=orders)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('admin_login'))

@app.route('/order_success')
def order_success():
    return render_template('order_success.html')

# Call this once to initialize your database
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            image TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            address TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Uncomment this line once to create tables
# init_db()

if __name__ == '__main__':
    app.run(debug=True)
