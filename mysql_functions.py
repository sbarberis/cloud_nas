import mysql.connector
import json


class MySqlFunctions:
    def __init__(self):
        dbconfig = self.load_configs()

        self.cnx = mysql.connector.connect(pool_name="mypool",
                                           **dbconfig)

    def get_connection(self):
        return self.cnx

    @staticmethod
    def load_configs() -> dict:
        with open('./db_config.json') as json_file:
            data = json.load(json_file)
        return data

    def fetch_data(self, query: str, offset: int = 0, limit: int | None = None) -> list:
        mysql_cursor = None
        try:
            if offset < 0:
                offset = 0
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

    def row_count(self, table_name: str) -> int:
        base_query = f'select count(*) tot from {table_name}'
        result = self.fetch_data(base_query, 0)
        total = 0
        for row in result:
            total = row['tot']
        return total

    def fetch_file_on_server_count(self) -> int:
        return self.row_count('files_su_server')

    def fetch_file_on_tape_count(self):
        return self.row_count('files_su_nastro')

    def fetch_file_su_server(self, form_search, offset: int = 0, limit: int | None = None) -> list:
        base_query = 'select * from files_su_server'
        if form_search:
            if form_search.file_name:
                file_name = form_search.file_name.lower()
                base_query = f"{base_query} where lower(fs_nome_file) like \'%{file_name}%\'"

        return self.fetch_data(base_query, offset=offset, limit=limit)
