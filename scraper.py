import json
import requests
from bs4 import BeautifulSoup

def scrape_book_marks(book_slug):
    # Hardcoded /all/ path to capture the full list page you found
    url = f"https://bookmarks.reviews/reviews/all/{book_slug}/"
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
    
    # Target all main text blocks to harvest records sequentially
    for div in soup.find_all("div"):
        text = div.get_text(" ", strip=True)
        
        if text.startswith(("Rave ", "Positive ", "Mixed ", "Pan ")):
            try:
                parts = text.split(" ", 1)
                rating = parts[0].strip()
                remainder = parts[1].strip()
                
                if "," in remainder:
                    meta_parts = remainder.split(",", 1)
                    critic = meta_parts[0].strip()
                    outlet_raw = meta_parts[1].strip()
                    
                    # Extract source outlet and isolate review snippet body text
                    outlet = outlet_raw.split("...")[0].replace("Read Full Review >>", "").strip()
                    snippet = text.split(critic)[-1].replace("Read Full Review >>", "").strip()
                    snippet = snippet.replace(outlet_raw.split("...")[0], "", 1).lstrip(", ").strip()
                    
                    if "Similar Books" in text or len(critic) > 40 or len(outlet) > 40:
                        continue
                        
                    if not any(d['critic'] == critic for d in reviews_extracted):
                        reviews_extracted.append({
                            "critic": critic,
                            "source_outlet": outlet,
                            "aggregated_rating": rating,
                            "review_snippet": snippet[:300] + "..." if len(snippet) > 300 else snippet
                        })
            except Exception:
                continue

    output_filename = f"{book_slug}_reviews.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(reviews_extracted, f, indent=4, ensure_ascii=False)
    print(f"Success! Saved {len(reviews_extracted)} reviews to {output_filename}")

if __name__ == "__main__":
    scrape_book_marks("conclave")
