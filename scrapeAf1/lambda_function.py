import json

from utils import *

AF1_URL = "https://www.af1racingaustin.com/search/inventory/availability/In%20Stock/usage/Used"
BUCKET = "moto-scraper"
topic_arn = 'arn:aws:sns:us-east-1:986354456027:af1-used-site-updated'

def lambda_handler(event, context):
    last_known_hash = get_latest_hash_in_s3(AF1_URL, BUCKET)
    current_hash = get_site_hash_now(AF1_URL)

    if not last_known_hash:
        store_hash_in_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="page_hashes"), current_hash)
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

        # send sns
        send_sns(topic_arn)

        return {
            'statusCode': 200,
            'body': json.dumps('New site update, sent SNS to !')
        }

    else:
        return {
            'statusCode': 501,
            'body': json.dumps('Unknown Error!')
        }


#get_latest_hash_in_s3(AF1_URL, BUCKET)

#print(current_hash)


