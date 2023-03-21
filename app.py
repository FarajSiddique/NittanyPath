from flask import Flask, render_template, request
import sqlite3 as sql
from passlib.hash import sha256_crypt

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/name', methods=['POST', 'GET'])
def name():
    error = None
    if request.method == 'POST':
        result = valid_name(request.form['username'], request.form['password'])
        if result:
            return render_template('homepage.html', error=error, result=result)
        else:
            error = 'invalid input name'
    return render_template('input.html', error=error)


def valid_name(username, password):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM users WHERE username = ?;', (username,))
    connection.commit()
    try:
        hashedPassword = cursor.fetchone()[1]
        matchedPassword = sha256_crypt.verify(password, hashedPassword)
    except:
        matchedPassword = None
    return matchedPassword

def hash_passwords():
    connection = sql.connect("database.db")
    cursor = connection.cursor()
    cursor2 = connection.cursor()
    passwords = cursor.execute('SELECT * FROM users;').fetchall()
    for passw in passwords:
        rowPassword = passw[1]
        hashedPassword = sha256_crypt.hash(rowPassword)
        cursor2.execute('UPDATE users SET hashedPass=? WHERE password=?;', (hashedPassword, rowPassword))
        connection.commit()
    connection.close()

if __name__ == "__main__":
    app.run()


