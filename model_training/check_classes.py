import tensorflow as tf
from pathlib import Path

DATASET_PATH = (
    Path("dataset")
    / "Garbage classification"
    / "Garbage classification"
)

ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="validation",
    seed=42,
    image_size=(224,224),
    batch_size=32,
    shuffle=False
)

print(ds.class_names)