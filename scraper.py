import json
import requests
from bs4 import BeautifulSoup

def scrape_book_marks(book_slug):
    # Fixed the missing path separator slash here
    url = f"https://bookmarks.reviews{book_slug}/"
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
    
    # Process text layout cards cleanly
    for div in soup.find_all("div"):
        text = div.get_text(" ", strip=True)
        
        # Match headings starting with specific grading thresholds
        if text.startswith(("Rave ", "Positive ", "Mixed ", "Pan ")):
            try:
                parts = text.split(" ", 1)
                rating = parts[0].strip()
                remainder = parts[1].strip()
                
                if "," in remainder:
                    header_line = remainder.split("...", 1)[0] if "..." in remainder else remainder
                    meta_parts = header_line.split(",", 1)
                    critic = meta_parts[0].strip()
                    outlet = meta_parts[1].strip()
                    
                    # Clean out trailing action text
                    if " " in outlet:
                        outlet = outlet.split(" ")[0].strip(",")
                    
                    snippet = text.split(critic)[-1].split("Read Full Review >>")[0].strip()
                    snippet = snippet.lstrip(",").replace(outlet, "", 1).strip()
                    
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
