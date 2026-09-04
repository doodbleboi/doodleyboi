import json
import requests
from bs4 import BeautifulSoup

def scrape_book_marks(book_slug):
    url = f"https://bookmarks.reviews/reviews/{book_slug}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    }
    print(f"Fetching reviews from: {url}")
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        print(f"Network error: {e}")
        return

    if response.status_code != 200:
        print(f"Failed to fetch page. Status: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    reviews_extracted = []

    for review in soup.find_all("div", class_="what-reviewers-say"):
        for div in review.find_all("div"):
            text = div.get_text(" ", strip=True)
            if text.startswith(("Rave ", "Positive ", "Mixed ", "Pan ")) and "," in text:
                try:
                    rating_part, remainder = text.split(" ", 1)
                    meta, snippet_part = remainder.split(",", 1) if "," in remainder else (remainder, "")
                    critic = meta.strip()
                    outlet = snippet_part.split("...")[0].strip() if "..." in snippet_part else ""
                    snippet = snippet_part.split("...", 1)[-1].replace("Read Full Review >>", "").strip() if "..." in snippet_part else snippet_part

                    if not any(d["critic"] == critic for d in reviews_extracted) and len(critic) < 50:
                        reviews_extracted.append({
                            "critic": critic,
                            "source_outlet": outlet,
                            "aggregated_rating": rating_part,
                            "review_snippet": snippet[:300]
                        })
                except Exception:
                    continue

    output_filename = f"{book_slug}_reviews.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(reviews_extracted, f, indent=4, ensure_ascii=False)
    print(f"Success! Saved {len(reviews_extracted)} reviews to {output_filename}")

if __name__ == "__main__":
    scrape_book_marks("conclave")
