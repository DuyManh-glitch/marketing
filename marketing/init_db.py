import sqlite3

conn = sqlite3.connect('marketing.db')
c = conn.cursor()

# ==============================
# 1. XÓA CÁC BẢNG CŨ (nếu cần)
# ==============================
c.execute("DROP TABLE IF EXISTS order_items")
c.execute("DROP TABLE IF EXISTS orders")
c.execute("DROP TABLE IF EXISTS cart_items")
c.execute("DROP TABLE IF EXISTS feedback")
c.execute("DROP TABLE IF EXISTS products")
c.execute("DROP TABLE IF EXISTS categories")
c.execute("DROP TABLE IF EXISTS campaigns")
c.execute("DROP TABLE IF EXISTS users")

# ==============================
# 2. BẢNG USERS
# ==============================
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password TEXT
)
""")

# ==============================
# 3. BẢNG CATEGORIES
# ==============================
c.execute("""
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

# Thêm 3 loại danh mục
categories = [
    ("Điện tử, điện máy",),
    ("Điện gia dụng",),
    ("Đồ gia dụng",)
]
c.executemany("INSERT INTO categories (name) VALUES (?)", categories)

# Lấy ID của từng loại
c.execute("SELECT id FROM categories WHERE name = 'Điện tử, điện máy'")
cat_dien_tu = c.fetchone()[0]
c.execute("SELECT id FROM categories WHERE name = 'Điện gia dụng'")
cat_dien_gia_dung = c.fetchone()[0]
c.execute("SELECT id FROM categories WHERE name = 'Đồ gia dụng'")
cat_do_gia_dung = c.fetchone()[0]

# ==============================
# 4. BẢNG PRODUCTS
# ==============================
c.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    price INTEGER,
    image_url TEXT,
    category_id INTEGER,
    FOREIGN KEY(category_id) REFERENCES categories(id)
)
""")

# Dữ liệu sản phẩm mẫu
products = [
    # Điện tử, điện máy
    ("Máy lạnh Inverter", "Làm lạnh nhanh, tiết kiệm điện", 9000000, "static/images/may_lanh.jpg", cat_dien_tu),
    ("Tủ lạnh LG", "Dung tích lớn, tiết kiệm điện", 8500000, "static/images/tu_lanh.jpg", cat_dien_tu),
    ("Máy giặt Samsung", "Giặt sạch, vận hành êm", 7000000, "static/images/may_giat.jpg", cat_dien_tu),
    ("Tivi Sony 50 inch", "Hình ảnh sắc nét", 10000000, "static/images/tivi.jpg", cat_dien_tu),

    # Điện gia dụng
    ("Quạt điều hòa", "Mát lạnh tự nhiên", 1800000, "static/images/quat_dieu_hoa.jpg", cat_dien_gia_dung),
    ("Máy xay sinh tố", "Xay nhuyễn mọi loại thực phẩm", 500000, "static/images/may_xay.jpg", cat_dien_gia_dung),
    ("Bếp điện từ", "Nấu ăn nhanh chóng", 1300000, "static/images/bep_dien.jpg", cat_dien_gia_dung),
    ("Robot hút bụi", "Dọn dẹp tự động thông minh", 4500000, "static/images/robot.jpg", cat_dien_gia_dung),

    # Đồ gia dụng
    ("Bộ nồi inox", "Chống dính, nấu ăn ngon", 1200000, "static/images/bo_noi.jpg", cat_do_gia_dung),
    ("Hộp đựng thức ăn", "Bảo quản thực phẩm tiện lợi", 300000, "static/images/hop_thuc_an.jpg", cat_do_gia_dung),
    ("Hộp nhựa đa năng", "Đựng đồ dùng trong nhà", 200000, "static/images/hop_da_nang.jpg", cat_do_gia_dung),
]

c.executemany("""
    INSERT INTO products (name, description, price, image_url, category_id)
    VALUES (?, ?, ?, ?, ?)
""", products)

# ==============================
# 5. BẢNG CAMPAIGN
# ==============================
c.execute("""
CREATE TABLE IF NOT EXISTS campaign (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    budget INTEGER,
    image_url TEXT
)
""")

# ==============================
# 6. BẢNG FEEDBACK
# ==============================
c.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# ==============================
# 7. BẢNG CART_ITEMS
# ==============================
c.execute("""
CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
)
""")

c.execute("DROP TABLE IF EXISTS orders")
c.execute("""
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    total_price INTEGER,
    payment_method TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    customer_name TEXT,
    phone TEXT,
    address TEXT,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

c.execute("DROP TABLE IF EXISTS order_items")
c.execute("""
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price INTEGER,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
)
""")

# ==============================
# KẾT THÚC
# ==============================
conn.commit()
conn.close()

print("✅ Đã tạo lại toàn bộ database 'marketing.db' với phân loại danh mục rõ ràng.")
