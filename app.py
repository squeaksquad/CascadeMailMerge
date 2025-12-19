import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- BAKED-IN TEMPLATES ---
REQ_TEMPLATE = """Hi <field_First Name>,

You may now access the Assistant Schedule.

Congrats! You have completed your prep and closing shift requirements.

Let us know if you have any questions.

Thanks,

Bryan"""

NOREQ_TEMPLATE = """Hi <field_First Name>,

You may now access the Assistant Schedule.

Consider our weekly requirements as you select your shifts.

You have completed <field_Prep Done> morning prep shift(s) and <field_Closing Done> closing shift(s).
You have <field_Prep Left> prep shift(s) and <field_Closing Left> closing shift(s) left to fulfill.

Please let us know if you have any questions.

Thanks,
Bryan"""

st.set_page_config(page_title="Shift Mail Merge", page_icon="✉️")
st.title("✉️ Shift Mail Merge Generator")

# User Inputs
gsheet_url = st.text_input("Assistant Schedule Google Sheet Link", "https://docs.google.com/spreadsheets/d/...")
csv_file = st.file_uploader("Upload 'Shift Test Gemini.csv'", type=["csv"])

def get_semester_code(date_obj):
    month, year = date_obj.month, date_obj.year
    year_short = str(year)[-2:]
    if month == 12: return f"SP{str(year + 1)[-2:]}"
    if month == 1: return f"SP{year_short}"
    if month in [4, 5]: return f"SU{year_short}"
    if month in [8, 9]: return f"FA{year_short}"
    return f"XX{year_short}"

if csv_file:
    df = pd.read_csv(csv_file)
    df['Signup Date'] = df['Signup Date'].ffill()
    df['Signup Time'] = df['Signup Time'].ffill()

    output_data = []
    for _, row in df.iterrows():
        try:
            dt = pd.to_datetime(row['Signup Date'])
        except:
            dt = datetime.now()
        
        sem = get_semester_code(dt)
        subject = f"{sem} Assistant Schedule: *Sign Up for Your Shifts!*"
        
        # Select Template
        body = REQ_TEMPLATE if row['Complete'] else NOREQ_TEMPLATE
        
        # Personalize
        body = body.replace("<field_First Name>", str(row['First Name']))
        body = body.replace("<field_Prep Done>", str(row['Prep Done']).replace(".0", ""))
        body = body.replace("<field_Closing Done>", str(row['Closing Done']).replace(".0", ""))
        body = body.replace("<field_Prep Left>", str(row['Prep Left']).replace(".0", ""))
        body = body.replace("<field_Closing Left>", str(row['Closing Left']).replace(".0", ""))
        
        # Add personalized Hyperlink
        link_html = f'<a href="{gsheet_url}">{sem} Assistant Schedule</a>'
        body = body.replace("Assistant Schedule", link_html)
        
        output_data.append({
            "First Name": row['First Name'],
            "Email": row['Email'],
            "Subject": subject,
            "Body": body
        })

    output_df = pd.DataFrame(output_data)
    st.success("CSV Generated!")
    st.download_button("Download for Google Sheets", output_df.to_csv(index=False), "mail_merge_ready.csv")
