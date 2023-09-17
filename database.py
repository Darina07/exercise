from sqlalchemy import create_engine, text
import mysql.connector
import configparser


class MySQLConnection:
    _instance = None

    def __init__(self):
        self.host = None
        self.username = None
        self.password = None
        self.database = None
        self.connection = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load_config()
        return cls._instance

    def load_config(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        # Load database credentials from the config.ini file
        self.host = config['database']['host']
        self.username = config['database']['username']
        self.password = config['database']['password']
        self.database = config['database']['database']

    def connect(self):
        if not self.connection:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database
            )

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query, params=None):
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        cursor.close()
        return result
