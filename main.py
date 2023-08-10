import streamlit as st
from PIL import Image
import easyocr
import re
import pandas as pd
import mysql.connector


def main():
    st.title(":orange[Extracting Business Card Data]")

    upload_img = st.file_uploader(":red[Upload the Business Card]", type=["jpg", "jpeg"])

    st.sidebar.header(":orange[Choose The option]")
    extract_button = st.sidebar.button(':green[Extract Data]')
    update_button = st.sidebar.button(":green[Save to DB]")
    view_button = st.sidebar.button(':green[View Data]')

    # connect to db
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mysql_pwd1",
        database="bizcardx"
    )
    mycursor = mydb.cursor()

    col1, col2 = st.columns(2, gap="medium")

    if upload_img is not None:
        with col1:
            # Use PIL to open and display the uploaded image
            image = Image.open(upload_img)
            st.image(image, caption="Uploaded Image", use_column_width=True)

            reader = easyocr.Reader(['en'])
            results = reader.readtext(image)

            text = ''
            for result in results:
                text += result[1] + ' '

            lst = []
            for detection in results:
                txt, confidence, box = detection
                lst.append(confidence)

            # name
            name = lst[0]
            role = lst[1]

            # company
            last_ele = re.sub(r'[^a-zA-Z0-9]', '', lst[-1])

            if len(last_ele) < 3:
                company = lst[-2]
            else:
                company = lst[-1]

            # phone
            phone_pattern = r"\+\d{2,3}-\d{3}-\d{4}|\d{2,3}-\d{3}-\d{4}"
            phone_match = re.findall(phone_pattern, text)

            if phone_match:
                phone = ",".join(phone_match)
            else:
                phone = 'None'

            ## mail_id
            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
            email_match = re.search(email_pattern, text)
            if email_match:
                email = email_match.group()

            # website
            web_pattern = r"\b(?:www\s*\.?|WWW\s*\.?)\w+\s*\.\s*\w+\b"
            web_match = re.search(web_pattern, text, re.IGNORECASE)
            if web_match:
                website = web_match.group()
            else:
                website = 'None'

            # address
            add_pattern1 = r'\b\d{3}\s\w+'
            add_match1 = re.search(add_pattern1, text)
            if add_match1:
                add1 = add_match1.group()
            else:
                add1 = "None"

            add_pattern2 = r'\b(?:Avenue|Lane|Road|Boulevard|Drive|Street|Ave|Dr|Rd|Blvd|Ln|St)\b'
            add_match2 = re.search(add_pattern2, text)

            if add_match2:
                add2 = add_match2.group()
            else:
                add2 = "No match found"

            address = add1 + ' ' + add2
            # city
            add_end2 = add_match2.end()
            add_end1 = add_match1.end()
            next_word_pattern = r"\b\w+\b"
            next_word_match1 = re.search(next_word_pattern, text[add_end2:])
            next_word_match2 = re.search(next_word_pattern, text[add_end1:])
            if next_word_match1:
                city = next_word_match1.group().strip()
            elif next_word_match1 is None:
                city = next_word_match2.group().strip()
            else:
                city = 'None'

            # state
            indian_states = [
                "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
                "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
                "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
                "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
                "Uttar Pradesh", "Uttarakhand", "West Bengal", "TamilNadu"
            ]

            state_pattern = r"\b(?:{})\b".format("|".join(indian_states))
            state_match = re.search(state_pattern, text, re.IGNORECASE)
            if state_match:
                state = state_match.group()
            else:
                state = 'None'

            # pincode
            pin_pattern = r'\b\d{6,7}\b'
            pin_match = re.search(pin_pattern, text)
            if pin_match:
                pincode = pin_match.group()
            else:
                pincode = 'none'

            dic = {'Name': name,
                   'Role': role,
                   'Phone': phone,
                   'email': email,
                   'website': website,
                   'Company': company,
                   'Address': address,
                   'City': city,
                   'state': state,
                   'pincode': pincode}

            data = (name, role, phone, email, website, company, address, city, state, pincode)
    if extract_button:
        with col2:
            st.subheader(":orange[Card Details]")
            st.table(dic)

    if update_button:
        insert = "INSERT INTO card_details (Name, Designation, Phone, email, website, Company, " \
                 "Address, City, state, pincode) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        mycursor.execute(insert, data)
        mydb.commit()
        st.success("#### Uploaded to database successfully!")

    if view_button:
        mycursor.execute("SELECT Name, Designation, Phone, email, website, Company, " \
                         "Address, City, state, pincode FROM card_details")
        details = mycursor.fetchall()
        st.dataframe(details)

    mycursor.execute("SELECT Name FROM card_details")
    name = mycursor.fetchall()
    business_cards = {}
    for row in name:
        business_cards[row[0]] = row[0]
    selected_card = st.sidebar.selectbox(":red[select card holder name to delete]", list(business_cards.keys()))
    delete_button = st.sidebar.button(":green[Delete]")
    if delete_button:
        mycursor.execute(f"DELETE FROM card_details WHERE Name='{selected_card}'")
        mydb.commit()
        st.success("Selected Business card details deleted from database.")


if __name__ == '__main__':
    main()
