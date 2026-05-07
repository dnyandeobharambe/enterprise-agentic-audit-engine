import os
import sqlite3

# Get current script path
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "inventory.db")

print(f"--- Diagnostic Report ---")
print(f"Target DB Path: {db_path}")
print(f"File Exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables Found: {[t[0] for t in tables]}")
    conn.close()
    