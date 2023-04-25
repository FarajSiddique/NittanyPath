from flask import Flask, render_template, request, session, redirect
import sqlite3 as sql
from passlib.hash import sha256_crypt
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16) ## Authenticate session per user to ensure security
host = 'http://127.0.0.1:5000/'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/name', methods=['POST', 'GET'])
def name():
    error = None
    if request.method == 'POST':
        result = valid_name(request.form['username'], request.form['password']) ##Fetch username and password and check if valid
        email = request.form['username']
        session['username'] = email  ##  Store username for future reference when performing actions
        if result:
            role = request.form['user-type']
            session['role'] = role  ##  store Role to check in future actions
            if role == 'bidder': ## Check if role is bidder, if so fetch bidder data, address data and zipcode data
                connection = sql.connect('database.db')
                cursor = connection.execute('SELECT * from bidders WHERE email=?;', (email, ))
                data = cursor.fetchone()
                if data is not None:
                    cursor2 = connection.execute('SELECT * from address WHERE address_id=?;', (data[5], ))
                    address_data = cursor2.fetchone()
                    cursor2 = connection.execute('SELECT * from zipcode_info WHERE zipcode=?;', (address_data[1], ))
                    zipcode_data = cursor2.fetchone()
                    street_address = f'{address_data[2]} {address_data[3]} {zipcode_data[1]}, {zipcode_data[2]} {zipcode_data[0]}'
                    ## Format string to show proper street address
                    cursor.close()
                    cursor2.close()
                    connection.close()
                    return render_template('homepage.html', error=error, result=result, data=data, street_address=street_address)
                else: ## If data is none, user is not a bidder
                    error = 'invalid role selected'
            elif role == 'seller':  ## If role is seller, fetch seller data, bidder data, address data, zip code info and
                                    ## payment info
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
                else: ## If seller data is none, user is not a seller
                    error = 'invalid role selected'
            else: ## Else, user is a helpdeskIT staff. Fetch request tickets if any and also position he/she serves
                connection = sql.connect('database.db')
                cursor = connection.execute('SELECT * from helpdesk WHERE email=?', (email,))
                helpdesk_data = cursor.fetchone()
                if helpdesk_data is not None:
                    cursor = connection.execute('SELECT * from requests WHERE helpdesk_staff_email=?', (email,))
                    request_tickets = cursor.fetchall()
                    return render_template('helpdesk.html', helpdesk_data=helpdesk_data, request_tickets=request_tickets)
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
def categories(): ## Grab all categories and order by parent category
    connection = sql.connect("database.db")
    cursor = connection.cursor()
    categories_list = cursor.execute('SELECT * FROM categories ORDER BY parent_category').fetchall()
    cursor.close()
    connection.close()
    return render_template('categories.html', categories=categories_list)

@app.route('/list-item-dashboard', methods=['POST', 'GET'])
def list_item_page(): ## Logic for listing an item here. First grab category list.
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    categories_list = cursor.execute('SELECT * FROM categories ORDER BY parent_category').fetchall()
    message = ""
    if request.method == "POST":
        username = session.get('username')
        connection = sql.connect('database.db')
        cursor = connection.cursor()
        cursor.execute('SELECT MAX(listing_id) FROM auction_listings')
        new_listing_id = cursor.fetchone()[0] + 1
        category = request.form['category_name']
        auction_title = request.form['auction_title']
        product_name = request.form['product_name']
        product_description = request.form['description']
        quantity = request.form['quantity']
        reserve_price = request.form['reserve_price']
        max_bids = request.form['max_bids']
        ## Fetch form info. Create new listing id that is one bigger than the max id in database
        new_category = connection.execute(
            'INSERT INTO auction_listings (seller_email, listing_id, category, auction_title,'
            'product_name, product_description, quantity, reserve_price, max_bids, status) '
            'VALUES (?,?,?,?,?,?,?,?,?,?)', (username, new_listing_id, category, auction_title,
                                             product_name, product_description, quantity,
                                             reserve_price, max_bids, 1))
        message = "Thank you for posting an item!"
        connection.commit()
        cursor.close()
        connection.close()
    return render_template('list-item.html', categories_list=categories_list, message=message)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/<item>')
def item_page(item): ## Display all items for auction in a particular category
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * from auction_listings WHERE category = ?', (item, ))
    available_items_list = cursor.fetchall()
    return render_template("item.html", item_list=available_items_list)


@app.route('/bid/int:<item_num>', methods=['POST', 'GET'])
def bid(item_num): ## Bidding logic here. First grab all previous bids.
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * from bids WHERE listing_id=? ORDER BY bid_price ASC', (item_num,))
    bid_list = cursor.fetchall()
    ## Grab auction listing info for particular listing id
    cursor = connection.execute('SELECT * FROM auction_listings WHERE listing_id=?', (item_num,))
    item_info = cursor.fetchone()
    message = 'You have not placed a bid yet'
    ## max bids is defaulted to max bids - the previous amount of bids placed on the item in case a user has already
    ## bidded on it.
    max_bids = session.get('max_bids', item_info[8] - len(bid_list))
    ## Keep track of previous bidder. Defaulted to None
    previous_bidder = session.get('bidder', None)

    if bid_list:
        ## Grab last highest bid amount from bid list. Store it in 'previous_bid' to keep track of it
        last_price = max(bid_list, key=lambda x: x[4])[4]
        session['previous_bid'] = last_price

    if request.method == 'POST':
        ## Grab previous bid. Defaulted to zero
        previous_bid = session.get('previous_bid', 0)
        ## Grab current bid amount from form
        current_bid = int(request.form['current_bid'])
        ## Grab current user
        current_bidder = session.get('username', None)

        if current_bidder == previous_bidder: ## Check if user placed a bid previously. Must wait for another user
                                            # to bid first
            message = 'You have already placed a bid'
        elif current_bid >= previous_bid + 1: ## Check if bid is one or more higher than previous
            session['previous_bid'] = current_bid
            session['max_bids'] = max_bids - 1 ## Update max bids
            session['bidder'] = current_bidder
            if session['max_bids'] == 0: ## Check if any bids remaining
                if int(item_info[7][1:]) <= current_bid: ## Check if higher than reserve price. If so, auction successful
                    message = 'Congratulations! You have won the auction!'  ##COMPARE WITH RESERVE PRICE
                else: ## Auction failed. Reserve price higher than winning bid.
                    message = 'Sorry! This auction was unsuccessful.'
                ## Change status of item to sold
                cursor = connection.execute(
                    'UPDATE auction_listings SET status = 2 WHERE listing_id=?', (item_num,))
                connection.commit() ## Delist item
            else:  ##Write into DB the bid information
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
def view_listings(): ## View listings a seller currently has up
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM auction_listings WHERE seller_email = ?', (session.get('username'), ))
    listing_data = cursor.fetchall()
    return render_template('view-listings.html', listing_data=listing_data)

@app.route('/update-status-inactive', methods=['POST','GET'])
def update_status_inactive(): ## Update listing status from active to inactive
    listing_id = request.form['listing-id']
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('UPDATE auction_listings SET status = 0 WHERE listing_id=?', (listing_id, ))
    connection.commit()
    connection.close()
    return redirect(request.referrer)

@app.route('/update-status-active', methods=['POST'])
def update_status_active(): ## Update listing status from inactive to active
    listing_id = request.form['listing-id']
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('UPDATE auction_listings SET status = 1 WHERE listing_id=?', (listing_id, ))
    connection.commit()
    connection.close()
    return redirect(request.referrer)

if __name__ == "__main__":
    app.run(debug=True)

