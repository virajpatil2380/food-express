from backend.database import get_db_connection


class MenuModel:
    @staticmethod
    def get_menu(category_name=None):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"

        sql = """
            SELECT m.item_id, m.name, m.description, m.price, m.image_url, m.is_available, m.category_id, c.name as category_name
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

    @staticmethod
    def get_item_by_id(item_id):
        """Fetch a single menu item by its ID."""
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"

        sql = f"""
            SELECT m.item_id, m.name, m.description, m.price, m.image_url, m.is_available, m.category_id, c.name as category_name
            FROM menu_items m
            LEFT JOIN categories c ON m.category_id = c.category_id
            WHERE m.item_id = {ph};
        """
        cursor.execute(sql, (item_id,))
        row = cursor.fetchone()
        if engine_type == "sqlite" and row:
            row = dict(row)
        conn.close()
        return row

    @staticmethod
    def get_categories():
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category_id, name FROM categories ORDER BY category_id;")
        if engine_type == "sqlite":
            rows = [dict(r) for r in cursor.fetchall()]
        else:
            rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def add_category(name):
        """Add a new category and return its ID."""
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"
        cursor.execute(f"INSERT INTO categories (name) VALUES ({ph});", (name,))
        conn.commit()
        cat_id = cursor.lastrowid
        conn.close()
        return cat_id

    @staticmethod
    def add_menu_item(name, price, category_id, description="", image_url=""):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"

        # Default placeholder image if none provided
        if not image_url:
            image_url = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80"

        sql = f"INSERT INTO menu_items (name, price, category_id, description, image_url, is_available) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, 1);"
        cursor.execute(sql, (name, price, category_id, description, image_url))
        conn.commit()
        item_id = cursor.lastrowid
        conn.close()
        return item_id

    @staticmethod
    def update_menu_item(item_id, name, price, category_id, description="", image_url=""):
        """Full update of a menu item's details."""
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"

        sql = f"""
            UPDATE menu_items
            SET name = {ph}, price = {ph}, category_id = {ph}, description = {ph}, image_url = {ph}
            WHERE item_id = {ph};
        """
        cursor.execute(sql, (name, price, category_id, description, image_url, item_id))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    @staticmethod
    def update_availability(item_id, is_available):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"

        sql = f"UPDATE menu_items SET is_available = {ph} WHERE item_id = {ph};"
        cursor.execute(sql, (1 if is_available else 0, item_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_menu_item(item_id):
        """Delete a menu item. Also removes related order_items references."""
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"

        # Remove from order_items first to avoid FK constraint issues
        cursor.execute(f"DELETE FROM order_items WHERE item_id = {ph};", (item_id,))
        cursor.execute(f"DELETE FROM menu_items WHERE item_id = {ph};", (item_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
