import sqlite3
import pymysql
import os
import sys
import random
from backend.config import Config


def get_db_connection():
    """Connect to MySQL or fallback to SQLite."""
    use_sqlite = False

    if Config.DB_ENGINE.lower() == "sqlite":
        use_sqlite = True
    else:
        try:
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            return conn, "mysql"
        except Exception:
            use_sqlite = True

    if use_sqlite:
        db_path = os.path.abspath(Config.SQLITE_DB_PATH)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"


def init_db():
    """Create tables, seed staff accounts, categories, and menu items."""
    conn, engine_type = get_db_connection()
    cursor = conn.cursor()

    if engine_type == "sqlite":
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA table_info(orders);")
        cols = [r[1] for r in cursor.fetchall()]
        if cols and "rating" not in cols:
            for t in ["order_items", "payments", "orders", "menu_items", "categories", "users"]:
                cursor.execute(f"DROP TABLE IF EXISTS {t};")
            conn.commit()

        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'Customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS menu_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            image_url TEXT,
            is_available BOOLEAN DEFAULT 1,
            FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            delivery_user_id INTEGER,
            total_amount REAL NOT NULL,
            delivery_address TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            payment_method TEXT DEFAULT 'COD',
            payment_status TEXT DEFAULT 'Pending',
            transaction_id TEXT,
            otp_code TEXT,
            rating INTEGER,
            review_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (delivery_user_id) REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES menu_items(item_id)
        );
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            upi_id TEXT,
            transaction_id TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
        );
        """)
    else:
        # MySQL schema
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(15) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('Customer', 'Kitchen', 'Admin', 'Delivery') DEFAULT 'Customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            category_id INT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            image_url TEXT,
            is_available BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT DEFAULT 1,
            delivery_user_id INT,
            total_amount DECIMAL(10,2) NOT NULL,
            delivery_address TEXT NOT NULL,
            status ENUM('Pending', 'Preparing', 'Ready', 'Out for Delivery', 'Delivered', 'Cancelled') DEFAULT 'Pending',
            payment_method ENUM('UPI', 'COD', 'Card') DEFAULT 'COD',
            payment_status ENUM('Pending', 'Completed', 'Failed') DEFAULT 'Pending',
            transaction_id VARCHAR(100),
            otp_code VARCHAR(10),
            rating INT,
            review_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (delivery_user_id) REFERENCES users(user_id)
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            item_id INT NOT NULL,
            quantity INT NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES menu_items(item_id)
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            upi_id VARCHAR(100),
            transaction_id VARCHAR(100) UNIQUE NOT NULL,
            status VARCHAR(50) DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
        );
        """)

        # Add delivery_user_id column if missing
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN delivery_user_id INT AFTER user_id;")
        except Exception:
            pass

        # Add otp_code column if missing
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN otp_code VARCHAR(10) AFTER transaction_id;")
        except Exception:
            pass

        # Add rating column if missing
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN rating INT AFTER otp_code;")
        except Exception:
            pass

        # Add review_text column if missing
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN review_text TEXT AFTER rating;")
        except Exception:
            pass

        # Add 'Ready' to status enum if missing
        try:
            cursor.execute("""
                ALTER TABLE orders MODIFY COLUMN status
                ENUM('Pending', 'Preparing', 'Ready', 'Out for Delivery', 'Delivered', 'Cancelled')
                DEFAULT 'Pending';
            """)
        except Exception:
            pass

        # Add 'Delivery' to role enum if missing
        try:
            cursor.execute("""
                ALTER TABLE users MODIFY COLUMN role
                ENUM('Customer', 'Kitchen', 'Admin', 'Delivery')
                DEFAULT 'Customer';
            """)
        except Exception:
            pass

    conn.commit()

    # ── Seed Staff Accounts ──
    ph = "%s" if engine_type == "mysql" else "?"
    staff_seed = [
        ("Customer Demo", "customer@foodexpress.com", "9876543210", "pass123", "Customer"),
        ("Admin Manager", "admin@foodexpress.com", "9123456789", "admin123", "Admin"),
        ("Kitchen Staff", "kitchen@foodexpress.com", "9988776655", "kitchen123", "Kitchen"),
        ("Delivery Boy", "delivery@foodexpress.com", "9900112233", "delivery123", "Delivery"),
    ]
    for u in staff_seed:
        cursor.execute(f"SELECT user_id FROM users WHERE email = {ph};", (u[1],))
        if not cursor.fetchone():
            cursor.execute(
                f"INSERT INTO users (name, email, phone, password, role) VALUES ({ph}, {ph}, {ph}, {ph}, {ph});",
                u
            )
    conn.commit()

    # ── Seed Categories & Menu Items ──
    cursor.execute("SELECT COUNT(*) as cnt FROM categories;")
    row = cursor.fetchone()
    cat_cnt = row['cnt'] if isinstance(row, dict) else row[0]
    if cat_cnt == 0:
        categories = ["Starters", "Main Course", "Desserts", "Beverages"]
        for cat in categories:
            cursor.execute(f"INSERT INTO categories (name) VALUES ({ph});", (cat,))
        conn.commit()

        menu = [
            (1, "Paneer Tikka", "Grilled cottage cheese with aromatic Indian spices", 240.00, "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=600&q=80", True),
            (1, "Crispy Spring Rolls", "Golden fried veggie rolls with spicy dip", 180.00, "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80", True),
            (2, "Butter Chicken", "Rich creamy tomato gravy with tender chicken", 340.00, "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=600&q=80", True),
            (2, "Dal Makhani", "Slow cooked black lentils with cream & butter", 260.00, "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80", True),
            (2, "Garlic Naan", "Clay oven baked flatbread with garlic butter", 60.00, "https://plus.unsplash.com/premium_photo-1666663150789-be4318924491?auto=format&fit=crop&w=600&q=80", True),
            (3, "Gulab Jamun", "Soft milk dumplings in rose sugar syrup", 120.00, "https://images.unsplash.com/photo-1666190092159-3171cf0fbb12?auto=format&fit=crop&w=600&q=80", True),
            (3, "Chocolate Lava Cake", "Warm cake with molten chocolate center", 190.00, "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=600&q=80", True),
            (4, "Mango Lassi", "Sweet yogurt smoothie with Alphonso mangoes", 110.00, "https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?auto=format&fit=crop&w=600&q=80", True),
            (4, "Iced Cold Coffee", "Espresso with cold milk & vanilla ice cream", 140.00, "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=600&q=80", True),
        ]
        for item in menu:
            cursor.execute(
                f"INSERT INTO menu_items (category_id, name, description, price, image_url, is_available) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph});",
                item
            )
        conn.commit()

    conn.close()
