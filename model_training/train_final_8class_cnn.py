from pathlib import Path
import json

import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras import layers, models


# =========================================================
# PATHS
# =========================================================

DATASET_PATH = (
    Path("dataset")
    / "Garbage classification"
    / "Garbage classification"
)

MODEL_FOLDER = Path("model_training")

MODEL_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# SETTINGS
# =========================================================

IMAGE_SIZE = (224, 224)

BATCH_SIZE = 32

VALIDATION_SPLIT = 0.20

SEED = 42

EPOCHS = 50


# =========================================================
# CHECK DATASET
# =========================================================

if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Dataset folder not found: "
        f"{DATASET_PATH.resolve()}"
    )


# =========================================================
# LOAD TRAINING DATASET
# =========================================================

train_dataset = (
    tf.keras.utils
    .image_dataset_from_directory(
        DATASET_PATH,
        validation_split=VALIDATION_SPLIT,
        subset="training",
        seed=SEED,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
    )
)


# =========================================================
# LOAD VALIDATION DATASET
# =========================================================

validation_dataset = (
    tf.keras.utils
    .image_dataset_from_directory(
        DATASET_PATH,
        validation_split=VALIDATION_SPLIT,
        subset="validation",
        seed=SEED,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
    )
)


# =========================================================
# CLASS NAMES
# =========================================================

class_names = train_dataset.class_names

number_of_classes = len(
    class_names
)

print("\nClasses:")

for index, class_name in enumerate(
    class_names
):
    print(
        f"{index}: {class_name}"
    )

print(
    "\nNumber of classes:",
    number_of_classes
)


# =========================================================
# VERIFY FINAL CLASS SET
# =========================================================

expected_classes = [
    "broken_toys",
    "cardboard",
    "e_waste",
    "glass",
    "metal",
    "organic",
    "paper",
    "plastic",
]

if class_names != expected_classes:
    raise ValueError(
        "\nDataset classes do not match "
        "the expected final 8 classes.\n"
        f"Found: {class_names}\n"
        f"Expected: {expected_classes}"
    )


# =========================================================
# SAVE CLASS NAMES
# =========================================================

CLASS_NAMES_PATH = (
    MODEL_FOLDER
    / "class_names_final_8.json"
)

with open(
    CLASS_NAMES_PATH,
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        class_names,
        file,
        indent=4
    )

print(
    f"\nClass names saved at: "
    f"{CLASS_NAMES_PATH}"
)


# =========================================================
# CLASS WEIGHTS
# =========================================================

all_labels = []

for _, labels in train_dataset:
    all_labels.extend(
        labels.numpy()
    )

all_labels = np.array(
    all_labels
)

class_weights = compute_class_weight(
    class_weight="balanced",
    classes=np.arange(
        number_of_classes
    ),
    y=all_labels,
)

class_weight_dict = {
    index: float(weight)
    for index, weight
    in enumerate(class_weights)
}

print("\nClass weights:")

for index, weight in (
    class_weight_dict.items()
):
    print(
        f"{class_names[index]}: "
        f"{weight:.3f}"
    )


# =========================================================
# PREFETCH
# =========================================================

AUTOTUNE = tf.data.AUTOTUNE

train_dataset = (
    train_dataset.prefetch(
        buffer_size=AUTOTUNE
    )
)

validation_dataset = (
    validation_dataset.prefetch(
        buffer_size=AUTOTUNE
    )
)


# =========================================================
# DATA AUGMENTATION
# =========================================================

data_augmentation = (
    models.Sequential(
        [
            layers.RandomFlip(
                "horizontal"
            ),

            layers.RandomRotation(
                0.08
            ),

            layers.RandomZoom(
                0.10
            ),

            layers.RandomContrast(
                0.10
            ),

            layers.RandomTranslation(
                height_factor=0.05,
                width_factor=0.05,
            ),
        ],
        name="data_augmentation",
    )
)


# =========================================================
# CUSTOM CNN MODEL
# =========================================================

