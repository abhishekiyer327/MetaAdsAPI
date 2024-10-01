import os
from datetime import datetime, timedelta
import json
import pandas as pd
import time

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.adobjects.campaign import Campaign

# Google Sheets API
from google.oauth2 import service_account
import gspread
from gspread_dataframe import set_with_dataframe

# Meta API Config Details
app_id = os.environ.get('APP_ID')
app_secret = os.environ.get('APP_SECRET')
access_token = os.environ.get('ACCESS_TOKEN')
ad_account_id = os.environ.get('AD_ACCOUNT_ID')

# Google Sheets Config Details
GOOGLE_SHEET_SECRET = os.environ.get('GOOGLE_SHEET_SECRET')
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')

meta_api_dict = {
    'campaigns': {},
    'adinsights': {
        'primary_key': 'adid_date',
        'primary_key_pos': 12

    }
}

# Output File Name
output_file = f'data/campaigns{datetime.now().date()}.csv'

scopes = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']


def init_facebook_api() -> AdAccount:
    """
    Function to initialize the Facebook API
    """
    FacebookAdsApi.init(app_id, app_secret, access_token)
    my_account = AdAccount(ad_account_id)
    return my_account


def get_campaigns(my_account: AdAccount) -> list:
    """
    Function to get all the campaigns associated with the Ad Account
    """
    campaigns = my_account.get_campaigns(fields=[Campaign.Field.name, Campaign.Field.status, Campaign.Field.objective,
                                                 Campaign.Field.created_time, Campaign.Field.updated_time,
                                                 Campaign.Field.start_time, Campaign.Field.stop_time,
                                                 Campaign.Field.effective_status, Campaign.Field.id,
                                                 Campaign.Field.account_id])
    return campaigns


def get_ads(my_account: AdAccount, historical=False) -> list:
    """
    Function to get all the ads associated with the Ad Account
    """
    if historical:
        ads = my_account.get_ads(fields=[Ad.Field.name, Ad.Field.configured_status, Ad.Field.effective_status,
                                         Ad.Field.creative],
                                 params={'limit': 20000})
    else:
        ads = my_account.get_ads(fields=[Ad.Field.name, Ad.Field.configured_status, Ad.Field.effective_status,
                                         Ad.Field.creative],
                                 params={'limit': 20000,
                                         'filtering': [{"field": "ad.updated_time", "operator": "GREATER_THAN",
                                                        "value": f"{int(((datetime.now() -
                                                                          timedelta(days=1)).replace(hour=0, minute=0, second=0)
                                                                         ).timestamp())}"}]
                                         })
    return ads


def get_adsets(my_account: AdAccount) -> list:
    """
    Function to get all the adsets associated with the Ad Account
    """
    adsets = my_account.get_ad_sets(fields=[AdSet.Field.name, AdSet.Field.status, AdSet.Field.targeting,
                                            AdSet.Field.created_time, AdSet.Field.updated_time,
                                            AdSet.Field.start_time, AdSet.Field.end_time,
                                            AdSet.Field.effective_status, AdSet.Field.id, AdSet.Field.account_id])
    return adsets


def get_ad_insights(add_id: str, historical=False) -> list:
    """
    Function to get the ads insights
    :param add_id: Ad ID
    :param historical: Get historical data or not
    :return: List of Ad Insights
    """
    ad = Ad(add_id)
    if historical:
        ad_insights = ad.get_insights(fields=[AdsInsights.Field.ad_id, AdsInsights.Field.ad_name,
                                              AdsInsights.Field.campaign_id, AdsInsights.Field.campaign_name,
                                              AdsInsights.Field.adset_id, AdsInsights.Field.adset_name,
                                              AdsInsights.Field.impressions, AdsInsights.Field.spend,
                                              AdsInsights.Field.clicks, AdsInsights.Field.date_start,
                                              AdsInsights.Field.date_stop],
                                      params={'since': '2023-01-01', 'until': '2024-05-20', 'time_increment': '1'})
    else:
        ad_insights = ad.get_insights(fields=[AdsInsights.Field.ad_id, AdsInsights.Field.ad_name,
                                              AdsInsights.Field.campaign_id, AdsInsights.Field.campaign_name,
                                              AdsInsights.Field.adset_id, AdsInsights.Field.adset_name,
                                              AdsInsights.Field.impressions, AdsInsights.Field.spend,
                                              AdsInsights.Field.clicks, AdsInsights.Field.date_start,
                                              AdsInsights.Field.date_stop],
                                      params={'since': f'{datetime.now().date() - timedelta(days=1)}',
                                              'until': f'{datetime.now().date()}', 'time_increment': '1'})
    try:
        return ad_insights
    except:
        return {}


