from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix


DATASET_PATH = (
    Path("dataset")
    / "Garbage classification"
    / "Garbage classification"
)

MODEL_PATH = Path("model_training") / "balanced_waste_classifier.keras"

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
VALIDATION_SPLIT = 0.20
RANDOM_SEED = 123


validation_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=VALIDATION_SPLIT,
    subset="validation",
    seed=RANDOM_SEED,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=True,
)

class_names = validation_dataset.class_names
validation_dataset = validation_dataset.unbatch()
validation_dataset = validation_dataset.batch(BATCH_SIZE)

model = tf.keras.models.load_model(MODEL_PATH)

true_labels = []
predicted_labels = []

for images, labels in validation_dataset:
    predictions = model.predict(images, verbose=0)

    batch_predictions = np.argmax(
        predictions,
        axis=1
    )

    true_labels.extend(labels.numpy())
    predicted_labels.extend(batch_predictions)


accuracy = np.mean(
    np.array(true_labels) == np.array(predicted_labels)
)

print("\nOverall validation accuracy:")
print(f"{accuracy * 100:.2f}%")

print("\nClassification report:")
print(
    classification_report(
    true_labels,
    predicted_labels,
    labels=list(range(len(class_names))),
    target_names=class_names,
    digits=4,
    zero_division=0
)
)

print("\nConfusion matrix:")
print(
   confusion_matrix(
    true_labels,
    predicted_labels,
    labels=list(range(len(class_names)))
)
)