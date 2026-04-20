import pandas as pd
from sqlalchemy import create_engine, text

TRUNCATE_SQL = """
TRUNCATE TABLE activist_codes_applied, event_participants, online_actions,
               contributions, addresses, contacts, events, activist_codes, tags
RESTART IDENTITY CASCADE;
"""

ENGINE = create_engine(
    "postgresql+psycopg2://liml@localhost/arizona_list",
    connect_args={"client_encoding": "utf8"},
)

def read_tsv(path):
    return pd.read_csv(path, encoding="utf-16", sep="\t", on_bad_lines="skip", low_memory=False)

def to_date(s):
    return pd.to_datetime(s, errors="coerce")

def fix_bools(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = df[col].map(lambda x: bool(x) if pd.notna(x) else None)
    return df

def load(df, table, msg=""):
    df.to_sql(table, ENGINE, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"  ✓ {table:<30} {len(df):>8,} rows  {msg}")


# ── Clear all tables ──────────────────────────────────────────────────────
print("Clearing all tables...")
with ENGINE.connect() as conn:
    conn.execute(text(TRUNCATE_SQL))
    conn.commit()

# ── 1. activist_codes ─────────────────────────────────────────────────────
print("[1/8] activist_codes")
ac = pd.read_excel("Activist Code List  2.xlsx", engine="openpyxl")
ac.columns = ["type", "long_name", "medium", "short", "scope", "activist"]
ac["activist"] = ac["activist"].map(lambda x: bool(x) if pd.notna(x) else None)
ac = ac.dropna(subset=["long_name"]).drop_duplicates("long_name")
load(ac, "activist_codes")

# ── 2. tags ───────────────────────────────────────────────────────────────
print("[2/8] tags")
tags = pd.read_excel("Tags 2.xlsx", engine="openpyxl")
tags.columns = ["id", "path", "name", "created_by", "date_created", "description"]
tags["date_created"] = to_date(tags["date_created"])
load(tags, "tags")

# ── 3. contacts ───────────────────────────────────────────────────────────
print("[3/8] contacts")
db = read_tsv("Database List 4.9.26.xls")
db = db.rename(columns={
    "VANID": "vanid", "Last": "last", "First": "first", "Mid": "mid",
    "Suf": "suffix", "HomePhone": "home_phone", "City": "city",
    "State/Province": "state", "Zip/Postal": "zip", "AddressID": "address_id",
    "PreferredEmail": "preferred_email", "OtherEmail": "other_email",
    "Deceased": "deceased", "NoCall": "no_call", "NoEmail": "no_email",
    "NoMail": "no_mail", "Cell Phone": "cell_phone", "CD": "cd",
    "County": "county", "Date Acquired": "date_acquired",
    "Date Created": "date_created", "DOB": "dob", "Deceased Date": "deceased_date",
    "Number of Contributions": "number_of_contributions",
    "Total Amount of Contributions": "total_amount_of_contributions",
    "Average Contribution Amount": "average_contribution_amount",
    "Employer Name": "employer_name", "Occupation": "occupation",
    "OriginCodeName": "origin_code_name", "Type of Contact": "type_of_contact",
})
for col in ["date_acquired", "date_created", "dob", "deceased_date"]:
    db[col] = to_date(db[col])
fix_bools(db, ["deceased", "no_call", "no_email", "no_mail"])
db["address_id"] = None  # set after addresses are loaded
for col in ["prefix", "suffix"]:
    if col not in db.columns:
        db[col] = None
contacts_cols = [
    "vanid", "first", "last", "mid", "prefix", "suffix", "type_of_contact",
    "home_phone", "cell_phone", "preferred_email", "other_email",
    "employer_name", "occupation", "county", "city", "state", "zip", "cd",
    "dob", "date_acquired", "date_created", "deceased_date",
    "deceased", "no_call", "no_email", "no_mail",
    "number_of_contributions", "total_amount_of_contributions",
    "average_contribution_amount", "origin_code_name", "address_id",
]
load(db[contacts_cols], "contacts")
valid_vanids = set(db["vanid"].dropna().astype(int))

# ── 4. addresses ──────────────────────────────────────────────────────────
print("[4/8] addresses")
addr = read_tsv("Addresses Report 4.9.26.xls")
addr = addr[[
    "Address ID", "VANID", "Street Address", "City", "State/Province",
    "Zip/Postal", "Country", "Type", "Status", "Is Preferred",
    "Is Best Address", "Is Complete Address", "USPS Verified",
    "Date Created", "Date Added",
]].rename(columns={
    "Address ID": "address_id", "VANID": "vanid", "Street Address": "street_address",
    "City": "city", "State/Province": "state", "Zip/Postal": "zip",
    "Country": "country", "Type": "type", "Status": "status",
    "Is Preferred": "is_preferred", "Is Best Address": "is_best_address",
    "Is Complete Address": "is_complete_address", "USPS Verified": "usps_verified",
    "Date Created": "date_created", "Date Added": "date_added",
})
for col in ["date_created", "date_added"]:
    addr[col] = to_date(addr[col])
fix_bools(addr, ["is_preferred", "is_best_address", "is_complete_address", "usps_verified"])
addr = addr[addr["vanid"].isin(valid_vanids)]
load(addr, "addresses")

# Update preferred address FK on contacts
with ENGINE.connect() as conn:
    conn.execute(text("""
        UPDATE contacts c
        SET address_id = a.address_id
        FROM addresses a
        WHERE a.vanid = c.vanid AND a.is_preferred = TRUE
    """))
    conn.commit()
print("  ✓ preferred address FK updated on contacts")

# ── 5. contributions ──────────────────────────────────────────────────────
print("[5/8] contributions")
contrib = read_tsv("All Contributions Ever 4.9.26.xls")
contrib = contrib.rename(columns={
    "Contribution ID": "contribution_id", "VANID": "vanid",
    "Date Received": "date_received", "Amount": "amount",
    "Remaining Amount": "remaining_amount", "Source Code": "source_code",
    "Designation": "designation", "Payment Method": "payment_method",
    "Contribution Type": "contribution_type", "Period": "period", "Cycle": "cycle",
})
contrib["vanid"] = pd.to_numeric(contrib["vanid"], errors="coerce")
contrib["date_received"] = to_date(contrib["date_received"])
contrib = contrib[contrib["vanid"].isin(valid_vanids)]
load(contrib[[
    "contribution_id", "vanid", "date_received", "amount", "remaining_amount",
    "source_code", "designation", "payment_method", "contribution_type", "period", "cycle",
]], "contributions")

# ── 6. events + event_participants ────────────────────────────────────────
print("[6/8] events + event_participants")
ev = read_tsv("All Event Participant Report 4.9.26.xls")
ev["VANID"] = pd.to_numeric(ev["VANID"], errors="coerce")
ev["Event ID"] = pd.to_numeric(ev["Event ID"], errors="coerce")

events_dim = ev[[
    "Event ID", "Event Name", "Event Type", "Event Date", "Shift Name",
    "Shift Start Time", "Shift End Time", "Location Name",
    "Campaign", "Campaign Type", "Assigned Staff",
]].drop_duplicates("Event ID").rename(columns={
    "Event ID": "event_id", "Event Name": "event_name", "Event Type": "event_type",
    "Event Date": "event_date", "Shift Name": "shift_name",
    "Shift Start Time": "shift_start_time", "Shift End Time": "shift_end_time",
    "Location Name": "location_name", "Campaign": "campaign",
    "Campaign Type": "campaign_type", "Assigned Staff": "assigned_staff",
})
events_dim["event_date"] = to_date(events_dim["event_date"])
events_dim = events_dim.drop(columns=["shift_start_time", "shift_end_time"])
load(events_dim, "events")

ep = ev[[
    "VANID", "Event ID", "Signup Date", "Status", "Role",
    "Recruited By", "Input Type", "Hours Completed", "Hosted",
]].rename(columns={
    "VANID": "vanid", "Event ID": "event_id", "Signup Date": "signup_date",
    "Status": "status", "Role": "role", "Recruited By": "recruited_by",
    "Input Type": "input_type", "Hours Completed": "hours_completed", "Hosted": "hosted",
})
ep["signup_date"] = to_date(ep["signup_date"])
fix_bools(ep, ["hosted"])
ep = ep[ep["vanid"].isin(valid_vanids)].drop_duplicates(["vanid", "event_id"])
load(ep, "event_participants")

# ── 7. activist_codes_applied ─────────────────────────────────────────────
print("[7/8] activist_codes_applied")
valid_codes = set(ac["long_name"].dropna())
aca = read_tsv("All Activist Codes Applied 9.27.21-4.9.26.xls")
aca = aca.rename(columns={
    "VANID": "vanid", "ActivistCodeID": "activist_code_id",
    "ActivistCodeType": "activist_code_type", "ActivistCodeName": "activist_code_name",
    "DateCreated": "date_created", "DateContacted": "date_contacted",
    "Scope": "scope", "CreatedBy": "created_by", "ContactedBy": "contacted_by",
    "InputType": "input_type", "Committeename": "committee_name",
})
aca["date_created"] = to_date(aca["date_created"])
aca["date_contacted"] = to_date(aca["date_contacted"])
aca = aca[aca["vanid"].isin(valid_vanids)]
aca = aca[aca["activist_code_name"].isin(valid_codes)]
aca = aca.drop_duplicates(["vanid", "activist_code_name", "date_created"])
load(aca[[
    "vanid", "activist_code_name", "date_created", "activist_code_id",
    "activist_code_type", "scope", "input_type", "created_by",
    "contacted_by", "committee_name", "date_contacted",
]], "activist_codes_applied")

# ── 8. online_actions ─────────────────────────────────────────────────────
print("[8/8] online_actions")
oa = read_tsv("All Online Action Data 4.9.26.xls")
oa = oa.rename(columns={
    "Submission ID": "submission_id", "VANID": "vanid", "Form ID": "form_id",
    "Form Name": "form_name", "Form Type": "form_type",
    "Date Submitted": "date_submitted", "Amount": "amount",
    "Payment Method": "payment_method", "Source Code": "source_code",
    "Designation": "designation", "Status": "status",
    "Is New Contact": "is_new_contact", "Channel": "channel",
    "Device Type": "device_type", "Referred By": "referred_by",
})
oa["date_submitted"] = to_date(oa["date_submitted"])
fix_bools(oa, ["is_new_contact"])
oa = oa[oa["vanid"].isin(valid_vanids)]
load(oa[[
    "submission_id", "vanid", "form_id", "form_name", "form_type",
    "date_submitted", "amount", "payment_method", "source_code",
    "designation", "status", "is_new_contact", "channel", "device_type", "referred_by",
]], "online_actions")

# ── Summary ───────────────────────────────────────────────────────────────
print("\n=== Final row counts ===")
with ENGINE.connect() as conn:
    for tbl in ["contacts", "addresses", "contributions", "online_actions",
                "events", "event_participants", "activist_codes_applied",
                "activist_codes", "tags"]:
        n = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
        print(f"  {tbl:<30} {n:>8,}")
print("\nDone.")
