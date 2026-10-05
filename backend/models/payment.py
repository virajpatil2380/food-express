import uuid
from backend.database import get_db_connection

class PaymentModel:
    @staticmethod
    def initiate_upi_payment(order_id, upi_id, amount):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"
        
        tx_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        upi_string = f"upi://pay?pa=foodexpress@upi&pn=FoodExpress&tr={tx_id}&am={amount:.2f}&cu=INR"
        
        # Insert payment record
        sql = f"""
            INSERT INTO payments (order_id, amount, payment_method, upi_id, transaction_id, status)
            VALUES ({ph}, {ph}, 'UPI', {ph}, {ph}, 'Pending');
        """
        cursor.execute(sql, (order_id, amount, upi_id, tx_id))
        
        # Update order with transaction_id and payment_method
        sql_order = f"UPDATE orders SET payment_method = 'UPI', transaction_id = {ph} WHERE order_id = {ph};"
        cursor.execute(sql_order, (tx_id, order_id))
        
        conn.commit()
        conn.close()
        
        return {
            "order_id": order_id,
            "transaction_id": tx_id,
            "amount": amount,
            "upi_id": upi_id,
            "upi_intent_url": upi_string,
            "status": "Pending"
        }

    @staticmethod
    def verify_payment(order_id, transaction_id, status="Completed"):
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if engine_type == "mysql" else "?"
        
        # Update payments table
        cursor.execute(f"UPDATE payments SET status = {ph} WHERE transaction_id = {ph};", (status, transaction_id))
        
        # Update orders table
        cursor.execute(
            f"UPDATE orders SET payment_status = {ph}, transaction_id = {ph} WHERE order_id = {ph};",
            (status, transaction_id, order_id)
        )
        
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def get_analytics():
        conn, engine_type = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total_orders, COALESCE(SUM(total_amount), 0) as total_revenue FROM orders WHERE status != 'Cancelled';")
        if engine_type == "sqlite":
            res = dict(cursor.fetchone())
        else:
            res = cursor.fetchone()
            
        total_orders = res["total_orders"]
        total_revenue = float(res["total_revenue"])
        aov = (total_revenue / total_orders) if total_orders > 0 else 0.0
        
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
