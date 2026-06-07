import subprocess, json, os, sqlite3, datetime
from flask import Flask, render_template, request, jsonify, g

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), '..', 'congress_trades.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('../db_schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def run_scraper(script):
    result = subprocess.run(['python3', os.path.join('..', script)], capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def run_backtest():
    result = subprocess.run(['python3', os.path.join('..', 'backtest.py')], capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    house_out, house_err, house_code = run_scraper('scrape_house.py')
    senate_out, senate_err, senate_code = run_scraper('scrape_senate.py')
    return jsonify({
        'house': {'output': house_out, 'error': house_err, 'code': house_code},
        'senate': {'output': senate_out, 'error': senate_err, 'code': senate_code}
    })

@app.route('/backtest', methods=['POST'])
def backtest():
    out, err, code = run_backtest()
    return jsonify({'output': out, 'error': err, 'code': code})

@app.route('/run_all', methods=['POST'])
def run_all():
    # scrape house & senate
        house_out, house_err, house_code = run_scraper('scrape_house.py')
        senate_out, senate_err, senate_code = run_scraper('scrape_senate.py')
    # backtest
        backout, berr, bcode = run_backtest()
    return jsonify({
        'house': {'output': house_out, 'error': house_err, 'code': house_code},
        'senate': {'output': senate_out, 'error': senate_err, 'code': senate_code},
        'backtest': {'output': backout, 'error': berr, 'code': bcode}
    })

if __name__ == '__main__':
    # init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)