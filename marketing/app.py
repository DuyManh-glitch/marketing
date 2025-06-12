from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Thay bằng secret key thật

DATABASE = 'marketing.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM campaigns")  # Lấy tất cả chiến dịch
    campaigns = c.fetchall()
    c.execute("SELECT * FROM products LIMIT 4")  # Lấy 4 sản phẩm đầu tiên
    products = c.fetchall()
    conn.close()
    return render_template('index.html', campaigns=campaigns, products=products)

# Trang danh sách chiến dịch riêng
@app.route('/campaign')
def campaign():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM campaigns")  # sửa lại thành campaigns
    campaign = c.fetchall()
    conn.close()
    return render_template('campaign.html', campaign=campaign)

# Danh sách sản phẩm, có thể lọc theo danh mục
@app.route('/products')
def products():
    category_id = request.args.get('category')
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name FROM categories")
    categories = c.fetchall()

    if category_id:
        c.execute("""
            SELECT products.*, categories.name AS category_name
            FROM products
            JOIN categories ON products.category_id = categories.id
            WHERE categories.id = ?
        """, (category_id,))
    else:
        c.execute("""
            SELECT products.*, categories.name AS category_name
            FROM products
            JOIN categories ON products.category_id = categories.id
        """)
    products = c.fetchall()
    conn.close()

    return render_template('products.html', products=products, categories=categories,
                           current_category_id=int(category_id) if category_id else None)

# Chi tiết sản phẩm
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if not product:
        return "Không tìm thấy sản phẩm", 404
    return render_template('product_detail.html', product=product)

