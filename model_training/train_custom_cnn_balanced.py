from pathlib import Path
import json

import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras import layers, models, regularizers


DATASET_PATH = (
    Path("dataset")
    / "Garbage classification"
    / "Garbage classification"
)

MODEL_FOLDER = Path("model_training")
MODEL_FOLDER.mkdir(parents=True, exist_ok=True)

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
VALIDATION_SPLIT = 0.20
SEED = 42
EPOCHS = 45


if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Dataset folder not found: {DATASET_PATH.resolve()}"
    )


train_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=VALIDATION_SPLIT,
    subset="training",
    seed=SEED,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
)

validation_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=VALIDATION_SPLIT,
    subset="validation",
    seed=SEED,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
)


class_names = train_dataset.class_names
number_of_classes = len(class_names)

print("Classes:", class_names)
print("Number of classes:", number_of_classes)


with open(
    MODEL_FOLDER / "class_names.json",
    "w",
    encoding="utf-8",
) as file:
    json.dump(class_names, file, indent=4)


all_labels = []

for _, labels in train_dataset:
    all_labels.extend(labels.numpy())

all_labels = np.array(all_labels)

class_weights = compute_class_weight(
    class_weight="balanced",
    classes=np.arange(number_of_classes),
    y=all_labels,
)

class_weight_dict = {
    index: float(weight)
    for index, weight in enumerate(class_weights)
}

print("\nClass weights:")

for index, weight in class_weight_dict.items():
    print(f"{class_names[index]}: {weight:.2f}")


AUTOTUNE = tf.data.AUTOTUNE

train_dataset = (
    train_dataset
    .cache()
    .prefetch(AUTOTUNE)
)

validation_dataset = (
    validation_dataset
    .cache()
    .prefetch(AUTOTUNE)
)


data_augmentation = models.Sequential(
    [
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.10),
        layers.RandomZoom(0.15),
        layers.RandomContrast(0.15),
        layers.RandomBrightness(0.10),
        layers.RandomTranslation(
            height_factor=0.08,
            width_factor=0.08,
        ),
    ],
    name="data_augmentation",
)


model = models.Sequential(
    [
        layers.Input(shape=(224, 224, 3)),

        data_augmentation,

        layers.Rescaling(1.0 / 255),

        layers.Conv2D(
            32,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),
        layers.BatchNormalization(),
        layers.Activation("relu"),

        layers.Conv2D(
            32,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D(),
        layers.Dropout(0.15),

        layers.Conv2D(
            64,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),
        layers.BatchNormalization(),
        layers.Activation("relu"),

        layers.Conv2D(
            64,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D(),
        layers.Dropout(0.20),

        layers.Conv2D(
            128,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),
        layers.BatchNormalization(),
        layers.Activation("relu"),

        layers.Conv2D(
            128,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D(),
        layers.Dropout(0.25),

        layers.Conv2D(
            256,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),
        layers.BatchNormalization(),
        layers.Activation("relu"),

        layers.Conv2D(
            256,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D(),
        layers.Dropout(0.30),

        layers.Conv2D(
            512,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),
        layers.BatchNormalization(),
        layers.Activation("relu"),

        layers.GlobalAveragePooling2D(),

        layers.Dense(
            256,
            use_bias=False,
        ),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.Dropout(0.40),

        layers.Dense(
            128,
            activation="relu",
        ),
        layers.Dropout(0.30),

        layers.Dense(
            number_of_classes,
            activation="softmax",
        ),
    ]
)


model.compile(
    optimizer=tf.keras.optimizers.AdamW(
        learning_rate=0.0003,
        weight_decay=0.00001,
    ),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)


model.summary()


BEST_MODEL_PATH = (
    MODEL_FOLDER
    / "best_custom_cnn_balanced.keras"
)

FINAL_MODEL_PATH = (
    MODEL_FOLDER
    / "custom_cnn_balanced_final.keras"
)


callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=7,
        restore_best_weights=True,
        verbose=1,
    ),

    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=2,
        min_lr=0.000001,
        verbose=1,
    ),

    tf.keras.callbacks.ModelCheckpoint(
        filepath=BEST_MODEL_PATH,
        monitor="val_accuracy",
        mode="max",
        save_best_only=True,
        verbose=1,
    ),

    tf.keras.callbacks.CSVLogger(
        MODEL_FOLDER / "balanced_cnn_training_log.csv"
    ),
]

history = model.fit(
    train_dataset,
    validation_data=validation_dataset,
    epochs=EPOCHS,
    callbacks=callbacks,
    class_weight=class_weight_dict,
)


model.save(FINAL_MODEL_PATH)

print("\nTraining completed.")
print(f"Best model saved at: {BEST_MODEL_PATH}")
print(f"Final model saved at: {FINAL_MODEL_PATH}")
print(f"Class names saved at: {MODEL_FOLDER / 'class_names.json'}")