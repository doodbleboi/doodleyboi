import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_external_body(session, target_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        print(f"   --> Launching sub-request to publisher: {target_url}")
        res = session.get(target_url, headers=headers, timeout=10)
        if res.status_code != 200:
            return f"[Could not download full text. HTTP Status {res.status_code}]"
            
        sub_soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = sub_soup.find_all("p")
        full_text_fragments = []
        
        for p in paragraphs:
            txt = p.get_text(" ", strip=True)
            if len(txt) > 60 and not any(k in txt.lower() for k in ["cookie", "subscribe", "sign in", "all rights reserved"]):
                if txt not in full_text_fragments:
                    full_text_fragments.append(txt)
                    
        if full_text_fragments:
            return " ".join(full_text_fragments[:25])
            
        return "[Full review body text not readable via semantic selectors]"
    except Exception as e:
        return f"[Failed to parse due to network exception or paywall: {e}]"

def scrape_book_marks(book_slug):
    base_url = f"https://bookmarks.reviews/reviews/all/{book_slug}/"
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    })
    
    print(f"Connecting to root endpoint: {base_url}")
    response = session.get(base_url)
    if response.status_code != 200:
        print(f"Failed to fetch page. Status: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    reviews_extracted = []
    
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
                    outlet = outlet_raw.split("...")[0].replace("Read Full Review >>", "").strip()
                    
                    if "Similar Books" in text or len(critic) > 40 or len(outlet) > 40:
                        continue
                        
                    outbound_url = None
                    link_element = div.find("a")
                    if link_element and link_element.get("href"):
                        outbound_url = urljoin(base_url, link_element.get("href"))

                    if not any(d['critic'] == critic for d in reviews_extracted):
                        full_review_content = "[No external hyperlink found]"
                        if outbound_url and "bookmarks.reviews" not in outbound_url:
                            full_review_content = extract_external_body(session, outbound_url)
                        
                        reviews_extracted.append({
                            "critic": critic,
                            "source_outlet": outlet,
                            "aggregated_rating": rating,
                            "outbound_link": outbound_url,
                            "book_marks_snippet": text.split(critic)[-1].replace("Read Full Review >>", "").strip(),
                            "extracted_full_review_text": full_review_content
                        })
            except Exception:
                continue

    output_filename = f"{book_slug}_full_reviews.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(reviews_extracted, f, indent=4, ensure_ascii=False)
    print(f"\nSuccess! Gathered data for {len(reviews_extracted)} critics and saved to {output_filename}")

if __name__ == "__main__":
    scrape_book_marks("conclave")
