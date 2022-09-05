import os
from cs50 import SQL
import requests
from flask import Flask, flash, jsonify, redirect, render_template, url_for, request, session
from flask_session import Session

# Configuring the app. A session is created to remember users
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///huts.db")

# API key: EsiDVBUxWV1HTRIWIxjxw99L4uKEVLzkIVrzVJbf
# The API key is saved to an environment variable:
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

# A global variable containing every region is created, so each function can
# pass it to the html template. (Probably a better way to do this?)
r = db.execute("SELECT region FROM huts ORDER BY region")
regions = []
for dic in r:
    if dic['region'] not in regions:
        regions.append(dic['region'])

@app.route('/', methods=["GET", "POST"])
def index():
    '''From the index page users can search for huts and add
    them to their 'my huts' list or wishlist. The hut IDs will
    be added to the session.
    '''
    if request.method == 'POST':
        add_visited = request.form.get("addToMyHuts")
        add_wishlist = request.form.get("addToWishlist")
        if add_visited:
            if "visited" not in session:
                session["visited"] = []
            if "wishlist" not in session:
                session["wishlist"] = []
            if add_visited not in session['visited']:
                if add_visited in session["wishlist"]:
                    session['wishlist'].remove(add_visited)
                flash("Added to My Huts")
                session["visited"].append(add_visited)
                return redirect('/myhuts')
            flash("Already in My Huts")
            return redirect('/')

        if add_wishlist:
            if "wishlist" not in session:
                session["wishlist"] = []
            if add_wishlist not in session["wishlist"]:
                if add_wishlist in session["visited"]:
                    flash("Already in My Huts")
                    return redirect("/")
                flash("Added to wishlist")
                session["wishlist"].append(add_wishlist)
                return redirect('/wishlist')
            flash("Already in Wishlist")
            return redirect('/')
    else:
        return render_template("index.html", regions=regions)

@app.route('/browse')
def browse():
    '''When a user selects a region to browse from the navbar, the region
    is sent here via a get request, and then there's a redirect to 'browse_results'
    '''
    if request.method == 'GET':
        region = request.args.get("region")
        if region:
            return redirect(url_for('browse_results', region=region))
        return redirect('/')

@app.route('/browseresults/<region>', methods=['GET', 'POST'])
def browse_results(region):
    '''The selected region is sent here via 'browse' so that a URL is dynamically
    created for each region. This function will select all the huts from that region
    from the db and display them on the 'browse results' template.
    '''
    if request.method == "GET":
        huts = db.execute("SELECT * FROM huts WHERE region = ? ORDER BY name", region)
        return render_template("browse_results.html", huts=huts, region=region, regions=regions)

    add_visited = request.form.get("addToVisited")
    add_wishlist = request.form.get("addToWishlist")
    if add_visited:
        if "visited" not in session:
            session["visited"] = []
        if add_visited not in session['visited']:
            if add_visited in session["wishlist"]:
                session['wishlist'].remove(add_visited)
            flash("Added to My Huts")
            session["visited"].append(add_visited)
            return redirect(url_for('browse_results', region=region, regions=regions))
        flash("Already in My Huts")
        return redirect(url_for('browse_results', region=region, regions=regions))

    if add_wishlist:
        if "wishlist" not in session:
            session["wishlist"] = []
        if add_wishlist not in session["wishlist"]:
            if add_wishlist in session["visited"]:
                flash("Already in My Huts")
                return redirect(url_for('browse_results', region=region, regions=regions))
            flash("Added to Wishlist")
            session["wishlist"].append(add_wishlist)
            return redirect(url_for('browse_results', region=region, regions=regions))
        flash("Already in Wishlist")
        return redirect(url_for('browse_results', region=region, regions=regions))


@app.route('/myhuts', methods=["GET", "POST"])
def my_huts():
    '''Selects from the db all the hut IDs stored in the 'visited' variable in the
    session and returns the hut details to the 'my huts' template.
    '''
    huts = []
    if request.method == "GET":
        if 'visited' in session:
            huts = db.execute("SELECT * FROM huts WHERE id IN (?)", session['visited'])
        return render_template('myhuts.html', huts=huts, regions=regions)

    remove = request.form.get("remove")
    if remove:
        session["visited"].remove(remove)
    return redirect("/myhuts")

@app.route('/wishlist', methods=["GET", "POST"])
def wishlist():
    '''Selects from the db all the hut IDs from the 'wishlist' variable in the
    session and returns the hut details to the 'wishlist' template.
    '''
    huts = []
    if request.method == "GET":
        if 'wishlist' in session:
            huts = db.execute("SELECT * FROM huts WHERE id IN (?)", session['wishlist'])
        return render_template('wishlist.html', huts=huts, regions=regions)

    remove = request.form.get("remove")
    if remove:
        session["wishlist"].remove(remove)
    return redirect("/wishlist")

@app.route('/hutsearch')
def hut_search():
    '''As users search for a hut by name, the huts database is searched using the input
    along with wildcards. The results are returned as JSON and Javascript is used to update
    the HTML with the search results'''
    q = request.args.get('q')
    if q:
        huts = db.execute("SELECT id, name FROM huts WHERE name LIKE ? LIMIT 50", "%" + q + "%")
    else:
        huts = []
    return jsonify(huts)

@app.route('/checkalerts', methods=['GET', 'POST'])
def check_alerts():
    '''Users can search for a hut, which will send the hut ID to this function via post.
    The alerts API will be called, using the hut id and any alerts will be returned with
    the 'alerts' template.
    '''
    if request.method == "GET":
        return render_template("alerts.html", regions=regions)

    hut_id = request.form.get("hut")
    if hut_id:
        hut = db.execute("SELECT name FROM huts WHERE id = (?)", hut_id)
        try:
            key = os.environ.get("API_KEY")
            response = requests.get(f'https://api.doc.govt.nz/v2/huts/{hut_id}/alerts',
                                    headers={'x-api-key': key})
            response.raise_for_status()
        except requests.RequestException:
            return None
        try:
            alert = response.json()
            hut_alert = []
            if alert:
                hut_alert = {
                    'name': alert[0]['name'],
                    'date': alert[0]['alerts'][0]['displayDate'],
                    'heading': alert[0]['alerts'][0]['heading'],
                    'detail': alert[0]['alerts'][0]['detail'].replace('<p>', '')
                                                            .replace('</p>', '')
                                                            .replace('<ul>', '')
                                                            .replace('</ul>', '')
                                                            .replace('<li>', '')
                                                            .replace('</li>', ',')
                                                            .replace('&rsquo;', "'")
                }
                return render_template('alerts.html', alert=hut_alert, hut=hut, regions=regions)
            return render_template('alerts.html', alert=hut_alert, hut=hut, regions=regions)
        except (KeyError, TypeError, ValueError):
            return None


if __name__ == "__main__":
    app.run(debug=True)
