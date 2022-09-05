'''This script creates a database of all the huts, by
calling the DOC huts API. For each hut, another API is called to add
extra details. The regions for some huts are blank, so these have been replaced
with 'other' to avoid any issues. Some regions contain a forward slash, which
have also been replaced to avoid issues when using them in URLs.
'''
import os
import sqlite3
import requests

if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

# Contacting API and making a JSON object of all DOC huts
try:
    key = os.environ.get("API_KEY")
    hutsResponse = requests.get('https://api.doc.govt.nz/v2/huts?coordinates=wgs84',
                                headers={'x-api-key': key})
    hutsResponse.raise_for_status()
except requests.exceptions.RequestException as err:
    raise SystemExit(err) from err
huts = hutsResponse.json()

# Make a database connection and create a table
con = sqlite3.connect('huts.db')
cur = con.cursor()

cur.execute('''
    CREATE TABLE huts
    (id INTEGER PRIMARY KEY, name TEXT, region TEXT, place TEXT, link TEXT, lon REAL, lat REAL)''')

#Adding everything to the database
for hut in huts:
    # Change blank regions to 'Other'
    if hut['region'] == None:
        hut['region'] = 'Other'
    # Call another API to get more details to each hut
    hut_id = hut['assetId']
    detailsResponse = requests.get(f'https://api.doc.govt.nz/v2/huts/{hut_id}/detail',
                                    headers={'x-api-key': key})
    details = detailsResponse.json()
    if 'place' not in details or 'staticLink' not in details:
        details['place'] = "No details available"
        details['staticLink'] = "-"
    cur.execute(
        "INSERT INTO huts VALUES (?, ?, ?, ?, ?, ?, ?)",
        (hut['assetId'], hut['name'], hut['region'].replace("/", " and "),
        details['place'], details['staticLink'], hut['lon'], hut['lat']))

con.commit()
con.close()
