import os
import sqlite3
from fastmcp import FastMCP

# 1. Path Management
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "inventory.db")
POLICY_PATH = os.path.join(BASE_DIR, "data", "policy.txt")

mcp = FastMCP("Infra_Sensor_v1")

# --- Standard Functions (Internal Logic) ---

def read_policy() -> str:
    """Reads the local policy.txt file for compliance checks."""
    if not os.path.exists(POLICY_PATH):
        return "Error: policy.txt not found."
    with open(POLICY_PATH, "r") as f:
        return f.read()

def fetch_inventory_data(site_name: str = None) -> str:
    """Internal logic to query the SQLite database."""
    if not os.path.exists(DB_PATH):
        return f"Error: DB not found at {DB_PATH}"

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = "SELECT site, node_id, ram_gb, firmware, status FROM inventory"
        
        if site_name:
            query += " WHERE site LIKE ?"
            cursor.execute(query, (f"%{site_name}%",))
        else:
            cursor.execute(query)
            
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No records found."
            
        output = "Site | ID | RAM (GB) | FW | Status\n" + "-"*45 + "\n"
        for r in rows:
            output += f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}\n"
        return output
    except Exception as e:
        return f"Database Error: {str(e)}"
    
def update_site_firmware(site: str, version: str) -> str:
    """Writes the new version to the SQLite DB."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE inventory SET firmware = ?, status = 'Online' WHERE site = ?",
            (version, site)
        )
        conn.commit()
        conn.close()
        return f"Successfully updated {site} to v{version}"
    except Exception as e:
        return f"Database error: {str(e)}"

# --- MCP Tool Wrappers (External Interface) ---

@mcp.tool()
def get_inventory(site_name: str = None) -> str:
    """Fetches the current hardware inventory."""
    return fetch_inventory_data(site_name)

@mcp.tool()
def get_policy() -> str:
    """Returns the current infrastructure compliance policy."""
    return read_policy()

if __name__ == "__main__":
    mcp.run()