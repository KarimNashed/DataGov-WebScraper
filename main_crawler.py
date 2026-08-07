import requests
from bs4 import BeautifulSoup
import time
import database_handler as db_handler
from datetime import datetime

# helper to fix the dates for mysql
def fix_date(d_str):
    if d_str == "" or d_str == None: #if empty turns them into NULL
        return None
    try:
        return datetime.strptime(d_str, "%B %d, %Y").strftime("%Y-%m-%d")
    except:
        pass
    try:
        return datetime.strptime(d_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except:
        return None

#organization information
def get_org_info(link):
    headers = {"User-Agent": "Mozilla/5.0"} # so the website doesn't block me
    res = requests.get(link, headers=headers) # HTML of the secondary page

    desc = "No description"
    phone = "Unknown"

    if res.status_code == 200: #HTTP 200 code means "OK", only proceeds if the page successfully loaded
        s = BeautifulSoup(res.text, 'html.parser')

        # Find the tab menu to lock onto the correct part of the page
        page_header = s.find('header', class_='page-header')

        if page_header != None:
            # Look at the whole section that contains the header
            main_section = page_header.parent
            if main_section != None:
                # The description is the first paragraph in this section!
                p_tag = main_section.find('p')

                if p_tag != None:
                    # Check if it's the default empty message
                    if p_tag.get('class') == ['empty'] or "no description" in p_tag.text.lower():
                        desc = "No description"
                    else:
                        desc = p_tag.text.strip()

    return desc, phone

# Scrape the Dataset
def scrape_dataset(url, db_conn):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print("Could not load", url)
        return

    soup = BeautifulSoup(res.text, 'html.parser')

    # setup variables for dataset
    identifier = None
    access = "Unknown"
    license = "Unknown"
    c_date = None
    u_date = None
    pub = "Unknown"
    main = "Unknown"
    category = "Unknown"
    name = "Unknown"
    description = "Unknown"

    h1 = soup.find('h1', itemprop='name')
    if h1:
        name = h1.text.strip()

    desc_div = soup.find('div', itemprop='description')
    if desc_div:
        description = desc_div.text.strip()
    else:
        description = "No description"

    # metadata table loop
    rows = soup.find_all('th', class_='dataset-label')
    for row in rows:
        lbl = row.text.strip()
        td = row.find_next_sibling('td')

        # check
        if not td:
            continue

        val = td.text.strip()

        if lbl == "Identifier":
            identifier = val
        elif lbl == "Public Access Level":
            access = val
        elif lbl == "License":
            license = val
        elif lbl == "Metadata Created Date":
            c_date = fix_date(val)
        elif lbl == "Metadata Updated Date":
            u_date = fix_date(val)
        elif lbl == "Publisher":
            pub = val
        elif lbl == "Maintainer":
            main = val
        elif lbl == "Category" or lbl == "Topic":
            category = val

    # extract tags
    tags = []
    ul_tags = soup.find('ul', class_='tag-list')
    if ul_tags != None:
        a_tags = ul_tags.find_all('a', class_='tag')
        for a in a_tags:
            tags.append(a.text.strip())

    # extract files
    files = []
    res_list = soup.find('ul', class_='resource-list')
    if res_list != None:
        items = res_list.find_all('li', class_='resource-item')
        for item in items:
            fmt_span = item.find('span', class_='format-label')
            if fmt_span != None:
                file_fmt = fmt_span.text.strip()
            else:
                file_fmt = "Unknown"

            f_url = "No URL"
            b_group = item.find('div', class_='btn-group')
            if b_group != None:
                btn = b_group.find('a', class_='btn btn-primary')
                if btn != None and 'href' in btn.attrs:
                    f_url = btn['href']

            if f_url != "No URL":
                files.append({"Format": file_fmt, "URL": f_url})

    print("Scraped dataset:", name)
    print("Found", len(tags), "tags and", len(files), "files")

    # extract org name safely from the sidebar box
    org_name = "Unknown"
    org_info_sec = soup.find('section', id='organization-info')
    if org_info_sec != None:
        name_h1 = org_info_sec.find('h1', class_='heading')
        if name_h1 != None:
            org_name = name_h1.text.strip()

    # extract org type
    otype = "Unknown"
    type_span = soup.find('span', class_='organization-type')
    if type_span != None:
        otype = type_span.text.strip()

    # extract email
    email = "Unknown"
    contact_sec = soup.find('section', class_='contact')
    if contact_sec != None:
        a_tag = contact_sec.find('a')
        if a_tag != None and 'href' in a_tag.attrs:
            email = a_tag['href'].replace('mailto:', '')
        elif a_tag != None:
            email = a_tag.text.strip()

    # get the org link to visit the about page for the full description
    org_url = None
    org_image_div = soup.find('div', class_='image')
    if org_image_div != None:
        a_tag = org_image_div.find('a')
        if a_tag != None and 'href' in a_tag.attrs:
            org_path = a_tag['href'].replace('/organization/', '/organization/about/')
            org_url = "https://catalog.data.gov" + org_path

    # visit the about page
    if org_url != None:
        desc, phone = get_org_info(org_url)
    else:
        desc = "Unknown"
        phone = "Unknown"

    # Insert to db
    org_id = db_handler.insert_org(db_conn, org_name, desc, otype, email, phone)

    if org_id != None and identifier != None:
        success = db_handler.insert_data(
            db_conn, identifier, name, description, access, license,
            c_date, u_date, pub, main, category, org_id
        )

        if success == True:
            for t in tags:
                db_handler.insert_tag(db_conn, identifier, t)

            for f in files:
                db_handler.insert_file(db_conn, identifier, f["Format"], f["URL"])

            print("Saved successfully!")
            print("-" * 50)


# main loop
db = db_handler.connect_db()

if db == None:
    print("Stopping because db didn't connect")
else:
    headers = {"User-Agent": "Mozilla/5.0"}

    # loop through 100 pages
    for i in range(1, 101):
        print("\n--- Page", i, "---")
        url = "https://catalog.data.gov/dataset/?page=" + str(i)

        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print("Error loading page", i)
            continue

        soup = BeautifulSoup(res.text, 'html.parser')
        datasets = soup.find_all('div', class_='dataset-content')

        for d in datasets:
            a_tag = d.find('h3', class_='dataset-heading').find('a')
            if a_tag == None:
                continue

            link = "https://catalog.data.gov" + a_tag['href']
            print("Visiting:", link)
            scrape_dataset(link, db)

            time.sleep(1)  # sleep so to not crash the server

    db.close()
    print("DONE")