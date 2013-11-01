import sqlite3

if __name__ == '__main__':
    
    con = sqlite3.connect('/home/haichun/panzx/db.sql3')
    sql = input('SQL:')
    con.execute(sql)
    con.commit()
    con.close()
