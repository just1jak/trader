from flask import Flask, render_template, request, jsonify
import subprocess
import json
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_analysis', methods=['POST'])
def run_analysis():
    try:
        # Run the scrapers
        house_result = subprocess.run(['python3', '../scrape_house.py'], 
                                      capture_output=True, text=True, cwd='..')
        senate_result = subprocess.run(['python3', '../scrape_senate.py'], 
                                       capture_output=True, text=True, cwd='..')
        
        # Run the backtest
        backtest_result = subprocess.run(['python3', '../backtest.py'], 
                                         capture_output=True, text=True, cwd='..')
        
        # Load the generated trade files for display
        house_trades = []
        senate_trades = []
        if os.path.exists('../house_trades.json'):
            with open('../house_trades.json', 'r') as f:
                house_trades = json.load(f)
        if os.path.exists('../senate_trades.json'):
            with open('../senate_trades.json', 'r') as f:
                senate_trades = json.load(f)
        
        # Load backtest results if available (we'll parse the output for simplicity)
        # In a more robust version, we would have the backtest script return JSON
        backtest_output = backtest_result.stdout
        
        return jsonify({
            'status': 'success',
            'house_trades': house_trades,
            'senate_trades': senate_trades,
            'backtest_output': backtest_output,
            'house_log': house_result.stdout,
            'senate_log': senate_result.stdout,
            'backtest_log': backtest_result.stdout
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)