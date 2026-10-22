import json, os, urllib.parse, urllib.request

SERPAPI_KEY = os.environ["SERPAPI_KEY"]
TG_TOKEN = os.environ["TELEGRAM_TOKEN"]
TG_CHAT = os.environ["TELEGRAM_CHAT_ID"]

QUERIES = {"Osmo Pocket 3": "pocket 3", "Osmo Pocket 4": "pocket 4"}
MIN_PRICE = 150  # aksesuarları ele
STATE_FILE = "prices.json"


def search(q):
    params = urllib.parse.urlencode({
        "engine": "google_shopping", "q": q,
        "gl": "fi", "hl": "fi", "google_domain": "google.fi",
        "api_key": SERPAPI_KEY,
    })
    with urllib.request.urlopen(f"https://serpapi.com/search.json?{params}") as r:
        return json.load(r).get("shopping_results", [])


def telegram(text):
    data = urllib.parse.urlencode({
        "chat_id": TG_CHAT, "text": text, "disable_web_page_preview": "true"
    }).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data)


def main():
    try:
        old = json.load(open(STATE_FILE))
    except FileNotFoundError:
        old = {}
    new, alerts, cheapest = {}, [], []

    for q, must in QUERIES.items():
        rows = []
        for it in search(q):
            title, price = it.get("title", ""), it.get("extracted_price")
            if must not in title.lower() or not price or price < MIN_PRICE:
                continue
            key = f"{it.get('source')}|{title}"
            new[key] = price
            link = it.get("product_link") or it.get("link", "")
            rows.append((price, it.get("source"), title, link))
            if key in old and price < old[key]:
                alerts.append(f"📉 {it.get('source')}: {title}\n{old[key]}€ → {price}€\n{link}")
        rows.sort()
        if rows:
            cheapest.append(f"{q} en ucuz: {rows[0][0]}€ ({rows[0][1]})")

    if alerts:
        telegram("Fiyat düştü!\n\n" + "\n\n".join(alerts) + "\n\n" + "\n".join(cheapest))
    json.dump(new, open(STATE_FILE, "w"), ensure_ascii=False, indent=1)
    print("\n".join(cheapest) or "sonuç yok")


if __name__ == "__main__":
    main()
