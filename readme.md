This LionAuction application is built primarily on Python and Flask
with HTML and CSS for the website design. 

When a user first launches the application, they are routed to '/'
This route welcomes the user and prompts them to login with valid
credentials

The '/name' route prompts the user to input a valid username and password.
These credentials are checked within our SQLite table 'users' where we store
the username (email) and a hashed version of the password.

The user is then redirected to their respective dashboard depending on the role
he/she has chosen. 

If the user is a bidder. The user can view a list of categories to choose from.
When chosen, a user can see if any available listings are available to bid for in 
the category. 

If a user decides to enter the bidding process, they must enter at least one higher
than the previous bid. The user cannot bid again until another user has placed a bid

Once the max bids amount reaches zero, the most recent bid is compare to the 
reserve price the seller has set for the item. If it is higher, the auction is 
successful and the user wins the item. Otherwise, the auction has failed
and the seller does not sell the item.



If the user is a seller, the user can view a list of items that they currently
have put up for auction. The user can click a button to quickly change the status
of the listing to active or inactive.

The user can also put up a new listing using the listing form provided.


If a user is a HelpDesk IT staff, the user is prompted to thier respective portal.
The user's username and position is shown along with the request tickets he/she 
has active.