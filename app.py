from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import sqlite3
from formsubmission import RegistrationForm
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import math
from flask_session import Session  # ✅ Import Flask-Session
from flask_cors import CORS


app = Flask(__name__)
app.secret_key = "__privatekey__"

@app.route('/') # home page
def Home():
    return render_template('home.html')

# ————————————————————————————————————————————————- SESSION ————————————————————————————————————————————————

CORS(app, supports_credentials=True)  # ✅ Allow iOS to send session cookies

# Configure Flask to use server-side sessions
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"  # Use "filesystem" instead of default cookies
Session(app)  # ✅ Initialize the session


# CHECK USER SESSION
@app.route('/session_check', methods=['GET'])
def session_check():
    user_id = session.get('user_id')
    user_name = session.get('user_name')

    if user_id:
        return jsonify({"message": "User session active", "user_id": user_id, "user_name": user_name}), 200
    else:
        return jsonify({"error": "No active session"}), 401
    

# ——————————————————————————————————————————————— LOGIN & REGISTRATION ———————————————————————————————————————————————

# LOGIN
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    con = sqlite3.connect('users.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM profiles WHERE name=?", (username,))
    user = cur.fetchone()
    con.close()

    if user is None or not check_password_hash(user[2], password):  
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user_id'] = user[0]  # ✅ Store user_id in session
    session['user_name'] = username  # ✅ Store username in session

    print(f"🟢 Session Data: {session}")  # ✅ Debug: Print session contents
    return jsonify({'message': 'Login successful', 'user_id': user[0], 'user_name': username}), 200

# LOGOUT
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # ✅ This removes all session data
    return jsonify({"message": "Logout successful"}), 200

# REGISTRATION PAGE
@app.route('/registration', methods=['POST'])
def registration():
    try:
        # Get data from the incoming JSON request
        data = request.get_json()

        # Get the fields from the JSON data
        userName = data['username']
        passWord = data['password']
        phoneNumber = data['phoneNumber']
        email = data['email']

        # Hash the password
        hashed_password = generate_password_hash(passWord)

        # Check if the user already exists
        con = sqlite3.connect('users.db')
        c = con.cursor()
        c.execute("SELECT * FROM profiles WHERE name=?", (userName,))
        existing_user = c.fetchone()

        if existing_user:
            # If the user already exists, return an error message
            con.close()
            return jsonify({'error': 'User already exists. Please try a new username.'}), 409
        
        # If the user does not exist, proceed with registration
        c.execute("INSERT INTO profiles (name, passWord, phoneNumber, email) VALUES (?, ?, ?, ?)",
                  (userName, hashed_password, phoneNumber, email))
        con.commit()
        con.close()

        # Return success message after registration
        return jsonify({'message': 'Registration successful, you can now log in.'}), 201
    
    except Exception as e:
        # Catch any unexpected errors and return a response
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

# —————————————————————————————————————————————————————— ANCHORS ——————————————————————————————————————————————————————

# ADD ANCHOR ROUTE
@app.route('/add_anchor', methods=['POST'])
def add_anchor_to_dashboard():
    # Extract data from the incoming JSON payload
    data = request.get_json()

    # Get user_id from session (user is logged in)
    user_id = session.get('user_id')
    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401  # Unauthorized if no user is logged in

    # Extract individual data fields from the received JSON
    anchor_id = data.get('anchor_id') # user-defined
    anchor_name = data.get('anchor_name')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    # Check if all required data was received
    if anchor_id and anchor_name and latitude and longitude:
        try:
            # Insert the received anchor data into the 'anchors' table
            con = sqlite3.connect('users.db')
            c = con.cursor()
            c.execute("""INSERT INTO anchors (anchor_id, user_id, anchor_name, latitude, longitude, created_at) 
                         VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                      (anchor_id, user_id, anchor_name, latitude, longitude))
            con.commit()

            # Get the ID of the newly inserted anchor
            anchor_id = c.lastrowid

            con.close()

            # Return a success response to the frontend with the server-generated ID
            return jsonify({'message': 'Anchor successfully added to dashboard!', 'anchor_id': anchor_id}), 201
        except Exception as e:
            # In case of an error, return an error response
            return jsonify({'error': f'Error occurred while adding anchor: {str(e)}'}), 500
    else:
        # If any of the required fields are missing, return a bad request error
        return jsonify({'error': 'Missing data (anchor_name, latitude, or longitude)'}), 400



# EDIT ANCHOR PAGE
@app.route('/edit_anchor', methods=['POST'])
def edit_anchor():
    # Get user_id from the session
    user_id = session.get('user_id')

    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401 # Unauthorized no user logged in
    

    # Extract data from incoming frontend payload
    data = request.get_json()
    anchor_id = data.get('anchor_id')
    anchor_name = data.get('anchor_name')
    new_name = data.get('new_anchor_name')
    new_latitude = data.get('latitude')
    new_longitude = data.get('longitude')

    # Ensure we got everything needed
    if anchor_id and anchor_name and new_name and new_latitude and new_longitude:
        try:
            # Connect to db
            con = sqlite3.connect('users.db')
            c = con.cursor()

            # Fetch the anchor's current details
            c.execute("SELECT * FROM anchors WHERE anchor_id=? and user_id=?", (anchor_id, user_id))
            anchor = c.fetchone()

            if anchor:  # make sure its a valid in 
                # Update anchor in the database
                c.execute("""UPDATE anchors SET anchor_id = ?, anchor_name = ?, latitude = ?, longitude = ?, created_at = CURRENT_TIMESTAMP
                    WHERE anchor_name = ? and user_id = ?""", (anchor_id, new_name, new_latitude, new_longitude, anchor_name, user_id))
                con.commit()
                con.close()
                return jsonify({'message': 'Anchor updated successfully'}), 200
            else:
                return jsonify({'error': 'Anchor not found or not authorized to edit'}), 404
        except Exception as e:
            return jsonify({'error': f'Error occurred while updating anchor: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Missing data for anchor update'}), 400


# GET ANCHORS ROUTE
@app.route('/get_anchors', methods=['GET'])
def get_anchors():
    try:
        # ✅ Get user_id from session
        user_id = session.get('user_id') or request.args.get('user_id')

        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401  # Unauthorized
        
        print(f"User ID received: {user_id}")


        # ✅ Connect to SQLite database
        con = sqlite3.connect('users.db')
        cur = con.cursor()

        # ✅ Fetch only the anchors belonging to the logged-in user
        cur.execute("SELECT anchor_id, anchor_name, latitude, longitude FROM anchors WHERE user_id=?", (user_id,))
        anchors = cur.fetchall()
        print("Anchors fetched from DB:", anchors)  # Debug print
        con.close()

        # ✅ Convert data to JSON format
        anchor_list = [
            {
                "id": int(row[0]),
                "name": row[1],     # Anchor name
                "latitude": row[2], # Latitude
                "longitude": row[3] # Longitude
            }
            for row in anchors
        ]

        return jsonify({"anchors": anchor_list, "message": "Anchors fetched successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Error retrieving anchors: {str(e)}"}), 500



# DELETE ANCHOR ROUTE
@app.route('/delete_anchor', methods=['POST'])
def delete_anchor():
    try:
        # Extract data from the incoming JSON payload
        data = request.get_json()
        anchor_name = data.get('anchor_name')  # Get anchor name from request
        user_id = session.get('user_id')  # Get user_id from session

        print(f"🟢 Incoming Delete Request - Anchor Name: {anchor_name}, User ID: {user_id}")

        # Validate user session
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401

        # Validate anchor_name
        if not anchor_name:
            return jsonify({'error': 'Missing anchor name'}), 400

        # Database connection
        con = sqlite3.connect('users.db')
        cur = con.cursor()

        # ✅ Check if the anchor exists for the given user_id and anchor_name
        cur.execute("SELECT * FROM anchors WHERE user_id = ? AND anchor_name = ?", (user_id, anchor_name))
        anchor = cur.fetchone()

        if not anchor:
            print(f"❌ No anchor found for User ID {user_id} and Anchor Name {anchor_name}")
            return jsonify({'error': 'Anchor not found or unauthorized'}), 404

        # ✅ Delete the anchor
        cur.execute("DELETE FROM anchors WHERE user_id = ? AND anchor_name = ?", (user_id, anchor_name))
        con.commit()
        con.close()

        print(f"✅ Successfully deleted Anchor for User ID: {user_id} and Anchor Name: {anchor_name}")
        return jsonify({'message': 'Anchor deleted successfully'}), 200

    except Exception as e:
        print(f"❌ Error deleting anchor: {str(e)}")
        return jsonify({'error': f'Error deleting anchor: {str(e)}'}), 500



# —————————————————————————————————————————————————————— TAGS ——————————————————————————————————————————————————————


# NEED KEN TO SEND TAG INFO WITH TAG NAME, LATITUDE, and LONGITUDE
# Very SIMILAR TO ADDING AN ANCHOR

@app.route('/add_tag', methods=['POST'])
def add_tag_location():
    # Get user_id from session
    user_id = session.get('user_id')

    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401

    # Get data from the request
    data = request.get_json()
    tag_id = data.get('tag_id')
    tag_name = data.get('tag_name') 
    x_offset = data.get('x_offset')  # Relative position in meters on the X-axis
    y_offset = data.get('y_offset')  # Relative position in meters on the Y-axis

    if not tag_id or tag_name or x_offset is None or y_offset is None:
        return jsonify({'error': 'Missing required data (tag_id, anchor_id, x_offset, y_offset)'}), 400

    try:
        # Connect to the database
        con = sqlite3.connect('users.db')
        c = con.cursor()

        # Check if the tag exists in the tags table
        c.execute("SELECT tag_name FROM tags WHERE tag_name = ?", (tag_name,))
        existing_tag = c.fetchone()

        if not existing_tag:
            # If the tag doesn't exist, insert it into the tags table
            c.execute("""
                INSERT INTO tags (tag_id, tag_name, user_id, latitude, longitude)
                VALUES (?, ?, ?, ?)
            """, (tag_id, tag_name, user_id, x_offset, y_offset))  # Default location set to 0.0, 0.0

        # Fetch the anchor's GPS coordinates
        #c.execute("SELECT latitude, longitude FROM anchors WHERE id=?", (anchor_id,))

        # Update the tag's most recent location in the 'tags' table
       # c.execute("""
        #     UPDATE tags
        #     SET latitude = ?, longitude = ?
        #     WHERE tag_id = ?
        # """, (tag_lat, tag_lon, tag_id))

        # # Insert the new location into the tag_locations table to maintain the history
        # c.execute("""INSERT INTO tag_locations (tag_id, latitude, longitude, mode, timestamp) 
        #              VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""", 
        #           (tag_id, tag_lat, tag_lon, "UWB"))

        # # Commit the transaction
        con.commit()
        con.close()

        return jsonify({'message': 'Tag location successfully added and updated'}), 201

    except Exception as e:
        return jsonify({'error': f'Error occurred while adding tag location: {str(e)}'}), 500


@app.route('/add_tag_tcp', methods=['POST'])
def add_tag_from_tcp():
    # Get JSON data from the TCP client
    data = request.json

    if not data:
        return jsonify({"message": "No data received or data is not valid JSON."}), 400

    tag_id = data.get('tag_id')
    tag_name = data.get('tag_name')
    tag_latitude = data.get('latitude')  # Latitude of the tag
    tag_longitude = data.get('longitude')  # Longitude of the tag
    user_id = data.get('user_id')

    # Connect to the SQLite database
    con = sqlite3.connect('users.db')
    cur = con.cursor()

    # Check if the tag already exists in the tags table by tag_name
    cur.execute("SELECT * FROM tags WHERE tag_name = ?", (tag_name,))
    existing_tag = cur.fetchone()

    if existing_tag:
        # Tag exists, update latitude and longitude
        cur.execute("""
            UPDATE tags
            SET tag_id = ?, user_id = ?, latitude = ?, longitude = ?
            WHERE tag_name = ?
        """, (tag_id, user_id, tag_latitude, tag_longitude, tag_name))
        message = "Tag updated successfully!"

    else:
        # Tag doesn't exist, add a new tag
        cur.execute("""
            INSERT INTO tags (tag_id, user_id, tag_name, latitude, longitude)
            VALUES (?, ?, ?, ?)
        """, (tag_id, user_id, tag_name, tag_latitude, tag_longitude))
        con.commit()
        message = "New tag added successfully!"

    # Retrieve the tag_id of the newly inserted or updated tag
    cur.execute("SELECT tag_id FROM tags WHERE tag_name = ?", (tag_name,))
    tag_id = cur.fetchone()[0]  # Fetch the tag_id after insert or update

    # Save the location into the tag_locations table
    cur.execute("""
        INSERT INTO tag_locations (tag_id, tag_name, latitude, longitude, mode)
        VALUES (?, ?, ?, ?, ?)
    """, (tag_id, tag_name, tag_latitude, tag_longitude, "TCP"))

    # Commit the transaction and close the connection
    con.commit()
    con.close()

    # Send response
    return jsonify({"message": message, "tag": tag_name, "latitude": tag_latitude, "longitude": tag_longitude})



# EDIT TAG PAGE
@app.route('/edit_tag', methods=['POST'])
def edit_tag():
    # Get user_id from session (assuming user is logged in)
    user_id = session.get('user_id')

    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401  # Unauthorized if no user is logged in

    # Extract data from incoming JSON request
    data = request.get_json()

    # Extract tag details from the request
    tag_id = data.get('tag_id')  # the ID of the tag to edit
    new_tag_name = data.get('tag_name')  # new name for the tag
    new_latitude = data.get('latitude')  # new latitude for the initial position
    new_longitude = data.get('longitude')  # new longitude for the initial position


    new_mode = data.get('mode', 'UWB')  # new mode (default to 'UWB' if not provided)

    # Ensure that we have the required data
    if tag_id and (new_tag_name or new_latitude is not None or new_longitude is not None):
        try:
            # Connect to the database
            con = sqlite3.connect('users.db')
            c = con.cursor()

            # Fetch the tag's current details from the 'tags' table
            c.execute("SELECT * FROM tags WHERE tag_id=?", (tag_id,))
            tag = c.fetchone()

            if not tag:
                return jsonify({'error': 'Tag not found'}), 404  # If tag does not exist, return an error

            # Update the tag's name
            if new_tag_name:
                c.execute("""UPDATE tags SET tag_name = ?, created_at = CURRENT_TIMESTAMP WHERE tag_id = ?""",
                          (new_tag_name, tag_id))

            # If new latitude and longitude are provided, update the tag's initial position
            if new_latitude is not None and new_longitude is not None:
                # We assume we're updating the initial position in the 'tag_locations' table
                c.execute("""UPDATE tag_locations SET latitude = ?, longitude = ?, mode = ?, timestamp = CURRENT_TIMESTAMP
                             WHERE tag_id = ?""", (new_latitude, new_longitude, new_mode, tag_id))

            con.commit()
            con.close()

            # Return success response
            return jsonify({'message': 'Tag successfully updated'}), 200

        except Exception as e:
            # Handle any errors
            return jsonify({'error': f'Error occurred while updating tag: {str(e)}'}), 500

    else:
        return jsonify({'error': 'Missing required data (tag_id, tag_name, latitude, longitude)'}), 400

# DELETE TAG PAGE
@app.route('/delete_tag', methods=['POST'])
def delete_tag():
    # Get user_id from session (assuming the user is logged in)
    user_id = session.get('user_id')

    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401  # Unauthorized if no user is logged in

    # Extract data from incoming JSON request
    data = request.get_json()

    # Extract the tag_id from the request
    tag_name = data.get('tag_name')

    # Ensure that the tag_id is provided
    if tag_name:
        try:
            # Connect to the database
            con = sqlite3.connect('users.db')
            c = con.cursor()

            # Fetch the tag's current details from the 'tags' table
            c.execute("SELECT * FROM tags WHERE tag_name=?", (tag_name,))
            tag = c.fetchone()

            if not tag:
                return jsonify({'error': 'Tag not found'}), 404  # If tag does not exist, return an error

            # Check if the user owns the tag (based on user_id)
            if tag[1] != user_id:  # Assuming 'user_id' is at index 1 in the fetched tag tuple
                return jsonify({'error': 'You do not have permission to delete this tag'}), 403  # Forbidden

            # Delete related entries in 'tag_locations'
            c.execute("DELETE FROM tag_locations WHERE tag_name=?", (tag_name,))

            # Delete the tag from the database
            c.execute("DELETE FROM tags WHERE tag_name=?", (tag_name,))
            con.commit()
            con.close()

            # Return success response
            return jsonify({'message': 'Tag successfully deleted'}), 200

        except Exception as e:
            # Handle any errors
            return jsonify({'error': f'Error occurred while deleting tag: {str(e)}'}), 500

    else:
        return jsonify({'error': 'Missing tag_id'}), 400  # Bad request if no tag_id is provided

# Acquire a Tag's most recent location
@app.route('/get_tags', methods=['GET'])
def get_tag_location():
    # Get user_id from session
    user_id = session.get('user_id') or request.args.get('user_id')

    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401  # Unauthorized if no user is logged in

    try:
        # Connect to Database
        con = sqlite3.connect('users.db')
        c = con.cursor()

        # Fetch the latitude, longitude, and tag_name for all tags of the given user_id
        c.execute("""
            SELECT tag_id, tag_name, latitude, longitude
            FROM tags
            WHERE user_id = ?
            """, (user_id,))

        # Fetch all the results
        tags_locations = c.fetchall()
        con.close()

        # If no tags are found, return an appropriate message
        if not tags_locations:
            return jsonify({'message': 'No tags found for the specified user'}), 404

        # Prepare the response with a list of tags and their locations
        result = []
        for tag in tags_locations:
            result.append({
                'id': str(tag[0]),
                'name': tag[1],
                'latitude': tag[2],
                'longitude': tag[3]
            })

        # Return the list of tags with their locations
        return jsonify({'tags_location': result}), 200

    except Exception as e:
        return jsonify({'error': f'Error occurred while fetching tags location: {str(e)}'}), 500

    

# Request 24-hour history of a tag
@app.route('/get_tag_location_history', methods=['GET'])
def get_tag_location_history():
    # Get user_id from session (assuming user is logged in)
    user_id = session.get('user_id')

    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401  # Unauthorized if no user is logged in

    # Get tag_id from incoming JSON request
    data = request.get_json()
    tag_id = data.get('tag_id')

    if not tag_id:
        return jsonify({'error': 'Missing tag_id'}), 400  # Bad request if no tag_id is provided

    try:
        # Connect to Database
        con = sqlite3.connect('users.db')
        c = con.cursor()

        # Have to figure out how to acquire this data 

    except Exception as e:
        return jsonify({'error': f'Error occurred while fetching tag location history: {str(e)}'}), 500



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
