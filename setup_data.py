import sqlite3
import os

# 1. Ensure the data directory exists
os.makedirs('data', exist_ok=True)

def init_db():
    # 2. Connect to the database (this creates the file if it doesn't exist)
    db_path = os.path.join('data', 'inventory.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 3. Define the Schema
    cursor.execute('DROP TABLE IF EXISTS inventory')
    cursor.execute('''
        CREATE TABLE inventory (
            site TEXT, 
            node_id TEXT, 
            ram_gb INTEGER, 
            firmware REAL,
            status TEXT
        )
    ''')

    # 4. Insert the "Reality" data for the AuditAgent to check
    nodes = [
        ('Bellevue-01', 'B-101', 8, 4.1, 'Active'),    # Low RAM & Old Firmware
        ('Bellevue-01', 'B-102', 32, 4.5, 'Active'),   # Passing
        ('Seattle-05', 'S-501', 32, 4.5, 'Active'),    # Passing
        ('Seattle-05', 'S-502', 16, 4.2, 'Active'),    # Minimum Passing
        ('Kirkland-02', 'K-201', 64, 3.9, 'Active')    # High RAM but Old Firmware
    ]
    
    cursor.executemany('INSERT INTO inventory VALUES (?,?,?,?,?)', nodes)
    conn.commit()
    conn.close()
    print(f"✅ Success: {db_path} created with 5 nodes.")

if __name__ == "__main__":
    init_db()
    