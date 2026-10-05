import random
from backend.database import get_db_connection


class OrderModel:
    @staticmethod
    def create_order(user_id, delivery_address, items, payment_method="COD"):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"

        try:
            total_amount = sum(item["qty"] * float(item["price"]) for item in items)
            total_with_gst = total_amount * 1.05
            otp_code = f"{random.randint(1000, 9999)}"

            sql = f"""
                INSERT INTO orders (user_id, total_amount, delivery_address, status, payment_method, payment_status, otp_code)
                VALUES ({ph}, {ph}, {ph}, 'Pending', {ph}, 'Pending', {ph});
            """
            cursor.execute(sql, (user_id or 1, total_with_gst, delivery_address, payment_method, otp_code))
            order_id = cursor.lastrowid

            for item in items:
                cursor.execute(
                    f"INSERT INTO order_items (order_id, item_id, quantity, unit_price) VALUES ({ph}, {ph}, {ph}, {ph});",
                    (order_id, item["item_id"], item["qty"], item["price"])
                )

            conn.commit()
            return order_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_order_by_id(order_id):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"

        cursor.execute(f"""
            SELECT o.*, u.name as customer_name, u.phone as customer_phone,
                   d.name as delivery_boy_name, d.phone as delivery_boy_phone
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
            LEFT JOIN users d ON o.delivery_user_id = d.user_id
            WHERE o.order_id = {ph};
        """, (order_id,))

        row = cursor.fetchone()
        order = dict(row) if (engine_type == "sqlite" and row) else row

        if not order:
            conn.close()
            return None

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

    @staticmethod
    def get_user_orders(user_id):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"

        cursor.execute(f"""
            SELECT o.*, d.name as delivery_boy_name, d.phone as delivery_boy_phone
            FROM orders o
            LEFT JOIN users d ON o.delivery_user_id = d.user_id
            WHERE o.user_id = {ph}
            ORDER BY o.created_at DESC;
        """, (user_id,))

        orders = [dict(r) for r in cursor.fetchall()] if engine_type == "sqlite" else cursor.fetchall()

        for o in orders:
            cursor.execute(f"""
                SELECT oi.item_id, oi.quantity, oi.unit_price, m.name
                FROM order_items oi JOIN menu_items m ON oi.item_id = m.item_id
                WHERE oi.order_id = {ph};
            """, (o["order_id"],))
            o["items"] = [dict(r) for r in cursor.fetchall()] if engine_type == "sqlite" else cursor.fetchall()

        conn.close()
        return orders

    @staticmethod
    def get_all_orders(status_filter=None):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"

        sql = """
            SELECT o.order_id, o.user_id, u.name as customer_name, u.phone as customer_phone,
                   o.delivery_user_id, d.name as delivery_boy_name,
                   o.total_amount, o.delivery_address, o.status, o.payment_method, o.payment_status,
                   o.transaction_id, o.otp_code, o.rating, o.review_text, o.created_at
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
            LEFT JOIN users d ON o.delivery_user_id = d.user_id
        """
        params = []
        if status_filter and status_filter.lower() != "all":
            sql += f" WHERE o.status = {ph}"
            params.append(status_filter)

        sql += " ORDER BY o.created_at DESC;"
        cursor.execute(sql, params)
        orders = [dict(r) for r in cursor.fetchall()] if engine_type == "sqlite" else cursor.fetchall()

        for o in orders:
            cursor.execute(f"""
                SELECT oi.item_id, oi.quantity, oi.unit_price, m.name
                FROM order_items oi JOIN menu_items m ON oi.item_id = m.item_id
                WHERE oi.order_id = {ph};
            """, (o["order_id"],))
            o["items"] = [dict(r) for r in cursor.fetchall()] if engine_type == "sqlite" else cursor.fetchall()

        conn.close()
        return orders

    @staticmethod
    def get_delivery_partners():
        """Fetch all users registered as Delivery Partners."""
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, email, phone FROM users WHERE role = 'Delivery';")
        partners = [dict(r) for r in cursor.fetchall()] if engine_type == "sqlite" else cursor.fetchall()
        conn.close()
        return partners

    @staticmethod
    def get_delivery_orders(delivery_user_id=None):
        """
        If delivery_user_id is specified (Delivery Boy logged in), fetch ONLY orders assigned to him!
        If None (Admin view), fetch all orders in Ready, Out for Delivery, or Delivered state.
        """
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"

        sql = """
            SELECT o.order_id, o.user_id, u.name as customer_name, u.phone as customer_phone,
                   o.delivery_user_id, d.name as delivery_boy_name, d.phone as delivery_boy_phone,
                   o.total_amount, o.delivery_address, o.status,
                   o.payment_method, o.payment_status, o.otp_code, o.created_at
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
            LEFT JOIN users d ON o.delivery_user_id = d.user_id
        """
        params = []
        if delivery_user_id:
            sql += f" WHERE o.delivery_user_id = {ph} AND o.status IN ('Out for Delivery', 'Delivered')"
            params.append(delivery_user_id)
        else:
            sql += " WHERE o.status IN ('Ready', 'Out for Delivery', 'Delivered')"

        sql += " ORDER BY o.created_at DESC;"
        cursor.execute(sql, params)
        orders = [dict(r) for r in cursor.fetchall()] if engine_type == "sqlite" else cursor.fetchall()

        for o in orders:
            cursor.execute(f"""
                SELECT oi.item_id, oi.quantity, oi.unit_price, m.name
                FROM order_items oi JOIN menu_items m ON oi.item_id = m.item_id
                WHERE oi.order_id = {ph};
            """, (o["order_id"],))
            o["items"] = [dict(r) for r in cursor.fetchall()] if engine_type == "sqlite" else cursor.fetchall()

        conn.close()
        return orders

    @staticmethod
    def update_status(order_id, status):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"
        cursor.execute(f"UPDATE orders SET status = {ph} WHERE order_id = {ph};", (status, order_id))
        conn.commit()
        conn.close()

    @staticmethod
    def assign_delivery(order_id, delivery_user_id):
        """Admin assigns a specific Delivery Boy to an order and updates status to Out for Delivery."""
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"
        cursor.execute(
            f"UPDATE orders SET delivery_user_id = {ph}, status = 'Out for Delivery' WHERE order_id = {ph};",
            (delivery_user_id, order_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def save_rating(order_id, rating, review_text=""):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"
        cursor.execute(
            f"UPDATE orders SET rating = {ph}, review_text = {ph} WHERE order_id = {ph};",
            (rating, review_text, order_id)
        )
        conn.commit()
        conn.close()
        return True
