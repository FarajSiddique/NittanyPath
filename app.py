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
        email = request.form['username']
        if result:
            connection = sql.connect('database.db')
            cursor = connection.execute('SELECT * from bidders WHERE email=?;', (email, ))
            data = cursor.fetchone()
            print(data)
            cursor2 = connection.execute('SELECT * from address WHERE address_id=?;', (data[5], ))
            address_data = cursor2.fetchone()
            print(address_data)
            return render_template('homepage.html', error=error, result=result, data=data, addressData=address_data)
        else:
            error = 'invalid input name'
    return render_template('input.html', error=error)

def valid_name(username, password):
    ## Check validity of plain text password and stored hashed password
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
    ## Script that was ran to convert all plain text passwords given in CSV to hashed form
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

@app.route('/bidding')
def bidding():
    return render_template('bidding.html')

@app.route('/selling')
def selling():
    return render_template('selling.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == "__main__":
    app.run()


