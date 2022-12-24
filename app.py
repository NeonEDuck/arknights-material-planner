from flask import Flask, render_template
from config import DEBUG, PORT

app = Flask(__name__)
app.debug = DEBUG

@app.route('/')
def index():
    return render_template('index.jinja')

if __name__ == '__main__':
    app.run('0.0.0.0', port=PORT)