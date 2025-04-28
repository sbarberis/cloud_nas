import mysql.connector
import json

class MySqlFunctions:
    def __init__(self):
        dbconfig = self.load_configs()

        self.cnx = mysql.connector.connect(pool_name="mysql_pool_connections",
                                           pool_size=20,
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
            mysql_cursor.close()
            connection.close()


class MySqlDataInterface(MySqlFunctions):
    def __init__(self):
        super().__init__()

    def fetch_all_users(self) -> list:
        return self.fetch_data('select * from utenti')

    def fetch_file_su_server(self, offset: int = 0, limit: int | None = None) -> list:
        return self.fetch_data('select * from files_su_server', offset=offset, limit=limit)
