from model import magic
from flask import Flask, render_template,request, Response
import sqlite3
import json
import threading
from constants import CURRENT_YEAR, DATABASE_PATH
import datetime

app = Flask(__name__)
database_path = DATABASE_PATH


@app.route('/')
def homepage():
   return render_template("test.html",content="This is gruop 19 Post")


@app.route('/refresh')
def start_new_prediction():
    t = threading.Thread(target=magic)
    t.daemon = True
    t.start()

    response = Response(json.dumps("Process started."))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

import pandas as pd

@app.route('/rankings')
def rankings():
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()    
    cur.execute('SELECT * FROM prediction_rankings')
    rankings_raw = cur.fetchall()
    columns = [x[0] for x in cur.description]
    rankings = []
    for ranking in rankings_raw:
        ranking_on_date = {}
        for column, data in zip(columns[1:], ranking[1:]):
            ranking_on_date[column] = data
        rankings.append(ranking_on_date)

    # Chuyển đổi dữ liệu thành DataFrame
    df = pd.DataFrame(rankings)

    # Tạo bảng HTML Bootstrap
    table_html = df.to_html(index=False, classes='table table-striped table-bordered')

    # Tạo response
    response = Response(table_html)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response



@app.route('/summary')
def summary():
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()    
    cur.execute('SELECT * FROM summary')
    summary = cur.fetchall()[0]
    columns = [x[0] for x in cur.description]
    summary_dict = {}
    for column, data in zip(columns, summary):
        summary_dict[column] = data
    
    response = Response(json.dumps(summary_dict))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

import pandas as pd
from flask import Flask, Response

@app.route('/predictions')
def predictions():
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()

    # Thêm mã HTML cho trang chủ
    home_button = '<a class="btn btn-primary" href="/">Home Page</a>'
    
    query = 'SELECT * FROM prediction_results'
    req_params_raw = request.data
    if req_params_raw:
        req_params = json.loads(req_params_raw)
        query_type = 'AND' if 'against' in req_params else 'OR'
        teams = ["'" + team + "'" for team in req_params['teams']]
        teams = ",".join(teams)
        query += ' WHERE HomeTeam IN ({}) {} AwayTeam IN ({})'.format(teams, query_type, teams)
        
    cur.execute(query)
    predictions_raw = cur.fetchall()
    columns = [x[0] for x in cur.description]
    predictions = []
    for prediction in predictions_raw:
        prediction_match = {}
        for column, data in zip(columns[1:], prediction[1:]):
            prediction_match[column] = data
        predictions.append(prediction_match)

    df = pd.DataFrame(predictions)
    
    # Thêm cột số thứ tự
    df.insert(0, 'STT', range(1, len(df) + 1))

    # Chuyển đổi DataFrame thành HTML table với lớp CSS 'table' của Bootstrap
    table_html = df.to_html(index=False, classes='table table-striped table-bordered')

    # Thêm mã CSS của Bootstrap vào phản hồi
    response = Response(
        f"""
        <html>
        <head>
            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
        </head>
        <body>
            <div class="container">
                <h2>Predictions</h2>
                {home_button}  <!-- Thêm nút Trang chủ -->
                <br><br>
                {table_html}
            </div>
        </body>
        </html>
        """
    )
    response.headers['Content-Type'] = 'text/html'
    return response



from flask import Flask, Response, jsonify

@app.route('/previous_results')
def previous_results():
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    
    season_start = datetime.datetime(CURRENT_YEAR, 7, 1).date().strftime('%Y-%m-%d')
    query = 'SELECT * FROM previous_results WHERE Date > "{}"'.format(season_start)
    req_params_raw = request.data
    if req_params_raw:
        req_params = json.loads(req_params_raw)
        query_type = 'AND' if 'against' in req_params else 'OR'
        teams = ["'" + team + "'" for team in req_params['teams']]
        teams = ",".join(teams)
        query += ' AND (HomeTeam IN ({}) {} AwayTeam IN ({}))'.format(teams, query_type, teams)
        
    cur.execute(query)
    previous_results_raw = cur.fetchall()
    columns = [x[0] for x in cur.description]
    previous_results = []
    for result in previous_results_raw:
        match_result = {}
        for column, data in zip(columns[1:], result[1:]):
            match_result[column] = data
        previous_results.append(match_result)

    return jsonify(previous_results)

if __name__ == '__main__':
	app.run(debug=True)
