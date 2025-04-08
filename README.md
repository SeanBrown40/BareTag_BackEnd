# BareTag_BackEnd
app.py: Python-based Flask CRUD Server that interacts with our project's FrontEnd and manages an SQLite database to store
information about user profiles, anchors, and tags present in our system

basestation.py: Python script which interacts with the backend server to fetch anchor and tag data, processes distance measurements from tags to anchors, and calculates a tag's locationg using trilateration based on the distance measurements it is given. The script communicates with anchor via LoRa-based serial communication and computes the tag's geographical coordinates which it sends to the BackEnd database to be stored.
