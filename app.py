from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('blood_pressure.db')
    conn.row_factory = sqlite3.Row
    return conn

# 🔹 JSTに変換する関数
import pytz

def convert_to_jst(utc_time):
    utc_tz = pytz.utc
    jst_tz = pytz.timezone("Asia/Tokyo")

    # ✅ UTCとして認識した後、JSTへ変換
    utc_time = utc_time.replace(tzinfo=utc_tz)
    jst_time = utc_time.astimezone(jst_tz)

    print(f"【DEBUG】JST変換後（修正済）: {jst_time.strftime('%Y-%m-%d %H:%M:%S')}")  # ✅ 確認用
    return jst_time.strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
    conn = get_db_connection()
    records = conn.execute('SELECT * FROM blood_pressure ORDER BY date_time DESC').fetchall()
    conn.close()

    updated_records = []
    for record in records:
        record_dict = dict(record)

        try:
            dt_obj = datetime.strptime(record_dict['date_time'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            dt_obj = datetime.strptime(record_dict['date_time'], '%Y-%m-%dT%H:%M')

        # ✅ データベースの時間が既にJSTなら、変換しない！
        record_dict['date_time'] = dt_obj.strftime('%Y-%m-%d %H:%M:%S')

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
    latest_record = conn.execute('SELECT date_time FROM blood_pressure ORDER BY date_time DESC LIMIT 1').fetchone()
    
    if not latest_record:
        print("【DEBUG】データなし！")  # ✅ デバッグ用
        return json.dumps([])

    latest_date = latest_record["date_time"]

    try:
        # ✅ まず `'%Y-%m-%d %H:%M:%S'` のフォーマットで変換を試す
        latest_date_dt = datetime.strptime(latest_date, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        # ✅ ダメなら `'%Y-%m-%dT%H:%M'` で再試行
        latest_date_dt = datetime.strptime(latest_date, '%Y-%m-%dT%H:%M')

    # ✅ 1ヶ月前のデータ範囲を計算
    one_month_ago = (latest_date_dt - timedelta(days=30)).strftime('%Y-%m-%d')

    query = 'SELECT date_time, systolic, diastolic FROM blood_pressure WHERE date_time BETWEEN ? AND ? ORDER BY date_time'
    records = conn.execute(query, (one_month_ago, latest_date)).fetchall()
    conn.close()

    data = [{"date": record["date_time"], "systolic": record["systolic"], "diastolic": record["diastolic"]} for record in records]

    print(f"【DEBUG】取得データ: {data}")  # ✅ ターミナルで確認！

    return json.dumps(data)

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