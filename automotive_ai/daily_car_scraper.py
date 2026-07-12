import os
import datetime
import schedule
import time
import feedparser
import wikipedia
import trafilatura
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
OUTPUT_FOLDER = "car_reports"

CAR_KEYWORDS = [
    "car","automobile","vehicle","ev","electric car","sedan",
    "suv","hatchback","hybrid","toyota","honda","bmw","audi",
    "tata","mahindra","maruti","hyundai","kia","tesla"
]

# Automotive sources 
RSS_FEEDS = [
    "https://www.autocarindia.com/RSS/rss.ashx",
    "https://www.cardekho.com/rss-feed.xml",

    "https://www.motortrend.com/feed/",
    "https://www.topgear.com/rss.xml",
    "https://www.carscoops.com/feed/",
    "https://www.autoblog.com/rss.xml",

    "https://news.google.com/rss/search?q=cars+automotive"
]

def is_car_related(text):

    text = text.lower()
    return any(keyword in text for keyword in CAR_KEYWORDS)


def extract_full_text(url):

    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)

        if text and is_car_related(text):
            return text

    except:
        pass

    return None

def scrape_sources():

    all_content = ""

    for feed_url in RSS_FEEDS:

        print(f"Reading feed: {feed_url}")

        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:30]:

            link = entry.link
            title = entry.title

            if not is_car_related(title):
                continue

            print("Scraping:", title)

            article_text = extract_full_text(link)

            if article_text:
                all_content += "\n\n" + title + "\n\n" + article_text

    return all_content

def get_wikipedia_car_data():

    print("Fetching wikipedia car data...")

    topics = [
        "Automobile",
        "List of automobile manufacturers",
        "Electric car",
        "Car classification"
    ]

    content = ""

    for topic in topics:
        try:
            page = wikipedia.page(topic)
            content += "\n\n" + page.content
        except:
            pass

    return content

def create_pdf(text):

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    today = datetime.date.today().strftime("%Y-%m-%d")

    filepath = os.path.join(OUTPUT_FOLDER, f"cars_{today}.pdf")

    doc = SimpleDocTemplate(filepath)

    styles = getSampleStyleSheet()
    story = []

    for line in text.split("\n"):
        if line.strip():
            story.append(Paragraph(line, styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

    doc.build(story)

    print("Saved:", filepath)

def run_pipeline():

    print("Starting automotive data collection...")

    content = ""

    content += scrape_sources()
    content += get_wikipedia_car_data()

    create_pdf(content)

    print("DONE.")

run_pipeline()

schedule.every(24).hours.do(run_pipeline)

print("Scheduler running...")

while True:
    schedule.run_pending()
    time.sleep(60)