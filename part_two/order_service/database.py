import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def init_db(service_type='order'):
    """
    Initializes the orders database.
    """
    DATABASE = os.environ.get('DATABASE', 'orders.db')
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER,
                    quantity INTEGER,
                    timestamp TEXT
                )
            ''')
            conn.commit()
            logging.info("Orders database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"Failed to initialize database: {e}")

def buy_book(book_id, quantity=1):
    """
    Inserts a purchase record into the orders table.
    """
    DATABASE = os.environ.get('DATABASE', 'orders.db')
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (item_id, quantity, timestamp) VALUES (?, ?, datetime('now'))",
            (book_id, quantity)
        )
        conn.commit()
