# NittanyPath

This document is the readme for the phase 2 progress review of the LionAuction application. This application so far has perfected the user login and 
password authentication method.

Users, as long as they are a user within the given database, are able to log in and their information is stored in a table with the username (user's email) and hashed password.
The username is the primary key of the table and only the hashed password is stored and not the plain text password in order to keep each user's information safe and secure.

When a user logs in succesfully, the plaintext password is authenticated and verified with the hashed password stored within our database. We verify it using the sha256_crypt.verify method.

This method takes in two parameters. The plain text password that was inputted and the hashed password we have stored in our database. It will verify that the hashed password 
matches the plaintext password and will send the user to the corresponding homepage on success. 

If a failure occurs, the user is met with a message in red saying that it was invalid.
 

