from __future__ import annotations

import json
import logging as LOG
import os
from pathlib import Path
from time import sleep

import undetected_chromedriver as uc
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from hotel_reviews_bot.vector import vectorize
from logger import set_logging

set_logging(log_level=LOG.INFO)

BASE_BOOKINGS_PATH: Path = Path().cwd() / "hotel_reviews_bot"
REVIEWED = "Reviewed: "


def entry(url: str) -> tuple[str, str]:
    hotel_name = url.split("?")[0].split("/pt/")[-1].rstrip(".html")
    final_bookings_path = BASE_BOOKINGS_PATH / f"hotel_booking_{hotel_name}.json"

    if os.path.exists(final_bookings_path):
        # exit early
        return str(final_bookings_path), hotel_name

    LOG.info(f"Getting all reviews for {hotel_name=}")
    reviews = get_booking_reviews(url, max_pages=8)
    tranlsated_reviews = [parse_review(raw_review=review) for review in reviews]
    LOG.info(f"Found {len(reviews)} reviews:")
    with open(final_bookings_path, "w") as f:
        json.dump(tranlsated_reviews, f, indent=4)

    return str(final_bookings_path), hotel_name


def get_booking_reviews(url: str, max_pages: int = 5, timeout: int = 15) -> list[str]:
    options = uc.ChromeOptions()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--start-maximized")
    # might help debugging
    options.add_argument("--remote-debugging-port=9222")

    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    driver = uc.Chrome(options=options, version_main=138)
    driver.get(url)

    wait = WebDriverWait(driver, timeout)
    reviews = []

    for page in range(max_pages):
        try:
            container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='review-cards']")))
            review_elements = container.find_elements(By.CSS_SELECTOR, "[data-testid='review-card']")

            if not review_elements:
                LOG.error(f"⚠️ No reviews found on page {page + 1}")
                break

            for el in review_elements:
                text = el.text.strip()
                if text:
                    reviews.append(text)

            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Next page']")
                next_button.click()
                sleep(3)
            except Exception:
                LOG.error("✅ No more review pages.")
                break

        except Exception as e:
            LOG.error(f"❌ Failed to process page {page + 1}: {e}")
            break

    driver.quit()
    return reviews


def parse_review(raw_review: str) -> dict:
    lines = raw_review.strip().split("\n")

    # if last name exists, Reviewed: is 7th item else 6th item
    if REVIEWED in lines[5]:
        # Basic structure mapping
        review_date_index = 5
        try:
            base_review = {
                "name": lines[0],
                "country": lines[1],
                "room_type": lines[2],
                "stay_duration": lines[3],
                "trip_type": lines[4],
                "reviewed_date": lines[review_date_index].replace(REVIEWED, ""),
            }
        except Exception as e:
            LOG.error(f"Some error happened: {e}")
            raise

    elif REVIEWED in lines[6]:
        review_date_index = 6
        try:
            base_review = {
                "name": f"{lines[0]} {lines[1]}",
                "country": lines[2],
                "room_type": lines[3],
                "stay_duration": lines[4],
                "trip_type": lines[5],
                "reviewed_date": lines[review_date_index].replace(REVIEWED, ""),
            }
        except Exception as e:
            LOG.error(f"Some error happened: {e}")
            raise

    comment_index = review_date_index + 4
    try:
        # score_text -> "Scored 6.0"
        interim_review = base_review | dict(
            zip(
                ("title", "score_text", "score_value"),
                lines[review_date_index: comment_index],
                strict=True,
            )
        )
    except IndexError as e:
        LOG.error(f"Some error happened: {e}")
        raise

    if lines[comment_index] == "There are no comments available for this review":
        review = interim_review
    else:
        try:
            review = interim_review | dict(
                zip(
                    ("positive_text", "negative_text", "helpful_count"),
                    lines[comment_index:],
                    strict=True,
                )
            )
        except IndexError as e:
            LOG.error(f"Some error happened: {e}")
            raise

    return review


def init_bot(json_path: str, hotel_name: str) -> None:
    # TODO: store model name in env
    model = OllamaLLM(model="llama3.2:1b")
    template = """
    You are an expert in answering questions about a hotel or an apartment listing.
    Here are some relevant reviews: {reviews}

    Here is the question to answer: {question}
    """

    prompt = ChatPromptTemplate.from_template(template=template)
    # Pipe  creates a RunnableSequence where output of one callable is
    # passed in to the successive functions as an input.
    chain = prompt | model

    retriever = vectorize(
        file_path=json_path,
        collection_name=hotel_name,
    )
    while True:
        print(f"\n{'-' * 20}\n")
        question = input("Ask your question (q to quit): ").strip()
        if question.lower() == "q":
            break

        reviews: list[Document] = retriever.invoke(question)
        result = chain.invoke({"reviews": reviews, "question": question})
        print(result)


if __name__ == "__main__":
    url = "https://www.booking.com/hotel/pt/fellinglisbon-fado.html?label=gen173nr-1FCAEoggI46AdIM1gEaCeIAQKYATG4AQnIARHYAQHoAQH4AQKIAgGoAgO4Ap-h1cIGwAIB0gIkNGM0OTkyZWQtMGNlMy00Y2RiLWFkODctZjY4MDRjMDUyYTky2AIF4AIB&aid=304142&ucfs=1&checkin=2025-09-10&checkout=2025-09-14&dest_id=-2167973&dest_type=city&group_adults=4&no_rooms=1&group_children=0&nflt=privacy_type%3D3%3Btdb%3D3%3Bentire_place_bedroom_count%3D2%3Bmin_bathrooms%3D2&srpvid=26dd57745c8d0810&srepoch=1750422407&matching_block_id=132333001_390853514_4_0_0&atlas_src=sr_iw_title#tab-reviews"
    final_bookings_path, hotel_name = entry(url)
    init_bot(json_path=final_bookings_path, hotel_name=hotel_name)
