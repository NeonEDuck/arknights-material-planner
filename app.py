from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL, MySQLdb

from sqlalchemy.sql import func

app = Flask(__name__)

# app.secret_key = "caircocoders-ednalan"
        
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_DB'] = 'testingdb'
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('base.html')

@app.route("/searchdata",methods=["POST","GET"])
def searchdata():
    if request.method == 'POST':
        search_word = request.form['search_word']
        print(search_word)
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT * from tblprogramming WHERE title LIKE '%{}%' ORDER BY id DESC LIMIT 20".format(search_word)
        cur.execute(query)
        programming = cur.fetchall()
    return jsonify({'data': render_template('response.html', programming=programming)})

if __name__ == "__main__":
    app.run(debug=True)

