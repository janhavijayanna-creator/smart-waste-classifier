from __future__ import annotations

import hashlib
import time
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from ddgs import DDGS
from PIL import Image, UnidentifiedImageError


PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FOLDER = (
    PROJECT_ROOT
    / "dataset"
    / "Garbage classification"
    / "Garbage classification"
    / "broken_toys"
)

KEYWORDS = [
    "broken toy waste photo",
    "discarded broken toys photo",
    "damaged children's toys",
    "broken plastic toy",
    "broken toy car",
    "toy car missing wheels",
    "broken doll",
    "damaged doll toy",
    "doll missing arm",
    "torn teddy bear",
    "damaged stuffed toy",
    "broken action figure",
    "broken robot toy",
    "broken electronic toy",
    "cracked plastic toy",
    "broken toy parts",
    "discarded toy pieces",
    "old damaged toys garbage",
    "broken toys in trash",
    "toy waste recycling",
]

RESULTS_PER_KEYWORD = 60
MIN_WIDTH = 250
MIN_HEIGHT = 250
REQUEST_TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
    )
}


def existing_hashes(folder: Path) -> set[str]:
    hashes: set[str] = set()

    for path in folder.iterdir():
        if not path.is_file():
            continue

        try:
            hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())
        except OSError:
            continue

    return hashes


def download_image(
    url: str,
    folder: Path,
    known_hashes: set[str],
    file_number: int,
) -> bool:
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        content = response.content

        if len(content) < 5_000:
            return False

        image_hash = hashlib.sha256(content).hexdigest()

        if image_hash in known_hashes:
            return False

        image = Image.open(BytesIO(content))
        image.load()

        if image.width < MIN_WIDTH or image.height < MIN_HEIGHT:
            return False

        if image.mode != "RGB":
            image = image.convert("RGB")

        output_path = folder / f"broken_toy_{file_number:04d}.jpg"

        image.save(
            output_path,
            format="JPEG",
            quality=90,
            optimize=True,
        )

        known_hashes.add(image_hash)
        return True

    except (
        requests.RequestException,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):
        return False


def main() -> None:
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    known_hashes = existing_hashes(OUTPUT_FOLDER)

    current_files = list(OUTPUT_FOLDER.glob("broken_toy_*.jpg"))
    file_number = len(current_files) + 1
    downloaded = 0

    print("Saving images to:")
    print(OUTPUT_FOLDER)
    print()

    with DDGS() as search:
        for keyword_number, keyword in enumerate(KEYWORDS, start=1):
            print(
                f"[{keyword_number}/{len(KEYWORDS)}] "
                f"Searching: {keyword}"
            )

            try:
                results: list[dict[str, Any]] = list(
                    search.images(
                        query=keyword,
                        region="wt-wt",
                        safesearch="moderate",
                        type_image="photo",
                        max_results=RESULTS_PER_KEYWORD,
                    )
                )
            except Exception as error:
                print(f"Search failed: {error}")
                time.sleep(3)
                continue

            for result in results:
                image_url = result.get("image")

                if not image_url:
                    continue

                if download_image(
                    image_url,
                    OUTPUT_FOLDER,
                    known_hashes,
                    file_number,
                ):
                    downloaded += 1
                    file_number += 1
                    print(f"  Downloaded: {downloaded}", end="\r")

            print(f"\nTotal saved so far: {downloaded}")
            time.sleep(2)

    print("\nDownload finished.")
    print(f"New images saved: {downloaded}")
    print(f"Folder: {OUTPUT_FOLDER}")
    print()
    print("Important: manually delete images that show:")
    print("- normal unbroken toys")
    print("- cartoons, drawings or logos")
    print("- food, people or unrelated objects")
    print("- very blurry or unclear toys")


if __name__ == "__main__":
    main()