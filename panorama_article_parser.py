import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

BASE_URL = "https://panorama.pub"

MONTHS = {
    "янв.": "01",
    "февр.": "02",
    "мар.": "03",
    "апр.": "04",
    "мая": "05",
    "июн.": "06",
    "июл.": "07",
    "авг.": "08",
    "сент.": "09",
    "окт.": "10",
    "нояб.": "11",
    "дек.": "12"
}


def get_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error fetching {url}: {response.status_code}")
        return None


def extract_article_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    article_links = []
    articles = soup.find_all('a', href=True,
                             class_='flex flex-col rounded-md hover:text-secondary hover:bg-accent/[.1] mb-2')
    for article in articles:
        link = BASE_URL + article['href']
        article_links.append(link)
    return article_links


def get_all_pages(section_url):
    page_num = 1
    all_article_links = []

    while True:
        url = f"{section_url}?page={page_num}"
        html = get_html(url)
        if not html:
            break

        article_links = extract_article_links(html)
        if not article_links:
            break

        all_article_links.extend(article_links)
        page_num += 1

    return all_article_links


def parse_article_details(article_url):
    html = get_html(article_url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # заголовок
    title_tag = soup.find('h1', class_='font-bold text-2xl md:text-3xl lg:text-4xl pl-1 pr-2 self-center')
    title = title_tag.text.strip() if title_tag else "N/A"

    # время публикации, автор, тэги
    meta_info = soup.find('div', class_='flex flex-col gap-x-3 gap-y-1.5 flex-wrap sm:flex-row')
    time_published_raw = meta_info.find('svg',
                                        {'class': 'h-4 w-4 inline-block'}).next_sibling.strip() if meta_info else "N/A"
    time_published = convert_date(time_published_raw)

    author_tag = meta_info.find('div', itemprop='author') if meta_info else None
    author = author_tag.find('meta', itemprop='name')['content'] if author_tag else "N/A"
    tags = [tag.text for tag in meta_info.find_all('a', class_='badge')] if meta_info else []

    # текст статьи
    article_body = soup.find('div', class_='entry-contents pr-0 md:pr-8')
    paragraphs = article_body.find_all('p') if article_body else []
    article_text = ' '.join([p.text for p in paragraphs])

    return {
        "URL": article_url,
        "Title": title,
        "Time published": time_published,
        "Author": author,
        "Tags": ', '.join(tags),
        "Article text": article_text
    }


def convert_date(date_str):
    now = datetime.now()

    if "сегодня" in date_str:
        return now.strftime("%Y-%m-%d")
    elif "позавчера" in date_str:
        return (now - timedelta(days=2)).strftime("%Y-%m-%d")
    elif "вчера" in date_str:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        for month_rus, month_num in MONTHS.items():
            if month_rus in date_str:
                date_str = date_str.replace(month_rus, month_num)
        try:
            return datetime.strptime(date_str.split(' г.,')[0], "%d %m %Y").strftime("%Y-%m-%d")
        except ValueError:
            return date_str


def save_to_excel(data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Data saved to {filename}")


def main():
    sections = {
        "Наука": "/science",
        "Экономика": "/economics",
        "Политика": "/politics",
        "Общество": "/society"
    }

    all_articles = []

    for name, path in sections.items():
        section_url = BASE_URL + path
        print(f"Collecting articles from section: {name}")
        article_links = get_all_pages(section_url)
        print(f"Found {len(article_links)} articles in {name} section.")

        for link in article_links:
            article_details = parse_article_details(link)
            if article_details:
                all_articles.append(article_details)

        # сохранение промежуточного состояния данных
        save_to_excel(all_articles, f"panorama_articles_{name}.xlsx")
        print("\n")

    # сохранение всех данных в один файл
    save_to_excel(all_articles, "panorama_articles_all.xlsx")
    print("All articles saved to panorama_articles_all.xlsx")


if __name__ == "__main__":
    main()
