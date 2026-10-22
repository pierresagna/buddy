
import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


class Postgres:
    def __init__(self):
        self.connection = None

    def connect(self):
        if self.connection is None or self.connection.closed:
            self.connection = psycopg.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                dbname=os.getenv("DB_NAME", "buddy"),
                user=os.getenv("DB_USER", "buddy_user"),
                password=os.getenv("DB_PASSWORD", "buddy_password"),
            )
        return self.connection

    def close(self):
        if self.connection is not None and not self.connection.closed:
            self.connection.close()
            self.connection = None
