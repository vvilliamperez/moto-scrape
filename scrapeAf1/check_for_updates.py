import hashlib
import json

import requests
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup

from constants import AF1_URL, BUCKET, TOPIC_ARN
from utils import (
    url_to_s3_path,
    get_latest_object_from_s3,
    s3_client,
    archive_site_in_s3,
    send_sns,
)

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_site_hash_now(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove dynamic elements
    for tag in soup(["script", "style"]):
        tag.decompose()

    # You can also remove specific dynamic sections based on class or ID
    for dynamic_section in soup.find_all(class_="ad-section"):
        dynamic_section.decompose()

    # Get the main content as text
    main_content = soup.get_text()

    return hashlib.md5(main_content.encode("utf-8")).hexdigest()


def get_latest_hash_in_s3(url: str, bucket: str) -> str:
    try:
        key = url_to_s3_path(url)
        subdirectory = key.split("/")[0]
        subdirectory = "page_hashes" + "/" + subdirectory
        obj = get_latest_object_from_s3(bucket, subdirectory)
        if not obj:
            return None

        key = obj["Key"]
        response = s3_client.get_object(Bucket=bucket, Key=key)

        return response["Body"].read().decode("utf-8")
    except ClientError as e:
        logger.error(f"Error retrieving hash from S3: {e}")
        return None


def store_hash_in_s3(bucket_name: str, key: str, hash_value: str):
    """
    Store the MD5 hash in an S3 object.
    """
    try:
        response = s3_client.put_object(Bucket=bucket_name, Key=key, Body=hash_value)
        logger.info(f"Successfully stored hash: {hash_value} in S3 under key: {key}")
    except ClientError as e:
        logger.error(f"Error uploading to S3: {e}")


def check_for_updates() -> dict:
    last_known_hash = get_latest_hash_in_s3(AF1_URL, BUCKET)
    try:
        current_hash = get_site_hash_now(AF1_URL)
    except requests.exceptions.RequestException:
        current_hash = None


    logger.info(f"Last known hash: {last_known_hash}, Current hash: {current_hash}")

    if not last_known_hash:
        store_hash_in_s3(
            BUCKET, url_to_s3_path(AF1_URL, prefix="page_hashes"), current_hash
        )
        archive_site_in_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="archive"), AF1_URL)
        return {
            "statusCode": 200,
            "body": json.dumps("No previous hash found, storing current hash!"),
        }

    if current_hash == last_known_hash:
        return {
            "statusCode": 200,
            "body": json.dumps("No updates to the site. MD5 looks the same!"),
        }

    if current_hash != last_known_hash:
        # store current
        store_hash_in_s3(
            BUCKET, url_to_s3_path(AF1_URL, prefix="page_hashes"), current_hash
        )
        archive_site_in_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="archive"), AF1_URL)

        # send sns
        send_sns(TOPIC_ARN)

        return {"statusCode": 200, "body": json.dumps("New site update, sent SNS to !")}
    else:
        return {"statusCode": 500, "body": json.dumps("Unknown error occurred!")}
