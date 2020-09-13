from flask import Flask, jsonify
from polyinpoly import data

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/wpc/excessive_rainfall')
def excessive_rainfall():
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)