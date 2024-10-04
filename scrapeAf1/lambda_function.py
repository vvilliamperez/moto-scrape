import json

from check_for_updates import check_for_updates
from discord_bot import get_changes_and_send_discord_message
from utils import is_site_updated
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    log_data = {
        "event": event,
        "context": context,
    }
    logger.info(json.dumps(log_data))

    if is_site_updated(event):
        # get changes from archive and send discord message
        resp = get_changes_and_send_discord_message()
    else:
        resp = check_for_updates()
    return resp
