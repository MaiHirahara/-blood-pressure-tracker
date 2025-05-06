import sqlite3

def insert_record():
    systolic = int(input("収縮期血圧を入力: "))
    diastolic = int(input("拡張期血圧を入力: "))

    conn = sqlite3.connect('blood_pressure.db')
    cursor = conn.cursor()

    cursor.execute("INSERT INTO blood_pressure (systolic, diastolic) VALUES (?, ?)", 
                   (systolic, diastolic))

    conn.commit()
    conn.close()
    print("✅ データが追加されました！")

insert_record()