# Giỏ hàng
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash("Bạn cần đăng nhập để xem giỏ hàng.")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT cart_items.id, products.name, products.price, products.image_url, cart_items.quantity
        FROM cart_items
        JOIN products ON cart_items.product_id = products.id
        WHERE cart_items.user_id = ?
    """, (user_id,))
    items = c.fetchall()
    conn.close()
    total = sum(item['price'] * item['quantity'] for item in items)
    return render_template('cart.html', items=items, total=total)

# Thêm sản phẩm vào giỏ hàng
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash("Bạn cần đăng nhập để thêm sản phẩm vào giỏ.")
        return redirect(url_for('login'))

    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity <= 0:
            flash("Số lượng không hợp lệ.")
            return redirect(url_for('product_detail', product_id=product_id))
    except ValueError:
        flash("Số lượng không hợp lệ.")
        return redirect(url_for('product_detail', product_id=product_id))

    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    existing = c.fetchone()
    if existing:
        c.execute("UPDATE cart_items SET quantity = quantity + ? WHERE id = ?", (quantity, existing['id']))
    else:
        c.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))

    conn.commit()
    conn.close()

    flash("Đã thêm sản phẩm vào giỏ hàng.")
    return redirect(url_for('cart'))

# Xóa sản phẩm khỏi giỏ hàng
@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    if 'user_id' not in session:
        flash("Bạn cần đăng nhập để sửa giỏ hàng.")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM cart_items WHERE id = ? AND user_id = ?", (item_id, user_id))
    conn.commit()
    conn.close()

    flash("Đã xóa sản phẩm khỏi giỏ hàng.")
    return redirect(url_for('cart'))

# Thanh toán / Đặt hàng
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash("Bạn cần đăng nhập để thanh toán.")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT cart_items.id, products.id AS product_id, products.name, products.price, products.image_url, cart_items.quantity
        FROM cart_items
        JOIN products ON cart_items.product_id = products.id
        WHERE cart_items.user_id = ?
    """, (user_id,))
    items = c.fetchall()

    total = sum(item['price'] * item['quantity'] for item in items)

    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        payment_method = request.form.get('payment_method', 'Giao tiền khi nhận hàng')

        if not customer_name or not address or not phone:
            flash("Vui lòng nhập đầy đủ thông tin khách hàng.")
            return render_template('checkout.html', items=items, total=total,
                                   customer_name=customer_name, address=address,
                                   phone=phone, payment_method=payment_method)

        # Tạo đơn hàng
        c.execute("""
            INSERT INTO orders (user_id, total_price, customer_name, address, phone, payment_method)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, total, customer_name, address, phone, payment_method))
        order_id = c.lastrowid

        # Thêm sản phẩm vào order_items
        for item in items:
            c.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (order_id, item['product_id'], item['quantity'], item['price']))

        # Xóa giỏ hàng
        c.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))

        conn.commit()
        conn.close()

        flash("Thanh toán thành công! Cảm ơn bạn đã mua hàng.")
        return redirect(url_for('index'))

    conn.close()
    return render_template('checkout.html', items=items, total=total, payment_method='Giao tiền khi nhận hàng')

# Lịch sử đơn hàng
@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash("Bạn cần đăng nhập để xem đơn hàng.")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    orders = c.fetchall()

    orders_detail = []
    for order in orders:
        c.execute("""
            SELECT products.name, order_items.quantity, order_items.price,
            (order_items.quantity * order_items.price) AS total_price
            FROM order_items JOIN products ON order_items.product_id = products.id
            WHERE order_items.order_id = ?
        """, (order['id'],))
        items = c.fetchall()
        orders_detail.append({
            'order': order,
            'items': items
        })

    conn.close()
    return render_template('orders.html', orders=orders_detail)

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    # Kiểm tra đơn hàng tồn tại và thuộc về user, trạng thái chưa hủy
    c.execute("SELECT * FROM orders WHERE id = ? AND user_id = ? AND status NOT IN ('cancelled', 'completed')", (order_id, user_id))
    order = c.fetchone()
    if order is None:
        conn.close()
        flash("Đơn hàng không tồn tại hoặc không thể hủy.")
        return redirect(url_for('orders'))

    # Cập nhật trạng thái thành 'cancelled'
    c.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

    flash(f"Đơn hàng #{order_id} đã được hủy thành công.")
    return redirect(url_for('orders'))

# Đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Đăng nhập thành công!")
            return redirect(url_for('index'))
        else:
            flash("Tên đăng nhập hoặc mật khẩu không đúng.")
    return render_template('login.html')

# Đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                      (username, email, hashed_password))
            conn.commit()
            flash("Đăng ký thành công! Bạn có thể đăng nhập.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Tên đăng nhập hoặc email đã tồn tại.")
        finally:
            conn.close()
    return render_template('register.html')

# Phản hồi
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'user_id' not in session:
        flash("Bạn cần đăng nhập để gửi phản hồi.")
        return redirect(url_for('login'))
    if request.method == 'POST':
        message = request.form['message']
        user_id = session['user_id']
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO feedback (user_id, message) VALUES (?, ?)", (user_id, message))
        conn.commit()
        conn.close()
        flash("Cảm ơn bạn đã gửi phản hồi!")
        return redirect(url_for('index'))
    return render_template('feedback.html')

# Thống kê đơn hàng và doanh thu của user
@app.route('/stats')
def stats():
    if 'user_id' not in session:
        flash("Bạn cần đăng nhập để xem thống kê.")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (user_id,))
    total_orders = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE user_id=?", (user_id,))
    total_revenue = c.fetchone()[0] or 0.0

    conn.close()

    return render_template('stats.html', total_orders=total_orders, total_spent=total_revenue)

# Đăng xuất
@app.route('/logout')
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.")
    return redirect(url_for('index'))

# Trang liên hệ (Contact)
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash("Vui lòng điền đầy đủ thông tin.")
            return render_template('contact.html', name=name, email=email, message=message)

        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)", (name, email, message))
        conn.commit()
        conn.close()

        flash("Cảm ơn bạn đã liên hệ. Chúng tôi sẽ phản hồi sớm!")
        return redirect(url_for('index'))

    return render_template('contact.html')

# Khởi tạo database (chạy một lần)
def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        category_id INTEGER,
        image_url TEXT,
        description TEXT,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );
    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        image_url TEXT
    );
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_price REAL NOT NULL,
        customer_name TEXT,
        address TEXT,
        phone TEXT,
        payment_method TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
