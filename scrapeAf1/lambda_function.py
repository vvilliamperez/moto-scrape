import json

from utils import *

AF1_URL = "https://www.af1racingaustin.com/search/inventory/availability/In%20Stock/usage/Used"
BUCKET = "moto-scraper"


def lambda_handler(event, context):
    last_known_hash = get_latest_hash_in_s3(AF1_URL, BUCKET)
    current_hash = get_site_hash_now(AF1_URL)

    if not last_known_hash:
        store_hash_in_s3(BUCKET, url_to_s3_path(AF1_URL), current_hash)
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
        store_hash_in_s3(BUCKET, url_to_s3_path(AF1_URL), current_hash)

        # begin scraping

        # send email

        return {
            'statusCode': 200,
            'body': json.dumps('New site update, sending SNS!')
        }

    else:
        return {
            'statusCode': 501,
            'body': json.dumps('Unknown Error!')
        }


#get_latest_hash_in_s3(AF1_URL, BUCKET)

#print(current_hash)


