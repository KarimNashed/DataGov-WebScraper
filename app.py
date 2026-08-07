import streamlit as st
import mysql.connector

# UI Setup
st.set_page_config(page_title="Data.gov Dashboard", layout="wide")
st.title("Data.gov Analytics Application")
st.sidebar.header("Navigation")

menu_choice = st.sidebar.radio("Select a Function", [
    "1. Register New User",
    "2. Add User Usage",
    "3. View User Usage",
    "4. Datasets by Org Type",
    "5. Top 5 Contributing Orgs",
    "6. Datasets by Format",
    "7. Datasets by Tag",
    "8. Aggregated Statistics",
    "9. Top 5 Datasets by Users",
    "10. Dataset Distribution by Project",
    "11. Top 10 Tags per Project Type"
])


# Database Connection
def get_database_connection():
    mydb = mysql.connector.connect(
        host=st.secrets["database"]["host"],
        port=st.secrets["database"]["port"],
        user=st.secrets["database"]["user"],
        password=st.secrets["database"]["password"],
        database=st.secrets["database"]["database"],
        ssl_ca=st.secrets["database"]["ssl_ca"]
    )
    return mydb


# Menu Logic
# Register New User
if menu_choice == "1. Register New User":
    st.header("Register a New User")

    new_email = st.text_input("Email:")
    new_username = st.text_input("Username:")
    new_gender = st.text_input("Gender (e.g., M, F):")
    new_birthdate = st.text_input("Birthdate (YYYY-MM-DD):")
    new_country = st.text_input("Country:")

    if st.button("Submit Registration"):
        mydb = get_database_connection()
        mycursor = mydb.cursor()

        sql = "INSERT INTO AppUser (Email, Username, Gender, Birthdate, Country) VALUES (%s, %s, %s, %s, %s)"

        try:
            # Safety check
            bdate_val = new_birthdate if new_birthdate != "" else None

            mycursor.execute(sql, (new_email, new_username, new_gender, bdate_val, new_country))
            mydb.commit()
            st.success("User registered successfully!")
        except Exception as e:
            st.error(f"Database Error: {e}")

        mydb.close()

# Add User Usage
elif menu_choice == "2. Add User Usage":
    st.header("Log Dataset Usage")

    proj_id = st.text_input("Enter existing Project ID:")
    dataset_id = st.text_input("Enter Dataset Identifier:")

    if st.button("Log Usage"):
        mydb = get_database_connection()
        mycursor = mydb.cursor()
        sql = "INSERT INTO UsageRecord (Project_ID, Identifier) VALUES (%s, %s)"
        try:
            mycursor.execute(sql, (proj_id, dataset_id))
            mydb.commit()
            st.success("Usage logged successfully!")
        except Exception as e:
            st.error(
                "Error logging usage. Make sure the Project ID and Dataset Identifier actually exist in the database.")
        mydb.close()

# View User Usage
elif menu_choice == "3. View User Usage":
    st.header("View Usage by User")

    search_email = st.text_input("Enter User Email to search:")

    if st.button("Search"):
        mydb = get_database_connection()
        mycursor = mydb.cursor()

        sql = """
            SELECT d.Name, p.Name as ProjectName
            FROM UsageRecord u
            JOIN Project p ON u.Project_ID = p.Project_ID
            JOIN Dataset d ON u.Identifier = d.Identifier
            WHERE p.Email = %s
        """
        mycursor.execute(sql, (search_email,))
        results = mycursor.fetchall()

        if len(results) == 0:
            st.info("No usage found for this user.")
        else:
            for row in results:
                st.write(f"- **{row[0]}** (Used in project: {row[1]})")
        mydb.close()

# Datasets by Organization Type
elif menu_choice == "4. Datasets by Org Type":
    st.header("Datasets by Organization Type")
    org_type = st.selectbox("Select Type:", ["Federal", "State", "City", "County", "Unknown", "University"])

    if st.button("Find Datasets"):
        mydb = get_database_connection()
        mycursor = mydb.cursor()
        sql = """
            SELECT d.Name 
            FROM Dataset d
            JOIN Organization o ON d.Organization_ID = o.Organization_ID
            WHERE o.OrganizationType = %s
            LIMIT 20
        """
        mycursor.execute(sql, (org_type,))
        results = mycursor.fetchall()

        # Safety check
        if len(results) == 0:
            st.info("No datasets found for this organization type.")
        else:
            for row in results:
                st.write("-", row[0])
        mydb.close()

# Top 5 Organizations
elif menu_choice == "5. Top 5 Contributing Orgs":
    st.header("Top 5 Contributing Organizations")
    mydb = get_database_connection()
    mycursor = mydb.cursor()
    sql = """
        SELECT o.Name, COUNT(d.Identifier)
        FROM Organization o
        JOIN Dataset d ON o.Organization_ID = d.Organization_ID
        GROUP BY o.Organization_ID
        ORDER BY COUNT(d.Identifier) DESC
        LIMIT 5;
    """
    mycursor.execute(sql)
    results = mycursor.fetchall()
    st.subheader("Results:")
    for row in results:
        st.write(row[0], "has", row[1], "datasets.")
    mydb.close()

