import sqlite3
import pymysql
import os
import sys
from config import Config

def get_db_connection():
    """
    Attempts to connect to MySQL based on Config.
    If MySQL connection fails or DB_ENGINE is sqlite, falls back to SQLite seamlessly.
    """
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
        except Exception as e:
            # Fall back to SQLite if MySQL fails
            use_sqlite = True

    if use_sqlite:
        db_path = os.path.abspath(Config.SQLITE_DB_PATH)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

def init_db():
    """Initializes database tables and seeds initial food data if empty."""
    conn, engine_type = get_db_connection()
    cursor = conn.cursor()

    if engine_type == "sqlite":
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
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
            is_available BOOLEAN DEFAULT 1,
            FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            total_amount REAL NOT NULL,
            delivery_address TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
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
        """)
    else:
        # MySQL Initialization
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(15) UNIQUE NOT NULL,
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
            is_available BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT DEFAULT 1,
            total_amount DECIMAL(10,2) NOT NULL,
            delivery_address TEXT NOT NULL,
            status ENUM('Pending', 'Preparing', 'Out for Delivery', 'Delivered', 'Cancelled') DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
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

    conn.commit()

    # Seed initial user if missing
    cursor.execute("SELECT COUNT(*) as cnt FROM users;")
    row = cursor.fetchone()
    user_count = row['cnt'] if isinstance(row, dict) else row[0]
    if user_count == 0:
        cursor.execute(
            "INSERT INTO users (name, email, phone) VALUES (%s, %s, %s);" if engine_type == "mysql"
            else "INSERT INTO users (name, email, phone) VALUES (?, ?, ?);",
            ("John Doe", "john@foodexpress.com", "9876543210")
        )
        conn.commit()

    # Seed initial categories & menu items if missing
    cursor.execute("SELECT COUNT(*) as cnt FROM categories;")
    row = cursor.fetchone()
    cat_count = row['cnt'] if isinstance(row, dict) else row[0]
    if cat_count == 0:
        categories = ["Starters", "Main Course", "Desserts", "Beverages"]
        for cat in categories:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s);" if engine_type == "mysql"
                else "INSERT INTO categories (name) VALUES (?);",
                (cat,)
            )
        conn.commit()

        initial_menu = [
            (1, "Paneer Tikka", "Grilled cottage cheese cubes marinated in aromatic spices", 240.00, True),
            (1, "Crispy Spring Rolls", "Golden fried veggie rolls served with sweet chili dip", 180.00, True),
            (2, "Butter Chicken", "Rich creamy tomato gravy with tender chicken pieces", 340.00, True),
            (2, "Dal Makhani", "Slow cooked black lentils with fresh cream & butter", 260.00, True),
            (2, "Garlic Naan", "Traditional oven baked bread brushed with garlic butter", 60.00, True),
            (3, "Gulab Jamun", "Soft milk solids dumplings soaked in rose sugar syrup", 120.00, True),
            (3, "Chocolate Lava Cake", "Warm chocolate cake with molten center", 190.00, True),
            (4, "Mango Lassi", "Refreshing yogurt drink blended with fresh mangoes", 110.00, True),
            (4, "Iced Cold Coffee", "Rich espresso whipped with cold milk & ice cream", 140.00, True)
        ]
        for item in initial_menu:
            cursor.execute(
                "INSERT INTO menu_items (category_id, name, description, price, is_available) VALUES (%s, %s, %s, %s, %s);"
                if engine_type == "mysql"
                else "INSERT INTO menu_items (category_id, name, description, price, is_available) VALUES (?, ?, ?, ?, ?);",
                item
            )
        conn.commit()

    conn.close()

# API Database Query Handlers
def fetch_menu(category_name=None):
    conn, engine_type = get_db_connection()
    cursor = conn.cursor()
    
    ph = "%s" if engine_type == "mysql" else "?"
    sql = """
        SELECT m.item_id, m.name, m.description, m.price, m.is_available, m.category_id, c.name as category_name
        FROM menu_items m
        LEFT JOIN categories c ON m.category_id = c.category_id
    """
    params = []
    if category_name and category_name.lower() != "all":
        sql += f" WHERE c.name = {ph}"
        params.append(category_name)
        
    sql += " ORDER BY m.category_id, m.name;"
    cursor.execute(sql, params)
    
    if engine_type == "sqlite":
        rows = [dict(r) for r in cursor.fetchall()]
    else:
        rows = cursor.fetchall()
        
    conn.close()
    return rows

def fetch_categories():
    conn, engine_type = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category_id, name FROM categories ORDER BY category_id;")
    if engine_type == "sqlite":
        rows = [dict(r) for r in cursor.fetchall()]
    else:
        rows = cursor.fetchall()
    conn.close()
    return rows

def insert_menu_item(name, price, category_id, description=""):
    conn, engine_type = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if engine_type == "mysql" else "?"
    
    sql = f"INSERT INTO menu_items (name, price, category_id, description, is_available) VALUES ({ph}, {ph}, {ph}, {ph}, 1);"
    cursor.execute(sql, (name, price, category_id, description))
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id

def set_item_availability(item_id, is_available):
    conn, engine_type = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if engine_type == "mysql" else "?"
    
    sql = f"UPDATE menu_items SET is_available = {ph} WHERE item_id = {ph};"
    cursor.execute(sql, (1 if is_available else 0, item_id))
    conn.commit()
    conn.close()

def place_order_transaction(user_id, delivery_address, items):
    """
    Executes atomic SQL transaction to insert into orders and order_items.
    """
    conn, engine_type = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if engine_type == "mysql" else "?"
    
    try:
        # Calculate total
        total_amount = sum(item["qty"] * float(item["price"]) for item in items)
        
        # 1. Insert into orders
        sql_order = f"INSERT INTO orders (user_id, total_amount, delivery_address, status) VALUES ({ph}, {ph}, {ph}, 'Pending');"
        cursor.execute(sql_order, (user_id or 1, total_amount, delivery_address))
        order_id = cursor.lastrowid
        
        # 2. Insert line items
        sql_item = f"INSERT INTO order_items (order_id, item_id, quantity, unit_price) VALUES ({ph}, {ph}, {ph}, {ph});"
        for item in items:
            cursor.execute(sql_item, (order_id, item["item_id"], item["qty"], item["price"]))
            
        conn.commit()
        conn.close()
        return order_id
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e

def fetch_order_by_id(order_id):
    conn, engine_type = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if engine_type == "mysql" else "?"
    
    cursor.execute(f"SELECT * FROM orders WHERE order_id = {ph};", (order_id,))
    if engine_type == "sqlite":
        row = cursor.fetchone()
        order = dict(row) if row else None
    else:
        order = cursor.fetchone()
        
    if not order:
        conn.close()
        return None
        
    # Fetch items
    cursor.execute(f"""
        SELECT oi.order_item_id, oi.item_id, oi.quantity, oi.unit_price, m.name
        FROM order_items oi
        JOIN menu_items m ON oi.item_id = m.item_id
        WHERE oi.order_id = {ph};
    """, (order_id,))
    
    if engine_type == "sqlite":
        order["items"] = [dict(r) for r in cursor.fetchall()]
    else:
        order["items"] = cursor.fetchall()
        
    conn.close()
    return order

def fetch_admin_orders(status_filter=None):
    conn, engine_type = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if engine_type == "mysql" else "?"
    
    sql = """
        SELECT o.order_id, o.user_id, u.name as customer_name, u.phone as customer_phone,
               o.total_amount, o.delivery_address, o.status, o.created_at
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.user_id
    """
    params = []
    if status_filter and status_filter.lower() != "all":
        sql += f" WHERE o.status = {ph}"
        params.append(status_filter)
        
    sql += " ORDER BY o.created_at DESC;"
    cursor.execute(sql, params)
    
    if engine_type == "sqlite":
        orders = [dict(r) for r in cursor.fetchall()]
    else:
        orders = cursor.fetchall()
        
    # Fetch line items for each order
    for o in orders:
        cursor.execute(f"""
            SELECT oi.item_id, oi.quantity, oi.unit_price, m.name
            FROM order_items oi
            JOIN menu_items m ON oi.item_id = m.item_id
            WHERE oi.order_id = {ph};
        """, (o["order_id"],))
        if engine_type == "sqlite":
            o["items"] = [dict(r) for r in cursor.fetchall()]
        else:
            o["items"] = cursor.fetchall()
            
    conn.close()
    return orders

def update_order_status_db(order_id, status):
    conn, engine_type = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if engine_type == "mysql" else "?"
    
    cursor.execute(f"UPDATE orders SET status = {ph} WHERE order_id = {ph};", (status, order_id))
    conn.commit()
    conn.close()

def fetch_analytics():
    conn, engine_type = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Total Revenue, Total Orders, AOV
    cursor.execute("SELECT COUNT(*) as total_orders, COALESCE(SUM(total_amount), 0) as total_revenue FROM orders WHERE status != 'Cancelled';")
    if engine_type == "sqlite":
        res = dict(cursor.fetchone())
    else:
        res = cursor.fetchone()
        
    total_orders = res["total_orders"]
    total_revenue = float(res["total_revenue"])
    aov = (total_revenue / total_orders) if total_orders > 0 else 0.0
    
    # 2. Revenue Trend over time
    date_func = "DATE(created_at)" if engine_type == "mysql" else "date(created_at)"
    cursor.execute(f"""
        SELECT {date_func} as order_date, SUM(total_amount) as daily_revenue, COUNT(*) as daily_orders
        FROM orders
        WHERE status != 'Cancelled'
        GROUP BY {date_func}
        ORDER BY order_date ASC;
    """)
    if engine_type == "sqlite":
        revenue_trend = [dict(r) for r in cursor.fetchall()]
    else:
        revenue_trend = cursor.fetchall()
        
    # 3. Top selling items
    cursor.execute("""
        SELECT m.name, SUM(oi.quantity) as total_qty, SUM(oi.quantity * oi.unit_price) as item_revenue
        FROM order_items oi
        JOIN menu_items m ON oi.item_id = m.item_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status != 'Cancelled'
        GROUP BY m.item_id, m.name
        ORDER BY total_qty DESC
        LIMIT 5;
    """)
    if engine_type == "sqlite":
        top_items = [dict(r) for r in cursor.fetchall()]
    else:
        top_items = cursor.fetchall()
        
    conn.close()
    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "aov": round(aov, 2),
        "revenue_trend": revenue_trend,
        "top_items": top_items
    }
