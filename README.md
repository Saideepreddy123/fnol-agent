#  Autonomous Insurance FNOL Processing Agent

This project implements a lightweight AI-assisted FNOL (First Notice of Loss) processing agent.  
It extracts key claim information from FNOL documents, identifies missing mandatory fields, and recommends a routing decision based on predefined business rules.

---

# Features 

- Extracts key fields from FNOL documents:
  - Policy Details  
  - Incident Details  
  - Claimant Information  
  - Contact Details  
  - Asset Details  
- Detects missing mandatory fields
- Applies routing logic:
  - Estimated damage < 25,000 → **Fast-track**
  - Any missing mandatory field → **Manual Review**
  - Fraud keywords → **Investigation Flag**
  - Claim Type = Injury → **Specialist Queue**
- Returns clean JSON output with:
  - Extracted fields  
  - Missing fields  
  - Recommended route  
  - Reasoning  

---

# Project Structure 

fnol-agent/
│── fnol_agent.py
│── sample.txt
│── requirements.txt
│── README.md
│
└── samples/
├── fnol_sample1.txt

---

# Installation

Install dependencies:

# bash 
pip install -r requirements.txt


#Running the FNOL Agent

#Process an FNOL text file:

python fnol_agent.py sample.txt





