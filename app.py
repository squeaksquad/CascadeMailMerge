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

# --- USER INPUTS ---
st.sidebar.header("Email Configuration")
gsheet_url = st.sidebar.text_input("Assistant Schedule Link", "https://docs.google.com/spreadsheets/d/...")
send_from = st.sidebar.text_input("Send From (Alias)", "bdimaio@berklee.edu")
bcc_email = st.sidebar.text_input("BCC Address", "studiomanagers@berklee.edu")

csv_file = st.file_uploader("Upload Assistant Shift Requirements Document", type=["csv"])

def get_semester_code(date_obj):
    month, year = date_obj.month, date_obj.year
    year_short = str(year)[-2:]
    if month == 12: return f"SP{str(year + 1)[-2:]}"
    if month == 1: return f"SP{year_short}"
    if month in [4, 5]: return f"SU{year_short}"
    if month in [8, 9]: return f"FA{year_short}"
    if month in [2, 3]: return f"SP{year_short}"
    return f"FA{year_short}"

if csv_file:
    df = pd.read_csv(csv_file)
    df.columns = [c.strip() for c in df.columns]
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
        body = REQ_TEMPLATE if row['Complete'] == True else NOREQ_TEMPLATE
        
        def clean_num(val):
            try:
                f = float(val)
                return str(int(f)) if f.is_integer() else str(f)
            except:
                return str(val)

        body = body.replace("<field_First Name>", str(row['First Name']))
        body = body.replace("<field_Prep Done>", clean_num(row['Prep Done']))
        body = body.replace("<field_Closing Done>", clean_num(row['Closing Done']))
        body = body.replace("<field_Prep Left>", clean_num(row['Prep Left']))
        body = body.replace("<field_Closing Left>", clean_num(row['Closing Left']))
        
        link_html = f'<a href="{gsheet_url}">{sem} Assistant Schedule</a>'
        body = body.replace("Assistant Schedule", link_html)
        
        output_data.append({
            "Send Date": row['Signup Date'],
            "Send Time": row['Signup Time'],
            "First Name": row['First Name'],
            "Email": row['Email'],
            "Send From": send_from,
            "BCC": bcc_email,
            "Subject": subject,
            "Body": body
        })

    output_df = pd.DataFrame(output_data)
    st.success(f"Processed {len(output_df)} emails!")
    st.dataframe(output_df.head())
    
    csv_buffer = io.StringIO()
    output_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download Mail Merge CSV",
        data=csv_buffer.getvalue(),
        file_name="ready_to_mail_merge.csv",
        mime="text/csv"
    )
