from pathlib import Path

import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.applications.mobilenet_v2 import (
    MobileNetV2,
    preprocess_input,
)
import numpy as np
from sklearn.utils.class_weight import compute_class_weight

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
all_labels = []

for _, labels in training_dataset:
    all_labels.extend(labels.numpy())

all_labels = np.array(all_labels)

class_weights_array = compute_class_weight(
    class_weight="balanced",
    classes=np.arange(len(class_names)),
    y=all_labels
)

class_weight_dict = {
    index: float(weight)
    for index, weight in enumerate(class_weights_array)
}

print("Class weights:")
for index, weight in class_weight_dict.items():
    print(f"{class_names[index]}: {weight:.2f}")
number_of_classes = len(class_names)

print("Classes:", class_names)
print("Number of classes:", number_of_classes)

base_model = MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)

base_model.trainable = True

for layer in base_model.layers[:-30]:
    layer.trainable = False

print("MobileNetV2 loaded successfully.")

data_augmentation = tf.keras.Sequential(
    [
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.10),
        layers.RandomZoom(0.10),
        layers.RandomContrast(0.10),
    ],
    name="data_augmentation",
)

inputs = tf.keras.Input(shape=(224, 224, 3))

x = data_augmentation(inputs)
x = preprocess_input(x)

x = base_model(
    x,
    training=False
)

x = layers.GlobalAveragePooling2D()(x)

x = layers.Dropout(0.2)(x)

outputs = layers.Dense(
    number_of_classes,
    activation="softmax"
)(x)

model = tf.keras.Model(
    inputs=inputs,
    outputs=outputs
)

print("Waste classification model created successfully.")

model.summary()

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.00001
    ),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

print("Model compiled successfully.")

EPOCHS = 30

BEST_MODEL_PATH = (
    Path("model_training")
    / "balanced_waste_classifier.keras"
)

callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=5,
        restore_best_weights=True
    ),
    tf.keras.callbacks.ModelCheckpoint(
        filepath=BEST_MODEL_PATH,
        monitor="val_accuracy",
        save_best_only=True
    )
]

history = model.fit(
    training_dataset,
    validation_data=validation_dataset,
    epochs=EPOCHS,
    callbacks=callbacks,
    class_weight=class_weight_dict
)

print("Model training completed successfully.")

MODEL_PATH = (
    Path("model_training")
    / "balanced_final.keras"
)
model.save(MODEL_PATH)

print(f"Model saved successfully at: {MODEL_PATH}")