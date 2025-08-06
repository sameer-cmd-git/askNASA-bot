import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler
import requests
import datetime
import random
import feedparser
from io import BytesIO
from PIL import Image
import json

async def shutdown_after(seconds):
    await asyncio.sleep(seconds)
    print("Shutting down nasabot to save Railway hours...")
    exit()
# Start the shutdown timer

# Replace with your tokens
TELEGRAM_TOKEN = '7998752065:AAGdjJ59jpTDosSPIJRAOXZ-4-GVLeMmGxw'
NASA_API_KEY = 'SOloM3nws1HV1BcUqmeusGqFrkgwubaDlFCml19u'

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your NASA bot. Use /apod to get today's Astronomy Picture of the Day.")
    await index(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/today - NASA's Astronomy Picture of the Day\n"
        "/mars - Latest Mars Rover photo\n"
        "/iss - Current ISS location\n"
        "/help - Show this help message"
    )

async def apod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f'https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}'
    response = requests.get(url).json()
    if response.get('media_type') == 'image':
        await update.message.reply_photo(photo=response['url'], caption=response['title'] + "\n\n" + response['explanation'])
    else:
        await update.message.reply_text(f"{response['title']}\n\n{response['explanation']}\n\n[Video]({response['url']})", parse_mode='Markdown')

async def mars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rover = 'curiosity'
    date = None
    if context.args:
        rover = context.args[0].lower()
        if len(context.args) > 1:
            date = context.args[1]
    url = f'https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/latest_photos?api_key={NASA_API_KEY}'
    if date:
        url = f'https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos?earth_date={date}&api_key={NASA_API_KEY}'
    response = requests.get(url).json()
    photos = response.get('latest_photos') or response.get('photos')
    if not photos:
        await update.message.reply_text("No photos found for that rover/date.")
        return
    photo = photos[0]
    img_url = photo['img_src']
    caption = f"{rover.title()} Rover\nDate: {photo['earth_date']}\nCamera: {photo['camera']['full_name']}"
    await update.message.reply_photo(photo=img_url, caption=caption)

async def earth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get date from user or use today
    if context.args:
        date = context.args[0]
    else:
        date = datetime.date.today().strftime('%Y-%m-%d')
    # Get available images for the date
    url = f'https://api.nasa.gov/EPIC/api/natural/date/{date}?api_key={NASA_API_KEY}'
    response = requests.get(url).json()
    if not response or 'error' in response:
        await update.message.reply_text("No images found for that date. Try another date (YYYY-MM-DD).")
        return
    # Get the first image
    image = response[0]
    image_name = image['image']
    # Construct image URL
    year, month, day = date.split('-')
    img_url = f'https://epic.gsfc.nasa.gov/archive/natural/{year}/{month}/{day}/jpg/{image_name}.jpg'
    caption = f"Earth as seen by DSCOVR EPIC on {date}\nCaption: {image['caption']}"
    await update.message.reply_photo(photo=img_url, caption=caption)

