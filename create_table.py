# Author: Sean Brown, University of Massachusetts Amherst
# Date: 4/4/2023
# Description: This python script assumes that you already have
# a database.db file at the root of your workspace.
# This python script will CREATE a table called students 
# in the database.db using SQLite3 which will be used
# to store the data collected by the forms in this app
# Execute this python script before testing or editing this app code. 
# Open a python terminal and execute this script:
# python create_table.py

import sqlite3

con = sqlite3.connect('users.db')

# creates table to store users
con.execute("CREATE TABLE IF NOT EXISTS profiles(user_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, password TEXT, phoneNumber TEXT, email TEXT)") 

# creates table to store anchors to associate with users
con.execute("CREATE TABLE IF NOT EXISTS anchors (anchor_id INTEGER PRIMARY KEY, user_id INTEGER, anchor_name TEXT, latitude REAL, longitude REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES profiles(user_id))")

con.execute("CREATE TABLE IF NOT EXISTS tags (tag_id INTEGER PRIMARY KEY, user_id INTEGER, tag_name TEXT, latitude REAL, longitude REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES profiles(user_id))")

con.execute("CREATE TABLE IF NOT EXISTS tag_locations (location_id INTEGER PRIMARY KEY AUTOINCREMENT, tag_id INTEGER, tag_name TEXT, latitude REAL, longitude REAL, mode TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (tag_id) REFERENCES tags(tag_id))")

con.close()
