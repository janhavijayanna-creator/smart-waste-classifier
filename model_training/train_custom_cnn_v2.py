from pathlib import Path
import json

import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras import layers, models, regularizers


# =========================================================
# Paths and configuration
# =========================================================

DATASET_PATH = (
    Path("dataset")
    / "Garbage classification"
    / "Garbage classification"
)

MODEL_FOLDER = Path("model_training")
MODEL_FOLDER.mkdir(parents=True, exist_ok=True)

BEST_MODEL_PATH = MODEL_FOLDER / "best_custom_cnn_v2_lite.keras"
FINAL_MODEL_PATH = MODEL_FOLDER / "custom_cnn_v2_lite_final.keras"
CLASS_NAMES_PATH = MODEL_FOLDER / "class_names_v2.json"
TRAINING_LOG_PATH = MODEL_FOLDER / "custom_cnn_v2_lite_log.csv"

IMAGE_SIZE = (160, 160)
BATCH_SIZE = 32
VALIDATION_SPLIT = 0.20
SEED = 42
EPOCHS = 40


if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Dataset folder not found: {DATASET_PATH.resolve()}"
    )


# =========================================================
# Load dataset
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
number_of_classes = len(class_names)

print("\nClasses:", class_names)
print("Number of classes:", number_of_classes)


with open(
    CLASS_NAMES_PATH,
    "w",
    encoding="utf-8",
) as file:
    json.dump(class_names, file, indent=4)


# =========================================================
# Compute class weights
# =========================================================

all_labels = []

for _, labels_batch in train_dataset:
    all_labels.extend(labels_batch.numpy())

all_labels = np.asarray(all_labels)

weights = compute_class_weight(
    class_weight="balanced",
    classes=np.arange(number_of_classes),
    y=all_labels,
)

class_weight_dict = {
    index: float(weight)
    for index, weight in enumerate(weights)
}

print("\nClass weights:")

for index, weight in class_weight_dict.items():
    print(f"{class_names[index]}: {weight:.3f}")


# =========================================================
# Dataset performance
# =========================================================

AUTOTUNE = tf.data.AUTOTUNE

train_dataset = train_dataset.prefetch(AUTOTUNE)
validation_dataset = validation_dataset.prefetch(AUTOTUNE)


# =========================================================
# Data augmentation
# =========================================================

data_augmentation = models.Sequential(
    [
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.10),
        layers.RandomZoom(0.12),
        layers.RandomContrast(0.12),
        layers.RandomTranslation(
            height_factor=0.08,
            width_factor=0.08,
        ),
    ],
    name="data_augmentation",
)


# =========================================================
# Lightweight residual separable block
# =========================================================

def separable_residual_block(
    inputs,
    filters: int,
    stride: int = 1,
    dropout_rate: float = 0.0,
):
    shortcut = inputs

    x = layers.SeparableConv2D(
        filters,
        kernel_size=3,
        strides=stride,
        padding="same",
        use_bias=False,
        depthwise_regularizer=regularizers.l2(1e-4),
        pointwise_regularizer=regularizers.l2(1e-4),
    )(inputs)

    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)

    x = layers.SeparableConv2D(
        filters,
        kernel_size=3,
        padding="same",
        use_bias=False,
        depthwise_regularizer=regularizers.l2(1e-4),
        pointwise_regularizer=regularizers.l2(1e-4),
    )(x)

    x = layers.BatchNormalization()(x)

    if stride != 1 or shortcut.shape[-1] != filters:
        shortcut = layers.Conv2D(
            filters,
            kernel_size=1,
            strides=stride,
            padding="same",
            use_bias=False,
            kernel_regularizer=regularizers.l2(1e-4),
        )(shortcut)

        shortcut = layers.BatchNormalization()(shortcut)

    x = layers.Add()([x, shortcut])
    x = layers.Activation("relu")(x)

    if dropout_rate > 0:
        x = layers.SpatialDropout2D(dropout_rate)(x)

    return x


