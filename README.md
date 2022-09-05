# HUT BAGGER
#### Video Demo: https://youtu.be/O2UR54_2axI
#### Description:
This project is a web app created with flask where users can keep track of DOC huts they’ve visited.
Users can search or browse for huts, add huts to a wishlist and can also check huts for any alerts.

##### create_db.py
This script creates the database that will hold all of the huts and some details on each hut. The DOC
huts API is called and all the huts are added to a JSON object. A database is then created using SQLite.
I didn't use the CS50 library for thisas I was interested to learn how to use SQL without it. The 
regions for some huts are blank, so these have been replaced with 'other' to avoid any issues.  Some
regions contain a forward slash, which have also been replaced to avoid issues when using them in URLs. 
For each hut, another API is called to add extra details.

##### app.py
First the app is configured and a session is created. The app uses a flask session to keep track of
huts the user adds. This was chosen over having the user create an account for simplicity, and there's
no sensitive data involved. I'd consider changing thisin the future as it's more common now for people
to clear cookies.
A global variable containing every region is created, so each function can pass it to the html template
and the region dropdown can be accessed on the navbar from every page. There is probably a better way to 
do this as adding it to every HTML template creates a lot of repetition.

###### Index
From the index page users can search for huts and add them to their 'my huts' list or wishlist. As users 
search for a hut by name, the huts database is searched using the input along with wildcards. The results
are returned as JSON and Javascript is used to update the HTML with the search results. The hut IDs will
be added to the session. When a user adds a hut, they'll be redirected to the 'My Huts' page or 'wishlist'
page, and an alert will be flashed to tell the user the hut ahs been added to their list. There is also an
alert if a user tries to add a hut that is already in their list. There is also a navbar, which is visible
on each page, where the user can navigate to each page.

###### My Huts & Wishlist
For each hut ID stored in the session, the hut names and locations are selected from the database and
displayed in a table. The huts can be removed from the table, and a 'more info' button directs the  user
to the hut's page on the DOC website.

###### Browse
The user can browse all huts in a particular region by using a dropdown on the navbar. When a region is
selected, all the huts from that region are selected from the database and displayed in a table. The URL
for each region is dynamically created.

###### Check Alerts
Users can search for a hut, which will send the hut ID to the check alerts function via post. The alerts API
will be called using the hut id and any alerts will be returned with the 'alerts' template.