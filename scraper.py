cat << 'EOF' > scraper.py
import json
import re
import requests
from bs4 import BeautifulSoup

def scrape_book_marks(book_slug):
    url = f"https://bookmarks.reviews/reviews/{book_slug}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    }
    
    print(f"Fetching reviews from: {url}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page. Status: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    reviews_extracted = []
    
    # Book Marks wraps each critic review in a div block inside the main content area
    # Let's isolate the main "What The Reviewers Say" text blocks
    review_cards = soup.find_all(["div", "article"], class_=re.compile(r"review|critic|card|post|item"))
    
    # Fallback to general div parsing if semantic classes are hidden
    if not review_cards or len(review_cards) < 3:
        review_cards = soup.find_all("div")

    for card in review_cards:
        try:
            text = card.get_text(" ", strip=True)
            
            # Look for lines that establish a rating flag (Rave, Positive, Mixed, Pan)
            # closely followed by the critic name and the publication outlet
            if any(r in text for r in ["Rave", "Positive", "Mixed", "Pan"]):
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                if not lines:
                    lines = [text]
                
                # Check for standard review structure patterns text matches
                match = re.search(r'(Rave|Positive|Mixed|Pan)\s+([A-Za-z\s\.\-]+),\s+([A-Za-z\s&,\.\-\'\"]+)', text)
                if match:
                    rating = match.group(1)
                    critic = match.group(2).strip()
                    outlet = match.group(3).strip()
                    
                    # Grab review snippet text below the main match
                    snippet = ""
                    snippet_el = card.find(["div", "p", "span"], class_=re.compile(r"snippet|body|text|content"))
                    if snippet_el:
                        snippet = snippet_el.text.strip()
                    else:
                        # Fallback parsing line context logic
                        snippet = text.split(outlet)[-1].replace("Read Full Review >>", "").strip()

                    # Prevent duplicate pushes inside global loops
                    if not any(d['critic'] == critic and d['source_outlet'] == outlet for d in reviews_extracted):
                        reviews_extracted.append({
                            "critic": critic,
                            "source_outlet": outlet,
                            "aggregated_rating": rating,
                            "review_snippet": snippet[:400] + "..." if len(snippet) > 400 else snippet
                        })
        except Exception:
            continue

    # Clean up edge cases from generic matches (e.g. matching sidebar sections)
    reviews_extracted = [r for r in reviews_extracted if "Similar Books" not in r['source_outlet']]

    output_filename = f"{book_slug}_reviews.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(reviews_extracted, f, indent=4, ensure_ascii=False)
    print(f"Success! Saved {len(reviews_extracted)} reviews to {output_filename}")

if __name__ == "__main__":
    scrape_book_marks("conclave")
EOF
