from pathlib import Path
import json

import tensorflow as tf


DATASET_PATH = (
    Path("dataset")
    / "Garbage classification"
    / "Garbage classification"
)

MODEL_FOLDER = Path("model_training")

SOURCE_MODEL_PATH = (
    MODEL_FOLDER
    / "best_custom_cnn.keras"
)

BEST_FINE_TUNED_PATH = (
    MODEL_FOLDER
    / "best_custom_cnn_finetuned.keras"
)

FINAL_FINE_TUNED_PATH = (
    MODEL_FOLDER
    / "custom_cnn_finetuned_final.keras"
)

CLASS_NAMES_PATH = (
    MODEL_FOLDER
    / "class_names_finetuned.json"
)


IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
VALIDATION_SPLIT = 0.20
SEED = 42
FINE_TUNE_EPOCHS = 15


if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATASET_PATH.resolve()}"
    )

if not SOURCE_MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Existing model not found: {SOURCE_MODEL_PATH.resolve()}"
    )


# =========================================================
# Load the cleaned and balanced dataset
# =========================================================

train_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=VALIDATION_SPLIT,
    subset="training",
    seed=SEED,
    shuffle=True,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
)

validation_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=VALIDATION_SPLIT,
    subset="validation",
    seed=SEED,
    shuffle=True,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
)


class_names = train_dataset.class_names

print("\nClasses:", class_names)

with open(
    CLASS_NAMES_PATH,
    "w",
    encoding="utf-8",
) as file:
    json.dump(class_names, file, indent=4)


AUTOTUNE = tf.data.AUTOTUNE

train_dataset = train_dataset.prefetch(AUTOTUNE)
validation_dataset = validation_dataset.prefetch(AUTOTUNE)


# =========================================================
# Load your existing 81.39% custom CNN
# =========================================================

model = tf.keras.models.load_model(
    SOURCE_MODEL_PATH
)

print("\nExisting model loaded successfully.")


# =========================================================
# Freeze early feature extraction layers
# =========================================================

# Freeze approximately the first 60% of layers.
freeze_until = int(len(model.layers) * 0.60)

for index, layer in enumerate(model.layers):
    layer.trainable = index >= freeze_until


print("\nLayer training status:")

for index, layer in enumerate(model.layers):
    print(
        f"{index:02d} | "
        f"{layer.name:35s} | "
        f"trainable={layer.trainable}"
    )


# =========================================================
# Compile using a very small learning rate
# =========================================================

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.00001
    ),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)


callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        filepath=BEST_FINE_TUNED_PATH,
        monitor="val_accuracy",
        mode="max",
        save_best_only=True,
        verbose=1,
    ),

    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=5,
        restore_best_weights=True,
        verbose=1,
    ),

    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=2,
        min_lr=0.0000001,
        verbose=1,
    ),

    tf.keras.callbacks.CSVLogger(
        MODEL_FOLDER
        / "fine_tuning_log.csv"
    ),
]


# =========================================================
# Check accuracy before fine-tuning
# =========================================================

print("\nEvaluating before fine-tuning...")

initial_loss, initial_accuracy = model.evaluate(
    validation_dataset,
    verbose=1,
)

print(
    f"\nAccuracy before fine-tuning: "
    f"{initial_accuracy * 100:.2f}%"
)


# =========================================================
# Fine-tune
# =========================================================

print("\nStarting fine-tuning...\n")

history = model.fit(
    train_dataset,
    validation_data=validation_dataset,
    epochs=FINE_TUNE_EPOCHS,
    callbacks=callbacks,
)


model.save(FINAL_FINE_TUNED_PATH)


print("\nFine-tuning completed.")

print(
    f"Best fine-tuned model: "
    f"{BEST_FINE_TUNED_PATH}"
)

print(
    f"Final fine-tuned model: "
    f"{FINAL_FINE_TUNED_PATH}"
)