# MetaAdsAPI

Project to Get Meta Ad Spends data to Google Sheets incrementally

[![Get Data from API](https://github.com/abhinavsreesan/MetaAdsAPI/actions/workflows/run-python-script.yml/badge.svg)](https://github.com/abhinavsreesan/MetaAdsAPI/actions/workflows/run-python-script.yml)

## Summary

Repo to use a python script to read data from the Meta REST Api using Python SDK to get daily Ad Spends data and append incrementally to a Google Sheet.

## Requirements

### Meta API Details

Get the below details from the shopify store admin page:

    1. APP_ID
    2. APP_SECRET
    3. ACCESS_TOKEN
    4. AD_ACCOUNT_ID

### Google Sheets API Details

Create a service account and provide access to it from the GCP console and get the below details:

    1. Google Service Account Email
    2. Google Service Account Key File

Install the Google sheet library using the below command:

```bash
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Referenced from: https://medium.com/@zarafshanwaheed444/facebook-marketing-api-4e7e0ad1195d

## Github Actions

The script is scheduled to run daily at 12:00 AM UTC using GitHub Actions. The script will read the data from the Meta API and append it to the Google Sheet. 
It fetches the above-mentioned values from the below secrets:
    
    1. ACCESS_TOKEN
    2. APP_ID
    3. APP_SECRET
    4. AD_ACCOUNT_ID
    5. GOOGLE_SHEET_SECRET
    6. SPREADSHEET_ID
    


