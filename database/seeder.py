"""
Database Seeder for the Advanced ATM Simulator.
Initializes tables via schema.sql and seeds 100 authentic Indian demo customer accounts
and physical cash vault cassettes.
"""

import sys
from pathlib import Path
from typing import Dict, List

# Support running directly as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from core.security import generate_salt, hash_pin
from database.connection import get_db_connection, immediate_transaction

# 100 Authentic Indian Demo Account Profiles
INDIAN_NAMES = [
    ("Tarang Suryawanshi", "1234", 2500.0, 0, 0),   # 10001 (Lead Developer)
    ("Sameep Patel", "4321", 1000.0, 0, 0),         # 10002 (Project Partner)
    ("Diya Iyer", "9999", 50.0, 0, 0),              # 10003
    ("Aditya Verma", "0000", 300.0, 1, 3),          # 10004 (Locked Demo)
    ("Aarav Sharma", "1111", 5000.0, 0, 0),         # 10005
    ("Vivaan Patel", "2222", 7500.0, 0, 0),         # 10006
    ("Ananya Gupta", "3333", 12000.0, 0, 0),        # 10007
    ("Rahul Deshmukh", "4444", 3200.0, 0, 0),       # 10008
    ("Sneha Joshi", "5555", 1500.0, 0, 0),          # 10009
    ("Priya Nair", "6666", 8900.0, 0, 0),           # 10010
    ("Rohan Mehta", "7777", 4500.0, 0, 0),          # 10011
    ("Vikram Singh", "8888", 6200.0, 0, 0),         # 10012
    ("Pooja Reddy", "1212", 2100.0, 0, 0),          # 10013
    ("Neha Kulkarni", "2323", 9400.0, 0, 0),        # 10014
    ("Arjun Rao", "3434", 11000.0, 0, 0),           # 10015
    ("Rajesh Kumar", "4545", 5300.0, 0, 0),         # 10016
    ("Sunita Devi", "5656", 1800.0, 0, 0),          # 10017
    ("Amit Shah", "6767", 14500.0, 0, 0),           # 10018
    ("Kavita Menon", "7878", 3700.0, 0, 0),         # 10019
    ("Suresh Raina", "8989", 16000.0, 0, 0),        # 10020
    ("Rohit Sharma", "4545", 25000.0, 0, 0),        # 10021
    ("Virat Kohli", "1818", 50000.0, 0, 0),         # 10022
    ("MS Dhoni", "0707", 45000.0, 0, 0),            # 10023
    ("Sachin Tendulkar", "1010", 35000.0, 0, 0),    # 10024
    ("Hardik Pandya", "3333", 22000.0, 0, 0),       # 10025
    ("Jasprit Bumrah", "9393", 28000.0, 0, 0),      # 10026
    ("Shubman Gill", "7777", 19000.0, 0, 0),        # 10027
    ("KL Rahul", "0101", 24000.0, 0, 0),            # 10028
    ("Rishabh Pant", "1717", 21000.0, 0, 0),        # 10029
    ("Sanju Samson", "1414", 13000.0, 0, 0),        # 10030
    ("Ravindra Jadeja", "0808", 31000.0, 0, 0),     # 10031
    ("Smriti Mandhana", "1818", 27000.0, 0, 0),     # 10032
    ("Harmanpreet Kaur", "8484", 23000.0, 0, 0),    # 10033
    ("Mithali Raj", "0303", 30000.0, 0, 0),         # 10034
    ("Jhulan Goswami", "2525", 26000.0, 0, 0),      # 10035
    ("Deepti Sharma", "0606", 14000.0, 0, 0),       # 10036
    ("Jemimah Rodrigues", "0505", 15500.0, 0, 0),   # 10037
    ("Shafali Verma", "2828", 16500.0, 0, 0),       # 10038
    ("Richa Ghosh", "1313", 11500.0, 0, 0),         # 10039
    ("Pooja Vastrakar", "0909", 12500.0, 0, 0),     # 10040
    ("Renuka Singh", "1010", 13500.0, 0, 0),        # 10041
    ("Yuvraj Singh", "1212", 34000.0, 0, 0),        # 10042
    ("Virender Sehwag", "4444", 32000.0, 0, 0),     # 10043
    ("Gautam Gambhir", "0505", 29000.0, 0, 0),      # 10044
    ("Harbhajan Singh", "0303", 27500.0, 0, 0),     # 10045
    ("Zaheer Khan", "3434", 26500.0, 0, 0),         # 10046
    ("Anil Kumble", "1010", 38000.0, 0, 0),         # 10047
    ("VVS Laxman", "2810", 33000.0, 0, 0),          # 10048
    ("Sourav Ganguly", "0808", 41000.0, 0, 0),      # 10049
    ("Rahul Dravid", "1919", 42000.0, 0, 0),        # 10050
    ("Kapil Dev", "1983", 48000.0, 0, 0),           # 10051
    ("Sunil Gavaskar", "1000", 46000.0, 0, 0),      # 10052
    ("Ravi Shastri", "1985", 36000.0, 0, 0),        # 10053
    ("Dilip Vengsarkar", "1111", 20000.0, 0, 0),    # 10054
    ("Chetan Sharma", "2222", 18500.0, 0, 0),       # 10055
    ("Javagal Srinath", "3333", 22500.0, 0, 0),     # 10056
    ("Venkatesh Prasad", "4444", 21500.0, 0, 0),    # 10057
    ("Ashish Nehra", "6464", 24500.0, 0, 0),        # 10058
    ("Irfan Pathan", "5656", 23500.0, 0, 0),        # 10059
    ("Munaf Patel", "7878", 17500.0, 0, 0),         # 10060
    ("RP Singh", "8989", 19500.0, 0, 0),            # 10061
    ("Praveen Kumar", "1212", 16500.0, 0, 0),       # 10062
    ("Ishant Sharma", "2929", 25500.0, 0, 0),       # 10063
    ("Umesh Yadav", "1919", 24000.0, 0, 0),         # 10064
    ("Mohammed Shami", "1111", 29500.0, 0, 0),      # 10065
    ("Bhuvneshwar Kumar", "1515", 26000.0, 0, 0),   # 10066
    ("Kuldeep Yadav", "2323", 21000.0, 0, 0),       # 10067
    ("Yuzvendra Chahal", "0303", 22000.0, 0, 0),    # 10068
    ("Axar Patel", "2020", 23000.0, 0, 0),          # 10069
    ("Washington Sundar", "0505", 19000.0, 0, 0),   # 10070
    ("Shardul Thakur", "5454", 18000.0, 0, 0),      # 10071
    ("Deepak Chahar", "9090", 17000.0, 0, 0),       # 10072
    ("Mohammed Siraj", "7373", 25000.0, 0, 0),      # 10073
    ("Prasidh Krishna", "2424", 16000.0, 0, 0),     # 10074
    ("Arshdeep Singh", "0202", 20000.0, 0, 0),      # 10075
    ("Umran Malik", "1500", 15000.0, 0, 0),         # 10076
    ("Avesh Khan", "6565", 14000.0, 0, 0),          # 10077
    ("Mukesh Kumar", "4949", 13000.0, 0, 0),        # 10078
    ("Ravi Bishnoi", "5656", 18000.0, 0, 0),        # 10079
    ("Rinku Singh", "3535", 22000.0, 0, 0),         # 10080
    ("Yashasvi Jaiswal", "6464", 26000.0, 0, 0),    # 10081
    ("Tilak Varma", "0909", 19000.0, 0, 0),         # 10082
    ("Jitesh Sharma", "9999", 15000.0, 0, 0),       # 10083
    ("Shivam Dube", "2525", 21000.0, 0, 0),         # 10084
    ("Dhruv Jurel", "1616", 17000.0, 0, 0),         # 10085
    ("Sarfaraz Khan", "9797", 18500.0, 0, 0),       # 10086
    ("Devdutt Padikkal", "3737", 16500.0, 0, 0),    # 10087
    ("Ruturaj Gaikwad", "3131", 24000.0, 0, 0),     # 10088
    ("Sai Sudharsan", "2323", 17500.0, 0, 0),       # 10089
    ("Abhishek Sharma", "0404", 23500.0, 0, 0),     # 10090
    ("Nitish Kumar Reddy", "2727", 15500.0, 0, 0),  # 10091
    ("Mayank Yadav", "1567", 14500.0, 0, 0),        # 10092
    ("Harshit Rana", "2222", 13500.0, 0, 0),        # 10093
    ("Prabhsimran Singh", "8484", 12500.0, 0, 0),   # 10094
    ("Ayush Badoni", "0202", 11500.0, 0, 0),        # 10095
    ("Nehal Wadhera", "1818", 10500.0, 0, 0),       # 10096
    ("Abdul Samad", "0101", 12000.0, 0, 0),         # 10097
    ("Shahrukh Khan", "3535", 16000.0, 0, 0),       # 10098
    ("Rahul Tewatia", "9292", 19500.0, 0, 0),       # 10099
    ("Sai Kishore", "1111", 14000.0, 0, 0),         # 10100
]

