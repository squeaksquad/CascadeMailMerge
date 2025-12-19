import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- BAKED-IN TEMPLATES ---
# These are the original texts from your PDFs, now saved directly in the code.
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

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Assistant Mail Merge", page_icon="📧", layout="centered")

st.title("📧 Assistant Mail Merge Tool")
st.markdown("""
Use this tool to generate a personalized email list for shift signups. 
1. Enter the configuration details in the sidebar.
2. Upload your requirements document.
3. Download the processed file and paste it into the Google Sheet.
""")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Step 1: Configuration")
gsheet_url = st.sidebar.text_input("Assistant Schedule Google Sheet Link", placeholder="https://docs.google.com/spreadsheets/d/...")
send_from = st.sidebar.text_input("Send From (Email Alias)", value="bdimaio@berklee.edu")
bcc_email = st.sidebar.text_input("BCC Address", value="studiomanagers@berklee.edu")

st.sidebar.divider()
st.sidebar.info("Tip: Ensure the 'Send From' address is set up as an alias in your Gmail settings.")

# --- FILE UPLOAD ---
st.header("Step 2: Upload Data")
csv_file = st.file_uploader("Upload the Assistant Shift Requirements Document", type=["csv"])

# --- SEMESTER LOGIC ---
def get_semester_code(date_obj):
    month = date_obj.month
    year = date_obj.year
    year_short = str(year)[-2:]
    
    # Dec/Jan -> SP (Spring)
    if month == 12:
        return f"SP{str(year + 1)[-2:]}"
    if month == 1:
        return f"SP{year_short}"
    # Apr/May -> SU (Summer)
    if month in [4, 5]:
        return f"SU{year_short}"
    # Aug/Sep -> FA (Fall)
    if month in [8, 9]:
        return f"FA{year_short}"
    # Buffers for off-months
    if month in [2, 3]: return f"SP{year_short}"
    if month in [6, 7]: return f"SU{year_short}"
    return f"FA{year_short}"

# --- PROCESSING ---
if csv_file:
    try:
        df = pd.read_csv(csv_file)
        # Standardize column names (remove spaces)
        df.columns = [c.strip() for c in df.columns]
        
        # Fill in the grouped Dates and Times
        df['Signup Date'] = df['Signup Date'].ffill()
        df['Signup Time'] = df['Signup Time'].ffill()

        output_data = []

        for index, row in df.iterrows():
            # 1. Determine Semester
            try:
                date_dt = pd.to_datetime(row['Signup Date'])
            except:
                date_dt = datetime.now()
            
            sem_code = get_semester_code(date_dt)
            
            # 2. Select Template based on 'Complete' status
            is_complete = str(row['Complete']).upper() == 'TRUE'
            body = REQ_TEMPLATE if is_complete else NOREQ_TEMPLATE
            
            # 3. Personalization Replacements
            # Helper to format numbers (remove .0)
            def fmt(val):
                try:
                    f = float(val)
                    return str(int(f)) if f.is_integer() else str(f)
                except:
                    return str(val)

            body = body.replace("<field_First Name>", str(row['First Name']).strip())
            body = body.replace("<field_Prep Done>", fmt(row['Prep Done']))
            body = body.replace("<field_Closing Done>", fmt(row['Closing Done']))
            body = body.replace("<field_Prep Left>", fmt(row['Prep Left']))
            body = body.replace("<field_Closing Left>", fmt(row['Closing Left']))
            
            # 4. Create Hyperlink
            link_text = f"{sem_code} Assistant Schedule"
            link_html = f'<a href="{gsheet_url}">{link_text}</a>'
            body = body.replace("Assistant Schedule", link_html)
            
            # 5. Handle Formatting for Gmail (New lines to <br>)
            body = body.replace("\n", "<br>")
            
            # 6. Build Subject
            subject = f"{sem_code} Assistant Schedule: *Sign Up for Your Shifts!*"
            
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

        # --- RESULTS & DOWNLOAD ---
        result_df = pd.DataFrame(output_data)
        
        st.divider()
        st.header("Step 3: Download")
        st.success(f"Successfully processed {len(result_df)} assistants.")
        
        # Preview
        st.subheader("Preview (First 3 rows)")
        st.write(result_df[["First Name", "Email", "Subject"]].head(3))
        
        # CSV Download
        csv_buffer = io.StringIO()
        result_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download Processed Mail Merge CSV",
            data=csv_buffer.getvalue(),
            file_name=f"Mail_Merge_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Ensure your CSV has the columns: 'Signup Date', 'First Name', 'Email', 'Complete', 'Prep Done', etc.")
