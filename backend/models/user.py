from backend.database import get_db_connection

class UserModel:
    @staticmethod
    def create_user(name, email, phone, password, role="Customer"):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"
        
        # Check if email exists
        cursor.execute(f"SELECT user_id FROM users WHERE email = {ph};", (email,))
        if cursor.fetchone():
            conn.close()
            return None, "Email address already registered."

        sql = f"INSERT INTO users (name, email, phone, password, role) VALUES ({ph}, {ph}, {ph}, {ph}, {ph});"
        cursor.execute(sql, (name, email, phone, password, role))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {"user_id": user_id, "name": name, "email": email, "phone": phone, "role": role}, None

    @staticmethod
    def authenticate(email, password):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"
        
        cursor.execute(f"SELECT user_id, name, email, phone, password, role FROM users WHERE email = {ph};", (email,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None, "Invalid email or password."

        user = dict(row) if engine_type == "sqlite" else row
        if user["password"] != password:
            return None, "Invalid email or password."

        # Exclude password in response
        del user["password"]
        return user, None
