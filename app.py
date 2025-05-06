from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('blood_pressure.db')
    conn.row_factory = sqlite3.Row
    return conn

# 🔹 JSTに変換する関数
def convert_to_jst(utc_time):
    jst_time = utc_time.replace(tzinfo=timezone.utc) + timedelta(hours=9)
    return jst_time.strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
    conn = get_db_connection()
    records = conn.execute('SELECT * FROM blood_pressure ORDER BY date_time DESC').fetchall()
    conn.close()

    # 🔹 JST変換を適用（辞書に変換してから変更）
    updated_records = []
    for record in records:
        record_dict = dict(record)  # 🔹 sqlite3.Row を辞書に変換
        record_dict['date_time'] = convert_to_jst(datetime.strptime(record_dict['date_time'], '%Y-%m-%d %H:%M:%S'))
        updated_records.append(record_dict)

    return render_template('index.html', records=updated_records)

# ✅ グラフ表示ページを追加（この位置が適切！）
@app.route('/chart')
def chart():
    return render_template('chart.html')

import json
from datetime import datetime
import pytz  # 🔹 タイムゾーン変換用

@app.route('/chart-data')
def get_chart_data():
    conn = get_db_connection()

    # 🔹 最新のデータがある日付を取得
    latest_record = conn.execute('SELECT date_time FROM blood_pressure ORDER BY date_time DESC LIMIT 1').fetchone()
    
    if not latest_record:
        return json.dumps([])  # 🔹 データがない場合は空のリストを返す
    
    latest_date = latest_record["date_time"]  # 🔹 最新の日付
    one_month_ago = (datetime.strptime(latest_date, '%Y-%m-%d %H:%M:%S') - timedelta(days=30)).strftime('%Y-%m-%d')

    query = 'SELECT date_time, systolic, diastolic FROM blood_pressure WHERE date_time BETWEEN ? AND ? ORDER BY date_time'
    records = conn.execute(query, (one_month_ago, latest_date)).fetchall()
    conn.close()

    # 🔹 JSTに変換してデータを整理
    utc_tz = pytz.utc
    jst_tz = pytz.timezone("Asia/Tokyo")

    data = [{"date": datetime.strptime(record["date_time"], "%Y-%m-%d %H:%M:%S")
                        .replace(tzinfo=utc_tz)
                        .astimezone(jst_tz)
                        .strftime("%Y/%m/%d %H:%M"),
             "systolic": record["systolic"],
             "diastolic": record["diastolic"]}
            for record in records]

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

        conn = get_db_connection()
        conn.execute('INSERT INTO blood_pressure (systolic, diastolic, note) VALUES (?, ?, ?)',
                     (systolic, diastolic, note))
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