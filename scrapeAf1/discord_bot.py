import os

import discord
import logging
from constants import BUCKET, AF1_URL
from utils import (
    extract_json_from_string,
    get_latest_2_object_from_s3,
    url_to_s3_path,
    get_html_body_from_s3,
    compare_search_results,
    extract_search_results,
    extract_milage_from_string,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


def format_discord_message(item_data):
    if item_data is None:
        return "No valid item data to format."

    # Extract relevant fields
    name = item_data.get("item", "Unknown")

    """ Price can be in different keys depending on the item """
    price_keys = ["bestPrice", "itemPrice", "unitPrice", "itemDisplayPrice"]
    price = ""
    for key in price_keys:
        price = item_data.get(key)
        if price:
            break
    if not price:
        price = "Unknown"

    url = item_data.get("itemUrl", "")

    # If URL is missing the "https:" prefix, add it
    if not url.startswith("http"):
        url = "https:" + url

    milage = item_data.get("milage", "")
    if milage:
        milage = f"{int(milage):,}"  # format the milage with commas

    # Format the message for Discord
    formatted_message = f"**{name}**\nPrice: {price} {f"Milage: {milage}" if milage else ""}\n[Link]({url})"
    return formatted_message


def send_discord_message(message):
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        logger.info(f"We have logged in as {client.user}")
        try:
            logger.info(f"This many messages in removed: {len(message["removed"])}")
            logger.info(f"This many messages in added: {len(message["added"])}")
            logger.info(f"This many messages in updated: {len(message["updated"])}")
        except KeyError:
            logger.error("Error on key for message")

        # Get the channel by ID
        for guild in client.guilds:
            logger.info(f"Guild: {guild.name}")
            for channel in guild.text_channels:
                logger.info(f"Channel: {channel.name} (ID: {channel.id})")
                if channel.name == "af1-bot":
                    if message["removed"]:
                        for item in message["removed"]:
                            item_dict = extract_json_from_string(item)
                            item_dict["milage"] = extract_milage_from_string(item)
                            await channel.send(
                                f"Removed: {format_discord_message(item_dict)}"
                            )
                    if message["added"]:
                        for item in message["added"]:
                            item_dict = extract_json_from_string(item)
                            item_dict["milage"] = extract_milage_from_string(item)
                            await channel.send(
                                f"Added: {format_discord_message(item_dict)}"
                            )

        await client.close()

    client.run(DISCORD_TOKEN)


def get_changes_and_send_discord_message():
    obj1, obj2 = get_latest_2_object_from_s3(
        BUCKET, url_to_s3_path(AF1_URL, prefix="archive")
    )

    html1 = get_html_body_from_s3(BUCKET, obj1["Key"])
    html2 = get_html_body_from_s3(BUCKET, obj2["Key"])

    res1 = extract_search_results(html1)
    res2 = extract_search_results(html2)

    diff = compare_search_results(res1, res2)

    if not diff:
        logger.info("No changes detected from two different md5 hashes. Strange!")
        return

    logger.info(f"Diff: {diff}")
    send_discord_message(diff)
