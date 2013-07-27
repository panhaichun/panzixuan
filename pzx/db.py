import sqlite3
import config

class DBTemplate:
    
    def __init__(self, database):
        self.__database = database
        
    def __connect(self):
        return sqlite3.connect(self.__database)

    def execute(self, action):
        conn = None
        try:
            conn = self.__connect()
            result = action(conn)
            conn.commit()
            return result
        except:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def insert(self, sql, params=()):
        def __action(conn):
            cursor = conn.cursor()
            cursor.execute(sql, params)
            cursor.execute('select last_insert_rowid() from T_ROLE')
            insert_id = None
            data = cursor.fetchone()
            if data:
                insert_id = data[0]
            cursor.close()
            return insert_id
        return self.execute(__action)

    def update(self, sql, params=()):
        def __action(conn):
            cursor = conn.cursor()
            result = cursor.execute(sql, params)
            cursor.close()
            return result
        return self.execute(__action)
        
    def batch_update(self, sql, params=()):
        def __action(conn):
            cursor = conn.cursor()
            result = cursor.executemany(sql, params)
            cursor.close()
            return result
        return self.execute(__action)

    def query_list(self, sql, params=(), mapper=None):
        if mapper is None:
            mapper = lambda row_data: row_data[0] if row_data and len(row_data) == 1 else row_data
        def __action(conn):
            cursor = conn.cursor()
            cursor.execute(sql, params)
            data = cursor.fetchall()
            results = []
            if data:
                [results.append(mapper(row_data)) for row_data in data]
            cursor.close()
            return results
        return self.execute(__action)

    def query_object(self, sql, params=(), mapper=None):
        results = self.query_list(sql, params, mapper)
        return results[0] if results else None

db_template = DBTemplate(config.ds_database)
