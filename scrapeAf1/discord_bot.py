import discord

from scrapeAf1.lambda_function import DISCORD_TOKEN, BUCKET, AF1_URL
from scrapeAf1.utils import extract_json_from_string, get_latest_2_object_from_s3, url_to_s3_path, \
    get_html_body_from_s3, compare_search_results, extract_search_results


def format_discord_message(item_data):
    if item_data is None:
        return "No valid item data to format."

    # Extract relevant fields
    name = item_data.get('item', 'Unknown')
    price = item_data.get('bestPrice', 'Price not available')
    url = item_data.get('itemUrl', '')

    # If URL is missing the "https:" prefix, add it
    if not url.startswith('http'):
        url = "https:" + url

    # Format the message for Discord
    formatted_message = f"**{name}**\nPrice: {price}\n[View More]({url})"
    return formatted_message


def send_discord_message(message):
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'We have logged in as {client.user}')
        try:
            print("This many messages in removed: ", len(message['removed']))
            print("This many messages in added: ", len(message['added']))
            print("This many messages in updated: ", len(message['updated']))
        except KeyError:
            print("Error on key for message")



        # Get the channel by ID
        for guild in client.guilds:
            print(f'Guild: {guild.name}')
            for channel in guild.text_channels:
                print(f'Channel: {channel.name} (ID: {channel.id})')
                if channel.name == 'af1-bot':
                    if message['removed']:
                        for item in message['removed']:
                            item = extract_json_from_string(item)
                            await channel.send(f'Removed: {format_discord_message(item)}')
                    if message['added']:
                        for item in message['added']:
                            item = extract_json_from_string(item)
                            await channel.send(f'Added: {format_discord_message(item)}')

        await client.close()



    client.run(DISCORD_TOKEN)


def get_changes_and_send_discord_message():
    print(" TODO: scrape and send email")

    obj1, obj2 = get_latest_2_object_from_s3(BUCKET, url_to_s3_path(AF1_URL, prefix="archive"))

    html1 = get_html_body_from_s3(BUCKET, obj1['Key'])
    html2 = get_html_body_from_s3(BUCKET, obj2['Key'])

    res1 = extract_search_results(html1)
    res2 = extract_search_results(html2)

    diff = compare_search_results(res1, res2)

    print("Difference found!")

    send_discord_message(diff)
