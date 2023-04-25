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
            role = request.form['user-type']
            if role == 'bidder':
                connection = sql.connect('database.db')
                cursor = connection.execute('SELECT * from bidders WHERE email=?;', (email, ))
                data = cursor.fetchone()
                print(data)
                if data is not None:
                    cursor2 = connection.execute('SELECT * from address WHERE address_id=?;', (data[5], ))
                    address_data = cursor2.fetchone()
                    print(address_data)
                    cursor2 = connection.execute('SELECT * from zipcode_info WHERE zipcode=?;', (address_data[1], ))
                    zipcode_data = cursor2.fetchone()
                    print(zipcode_data)
                    street_address = f'{address_data[2]} {address_data[3]} {zipcode_data[1]}, {zipcode_data[2]} {zipcode_data[0]}'
                    cursor.close()
                    cursor2.close()
                    connection.close()
                    return render_template('homepage.html', error=error, result=result, data=data, street_address=street_address)
                else:
                    error = 'invalid role selected'
            elif role == 'seller':
                connection = sql.connect('database.db')
                cursor = connection.execute('SELECT * from sellers WHERE email=?', (email, ))
                seller_data = cursor.fetchone()
                if seller_data is not None:
                    cursor2 = connection.execute('SELECT * from bidders WHERE email=?;', (email,))
                    bidder_data = cursor2.fetchone()
                    cursor3 = connection.execute('SELECT * from address WHERE address_id=?;', (bidder_data[5],))
                    address_data = cursor3.fetchone()
                    cursor2 = connection.execute('SELECT * from zipcode_info WHERE zipcode=?;', (address_data[1],))
                    zipcode_data = cursor2.fetchone()
                    street_address = f'{address_data[2]} {address_data[3]} {zipcode_data[1]}, {zipcode_data[2]} {zipcode_data[0]}'
                    cursor2 = connection.execute('SELECT * FROM credit_cards WHERE owner_email=?;', (seller_data[0], ))
                    credit_card_info = cursor2.fetchone()
                    card_num = credit_card_info[0][-4:]  # last four digits of card number
                    cursor.close()
                    cursor2.close()
                    cursor3.close()
                    connection.close()
                    return render_template('selling.html', error=error, result=result, seller_data=seller_data,
                                           bidder_data=bidder_data, street_address=street_address,
                                           card_num=card_num)
                else:
                    error = 'invalid role selected'
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

@app.route('/categories')
def categories():
    connection = sql.connect("database.db")
    cursor = connection.cursor()
    categories_list = cursor.execute('SELECT * FROM categories').fetchall()
    cursor.close()
    connection.close()
    return render_template('categories.html', categories=categories_list)

@app.route('/selling')
def selling():
    return render_template('selling.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/<item>')
def item_page(item):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * from auction_listings WHERE category = ?', (item, ))
    available_items_list = cursor.fetchall()
    return render_template("item.html", item_list=available_items_list)

if __name__ == "__main__":
    app.run(debug=True)

