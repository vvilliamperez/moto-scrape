import json

from utils import *

AF1_URL = "https://www.af1racingaustin.com/search/inventory/availability/In%20Stock/usage/Used"
BUCKET = "moto-scraper"
topic_arn = 'arn:aws:sns:us-east-1:986354456027:af1-used-site-updated'


def check_for_updates():
    last_known_hash = get_latest_hash_in_s3(AF1_URL, BUCKET)
    current_hash = get_site_hash_now(AF1_URL)

    if not last_known_hash:
        store_hash_in_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="page_hashes"), current_hash)
        archive_site_in_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="archive"), AF1_URL)
        return {
            'statusCode': 200,
            'body': json.dumps('No previous hash found, storing current hash!')
        }

    if current_hash == last_known_hash:
        return {
            'statusCode': 200,
            'body': json.dumps('No updates to the site. MD5 looks the same!')
        }

    if current_hash != last_known_hash:
        # store current
        store_hash_in_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="page_hashes"), current_hash)
        archive_site_in_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="archive"), AF1_URL)

        # send sns
        send_sns(topic_arn)

        return {
            'statusCode': 200,
            'body': json.dumps('New site update, sent SNS to !')
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps('Unknown error occurred!')
        }


def scrape_and_send_email():
    print(" TODO: scrape and send email")
    pass


def is_site_updated(event):
    try:
        sns_message = event['Records'][0]['Sns']['Message']
        print(f"Received SNS message: {sns_message}")
        return sns_message is not None
    except KeyError:
        return False


def lambda_handler(event, context):
    if is_site_updated(event):
        # scrape and send email
        resp = scrape_and_send_email()
    else:
        resp = check_for_updates()
    return resp

# get_latest_hash_in_s3(AF1_URL, BUCKET)

# print(current_hash)
