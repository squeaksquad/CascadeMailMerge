import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- BAKED-IN TEMPLATES (With "Thanks," included) ---
REQ_TEMPLATE = """Hi <field_First Name>,

You may now access the Assistant Schedule.

Congrats! You have completed your prep and closing shift requirements.

Let us know if you have any questions.

Thanks,"""

NOREQ_TEMPLATE = """Hi <field_First Name>,

You may now access the Assistant Schedule.

Consider our weekly requirements as you select your shifts.

You have completed <field_Prep Done> morning prep shift(s) and <field_Closing Done> closing shift(s).
You have <field_Prep Left> prep shift(s) and <field_Closing Left> closing shift(s) left to fulfill.

Please let us know if you have any questions.

Thanks,"""

st.set_page_config(page_title="Assistant Mail Merge", page_icon="📧")
st.title("📧 Assistant Mail Merge Tool")

# Sidebar Configuration
st.sidebar.header("Step 1: Configuration")
gsheet_url = st.sidebar.text_input("Assistant Schedule Link", placeholder="https://...")
send_from = st.sidebar.text_input("Send From (Email Alias)", value="studiomanagers@berklee.edu")
bcc_email = st.sidebar.text_input("BCC Address", value="studiomanagers@berklee.edu")

# File Upload
st.header("Step 2: Upload Data")
csv_file = st.file_uploader("Upload the Assistant Shift Requirements Document", type=["csv"])

def get_semester_code(date_obj):
    month, year = date_obj.month, date_obj.year
    year_short = str(year)[-2:]
    if month == 12: return f"SP{str(year + 1)[-2:]}"
    if month == 1: return f"SP{year_short}"
    if month in [4, 5]: return f"SU{year_short}"
    if month in [8, 9]: return f"FA{year_short}"
    return f"FA{year_short}" if month > 6 else f"SP{year_short}"

if csv_file:
    try:
        df = pd.read_csv(csv_file)
        df.columns = [c.strip() for c in df.columns]
        
        # Ensure grouping dates/times are filled down
        df['Signup Date'] = df['Signup Date'].ffill()
        df['Signup Time'] = df['Signup Time'].ffill()

        output_data = []
        for _, row in df.iterrows():
            try:
                dt = pd.to_datetime(row['Signup Date'])
            except:
                dt = datetime.now()
            
            sem = get_semester_code(dt)
            is_complete = str(row['Complete']).upper() == 'TRUE'
            body = REQ_TEMPLATE if is_complete else NOREQ_TEMPLATE
            
            def fmt(val):
                try:
                    f = float(val)
                    return str(int(f)) if f.is_integer() else str(f)
                except: return str(val)

            # Personalization
            body = body.replace("<field_First Name>", str(row['First Name']).strip())
            body = body.replace("<field_Prep Done>", fmt(row['Prep Done']))
            body = body.replace("<field_Closing Done>", fmt(row['Closing Done']))
            body = body.replace("<field_Prep Left>", fmt(row['Prep Left']))
            body = body.replace("<field_Closing Left>", fmt(row['Closing Left']))
            
            # Hyperlink
            link_html = f'<a href="{gsheet_url}">{sem} Assistant Schedule</a>'
            body = body.replace("Assistant Schedule", link_html)
            
            # HTML Formatting (Preserve New Lines)
            body = body.replace("\n", "<br>")
            
            output_data.append({
                "Send Date": row['Signup Date'],
                "Send Time": row['Signup Time'],
                "First Name": row['First Name'],
                "Email": row['Email'],
                "Send From": send_from,
                "BCC": bcc_email,
                "Subject": f"{sem} Assistant Schedule: *Sign Up for Your Shifts!*",
                "Body": body
            })

        result_df = pd.DataFrame(output_data)
        st.success(f"Processed {len(result_df)} assistants.")
        st.download_button("Download Processed CSV", result_df.to_csv(index=False), "ready_to_mail_merge.csv")

    except Exception as e:
        st.error(f"Error processing CSV: {e}")
