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
    
    # Book Marks wraps individual reviews inside specialized review body blocks
    review_containers = soup.find_all("div", class_="inner-review-body")
    
    # Alternative target container if classes shift dynamically
    if not review_containers:
        review_containers = soup.find_all("div", class_="review-card")

    for container in review_containers:
        try:
            # 1. Pull the Critic and Source Outlet
            critic = "Unknown Critic"
            critic_span = container.find("span", class_="critic-name")
            if critic_span:
                critic = critic_span.get_text(strip=True)
                
            outlet = "Unknown Outlet"
            outlet_em = container.find("em", class_="outlet")
            if outlet_em:
                outlet = outlet_em.get_text(strip=True).strip(",")
            
            # 2. Extract Assigned Aggregated Rating Type
            rating = "Unrated"
            rating_div = container.find("div", class_="rating-image")
            if rating_div and rating_div.find("img"):
                img_alt = rating_div.find("img").get("alt", "")
                if img_alt:
                    rating = img_alt.strip().capitalize()

            # 3. Pull the Review Snippet text block
            snippet = ""
            snippet_div = container.find("div", class_="review-snippet")
            if snippet_div:
                snippet = snippet_div.get_text(strip=True)
                # Clean off trailing link indicators if present
                snippet = snippet.replace("Read Full Review >>", "").strip()

            if critic != "Unknown Critic" or outlet != "Unknown Outlet":
                reviews_extracted.append({
                    "critic": critic,
                    "source_outlet": outlet,
                    "aggregated_rating": rating,
                    "review_snippet": snippet[:400] + "..." if len(snippet) > 400 else snippet
                })
        except Exception:
            continue

    output_filename = f"{book_slug}_reviews.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(reviews_extracted, f, indent=4, ensure_ascii=False)
    print(f"Success! Saved {len(reviews_extracted)} reviews to {output_filename}")

if __name__ == "__main__":
    scrape_book_marks("conclave")
