from flask import Flask, render_template, request, session, redirect
import sqlite3 as sql
from passlib.hash import sha256_crypt
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
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
        session['username'] = email
        if result:
            role = request.form['user-type']
            session['role'] = role
            if role == 'bidder':
                connection = sql.connect('database.db')
                cursor = connection.execute('SELECT * from bidders WHERE email=?;', (email, ))
                data = cursor.fetchone()
                if data is not None:
                    cursor2 = connection.execute('SELECT * from address WHERE address_id=?;', (data[5], ))
                    address_data = cursor2.fetchone()
                    cursor2 = connection.execute('SELECT * from zipcode_info WHERE zipcode=?;', (address_data[1], ))
                    zipcode_data = cursor2.fetchone()
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
    categories_list = cursor.execute('SELECT * FROM categories ORDER BY parent_category').fetchall()
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


@app.route('/bid/int:<item_num>', methods=['POST', 'GET'])
def bid(item_num):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * from bids WHERE listing_id=? ORDER BY bid_price ASC', (item_num,))
    bid_list = cursor.fetchall()
    cursor = connection.execute('SELECT * FROM auction_listings WHERE listing_id=?', (item_num,))
    item_info = cursor.fetchone()
    message = 'You have not placed a bid yet'
    max_bids = session.get('max_bids', item_info[8] - len(bid_list))
    previous_bidder = session.get('bidder', None)

    if bid_list:
        last_price = max(bid_list, key=lambda x: x[4])[4]
        session['previous_bid'] = last_price

    if request.method == 'POST':
        previous_bid = session.get('previous_bid', 0)
        current_bid = int(request.form['current_bid'])
        current_bidder = session.get('username', None)

        if current_bidder == previous_bidder:
            message = 'You have already placed a bid'
        elif current_bid >= previous_bid + 1:
            session['previous_bid'] = current_bid
            session['max_bids'] = max_bids - 1
            session['bidder'] = current_bidder
            if session['max_bids'] == 0:
                print(item_info[7])
                if int(item_info[7][1:]) <= current_bid:
                    message = 'Congratulations! You have won the auction!'  ##COMPARE WITH RESERVE PRICE
                else:
                    message = 'Sorry! This auction was unsuccessful.'
                cursor = connection.execute(
                    'UPDATE auction_listings SET status = 2 WHERE listing_id=?', (item_num,))
                connection.commit() ## Delist item
            else:  ##Write into DB
                message = f'Your current bid of {current_bid} has been accepted.'
            connection = sql.connect('database.db')
            cursor = connection.cursor()
            cursor.execute('SELECT MAX(bid_id) FROM bids')
            new_bid_id = cursor.fetchone()[0] + 1
            seller_email = item_info[0]
            listing_id = item_info[1]
            bidder_email = session.get('username')
            cursor.execute('INSERT INTO bids (bid_id, seller_email, listing_id, bidder_email, bid_price) VALUES (?,?,?,?,?)',
                            (new_bid_id, seller_email, listing_id, bidder_email, current_bid))
            connection.commit()
        else:
            message = f'Your current bid of {current_bid} is not valid.'
        max_bids = session.get('max_bids')
        cursor = connection.execute('SELECT * from bids WHERE listing_id=? ORDER BY bid_price ASC', (item_num,))
        bid_list = cursor.fetchall()
        connection.close()
    return render_template('bid.html', item_info=item_info, message=message, max_bids=max_bids, bid_list=bid_list)

@app.route('/view-listings', methods=['POST', 'GET'])
def view_listings():
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM auction_listings WHERE seller_email = ?', (session.get('username'), ))
    listing_data = cursor.fetchall()
    return render_template('view-listings.html', listing_data=listing_data)

@app.route('/update-status-inactive', methods=['POST','GET'])
def update_status_inactive():
    listing_id = request.form['listing-id']
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('UPDATE auction_listings SET status = 0 WHERE listing_id=?', (listing_id, ))
    connection.commit()
    connection.close()
    return redirect(request.referrer)

@app.route('/update-status-active', methods=['POST'])
def update_status_active():
    listing_id = request.form['listing-id']
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('UPDATE auction_listings SET status = 1 WHERE listing_id=?', (listing_id, ))
    connection.commit()
    connection.close()
    return redirect(request.referrer)

if __name__ == "__main__":
    app.run(debug=True)

