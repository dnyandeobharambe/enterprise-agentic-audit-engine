import sqlite3
import os

class AuditUtils:
    def __init__(self, db_path="inventory.db", policy_path="policy.txt"):
        self.db_path = db_path
        self.policy_path = policy_path

    def get_inventory_status(self):
        """Fetches the state exactly as seen in your DB view."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Matching the columns in your image exactly
            cursor.execute("SELECT site, node_id, ram_gb, firmware, status FROM nodes")
            rows = cursor.fetchall()
            conn.close()
            
            # Format as a list of strings for better LLM readability
            inventory_list = [f"Site: {r[0]}, ID: {r[1]}, RAM: {r[2]}GB, Firmware: {r[3]}, Status: {r[4]}" for r in rows]
            return "\n".join(inventory_list)
        except sqlite3.Error as e:
            return f"Database Error: {e}"

    def get_audit_policy(self):
        """Reads the policy we established earlier."""
        if not os.path.exists(self.policy_path):
            return "Policy file not found."
        with open(self.policy_path, "r") as f:
            return f.read()
        