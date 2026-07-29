from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)


DATASET_PATH = (
    Path("dataset")
    / "Garbage classification"
    / "Garbage classification"
)

MODEL_PATH = (
    Path("model_training")
    / "best_custom_cnn_finetuned.keras"
)

CLASS_NAMES_PATH = (
    Path("model_training")
    / "class_names.json"
)

OUTPUT_PATH = (
    Path("model_training")
    / "confusion_matrix.png"
)

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
VALIDATION_SPLIT = 0.20

# Must match the seed used during training.
SEED = 42


if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Dataset folder not found: {DATASET_PATH.resolve()}"
    )

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH.resolve()}"
    )


# IMPORTANT:
# shuffle=True must match how the validation set was created during training.
validation_dataset = (
    tf.keras.utils.image_dataset_from_directory(
        DATASET_PATH,
        validation_split=VALIDATION_SPLIT,
        subset="validation",
        seed=SEED,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=True,
    )
)


dataset_class_names = validation_dataset.class_names

if CLASS_NAMES_PATH.exists():
    with open(
        CLASS_NAMES_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        class_names = json.load(file)
else:
    class_names = dataset_class_names


if class_names != dataset_class_names:
    raise ValueError(
        "The saved class names do not match the dataset.\n"
        f"Saved: {class_names}\n"
        f"Dataset: {dataset_class_names}"
    )


print("\nClasses:")
print(class_names)


model = tf.keras.models.load_model(MODEL_PATH)

print("\nModel loaded successfully.")


# Evaluate the model.
loss, accuracy = model.evaluate(
    validation_dataset,
    verbose=1,
)

print(f"\nValidation loss: {loss:.4f}")
print(f"Validation accuracy: {accuracy * 100:.2f}%")


# Collect predictions and true labels from the SAME batch iteration.
# This prevents shuffled labels and predictions from becoming misaligned.
true_labels = []
predicted_labels = []

for images, labels in validation_dataset:
    probabilities = model.predict_on_batch(images)
    predictions = np.argmax(probabilities, axis=1)

    true_labels.extend(labels.numpy())
    predicted_labels.extend(predictions)


true_labels = np.array(true_labels)
predicted_labels = np.array(predicted_labels)


print("\nTrue-label distribution:")

true_classes, true_counts = np.unique(
    true_labels,
    return_counts=True,
)

for class_index, count in zip(true_classes, true_counts):
    print(f"{class_names[class_index]}: {count}")


print("\nPredicted-label distribution:")

predicted_classes, predicted_counts = np.unique(
    predicted_labels,
    return_counts=True,
)

for class_index, count in zip(
    predicted_classes,
    predicted_counts,
):
    print(f"{class_names[class_index]}: {count}")


print("\nClassification Report:\n")

print(
    classification_report(
        true_labels,
        predicted_labels,
        labels=np.arange(len(class_names)),
        target_names=class_names,
        digits=4,
        zero_division=0,
    )
)


matrix = confusion_matrix(
    true_labels,
    predicted_labels,
    labels=np.arange(len(class_names)),
)


figure, axis = plt.subplots(
    figsize=(12, 10)
)

display = ConfusionMatrixDisplay(
    confusion_matrix=matrix,
    display_labels=class_names,
)

display.plot(
    ax=axis,
    xticks_rotation=45,
    values_format="d",
)

plt.title("Custom CNN Confusion Matrix")
plt.tight_layout()

plt.savefig(
    OUTPUT_PATH,
    dpi=300,
    bbox_inches="tight",
)

print(f"\nConfusion matrix saved at: {OUTPUT_PATH}")

plt.show()