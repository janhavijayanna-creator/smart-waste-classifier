from pathlib import Path

import tensorflow as tf


DATASET_PATH = (
    Path("dataset")
    / "Garbage classification"
    / "Garbage classification"
)

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
VALIDATION_SPLIT = 0.20
RANDOM_SEED = 123


if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Dataset folder was not found: {DATASET_PATH.resolve()}"
    )


training_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=VALIDATION_SPLIT,
    subset="training",
    seed=RANDOM_SEED,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
)

validation_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=VALIDATION_SPLIT,
    subset="validation",
    seed=RANDOM_SEED,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
)

class_names = training_dataset.class_names

print("\nDataset loaded successfully.")
print("Class names:", class_names)
print("Number of classes:", len(class_names))
print("Image size:", IMAGE_SIZE)
print("Batch size:", BATCH_SIZE)