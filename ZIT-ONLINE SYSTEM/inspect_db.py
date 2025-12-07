from app import app, db
from sqlalchemy import inspect, text
with app.app_context():
    print('engine url:', db.engine.url)
    print('tables:', inspect(db.engine).get_table_names())
    cur = db.session.execute(text("PRAGMA table_info('course');"))
    print('course columns:', cur.fetchall())
