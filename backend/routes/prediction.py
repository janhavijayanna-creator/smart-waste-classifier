from io import BytesIO
from pathlib import Path

import numpy as np
import tensorflow as tf
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from backend.recommendations import RECYCLING_RECOMMENDATIONS


router = APIRouter()

ALLOWED_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp",
]

MODEL_PATH = (
    Path("backend")
    / "best_final_8class_finetuned.keras"
)

CLASS_NAMES = [
    "broken_toys",
    "cardboard",
    "e_waste",
    "glass",
    "metal",
    "organic",
    "paper",
    "plastic",
]


if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Trained model was not found: {MODEL_PATH.resolve()}"
    )


model = tf.keras.models.load_model(MODEL_PATH)


@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG and WEBP images are allowed.",
        )

    image_bytes = await file.read()

    try:
        image = Image.open(BytesIO(image_bytes))
        image = image.convert("RGB")
        image = image.resize((224, 224))

        image_array = np.array(image, dtype=np.float32)
        image_array = np.expand_dims(image_array, axis=0)

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid image.",
        )

    predictions = model.predict(image_array, verbose=0)[0]

    top_indices = np.argsort(predictions)[::-1][:3]

    top_predictions = []

    for index in top_indices:
        class_name = CLASS_NAMES[int(index)]
        class_confidence = float(predictions[index]) * 100

        top_predictions.append(
            {
                "class": class_name,
                "confidence": round(class_confidence, 2),
            }
        )
    predicted_index = int(top_indices[0])
    predicted_class = CLASS_NAMES[predicted_index]
    confidence = float(predictions[predicted_index]) * 100

    CONFIDENCE_THRESHOLD = 60.0

    if confidence < CONFIDENCE_THRESHOLD:
        final_class = "uncertain"
        recommendation = (
            "The model is not confident about this object. "
            "Please retake the image with better lighting, "
            "a plain background, and the complete object visible."
        )
    else:
        final_class = predicted_class
        recommendation = RECYCLING_RECOMMENDATIONS[predicted_class]

    return {
        "predicted_class": final_class,
        "confidence": round(confidence, 2),
        "recommendation": recommendation,
        "top_predictions": top_predictions,
    }