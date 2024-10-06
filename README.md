# clan-tracker
Scripts for automating clan management and ranks using collectionlog.net and templeosrs.com.

To use this tool, simply run `python clan-tracker.py` with your favorite python3.11 installation. Some libraries may be required to be pip installed; please see requirements.txt and install any required packages using `pip install -r requirements.txt`.

# TempleOSRS
We use TempleOSRS's API to pull down EHB and EHP metrics across different game modes.

GIM tracking is unfortunately not exposed over the API despite being present on the web page. As such, all GIMs are tracked as mains until further notice.

To make this work best, make sure TempleOSRS is selected on the XP Updater plugin on RuneLite.

[API Docs](https://templeosrs.com/api_doc.php)
TempleOSRS has a 100 API request per minute limit per source IP, so everything is rate limited to fit well under that lest we face the wrath of the CloudFlare rate limiter.


# CollectionLog
CollectionLog's API provides killcounts and completion of certain items we use for point allocation. Unfortunately, many items that should be collection log slots are not, so tracking is imperfect and some things need to be handled manually despite this.

In order to be tracked, players will need to setup the RuneLite [Collection Log plugin](https://github.com/evansloan/collection-log).

[API Docs](https://docs.collectionlog.net/)
There aren't any publicly listed API rate limits, so we don't worry about limiting our connections here, but can and will if needed.


# TODO
- Move point calculation configuration into modular YAML file