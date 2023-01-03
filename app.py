from flask import Flask, render_template, request, jsonify
from data import operators, materials

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

    return render_template('index.jinja', operators=operators, materials=materials)

@app.route("/searchdata",methods=["POST","GET"])
def searchdata():
    if request.method == 'POST':
        search_word = request.form['search_word']
        print(search_word)
        # cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # query = "SELECT * from tblprogramming WHERE title LIKE '%{}%' ORDER BY id DESC LIMIT 20".format(search_word)
        # cur.execute(query)
        # programming = cur.fetchall()
    return jsonify({'data': render_template('response.html')})

if __name__ == "__main__":
    app.run(debug=True)
