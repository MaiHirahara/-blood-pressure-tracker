import sqlite3

def show_records():
    conn = sqlite3.connect('blood_pressure.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM blood_pressure ORDER BY date_time DESC")
    records = cursor.fetchall()

    conn.close()

    print("📋 血圧記録一覧:")
    for record in records:
        print(f"ID: {record[0]}, 収縮期: {record[1]}, 拡張期: {record[2]}, 測定日時: {record[3]}")

show_records()