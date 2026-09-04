import json
import re
import requests
from bs4 import BeautifulSoup


def scrape_book_marks(book_slug):
    """Scrapes critic reviews for a specific book on Book Marks by Lit Hub.

    Args:
        book_slug (str): The hyphenated title slug (e.g., 'the-familiar')
    """
    url = f"https://bookmarks.reviews/reviews/{book_slug}/"

    # Mimic a standard browser to avoid getting blocked by basic firewalls
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AnonymouslyScraping/1.0 (KHTML, like Gecko) Chrome/120.0.0.0"
        )
    }

    print(f"Fetching reviews from: {url}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(
            f"Failed to fetch page. Status code: {response.status_code}."
            " Double-check your slug!"
        )
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # Locate the container carrying the aggregated review blocks
    # Book Marks groups individual critic segments sequentially
    reviews_extracted = []

    # Book Marks isolates critique snippets inside individual article wrappers or specific custom class cards
    review_cards = soup.find_all(
        ["div", "article"], class_=re.compile(r"review|critic|card")
    )

    # In case classes shift, fall back to grabbing elements relative to header blocks
    if not review_cards:
        review_cards = soup.find_all(class_="what-reviewers-say")

    print(f"Found {len(review_cards)} potential review components on the page.")

    for card in review_cards:
        try:
            # 1. Extract the Critic & Outlet name
            # Book Marks usually places this inside a strong tag, header, or pull-left class
            critic_info = card.find(["strong", "h4", "span"], class_="critic")
            critic = critic_info.text.strip() if critic_info else "Unknown Critic"

            outlet_info = card.find(["em", "span"], class_="outlet")
            outlet = outlet_info.text.strip() if outlet_info else "Unknown Outlet"

            # 2. Extract Assigned Scale Rating (Rave, Positive, Mixed, Pan)
            # This is typically an image alt text or a distinct text label matching the rating structure
            rating_element = card.find(
                lambda tag: tag.name in ["div", "span", "img"]
                and any(
                    r in str(tag).lower()
                    for r in ["rave", "positive", "mixed", "pan"]
                )
            )
            rating = "Unrated/Undetermined"
            if rating_element:
                for r in ["rave", "positive", "mixed", "pan"]:
                    if r in str(rating_element).lower():
                        rating = r.capitalize()
                        break

            # 3. Pull Review Snippet text
            snippet_div = card.find(["div", "p"], class_="snippet")
            snippet = (
                snippet_div.text.strip()
                if snippet_div
                else card.get_text(strip=True)
            )

            # Deduplicate and clean up raw string fragments
            if critic != "Unknown Critic" or outlet != "Unknown Outlet":
                reviews_extracted.append(
                    {
                        "critic": critic,
                        "source_outlet": outlet,
                        "aggregated_rating": rating,
                        "review_snippet": snippet[:400]
                        + "...",  # Keeps the data clean
                    }
                )
        except Exception as e:
            # Skip corrupted blocks gracefully
            continue

    # Save data locally
    output_filename = f"{book_slug}_reviews.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(reviews_extracted, f, indent=4, ensure_ascii=False)

    print(f"Success! Saved {len(reviews_extracted)} reviews to {output_filename}")


if __name__ == "__main__":
    # Example: target the review slug for a chosen book entry
    # URL translates to https://bookmarks.reviews
    target_slug = "the-familiar"
    scrape_book_marks(target_slug)
