from pathlib import Path
import random
import shutil

random.seed(42)

DATASET_PATH = (
    Path("dataset")
    / "Garbage classification"
    / "Garbage classification"
)

TARGET_COUNTS = {
    "glass": 950,
    "paper": 900,
}

BACKUP_FOLDER = Path("dataset_backup")
BACKUP_FOLDER.mkdir(exist_ok=True)


for class_name, target_count in TARGET_COUNTS.items():

    class_folder = DATASET_PATH / class_name
    backup_folder = BACKUP_FOLDER / class_name

    backup_folder.mkdir(parents=True, exist_ok=True)

    images = []

    for ext in ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"]:
        images.extend(class_folder.glob(ext))

    print(f"\n{class_name}")
    print(f"Current images : {len(images)}")
    print(f"Target images  : {target_count}")

    if len(images) <= target_count:
        print("Already balanced.")
        continue

    random.shuffle(images)

    images_to_move = images[target_count:]

    for image in images_to_move:
        shutil.move(
            str(image),
            str(backup_folder / image.name)
        )

    print(f"Moved {len(images_to_move)} images.")
    print(f"Remaining {target_count} images.")