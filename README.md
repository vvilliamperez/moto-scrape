
# moto-scrape

AWS lambda for scraping used motorcycles listings, and notifying interested parties.

## System design

A cron service (aws event bridge scheduler) triggers this lambda every 5mins to check for updates (md5 hash of the page against a previous md5 cached in s3).
If there is it downloads an archive of the page to s3, updates the md5 cache, and sends out a sns notification.

The lambda is also itself subscribed to the sns topic and will run again, and check if it was triggerd by the sns.
When fired off from sns, it gets the last two archived page versions, compares them, and fires off a discord bot. 

 