DEMO_ACCOUNTS: List[Dict] = [
    {
        "account_number": str(10001 + i),
        "account_holder": name,
        "pin": pin,
        "balance": bal,
        "is_locked": locked,
        "failed_attempts": failed,
    }
    for i, (name, pin, bal, locked, failed) in enumerate(INDIAN_NAMES)
]


def init_database(db_path: Path = config.DB_PATH) -> None:
    """Creates tables and indexes from schema.sql if they do not already exist."""
    conn = get_db_connection(db_path)
    try:
        with open(config.SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
    finally:
        conn.close()


def seed_data(db_path: Path = config.DB_PATH, reset: bool = False) -> None:
    """
    Populates default demo accounts and cassette vault notes.
    If reset=True, clears existing data before seeding 100 Indian customer accounts.
    If reset=False, only inserts demo records if they do not already exist,
    preserving all live customer account modifications, balances, and vault states.
    """
    init_database(db_path)
    conn = get_db_connection(db_path)
    try:
        with immediate_transaction(conn):
            if reset:
                conn.execute("DELETE FROM transactions;")
                conn.execute("DELETE FROM accounts;")
                conn.execute("DELETE FROM cash_vault;")

            # Seed 100 accounts
            for acc in DEMO_ACCOUNTS:
                salt = generate_salt()
                pin_hash = hash_pin(acc["pin"], salt)
                if reset:
                    conn.execute(
                        """
                        INSERT INTO accounts (account_number, account_holder, pin_hash, salt, balance, is_locked, failed_attempts)
                        VALUES (?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            acc["account_number"],
                            acc["account_holder"],
                            pin_hash,
                            salt,
                            acc["balance"],
                            acc["is_locked"],
                            acc["failed_attempts"],
                        ),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO accounts (account_number, account_holder, pin_hash, salt, balance, is_locked, failed_attempts)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(account_number) DO NOTHING;
                        """,
                        (
                            acc["account_number"],
                            acc["account_holder"],
                            pin_hash,
                            salt,
                            acc["balance"],
                            acc["is_locked"],
                            acc["failed_attempts"],
                        ),
                    )

            # Seed vault cassettes
            for denom, count in config.DEFAULT_VAULT_INVENTORY.items():
                if reset:
                    conn.execute(
                        """
                        INSERT INTO cash_vault (denomination, note_count)
                        VALUES (?, ?);
                        """,
                        (denom, count),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO cash_vault (denomination, note_count)
                        VALUES (?, ?)
                        ON CONFLICT(denomination) DO NOTHING;
                        """,
                        (denom, count),
                    )
    finally:
        conn.close()


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    seed_data(reset=reset_flag)
    action = "reset and seeded" if reset_flag else "seeded (idempotent)"
    print(f"[+] Database {action} with 100 Indian customer accounts successfully at: {config.DB_PATH}")
