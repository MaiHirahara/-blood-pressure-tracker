from flask import Flask, render_template, request, redirect
import sqlite3  # ✅ SQLiteを使用！
import os
from datetime import datetime, timezone, timedelta
import pytz

app = Flask(__name__)

# 🔹 SQLiteへの接続
def get_db_connection():
    conn = sqlite3.connect("blood_pressure.db")  # ✅ SQLiteのデータベースに接続
    conn.row_factory = sqlite3.Row  # ✅ 辞書型でデータを取得できるように設定
    return conn

# JSTに変換する関数（変更なし）
def convert_to_jst(utc_time):
    utc_tz = pytz.utc
    jst_tz = pytz.timezone("Asia/Tokyo")
    utc_time = utc_time.replace(tzinfo=utc_tz)
    jst_time = utc_time.astimezone(jst_tz)
    return jst_time.strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()  # ✅ カーソルを作成
    cursor.execute('SELECT * FROM blood_pressure ORDER BY date_time DESC')  # ✅ クエリ実行
    records = cursor.fetchall()  # ✅ 結果を取得
    cursor.close()  # ✅ カーソルを閉じる

    updated_records = []
    for record in records:
        record_dict = {
            'date_time': str(record[3]),  # ✅ `int` を `str` に変換（重要！）
            'systolic': record[1],
            'diastolic': record[2],
            'note': record[4]
        }

        print(f"【DEBUG】取得した date_time の値: {record_dict['date_time']} （型: {type(record_dict['date_time'])}）")
        print(f"【DEBUG】元データ: {record[0]}（型: {type(record[0])}）")
        print(f"【DEBUG】変換後の date_time: {record_dict['date_time']}（型: {type(record_dict['date_time'])}）")
        print(f"【DEBUG】record の内容: {record}")
        print(f"【DEBUG】record[0]: {record[0]}（型: {type(record[0])}）")

        try:
            dt_obj = datetime.strptime(record_dict['date_time'], '%Y-%m-%d %H:%M:%S')  # ✅ SQLiteのデータはすでに適切なフォーマットのはず！
        except ValueError:
            dt_obj = datetime.strptime(record_dict['date_time'], '%Y-%m-%dT%H:%M')  # ✅ フォーマットが違う場合も対応

        # ✅ JSTに変換（必要な場合のみ）
        record_dict['date_time'] = convert_to_jst(dt_obj)

        updated_records.append(record_dict)

    return render_template('index.html', records=updated_records)

@app.route('/chart')
def chart():
    return render_template('chart.html')

import json
import pytz

@app.route('/chart-data')
def get_chart_data():
    conn = get_db_connection()

    start_date = request.args.get("start")
    end_date = request.args.get("end")

    print(f"【DEBUG】リクエストされた期間: {start_date} 〜 {end_date}") 

    if start_date and end_date:
        query = 'SELECT date_time, systolic, diastolic FROM blood_pressure WHERE date_time BETWEEN ? AND ? ORDER BY date_time'
        records = conn.execute(query, (start_date, end_date)).fetchall()
    else:
        latest_record = conn.execute('SELECT date_time FROM blood_pressure ORDER BY date_time DESC LIMIT 1').fetchone()

        if not latest_record:
            print("【DEBUG】データなし！")
            return json.dumps([])

        latest_date = latest_record["date_time"]

        try:
            latest_date_dt = datetime.strptime(latest_date, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            latest_date_dt = datetime.strptime(latest_date, '%Y-%m-%dT%H:%M')

        one_month_ago = (latest_date_dt - timedelta(days=30)).strftime('%Y-%m-%d')
        query = 'SELECT date_time, systolic, diastolic FROM blood_pressure WHERE date_time BETWEEN ? AND ? ORDER BY date_time'
        records = conn.execute(query, (one_month_ago, latest_date)).fetchall()

    conn.close()

    jst_data = []
    for record in records:
        jst_date_time = convert_to_jst(datetime.strptime(record["date_time"], '%Y-%m-%d %H:%M:%S'))
        jst_data.append({
            "date": jst_date_time,
            "systolic": record["systolic"],
            "diastolic": record["diastolic"]
        })

    print(f"【DEBUG】JST変換後のデータ: {jst_data}") 

    return json.dumps(jst_data)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_record(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM blood_pressure WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        systolic = request.form['systolic']
        diastolic = request.form['diastolic']
        note = request.form['note']

        # ✅ `date_time` を手動入力 or 未入力なら現在時刻
        date_time = request.form.get('date_time', '')
        if not date_time:
            date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # ✅ 秒まで統一
        else:
            try:
        # ✅ 最初に `'%Y-%m-%d %H:%M:%S'` フォーマットを試す
                date_time = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
        # ✅ ダメなら `'%Y-%m-%dT%H:%M'` を試して変換
                date_time = datetime.strptime(date_time, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db_connection()
        conn.execute('INSERT INTO blood_pressure (systolic, diastolic, date_time, note) VALUES (?, ?, ?, ?)',
                     (systolic, diastolic, date_time, note))
        conn.commit()
        conn.close()
        return redirect('/')

    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_record(id):
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM blood_pressure WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        systolic = request.form['systolic']
        diastolic = request.form['diastolic']
        note = request.form['note']

        conn.execute('UPDATE blood_pressure SET systolic = ?, diastolic = ?, note = ? WHERE id = ?',
                     (systolic, diastolic, note, id))
        conn.commit()
        conn.close()
        return redirect('/')

    conn.close()
    return render_template('edit.html', record=record)

if __name__ == '__main__':
    app.run(debug=True)