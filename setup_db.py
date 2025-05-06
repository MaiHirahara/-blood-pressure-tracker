import sqlite3

conn = sqlite3.connect('blood_pressure.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE blood_pressure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    systolic INTEGER NOT NULL,
    diastolic INTEGER NOT NULL,
    date_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    note TEXT
)
""")

conn.commit()
conn.close()
print("✅ データベースが作成されました！")