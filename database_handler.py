import mysql.connector

# Connect to the database
def connect_db():
    # connect to the database
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="******", #My password
            database="DBSProject"
        )
        print("Connected to DB successfully")
        return db
    except Exception as e:
        print("error connecting:", e)
        return None

# Organization Table
def insert_org(db, name, desc, org_type, email, phone):
    cursor = db.cursor()

    # exact duplicate check code:
    cursor.execute("SELECT Organization_ID FROM Organization WHERE Name = %s", (name,))
    result = cursor.fetchone()
    if result:
        return result[0]

    # If it didn't return above, it means it's new, so insert
    sql = "INSERT INTO Organization (Name, Description, OrganizationType, E_Mail, PhoneNumber) VALUES (%s, %s, %s, %s, %s)"
    vals = (name, desc, org_type, email, phone)

    try:
        cursor.execute(sql, vals)
        db.commit()
        return cursor.lastrowid  # return the newly generated ID
    except Exception as e:
        print("Error with org:", e)
        return None

# Dataset Table
def insert_data(db, ident, name, desc, acc, lic, c_date, u_date, pub, main, topic, org_id):
    cursor = db.cursor()
    sql = "INSERT INTO Dataset (Identifier, Name, Description, Access_Level, License, Creation_Date, Update_Date, Publisher, Maintainer, Topic, Organization_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    vals = (ident, name, desc, acc, lic, c_date, u_date, pub, main, topic, org_id)

    try:
        cursor.execute(sql, vals)
        db.commit()
        return True
    except Exception as e:
        print("Error with dataset:", e)
        return False

# File Table
def insert_file(db, ident, fmt, url):
    cursor = db.cursor()
    # use ignore so it doesnt crash on duplicates
    sql = "INSERT IGNORE INTO Files (Identifier, Format, URL) VALUES (%s, %s, %s)"
    vals = (ident, fmt, url)

    try:
        cursor.execute(sql, vals)
        db.commit()
    except Exception as e:
        print("Error with file:", e)

# Tag Table
def insert_tag(db, ident, tag):
    cursor = db.cursor()
    sql = "INSERT IGNORE INTO Tags (Identifier, Tag_Name) VALUES (%s, %s)"
    vals = (ident, tag)

    try:
        cursor.execute(sql, vals)
        db.commit()
    except Exception as e:
        print("Error with tag:", e)