def get_google_sheets_credentials():
    """
    Function to get the Google Sheets API credentials
    :return: Service object if the credentials are correct else -1 if the credentials are incorrect
    """
    credentials = service_account.Credentials.from_service_account_info(json.loads(GOOGLE_SHEET_SECRET, strict=False),
                                                                        scopes=scopes)
    if credentials:
        print('Log: Google Credentials Created Successfully')
        return credentials
    else:
        return -1


def write_dataframe_to_sheet(df: pd.DataFrame, api: str, credentials) -> int:
    """
    Function to write the dataframe to the Google Sheets
    :param credentials: Google API credentials
    :param df: Dataframe to write to the sheet
    :return: 0 if to write is successful else -1
    """

    gc = gspread.authorize(credentials)

    # open a google sheet
    gs = gc.open_by_key(SPREADSHEET_ID)
    # select a work sheet from its name
    try:
        worksheet1 = gs.worksheet(api)
    except:
        worksheet1 = gs.add_worksheet(title=api, rows=100, cols=20)
    # update the sheet with the dataframe
    set_with_dataframe(worksheet=worksheet1, dataframe=df, include_index=False,
                       include_column_header=True, resize=True)


def sheet_incremental_load(df: pd.DataFrame, api: str, credentials):
    sheet_exists = False
    gc = gspread.authorize(credentials)
    # open a google sheet
    gs = gc.open_by_key(SPREADSHEET_ID)
    # select a work sheet from its name
    try:
        worksheet1 = gs.worksheet(api)
        sheet_exists = True
    except:
        worksheet1 = gs.add_worksheet(title=api, rows=100, cols=20)
    # update the sheet with the dataframe
    if sheet_exists:
        # Append the data to the existing sheet
        primary_column = meta_api_dict[api]['primary_key']
        primary_column_list = df[primary_column].tolist()
        for value in primary_column_list:
            if worksheet1.find(str(value), in_column=int(meta_api_dict[api]['primary_key_pos'])):
                worksheet1.delete_rows(
                    worksheet1.find(str(value), in_column=int(meta_api_dict[api]['primary_key_pos'])).row)
            time.sleep(1)

        set_with_dataframe(worksheet=worksheet1, dataframe=df, include_index=False, include_column_header=False,
                           row=worksheet1.row_count + 1, resize=False)

    else:
        set_with_dataframe(worksheet=worksheet1, dataframe=df, include_index=False,
                           include_column_header=True, resize=True)


if __name__ == '__main__':
    my_account = init_facebook_api()
    creds = get_google_sheets_credentials()

    api_to_run = ['adinsights']

    for api in api_to_run:
        if api == 'campaigns':
            campaigns = get_campaigns(my_account)
            campaigns_df = pd.DataFrame([campaign for campaign in campaigns])
            print(campaigns_df.head(5))
            campaigns_df.to_csv(output_file, index=False)
            write_dataframe_to_sheet(campaigns_df, api, creds)
        elif api == 'ads':
            ads = get_ads(my_account)
            ads_df = pd.DataFrame([ad for ad in ads])
            print(ads_df.head(5))
            ads_df.to_csv(output_file, index=False)
            write_dataframe_to_sheet(ads_df, api, creds)
        elif api == 'adinsights':
            ad_insights_df = pd.DataFrame()
            ads = get_ads(my_account)
            print(f'Number of Ads: {len(ads)}')
            count = 1
            for num in range(0, len(ads)):
                ad_insight = get_ad_insights(ads[num]['id'])
                adinsight_df = pd.DataFrame([ad_insight[i] for i in range(0, len(ad_insight))]).drop_duplicates()
                if len(ad_insights_df) == 0:
                    ad_insights_df = adinsight_df
                else:
                    ad_insights_df = pd.concat([ad_insights_df, adinsight_df])
                print(f'Processed {count} Ads')
                count += 1
            if len(ad_insights_df) > 0:
                ad_insights_df["adid_date"] = ad_insights_df['ad_id'] + ad_insights_df['date_start']
                print(ad_insights_df.head(5))
                ad_insights_df.to_csv(output_file, index=False)
                sheet_incremental_load(ad_insights_df, api, creds)
