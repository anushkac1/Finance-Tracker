from db import get_db


def get_categories():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM Category')
    return cursor.fetchall()

