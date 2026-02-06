import re
import json
import sys
from datetime import datetime

# TEXT EXTRACTION (optional) 

try:
    import pdfplumber
except:
    pdfplumber = None

def load_pdf_text(path):
    """Extract text from PDF (text PDFs only)."""
    text = ""
    if pdfplumber:
        try:
            with pdfplumber.open(path) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
                text = "\n".join(pages).strip()
        except:
            text = ""
    return text


# FIELD EXTRACTION FUNCTIONS 

def find_policy_number(text):
    m = re.search(r"Policy Number[:\s]+([A-Z0-9]+)", text, re.I)
    return m.group(1).strip() if m else None


def find_policyholder_name(text):
    m = re.search(r"Policyholder Name[:\s]+([A-Za-z ]+)", text)
    return m.group(1).strip() if m else None


def find_effective_dates(text):
    m = re.search(r"Effective Dates[:\s]+(.+)", text)
    if m:
        return m.group(1).strip()
    return None


def find_incident_date(text):
    m = re.search(r"Incident Date[:\s]+(.+)", text)
    if m:
        return m.group(1).strip()
    return None


def find_incident_time(text):
    m = re.search(r"Incident Time[:\s]+(.+)", text)
    return m.group(1).strip() if m else None


def find_incident_location(text):
    m = re.search(r"Incident Location[:\s]+(.+)", text)
    return m.group(1).strip() if m else None


def find_description(text):
    m = re.search(r"Description[:\s]+(.+)", text)
    return m.group(1).strip() if m else ""


def find_claimant(text):
    m = re.search(r"Claimant[:\s]+([A-Za-z ]+)", text)
    return m.group(1).strip() if m else None


def find_contact_details(text):
    
    contacts = {}

    # Email extraction
    m_email = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,})", text)
    if m_email:
        contacts["email"] = m_email.group(1)

    # Phone number extraction (India format + generic)
    m_phone = re.search(r"(\+?\d{1,3}[-\s]?\d{10})", text)
    if m_phone:
        contacts["phone"] = m_phone.group(1)

    return contacts



def find_asset_details(text):
    asset = {}
    m_type = re.search(r"Asset Type[:\s]+(.+)", text)
    if m_type:
        asset["assetType"] = m_type.group(1).strip()

    m_id = re.search(r"Asset ID[:\s]+(.+)", text)
    if m_id:
        asset["assetId"] = m_id.group(1).strip()

    m_damage = re.search(r"(Estimated Damage|Initial Estimate)[:\s]+([\d,\.]+)", text)
    if m_damage:
        try:
            asset["estimatedDamage"] = float(m_damage.group(2).replace(",", ""))
        except:
            asset["estimatedDamage"] = None

    return asset


def find_claim_type(text):
    m = re.search(r"Claim Type[:\s]+([A-Za-z]+)", text)
    return m.group(1).lower() if m else None


def find_attachments(text):
    att = []
    if "photo" in text.lower():
        att.append("photos")
    if "report" in text.lower():
        att.append("report")
    return att


# MISSING FIELDS + ROUTING 

MANDATORY_FIELDS = [
    "policyNumber",
    "policyholderName",
    "effectiveDates",
    "incidentDate",
    "incidentTime",
    "incidentLocation",
    "description",
    "claimant",
    "contactDetails",
    "assetType",
    "claimType",
    "attachments",
    "initialEstimate"
]

def analyze_text(text):
    fields = {}

    fields["policyNumber"] = find_policy_number(text)
    fields["policyholderName"] = find_policyholder_name(text)
    fields["effectiveDates"] = find_effective_dates(text)
    fields["incidentDate"] = find_incident_date(text)
    fields["incidentTime"] = find_incident_time(text)
    fields["incidentLocation"] = find_incident_location(text)
    fields["description"] = find_description(text)
    fields["claimant"] = find_claimant(text)
    fields["contactDetails"] = find_contact_details(text)

    asset = find_asset_details(text)
    fields["assetType"] = asset.get("assetType")
    fields["assetId"] = asset.get("assetId")
    fields["estimatedDamage"] = asset.get("estimatedDamage")

    fields["claimType"] = find_claim_type(text)
    fields["attachments"] = find_attachments(text)
    fields["initialEstimate"] = fields["estimatedDamage"]

    return fields


def determine_missing(fields):
    missing = []
    for key in MANDATORY_FIELDS:
        val = fields.get(key)
        if val is None or val == "" or val == [] or val == {}:
            missing.append(key)
    return missing


def decide_route(fields, missing):
    reasons = []

    if missing:
        reasons.append("Missing mandatory fields: " + ", ".join(missing))
        return "Manual review", reasons

    damage = fields.get("estimatedDamage")

    if damage is not None and damage < 25000:
        reasons.append(f"Estimated damage {damage} < 25000 → Fast-track")
        return "Fast-track", reasons

    if fields.get("claimType") == "injury":
        return "Specialist Queue", ["Injury claim"]

    if "fraud" in fields.get("description", "").lower():
        return "Investigation Flag", ["Fraud keyword detected"]

    return "Manual review", ["Default: needs review"]


#  MAIN EXECUTION 

def process_document(path):
    if path.lower().endswith(".txt"):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = load_pdf_text(path)

    fields = analyze_text(text)
    missing = determine_missing(fields)
    route, reasons = decide_route(fields, missing)

    return {
        "extractedFields": fields,
        "missingFields": missing,
        "recommendedRoute": route,
        "reasoning": " | ".join(reasons)
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fnol_agent.py <file>")
        sys.exit(1)

    path = sys.argv[1]
    output = process_document(path)
    print(json.dumps(output, indent=2))
