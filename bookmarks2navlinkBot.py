#!/usr/bin/python3

# @BookmarksToNavlinksBot

#IMPORTS
import argparse
import json
import logging
import math
import queue
import sys

from telegram import Update

from telegram.ext import (
    Application, 
    # Job,
    CommandHandler, 
    ContextTypes, 
    MessageHandler, 
    filters
)

from ingrex_lib import ingrex

from collections import OrderedDict

# Setup argument parser
parser = argparse.ArgumentParser(description='Run the Telegram bot')
parser.add_argument('-d', '--debug', action='store_true', help='Run the bot in debug mode')
parser.add_argument('-v', '--verbose', action='store_true', help='Run the bot in verbose mode')
args = parser.parse_args()

# Setup logging
logging_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
if args.debug:
    logging.basicConfig(format=logging_format, level=logging.DEBUG)
elif args.verbose:
    logging.basicConfig(format=logging_format, level=logging.INFO)
else:
    logging.basicConfig(format=logging_format, level=logging.WARNING)


def is_json(myjson: str) -> bool:
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    await help_command(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    bot = context.bot
    await bot.sendMessage(
        chat_id=update.message.chat_id,
        text="I'm an Ingress IITC Bookmarks Navigation Helper Bot.\n" + 
        "\nJust copy and paste your Bookmarks right into this channel. " + 
        "I will reformat them into intel and gmaps link that can help you with navigation. " + 
        "I do not store anything, it's just reformatting of text.\n" +
        "\nEnlightened Hamburg"
    )

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the chat ID."""
    await context.bot.send_message(chat_id=update.message.chat_id, text=f"Your Chat ID: {update.message.chat_id}")
    logging.debug("ID command processed.")

def calc_dist(lat: float, lon: float, lat2: float, lng2: float) -> float:
    """Calculate the distance between two coordinates."""
    lat1 = float(lat)
    lng1 = float(lon)
    lat2 = float(lat2)
    lng2 = float(lng2)
    return round(ingrex.utils.calc_dist_hires(lat1, lng1, lat2, lng2) / 1000, 3)

def get_distance(link) -> str:
    """Calculate the distance for a given link."""
    lat1 = link["latLngs"][0]["lat"]
    lng1 = link["latLngs"][0]["lng"]
    lat2 = link["latLngs"][1]["lat"]
    lng2 = link["latLngs"][1]["lng"]
    dist = calc_dist(lat1, lng1, lat2, lng2)
    if dist < 1:
        return "{0} m".format(int(round(dist * 1000, 0)))
    else:
        return "{0} km".format(round(dist, 1))

chat_queue = {}

def is_bkmrk_json(text: str) -> bool:
    result = False
    if is_json(text):
        parsed_json = json.loads(text)
        if len(parsed_json) == 2:
            try:
               x = parsed_json['maps']
               x = parsed_json['portals']
               result = True
            except:
                result = False
    return result

async def format_bookmarks_and_message_them(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """Format bookmarks and send them as messages."""
    bot = context.bot
    chat_id = context.job.chat_id
    bkmrks = json.loads(text, object_pairs_hook=OrderedDict)
    for page in bkmrks:
        if page == 'portals':
            for folder in bkmrks[page]:
                folder_label = bkmrks[page][folder]['label']
                newline = ''
                url = 'http://maps.google.com/maps/dir/'
                line = '_Bookmarks Folder:_\n*{0}*\n\n_Bookmarks:_\n'.format(folder_label)
                for bkmrk in bkmrks[page][folder]['bkmrk']:
                    portal = bkmrks[page][folder]['bkmrk'][bkmrk]
                    p_label = portal['label']
                    url = '{url}{latlng}/'.format(url=url, latlng=portal['latlng'])
                    newline = '*{label}*\n\[ [intel](https://intel.ingress.com/intel?ll={latlng}&z=17&pll={latlng}) | [navi](https://maps.google.com/maps?daddr={latlng}) ] \n\n'.format(
                        label=p_label,
                        latlng=portal['latlng']
                    )
                    if len(line + newline) > 4096:
                        await bot.sendMessage(
                            chat_id=chat_id, 
                            text=line, 
                            parse_mode='Markdown', 
                            disable_web_page_preview=True
                        )
                        line = newline
                    else:
                        line += newline
                        
                if len(line) + len(newline) > 0:
                    await bot.sendMessage(
                        chat_id=chat_id, 
                        text=line, 
                        parse_mode='Markdown', 
                        disable_web_page_preview = True
                    )
                await bot.sendMessage(
                    chat_id=chat_id, 
                    text='_Navigation Route:_\n*{folder}*\n\[ [gmaps]({url}&nav=1) ]\n'.format(
                        folder = folder_label,
                        url = url),
                    parse_mode = 'Markdown',
                    disable_web_page_preview = True
                )

async def reply_to_pasted_json(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """Reply to pasted JSON."""
    bot = context.bot
    chat_id = context.job.chat_id
    if is_json(text):
        if is_bkmrk_json(text):
           await format_bookmarks_and_message_them(context, text)
        else:
            parsed_json = json.loads(text)
            await bot.sendMessage(chat_id=chat_id, text="Your JSON has {0} Objects".format(len(parsed_json)))
            try:
                line = ""
                for link in parsed_json:
                    lat1 = link["latLngs"][0]["lat"]
                    lon1 = link["latLngs"][0]["lng"]
                    lat2 = link["latLngs"][1]["lat"]
                    lon2 = link["latLngs"][1]["lng"]
                    newline = "Link from [here](https://intel.ingress.com/intel?ll={lat1},{lon1}&z=17&pll={lat1},{lon1}) to [there](https://intel.ingress.com/intel?ll={lat2},{lon2}&z=17&pll={lat2},{lon2}) is {dist} long.\n".format(
                        lat1 = lat1,
                        lon1 = lon1,
                        lat2 = lat2,
                        lon2 = lon2,
                        dist = get_distance(link)
                    )
                    if len(line + newline) > 4096:
                        await bot.sendMessage(chat_id=chat_id, text=line, parse_mode='Markdown', disable_web_page_preview=True)
                        line = newline
                    else:
                        line += newline
                if len(line) + len(newline) > 0:
                    await bot.sendMessage(chat_id=chat_id, text=line, parse_mode='Markdown', disable_web_page_preview=True)
            except (KeyError) as e:
                await bot.sendMessage(chat_id=chat_id, text="I don't know what kind of JSON this is.")
            except:
                await bot.sendMessage(chat_id=chat_id, text="I don't know what this is.")
                if chat_id == admin_chat_id:
                    await bot.sendMessage(chat_id=chat_id, text='Unexpected error:\n {0}'.format(sys.exc_info()[0]))
                print('Unexpected error:', sys.exc_info()[0])
                raise

async def callback_chat_queue(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for chat queue."""
    job = context.job
    chat_id = job.chat_id
    q = chat_queue.get(job.chat_id)
    # time.sleep(0)
    s = ""
    if not q.empty():
        while not q.empty():
            next = q.get()
            s += next
            # time.sleep(0)
    if len(s) > 0:
        await reply_to_pasted_json(context, s)

async def message_buffer(update, context) -> None:
    """Buffer incoming messages."""
    if context not in chat_queue:
        chat_queue.update({update.message.chat_id: queue.Queue()})
    
    q = chat_queue.get(update.message.chat_id)
    if q is None:
        logging.critical("no chatqueue found")
    
    q.put(update.message.text)
    context.job_queue.run_once(callback_chat_queue, 1, chat_id=update.message.chat_id)



async def post_init(application: Application) -> None:
    
    await application.bot.set_my_commands([
        ('start', 'Starts the bot'),
        ('help','Posts help message'),
        ('id','Posts your telegram id')
    ])
    global secrets
    owner_chat_id = secrets['BOT_OWNER_TELEGRAM_ID']
    if not owner_chat_id:
        logging.critical("Bot owner Chat could not be loaded. Please check your .secrets file.")
        return
        
    bot_started_message = f"Bot started: {__file__}"
    await application.bot.send_message(owner_chat_id, text=bot_started_message)
    logging.info("Startup message sent to bot owner.")
    secrets = {}
    print('===================================================')
    print('==================  Bot started  ==================')
    print('===================================================')


# async def send_startup_message(bot, owner_chat_id) -> None:
#     """Send a startup message."""
#     bot_started_message = f"Bot started: {__file__}"
#     async with bot:
#         await bot.send_message(owner_chat_id, text=bot_started_message)
#     logging.info("Startup message sent to bot owner.")
#     print('Bot started')
    

def main() -> None:
    """Main function."""
    
    def load_secrets():
        """Load secrets from .secrets file."""
        secrets = {}
        with open('.secrets', 'r') as file:
            lines = file.readlines()
            for line in lines:
                key, value = line.strip().split('=', 1)
                secrets[key] = value
        return secrets
        
    global secrets
    secrets = load_secrets()
    
    bot_token = secrets['BOOKMARKS_TO_NAVLINK_BOT_TOKEN']
    if not bot_token:
        logging.critical("Bot token could not be loaded. Please check your .secrets file.")
        return

    # Create the Application object and provide your bot token.
    builder = Application.builder()
    builder.token(bot_token)
    builder.post_init(post_init)
    application = builder.build()
    
    # Add the CommandHandler
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    
    # Create a CommandHandler for the 'id' command and add it to the application
    application.add_handler(CommandHandler('id', get_id))
    
    application.add_handler(MessageHandler(filters.TEXT, message_buffer))
    
    # Start the bot
    application.run_polling()



if __name__ == '__main__':
    main()
