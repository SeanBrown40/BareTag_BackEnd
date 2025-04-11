import requests
import math

#BASE_URL = "http://localhost:5000"
BASE_URL = "http://172.24.131.25:5000"
USERNAME = "sean"
PASSWORD = "sean"

# Function to log in and get the session cookie
def login():
    response = requests.post(f"{BASE_URL}/login", json={"username": USERNAME, "password": PASSWORD})
    if response.status_code == 200:
        print("Login successful!")
        return response.cookies  # Return session cookies
    else:
        print("Login failed:", response.json())
        return None

# Function to delete an anchor
def delete_anchor(anchor_name, cookies):
    response = requests.post(
        f"{BASE_URL}/delete_anchor",
        json={"anchor_name": anchor_name},
        cookies=cookies,
    )
    if response.status_code == 200:
        print(f"Anchor '{anchor_name}' deleted successfully!")
    else:
        print(f"Anchor '{anchor_name}' not found (may not exist yet).")

# Function to add an anchor
def add_anchor(anchor_id, anchor_name, latitude, longitude, cookies):
    response = requests.post(
        f"{BASE_URL}/add_anchor",
        json={
            "anchor_id": int(anchor_id),  # Ensure integer ID
            "anchor_name": anchor_name,
            "latitude": latitude,
            "longitude": longitude,
        },
        cookies=cookies,  # Pass session cookies
    )
    if response.status_code == 201:
        print(f"Anchor {anchor_id} added successfully!")
    else:
        print(f"Failed to add anchor {anchor_id}:", response.json())

# Function to add a tag from TCP
def add_tag(tag_id, tag_name, latitude, longitude, user_id, cookies):
    response = requests.post(
        f"{BASE_URL}/add_tag_tcp",
        json={
            "tag_id": tag_id,
            "tag_name": tag_name,
            "latitude": latitude,
            "longitude": longitude,
            "user_id": user_id,
        },
        cookies=cookies,  # Pass session cookies
    )
    if response.status_code == 200:
        print(f"Tag '{tag_name}' added successfully!")
    else:
        print(f"Failed to add tag '{tag_name}':", response.json())

# Convert 10 meters to degrees (approx.)
METERS_TO_DEGREES_LAT = 10 / 111320  # 1 degree lat = ~111.32 km
METERS_TO_DEGREES_LON = 10 / (111320 * math.cos(math.radians(42.3732))) 

# Main script
if __name__ == "__main__":
    cookies = login()
    if cookies:
        lat1, lon1 = 42.3732, -72.5199  # Base location in Amherst

        # Delete existing anchors
        delete_anchor("Anchor 1", cookies)
        delete_anchor("Anchor 2", cookies)
        delete_anchor("Anchor 3", cookies)

        # Add new anchors with IDs 1, 2, 3
        add_anchor(60, "Anchor 1", lat1, lon1, cookies)
        add_anchor(90, "Anchor 2", lat1 + METERS_TO_DEGREES_LAT, lon1, cookies)  # +10m latitude
        add_anchor(3, "Anchor 3", lat1, lon1 + METERS_TO_DEGREES_LON, cookies)  # +10m longitude

        # Register two tags after adding the anchors
        user_id = 1  # Assuming you have a valid user_id; replace with actual user_id if needed.
        add_tag("CD", "Tag 1", lat1 + METERS_TO_DEGREES_LAT, lon1, user_id, cookies)  # Tag 1 at +10m latitude
        add_tag("GH", "Tag 2", lat1, lon1 + METERS_TO_DEGREES_LON, user_id, cookies)  # Tag 2 at +10m longitude