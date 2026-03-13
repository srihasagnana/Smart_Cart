import mysql.connector
from config.settings import db_host,db_port, db_user,db_password, db_name

class Mysql:
    def __init__(self):
        self.conn=None
    def connection(self):
        if self.conn and self.conn.is_connected():
            return self.conn
        self.conn=mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        return self.conn

    def execute(self, query, params=None, commit=False):
        conn = self.connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit:
            conn.commit()
        return cursor

    def fetchall(self,query,params=None):
        cursor=self.execute(query,params)
        rows=cursor.fetchall()
        cursor.close()
        return rows

    def fetchone(self,query,params=None):
        cursor=self.execute(query,params)
        row=cursor.fetchone()
        cursor.close()
        return  row

    def close(self):
        if self.conn or self.connection():
            self.conn.close()
            self.conn=None