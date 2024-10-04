import os
from scrapeAf1.check_hash_for_update import check_for_updates
from scrapeAf1.discord_bot import get_changes_and_send_discord_message
from scrapeAf1.utils import is_site_updated

AF1_URL = "https://www.af1racingaustin.com/search/inventory/availability/In%20Stock/usage/Used"
BUCKET = "moto-scraper"
topic_arn = 'arn:aws:sns:us-east-1:986354456027:af1-used-site-updated'
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')


def lambda_handler(event, context):
    if is_site_updated(event):
        # get changes from archive and send discord message
        resp = get_changes_and_send_discord_message()
    else:
        resp = check_for_updates()
    return resp