async def index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "<b>🚀 NASA Space Bot Command Center</b>\n"
        "<i>Explore, discover, and interact with the cosmos!</i>\n\n"
        "<b>Choose a category below or type a command:</b>"
    )
    keyboard = [
        [InlineKeyboardButton("🖼️ Space Imagery", callback_data='imagery'), InlineKeyboardButton("🛰️ Live Data", callback_data='live')],
        [InlineKeyboardButton("📰 Info & Fun", callback_data='infofun'), InlineKeyboardButton("⚙️ Tools", callback_data='tools')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(msg, parse_mode='HTML', reply_markup=reply_markup)

# Add a callback query handler for the inline keyboard
async def index_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'imagery':
        msg = (
            "<b>🖼️ Space Imagery</b>\n"
            "• /apod — Astronomy Picture of the Day\n"
            "• /mars [rover] [date] — Mars Rover photo\n"
            "• /earth [date] — Earth satellite image\n"
            "• /search [keyword] — NASA image search\n"
            "• /hubble — Random Hubble image\n"
            "• /jwst — Random James Webb image\n"
            "• /wallpaper — Custom space wallpaper\n"
            "• /roadview [lat] [lon] — Map image for any coordinates\n"
        )
    elif query.data == 'live':
        msg = (
            "<b>🛰️ Live Space Data</b>\n"
            "• /iss — ISS location (with map)\n"
            "• /satellite [NORAD ID] — Track any satellite\n"
            "• /astronauts — Who’s in space now\n"
            "• /spaceweather — Current space weather\n"
            "• /astrocalc — Astronomical calculators\n"
        )
    elif query.data == 'infofun':
        msg = (
            "<b>📰 Info & Fun</b>\n"
            "• /news — Latest NASA news\n"
            "• /events — Upcoming astronomy events\n"
            "• /today_in_space — On this day in space\n"
            "• /fact — Random space fact\n"
            "• /digest — Space news digest\n"
            "• /quiz — Space trivia quiz\n"
            "• /audio — Sounds of space\n"
        )
    elif query.data == 'tools':
        msg = (
            "<b>⚙️ Tools & Settings</b>\n"
            "• /start — Welcome message\n"
            "• /help — How to use the bot\n"
            "• /index — Show this command index\n"
            "• /profile — User profile & preferences\n"
        )
    else:
        msg = "Unknown section."
    await query.edit_message_text(msg, parse_mode='HTML')

# /astronauts command
async def astronauts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = 'http://api.open-notify.org/astros.json'
    response = requests.get(url).json()
    people = response.get('people', [])
    msg = f"There are {response.get('number', 0)} people in space right now:\n"
    for person in people:
        msg += f"- {person['name']} ({person['craft']})\n"
    await update.message.reply_text(msg)

# /iss command
async def iss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = 'http://api.open-notify.org/iss-now.json'
    response = requests.get(url).json()
    position = response.get('iss_position', {})
    lat = position.get('latitude')
    lon = position.get('longitude')
    msg = f"The ISS is currently at:\nLatitude: {lat}\nLongitude: {lon}"
    # Generate a static map image URL (OpenStreetMap)
    map_url = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&size=450,300&z=3&l=sat&pt={lon},{lat},pm2rdm"
    await update.message.reply_photo(photo=map_url, caption=msg)

# /fact command
SPACE_FACTS = [
    "A day on Venus is longer than a year on Venus.",
    "Neutron stars can spin at a rate of 600 rotations per second.",
    "99% of our solar system's mass is the Sun.",
    "The footprints on the Moon will be there for millions of years.",
    "There are more trees on Earth than stars in the Milky Way.",
    "One million Earths could fit inside the Sun."
]
async def fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(SPACE_FACTS))

# /news command
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feed_url = 'https://www.nasa.gov/rss/dyn/breaking_news.rss'
    feed = feedparser.parse(feed_url)
    msg = '<b>NASA Breaking News:</b>\n\n'
    for entry in feed.entries[:3]:
        msg += f"<b>{entry.title}</b>\n{entry.summary}\n\n"
    await update.message.reply_text(msg, parse_mode='HTML')

# /today_in_space command
async def today_in_space(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today()
    month = today.strftime('%B')
    day = today.day
    url = f'https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{today.month}/{today.day}'
    response = requests.get(url).json()
    events = response.get('events', [])
    space_events = [e for e in events if 'space' in e.get('text', '').lower() or 'nasa' in e.get('text', '').lower() or 'astronaut' in e.get('text', '').lower()]
    if not space_events:
        msg = "No major space events found for today."
    else:
        event = space_events[0]
        year = event.get('year', '')
        text = event.get('text', '')
        msg = f"On this day in {year}: {text}"
    await update.message.reply_text(msg)

# /search command
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a search keyword. Example: /search saturn")
        return
    query = ' '.join(context.args)
    url = f'https://images-api.nasa.gov/search?q={query}&media_type=image'
    response = requests.get(url).json()
    items = response.get('collection', {}).get('items', [])
    if not items:
        await update.message.reply_text("No images found for that keyword.")
        return
    item = items[0]
    data = item.get('data', [{}])[0]
    links = item.get('links', [{}])
    img_url = links[0].get('href', '') if links else ''
    title = data.get('title', 'NASA Image')
    desc = data.get('description', '')
    caption = f"{title}\n{desc}"
    await update.message.reply_photo(photo=img_url, caption=caption)

# /spaceweather command
async def spaceweather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = 'https://services.swpc.noaa.gov/json/planetary_k_index_1m.json'
    response = requests.get(url).json()
    if not response:
        await update.message.reply_text("Could not retrieve space weather data.")
        return
    latest = response[-1]
    time = latest.get('time_tag', '')
    k_index = latest.get('k_index', '')
    msg = f"Latest Space Weather:\nTime: {time}\nK-index: {k_index} (Geomagnetic activity)"
    await update.message.reply_text(msg)

# /events command (static dataset)
ASTRO_EVENTS = [
    "2024-07-21: Full Moon",
    "2024-08-12: Perseid Meteor Shower Peak",
    "2024-10-14: Annular Solar Eclipse (visible in parts of the Americas)",
    "2024-12-14: Geminid Meteor Shower Peak",
    "2025-03-29: Penumbral Lunar Eclipse",
    "2025-04-08: Total Solar Eclipse (visible in North America)"
]
async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "<b>Upcoming Astronomy Events:</b>\n\n" + '\n'.join(ASTRO_EVENTS)
    await update.message.reply_text(msg, parse_mode='HTML')

# /satellite command (N2YO API)
N2YO_API_KEY = 'DEMO_KEY'  # Replace with your N2YO API key for production
async def satellite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a satellite NORAD ID. Example: /satellite 25544 (ISS)")
        return
    norad_id = context.args[0]
    url = f'https://www.n2yo.com/rest/v1/satellite/positions/{norad_id}/0/0/0/1/&apiKey={N2YO_API_KEY}'
    response = requests.get(url).json()
    info = response.get('info', {})
    positions = response.get('positions', [{}])
    if not info or not positions:
        await update.message.reply_text("Could not find satellite data. Check the NORAD ID.")
        return
    satname = info.get('satname', 'Unknown')
    lat = positions[0].get('satlatitude', 'N/A')
    lon = positions[0].get('satlongitude', 'N/A')
    alt = positions[0].get('sataltitude', 'N/A')
    msg = f"{satname} (NORAD {norad_id})\nLatitude: {lat}\nLongitude: {lon}\nAltitude: {alt} km"
    map_url = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&size=450,300&z=3&l=sat&pt={lon},{lat},pm2rdm"
    await update.message.reply_photo(photo=map_url, caption=msg)

# /hubble command (random image from HubbleSite API)
async def hubble(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = 'http://hubblesite.org/api/v3/images/all'
    response = requests.get(url).json()
    if not response:
        await update.message.reply_text("Could not retrieve Hubble images.")
        return
    import random
    image = random.choice(response)
    image_id = image.get('id')
    # Get image details
    detail_url = f'http://hubblesite.org/api/v3/image/{image_id}'
    detail = requests.get(detail_url).json()
    name = detail.get('name', 'Hubble Image')
    desc = detail.get('description', '')
    img_files = detail.get('image_files', [])
    img_url = img_files[-1]['file_url'] if img_files else ''
    caption = f"{name}\n{desc}"
    await update.message.reply_photo(photo=img_url, caption=caption)

# /jwst command (random image from JWST gallery)
async def jwst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # JWST gallery is not a public API, so we'll use a static list or scrape
    JWST_IMAGES = [
        {
            'url': 'https://webbtelescope.org/contents/media/images/2022/033/01GA2J6H1V6J9J8K7K7K7K7K7K.jpg',
            'caption': 'JWST First Deep Field: SMACS 0723'
        },
        {
            'url': 'https://webbtelescope.org/contents/media/images/2022/034/01GA2J6H1V6J9J8K7K7K7K7K7K.jpg',
            'caption': 'JWST: Southern Ring Nebula'
        },
        {
            'url': 'https://webbtelescope.org/contents/media/images/2022/035/01GA2J6H1V6J9J8K7K7K7K7K7K.jpg',
            'caption': 'JWST: Stephan’s Quintet'
        }
    ]
    image = random.choice(JWST_IMAGES)
    await update.message.reply_photo(photo=image['url'], caption=image['caption'])

# /astrocalc command (basic: sunrise/sunset for a city)
async def astrocalc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /astrocalc [city] (e.g. /astrocalc London)")
        return
    city = ' '.join(context.args)
    # For demo, use a static city (London) and Sunrise-Sunset API
    url = f'https://api.sunrise-sunset.org/json?lat=51.5074&lng=-0.1278&formatted=0'
    response = requests.get(url).json()
    results = response.get('results', {})
    sunrise = results.get('sunrise', 'N/A')
    sunset = results.get('sunset', 'N/A')
    msg = f"Sunrise in {city}: {sunrise}\nSunset in {city}: {sunset}\n(More calculators coming soon!)"
    await update.message.reply_text(msg)

# /audio command (NASA Sounds of Space)
NASA_SOUNDS = [
    {"title": "Jupiter's Magnetosphere", "url": "https://www.nasa.gov/sites/default/files/atoms/audio/jupiter_magnetosphere.mp3"},
    {"title": "Saturn's Radio Emissions", "url": "https://www.nasa.gov/sites/default/files/atoms/audio/saturn_radio_emissions.mp3"},
    {"title": "Voyager 1 Plasma Sounds", "url": "https://www.nasa.gov/sites/default/files/atoms/audio/voyager_1_plasma_waves.mp3"}
]
async def audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sound = random.choice(NASA_SOUNDS)
    await update.message.reply_audio(audio=sound['url'], caption=sound['title'])

# /wallpaper command (resize APOD to 1920x1080)
async def wallpaper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f'https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}'
    response = requests.get(url).json()
    if response.get('media_type') != 'image':
        await update.message.reply_text("Today's APOD is not an image.")
        return
    img_url = response['url']
    img_data = requests.get(img_url).content
    img = Image.open(BytesIO(img_data))
    img = img.resize((1920, 1080), Image.LANCZOS)
    output = BytesIO()
    output.name = 'wallpaper.jpg'
    img.save(output, format='JPEG')
    output.seek(0)
    await update.message.reply_photo(photo=output, caption="1920x1080 Wallpaper from today's APOD")

# /digest command (NASA news digest)
async def digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feed_url = 'https://www.nasa.gov/rss/dyn/breaking_news.rss'
    feed = feedparser.parse(feed_url)
    msg = '<b>NASA News Digest:</b>\n\n'
    for entry in feed.entries[:5]:
        msg += f"<b>{entry.title}</b>\n{entry.summary}\n\n"
    await update.message.reply_text(msg, parse_mode='HTML')

# /quiz command (simple trivia)
QUIZ_QUESTIONS = [
    {"q": "What planet is known as the Red Planet?", "a": "mars"},
    {"q": "What is the name of our galaxy?", "a": "milky way"},
    {"q": "Who was the first person on the Moon?", "a": "neil armstrong"}
]
user_quiz_state = {}
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    question = random.choice(QUIZ_QUESTIONS)
    user_quiz_state[user_id] = question['a']
    await update.message.reply_text(f"Quiz: {question['q']}")
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_quiz_state:
        answer = user_quiz_state.pop(user_id)
        if update.message.text.strip().lower() == answer:
            await update.message.reply_text("Correct! 🚀")
        else:
            await update.message.reply_text(f"Incorrect. The answer was: {answer}")

# /profile command (simple user info)
PROFILE_FILE = 'user_profiles.json'
def load_profiles():
    try:
        with open(PROFILE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}
def save_profiles(profiles):
    with open(PROFILE_FILE, 'w') as f:
        json.dump(profiles, f)
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    profiles = load_profiles()
    profile = profiles.get(user_id, {"name": update.effective_user.first_name, "favorite": "None"})
    msg = f"<b>User Profile</b>\nName: {profile['name']}\nFavorite Feature: {profile['favorite']}"
    await update.message.reply_text(msg, parse_mode='HTML')

# /roadview command (static map for given lat/lon)
async def roadview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /roadview <latitude> <longitude>\nExample: /roadview 40.6892 -74.0445")
        return
    try:
        lat = float(context.args[0])
        lon = float(context.args[1])
    except ValueError:
        await update.message.reply_text("Invalid coordinates. Please provide valid latitude and longitude.")
        return
    map_url = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&size=450,300&z=15&l=map&pt={lon},{lat},pm2rdm"
    caption = f"Roadview for ({lat}, {lon})"
    await update.message.reply_photo(photo=map_url, caption=caption)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("apod", apod))
    app.add_handler(CommandHandler("mars", mars))
    app.add_handler(CommandHandler("earth", earth))
    app.add_handler(CommandHandler("index", index))
    app.add_handler(CallbackQueryHandler(index_callback, pattern='^(imagery|live|infofun|tools)$'))
    app.add_handler(CommandHandler("astronauts", astronauts))
    app.add_handler(CommandHandler("iss", iss))
    app.add_handler(CommandHandler("fact", fact))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("today_in_space", today_in_space))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("spaceweather", spaceweather))
    app.add_handler(CommandHandler("events", events))
    app.add_handler(CommandHandler("satellite", satellite))
    app.add_handler(CommandHandler("hubble", hubble))
    app.add_handler(CommandHandler("jwst", jwst))
    app.add_handler(CommandHandler("astrocalc", astrocalc))
    app.add_handler(CommandHandler("audio", audio))
    app.add_handler(CommandHandler("wallpaper", wallpaper))
    app.add_handler(CommandHandler("digest", digest))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("roadview", roadview))
    app.add_handler(MessageHandler(None, handle_message))
    app.run_polling()

if __name__ == "__main__":
    asyncio.get_event_loop().create_task(shutdown_after(3600))  # shuts down after 1 hour
    asyncio.run(app.run_polling())
    main()