# =========================================================
# Build Custom CNN V2 Lite
# =========================================================

inputs = layers.Input(
    shape=(IMAGE_SIZE[0], IMAGE_SIZE[1], 3)
)

x = data_augmentation(inputs)
x = layers.Rescaling(1.0 / 255)(x)

x = layers.Conv2D(
    32,
    kernel_size=3,
    strides=2,
    padding="same",
    use_bias=False,
    kernel_regularizer=regularizers.l2(1e-4),
)(x)

x = layers.BatchNormalization()(x)
x = layers.Activation("relu")(x)


# 160 × 160 → 80 × 80
x = separable_residual_block(
    x,
    filters=32,
    stride=1,
    dropout_rate=0.05,
)

# 80 × 80 → 40 × 40
x = separable_residual_block(
    x,
    filters=64,
    stride=2,
    dropout_rate=0.10,
)

x = separable_residual_block(
    x,
    filters=64,
    stride=1,
    dropout_rate=0.10,
)

# 40 × 40 → 20 × 20
x = separable_residual_block(
    x,
    filters=128,
    stride=2,
    dropout_rate=0.15,
)

x = separable_residual_block(
    x,
    filters=128,
    stride=1,
    dropout_rate=0.15,
)

# 20 × 20 → 10 × 10
x = separable_residual_block(
    x,
    filters=256,
    stride=2,
    dropout_rate=0.20,
)

x = separable_residual_block(
    x,
    filters=256,
    stride=1,
    dropout_rate=0.20,
)

# Final feature extraction
x = layers.SeparableConv2D(
    384,
    kernel_size=3,
    padding="same",
    use_bias=False,
)(x)

x = layers.BatchNormalization()(x)
x = layers.Activation("relu")(x)

x = layers.GlobalAveragePooling2D()(x)

x = layers.Dense(
    256,
    use_bias=False,
    kernel_regularizer=regularizers.l2(1e-4),
)(x)

x = layers.BatchNormalization()(x)
x = layers.Activation("relu")(x)
x = layers.Dropout(0.40)(x)

x = layers.Dense(
    128,
    activation="relu",
    kernel_regularizer=regularizers.l2(1e-4),
)(x)

x = layers.Dropout(0.30)(x)

outputs = layers.Dense(
    number_of_classes,
    activation="softmax",
)(x)

model = models.Model(
    inputs=inputs,
    outputs=outputs,
    name="CustomCNN_V2_Lite",
)

model.summary()


# =========================================================
# Compile
# =========================================================

model.compile(
    optimizer=tf.keras.optimizers.AdamW(
        learning_rate=0.0005,
        weight_decay=1e-4,
    ),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)


# =========================================================
# Callbacks
# =========================================================

callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        filepath=BEST_MODEL_PATH,
        monitor="val_accuracy",
        mode="max",
        save_best_only=True,
        verbose=1,
    ),

    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=8,
        restore_best_weights=True,
        verbose=1,
    ),

    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=3,
        min_lr=0.000001,
        verbose=1,
    ),

    tf.keras.callbacks.CSVLogger(
        TRAINING_LOG_PATH
    ),
]


# =========================================================
# Train
# =========================================================

print("\nStarting Custom CNN V2 Lite training...\n")

history = model.fit(
    train_dataset,
    validation_data=validation_dataset,
    epochs=EPOCHS,
    callbacks=callbacks,
    class_weight=class_weight_dict,
)


# =========================================================
# Save final model
# =========================================================

model.save(FINAL_MODEL_PATH)

print("\nTraining completed.")
print(f"Best model saved at: {BEST_MODEL_PATH}")
print(f"Final model saved at: {FINAL_MODEL_PATH}")
print(f"Class names saved at: {CLASS_NAMES_PATH}")
print(f"Training log saved at: {TRAINING_LOG_PATH}")