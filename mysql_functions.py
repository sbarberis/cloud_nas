import mysql.connector
import json
from typing import Tuple


class MySqlFunctions:
    def __init__(self):
        dbconfig = self.load_configs()

        self.connector = mysql.connector.connect(**dbconfig)

    def get_connection(self):
        return self.connector

    @staticmethod
    def load_configs() -> dict:
        with open('./db_config.json') as json_file:
            data = json.load(json_file)
        return data

    def fetch_data(self, query: str, offset: int = 0, limit: int | None = None) -> list:
        mysql_cursor = None
        connection = None
        try:
            connection = self.get_connection()
            mysql_cursor = connection.cursor(dictionary=True)
            if limit:
                query = f"{query} limit {limit} offset {offset}"
            mysql_cursor.execute(query)
            result = mysql_cursor.fetchall()
            return result
        finally:
            if mysql_cursor:
                mysql_cursor.close()


class MySqlDataInterface(MySqlFunctions):
    def __init__(self):
        super().__init__()

    def fetch_all_users(self) -> list:
        return self.fetch_data('select * from utenti')

    def fetch_file_su_server(self, form_search, offset: int = 0, limit: int | None = None) -> list:
        base_query = 'select * from files_su_server'
        if form_search:
            if form_search.file_name:
                file_name = form_search.file_name.lower()
                base_query = f"{base_query} where lower(fs_nome_file) like \'%{file_name}%\'"

        return self.fetch_data(base_query, offset=offset, limit=limit)