# Datasets by Format
elif menu_choice == "6. Datasets by Format":
    st.header("Find Datasets by Format")
    file_format = st.text_input("Enter format (e.g., CSV, JSON, PDF):")

    if st.button("Search Format"):
        mydb = get_database_connection()
        mycursor = mydb.cursor()
        sql = """
            SELECT d.Name 
            FROM Dataset d
            JOIN Files f ON d.Identifier = f.Identifier
            WHERE f.Format = %s
            LIMIT 20
        """
        mycursor.execute(sql, (file_format,))
        results = mycursor.fetchall()

        if len(results) == 0:
            st.write("No datasets found.")
        else:
            for row in results:
                st.write("-", row[0])
        mydb.close()

# Datasets by Tag
elif menu_choice == "7. Datasets by Tag":
    st.header("Find Datasets by Tag")
    user_tag = st.text_input("Enter a tag (e.g., economy, health):")

    if st.button("Search Tag"):
        mydb = get_database_connection()
        mycursor = mydb.cursor()
        sql = """
            SELECT d.Name 
            FROM Dataset d
            JOIN Tags t ON d.Identifier = t.Identifier
            WHERE t.Tag_Name = %s
            LIMIT 20;
        """
        mycursor.execute(sql, (user_tag,))
        results = mycursor.fetchall()
        if len(results) == 0:
            st.write("No datasets found.")
        else:
            for row in results:
                st.write("-", row[0])
        mydb.close()

# Stats
elif menu_choice == "8. Aggregated Statistics":
    st.header("Database Statistics")
    mydb = get_database_connection()
    mycursor = mydb.cursor()

    mycursor.execute("SELECT COUNT(*) FROM Organization")
    org_count = mycursor.fetchone()[0]
    st.write("**Total Organizations:**", org_count)

    mycursor.execute("SELECT COUNT(*) FROM Dataset")
    dataset_count = mycursor.fetchone()[0]
    st.write("**Total Datasets:**", dataset_count)

    mycursor.execute("SELECT COUNT(*) FROM Files")
    file_count = mycursor.fetchone()[0]
    st.write("**Total Files/Formats:**", file_count)

    mydb.close()

#Top 5 Datasets by number of users
elif menu_choice == "9. Top 5 Datasets by Users":
    st.header("Most Used Datasets")
    mydb = get_database_connection()
    mycursor = mydb.cursor()

    sql = """
        SELECT d.Name, COUNT(DISTINCT p.Email) 
        FROM UsageRecord u
        JOIN Project p ON u.Project_ID = p.Project_ID
        JOIN Dataset d ON u.Identifier = d.Identifier
        GROUP BY d.Identifier, d.Name
        ORDER BY COUNT(DISTINCT p.Email) DESC
        LIMIT 5
    """
    mycursor.execute(sql)
    results = mycursor.fetchall()

    if len(results) == 0:
        st.info("No usage data recorded yet.")
    else:
        for row in results:
            st.write(row[0], "- Used by", row[1], "unique users.")
    mydb.close()

# Dataset Distribution by Project Category
elif menu_choice == "10. Dataset Distribution by Project":
    st.header("Datasets per Project Type")
    mydb = get_database_connection()
    mycursor = mydb.cursor()

    sql = """
        SELECT p.Category, COUNT(u.Identifier) 
        FROM UsageRecord u
        JOIN Project p ON u.Project_ID = p.Project_ID
        GROUP BY p.Category
    """
    mycursor.execute(sql)
    results = mycursor.fetchall()

    if len(results) == 0:
        st.info("No project data recorded yet.")
    else:
        for row in results:
            st.write("Project Category:", row[0], "- Datasets Used:", row[1])
    mydb.close()

# Top 10 Tags for every Project Category
elif menu_choice == "11. Top 10 Tags per Project Type":
    st.header("Top Tags by Project Type")
    proj_type = st.text_input("Enter Project Category (e.g., analytics, machine learning):")

    if st.button("Find Tags"):
        mydb = get_database_connection()
        mycursor = mydb.cursor()

        sql = """
            SELECT t.Tag_Name, COUNT(*) 
            FROM Tags t
            JOIN UsageRecord u ON t.Identifier = u.Identifier
            JOIN Project p ON u.Project_ID = p.Project_ID
            WHERE p.Category = %s
            GROUP BY t.Tag_Name
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """
        mycursor.execute(sql, (proj_type,))
        results = mycursor.fetchall()

        if len(results) == 0:
            st.info("No data found for this project category.")
        else:
            for row in results:
                st.write("Tag:", row[0], "- Count:", row[1])
        mydb.close()