model = models.Sequential(
    [

        layers.Input(
            shape=(224, 224, 3)
        ),

        data_augmentation,

        layers.Rescaling(
            1.0 / 255
        ),


        # BLOCK 1

        layers.Conv2D(
            32,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),

        layers.BatchNormalization(),

        layers.Activation(
            "relu"
        ),

        layers.Conv2D(
            32,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),

        layers.BatchNormalization(),

        layers.Activation(
            "relu"
        ),

        layers.MaxPooling2D(),

        layers.Dropout(
            0.15
        ),


        # BLOCK 2

        layers.Conv2D(
            64,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),

        layers.BatchNormalization(),

        layers.Activation(
            "relu"
        ),

        layers.Conv2D(
            64,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),

        layers.BatchNormalization(),

        layers.Activation(
            "relu"
        ),

        layers.MaxPooling2D(),

        layers.Dropout(
            0.20
        ),


        # BLOCK 3

        layers.Conv2D(
            128,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),

        layers.BatchNormalization(),

        layers.Activation(
            "relu"
        ),

        layers.Conv2D(
            128,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),

        layers.BatchNormalization(),

        layers.Activation(
            "relu"
        ),

        layers.MaxPooling2D(),

        layers.Dropout(
            0.25
        ),


        # BLOCK 4

        layers.Conv2D(
            256,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),

        layers.BatchNormalization(),

        layers.Activation(
            "relu"
        ),

        layers.Conv2D(
            256,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),

        layers.BatchNormalization(),

        layers.Activation(
            "relu"
        ),

        layers.MaxPooling2D(),

        layers.Dropout(
            0.30
        ),


        # BLOCK 5

        layers.Conv2D(
            512,
            kernel_size=3,
            padding="same",
            use_bias=False,
        ),

        layers.BatchNormalization(),

        layers.Activation(
            "relu"
        ),

        layers.GlobalAveragePooling2D(),


        # CLASSIFIER

        layers.Dense(
            256,
            use_bias=False,
        ),

        layers.BatchNormalization(),

        layers.Activation(
            "relu"
        ),

        layers.Dropout(
            0.40
        ),

        layers.Dense(
            128,
            activation="relu",
        ),

        layers.Dropout(
            0.30
        ),

        layers.Dense(
            number_of_classes,
            activation="softmax",
        ),
    ]
)


# =========================================================
# COMPILE
# =========================================================

model.compile(
    optimizer=
        tf.keras.optimizers.Adam(
            learning_rate=0.0005
        ),
    loss=
        "sparse_categorical_crossentropy",
    metrics=[
        "accuracy"
    ],
)


model.summary()


# =========================================================
# MODEL PATHS
# =========================================================

BEST_MODEL_PATH = (
    MODEL_FOLDER
    / "best_final_8class_cnn.keras"
)

FINAL_MODEL_PATH = (
    MODEL_FOLDER
    / "final_8class_cnn.keras"
)


# =========================================================
# CALLBACKS
# =========================================================

callbacks = [

    tf.keras.callbacks
    .EarlyStopping(
        monitor="val_loss",
        patience=7,
        restore_best_weights=True,
        verbose=1,
    ),

    tf.keras.callbacks
    .ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=3,
        min_lr=0.000001,
        verbose=1,
    ),

    tf.keras.callbacks
    .ModelCheckpoint(
        filepath=BEST_MODEL_PATH,
        monitor="val_accuracy",
        mode="max",
        save_best_only=True,
        verbose=1,
    ),
]


# =========================================================
# TRAIN
# =========================================================

print(
    "\nStarting final 8-class "
    "CNN training...\n"
)

history = model.fit(
    train_dataset,
    validation_data=
        validation_dataset,
    epochs=EPOCHS,
    callbacks=callbacks,
    class_weight=
        class_weight_dict,
)


# =========================================================
# SAVE FINAL MODEL
# =========================================================

model.save(
    FINAL_MODEL_PATH
)

print(
    "\nTraining completed."
)

print(
    f"Best model saved at: "
    f"{BEST_MODEL_PATH}"
)

print(
    f"Final model saved at: "
    f"{FINAL_MODEL_PATH}"
)

print(
    f"Class names saved at: "
    f"{CLASS_NAMES_PATH}"
)


# =========================================================
# FINAL VALIDATION
# =========================================================

validation_loss, validation_accuracy = (
    model.evaluate(
        validation_dataset,
        verbose=1
    )
)

print(
    "\nFinal validation accuracy: "
    f"{validation_accuracy * 100:.2f}%"
)

print(
    "Final validation loss: "
    f"{validation_loss:.4f}"
)