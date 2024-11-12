import random
import datetime
import sqlite3

"""
.jrrp 今日人品

    .jrrp //今日的人品值(1-100)，每日更换

"""

def register_function(jrpg_functions, jrpg_events, sqlite_conn):
    jrpg_functions['jrrp'] = jrrp().feach


class jrrp:

    def __init__(self):
        try:
            self.conn = sqlite3.connect("./data/jrpgbot/jrrp.db", check_same_thread=False)
            with self.conn:
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS jrrp (
                        user_id INTEGER,
                        date TEXT,
                        value INTEGER,
                        PRIMARY KEY (user_id, date))
                ''')
        except sqlite3.Error as e:
            raise e
        
    async def feach(self, args, userslot, sender_user_id, group_id):
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("SELECT value FROM jrrp WHERE user_id =? AND date =?", (sender_user_id, datetime.date.today().strftime("%Y-%m-%d")))
                row = cursor.fetchone()
                if row is None:
                    value = random.randint(1, 100)
                    cursor.execute("INSERT INTO jrrp (user_id, date, value) VALUES (?,?,?)", (sender_user_id, datetime.date.today().strftime("%Y-%m-%d"), value))
                    return f"你今天的人品值是 {value} ！"
                else:
                    return f"你今天的人品值是 {row[0]} ！"
        except sqlite3.Error as e:
            raise e
