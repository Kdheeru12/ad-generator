# scraper.py
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import re


def to_high_res_amazon_url(url, resolution="SL1500"):
    """
    Clean Amazon image URL and upgrade it to high-res (_SL1500_ or _UL1500_).
    """
    # Remove known sizing suffix patterns
    url = re.sub(r"\._[^.]+_\.", ".", url)

    # Add high-resolution suffix
    if f"_{resolution}_" not in url:
        url = url.replace(".jpg", f"._{resolution}_.jpg")

    return url


def scrape_product_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"  # noqa
    }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")

    title = soup.find("span", id="productTitle").get_text(strip=True)

    price = ""
    try:
        price = soup.find("span", attrs={"id": "priceblock_ourprice"}).string.strip()
    except Exception:
        try:
            price = soup.find("span", attrs={"id": "priceblock_dealprice"}).string.strip()
        except Exception:
            pass

    description_tag = soup.select_one("#productDescription, #feature-bullets > ul")
    description = description_tag.get_text(strip=True) if description_tag else ""

    alt_images_div = soup.find("div", {"id": "altImages"})
    image_tags = alt_images_div.find_all("img") if alt_images_div else []

    image_bytes_list = []
    downloaded = set()
    for idx, img in enumerate(image_tags):
        img_url = img.get("data-old-hires") or img.get("src")
        high_res_url = to_high_res_amazon_url(img_url)
        if high_res_url and high_res_url not in downloaded:
            # img_url = img_url.replace("_SS40_", "_SL1500_")
            try:
                img_data = requests.get(high_res_url, headers=headers).content
                image = Image.open(BytesIO(img_data)).convert("RGB")
                image_bytes_list.append(image)
                downloaded.add(high_res_url)
            except Exception as e:
                print(f"Image {idx+1} download failed: {e}")

    return {
        "title": title,
        "price": price,
        "description": description,
    }, image_bytes_list
