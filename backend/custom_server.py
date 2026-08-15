import json
import os
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError

from backend.database import (
    authenticate_user,
    clear_prediction_history,
    create_session,
    create_user,
    delete_prediction,
    delete_session,
    get_prediction_history,
    get_statistics,
    get_user_by_token,
    initialize_database,
    save_prediction,
)

from backend.recommendations import (
    RECYCLING_RECOMMENDATIONS,
)


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    PROJECT_ROOT
    / "backend"
    / "best_final_8class_finetuned.keras"
)

CLASS_NAMES_PATH = (
    PROJECT_ROOT
    / "model_training"
    / "class_names_final_8.json"
)


# =========================================================
# SERVER SETTINGS
# =========================================================

HOST = "0.0.0.0"

PORT = int(
    os.environ.get(
        "PORT",
        "8000"
    )
)

MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

CONFIDENCE_THRESHOLD = 60.0


# =========================================================
# VERIFY REQUIRED FILES
# =========================================================

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model was not found: {MODEL_PATH}"
    )

if not CLASS_NAMES_PATH.exists():
    raise FileNotFoundError(
        f"Class names file was not found: "
        f"{CLASS_NAMES_PATH}"
    )


# =========================================================
# LOAD CLASS NAMES
# =========================================================

with open(
    CLASS_NAMES_PATH,
    "r",
    encoding="utf-8",
) as file:
    CLASS_NAMES = json.load(file)


print("Classes loaded:")

for index, class_name in enumerate(
    CLASS_NAMES
):
    print(
        f"{index}: {class_name}"
    )


# =========================================================
# LOAD AI MODEL
# =========================================================

print("Loading custom CNN model...")

model = tf.keras.models.load_model(
    MODEL_PATH
)

print(
    "Custom CNN model loaded successfully."
)


# =========================================================
# INITIALIZE DATABASE
# =========================================================

initialize_database()

print("SQLite database initialized.")


# =========================================================
# PREDICTION FUNCTION
# =========================================================

def predict_image(
    image_bytes: bytes
) -> dict:
    try:
        image = Image.open(
            BytesIO(image_bytes)
        )

        image = image.convert("RGB")

        image = image.resize(
            (224, 224)
        )

    except UnidentifiedImageError as error:
        raise ValueError(
            "The uploaded file is not a valid image."
        ) from error

    except OSError as error:
        raise ValueError(
            "The image could not be opened."
        ) from error

    image_array = np.array(
        image,
        dtype=np.float32,
    )

    image_array = np.expand_dims(
        image_array,
        axis=0,
    )

    predictions = model.predict(
        image_array,
        verbose=0,
    )[0]

    if len(predictions) != len(CLASS_NAMES):
        raise ValueError(
            "The model output does not match "
            "the number of class names."
        )

    top_indices = np.argsort(
        predictions
    )[::-1][:3]

    top_predictions = []

    for index in top_indices:
        class_name = CLASS_NAMES[
            int(index)
        ]

        confidence = (
            float(predictions[index])
            * 100
        )

        top_predictions.append(
            {
                "class": class_name,
                "confidence": round(
                    confidence,
                    2,
                ),
            }
        )

    predicted_index = int(
        top_indices[0]
    )

    predicted_class = CLASS_NAMES[
        predicted_index
    ]

    confidence = (
        float(
            predictions[predicted_index]
        )
        * 100
    )

    if confidence < CONFIDENCE_THRESHOLD:
        final_class = "uncertain"

        recommendation = (
            "The model is not confident about this "
            "object. Please retake the image with "
            "better lighting, a plain background, "
            "and the complete object visible."
        )

    else:
        final_class = predicted_class

        recommendation = (
            RECYCLING_RECOMMENDATIONS.get(
                predicted_class,
                (
                    "No recycling recommendation "
                    "is available for this category."
                ),
            )
        )

    return {
        "predicted_class": final_class,
        "confidence": round(
            confidence,
            2,
        ),
        "recommendation": recommendation,
        "top_predictions": top_predictions,
    }


# =========================================================
# HTTP REQUEST HANDLER
# =========================================================

class WasteRequestHandler(
    BaseHTTPRequestHandler
):

    # =====================================================
    # CORS HEADERS
    # =====================================================

    def add_cors_headers(self):
        self.send_header(
            "Access-Control-Allow-Origin",
            "*",
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, DELETE, OPTIONS",
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization",
        )

    # =====================================================
    # SEND JSON RESPONSE
    # =====================================================

    def send_json(
        self,
        status_code: int,
        data: dict,
    ):
        response_body = json.dumps(
            data,
            indent=2,
        ).encode("utf-8")

        self.send_response(
            status_code
        )

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )

        self.send_header(
            "Content-Length",
            str(len(response_body)),
        )

        self.add_cors_headers()

        self.end_headers()

        self.wfile.write(
            response_body
        )

    # =====================================================
    # GET AUTHORIZATION TOKEN
    # =====================================================

    def get_authorization_token(self):
        authorization_header = (
            self.headers.get(
                "Authorization",
                "",
            )
        )

        if not authorization_header.startswith(
            "Bearer "
        ):
            return None

        return authorization_header.replace(
            "Bearer ",
            "",
            1,
        ).strip()

    # =====================================================
    # GET LOGGED-IN USER
    # =====================================================

    def get_authenticated_user(self):
        token = (
            self.get_authorization_token()
        )

        if not token:
            return None

        return get_user_by_token(
            token
        )

    # =====================================================
    # READ JSON REQUEST
    # =====================================================

    def read_json_body(self):
        content_length_header = (
            self.headers.get(
                "Content-Length"
            )
        )

        if not content_length_header:
            raise ValueError(
                "Content-Length header is required."
            )

        try:
            content_length = int(
                content_length_header
            )

        except ValueError as error:
            raise ValueError(
                "Invalid Content-Length header."
            ) from error

        if content_length <= 0:
            raise ValueError(
                "Request body is empty."
            )

        request_body = self.rfile.read(
            content_length
        )

        if not request_body:
            raise ValueError(
                "Request body is empty."
            )

        try:
            return json.loads(
                request_body.decode(
                    "utf-8"
                )
            )

        except json.JSONDecodeError as error:
            raise ValueError(
                "Invalid JSON request body."
            ) from error

    # =====================================================
    # REQUIRE AUTHENTICATION
    # =====================================================

    def require_authenticated_user(self):
        user = (
            self.get_authenticated_user()
        )

        if user is None:
            self.send_json(
                401,
                {
                    "error": (
                        "Authentication required. "
                        "Please log in."
                    ),
                },
            )

            return None

        return user

    # =====================================================
    # OPTIONS REQUEST
    # =====================================================

    def do_OPTIONS(self):
        self.send_response(204)

        self.add_cors_headers()

        self.end_headers()

    # =====================================================
    # GET REQUESTS
    # =====================================================

    def do_GET(self):
        path = urlparse(
            self.path
        ).path

        print("==========")
        print(
            "GET PATH:",
            repr(path),
        )

        # -------------------------------------------------
        # ROOT
        # -------------------------------------------------

        if path == "/":
            self.send_json(
                200,
                {
                    "message": (
                        "Smart Waste Classifier "
                        "custom backend is running."
                    ),
                },
            )

        # -------------------------------------------------
        # HEALTH
        # -------------------------------------------------

        elif path == "/health":
            self.send_json(
                200,
                {
                    "status": "healthy",
                    "model": "best_final_8class_finetuned.keras",
                    "database": "connected",
                    "authentication": "enabled",
                    "classes": len(
                        CLASS_NAMES
                    ),
                },
            )

        # -------------------------------------------------
        # CURRENT USER
        # -------------------------------------------------

        elif path == "/me":
            user = (
                self.require_authenticated_user()
            )

            if user is None:
                return

            self.send_json(
                200,
                {
                    "user": user,
                },
            )

        # -------------------------------------------------
        # USER HISTORY
        # -------------------------------------------------

        elif path == "/history":
            user = (
                self.require_authenticated_user()
            )

            if user is None:
                return

            try:
                history = (
                    get_prediction_history(
                        user["id"]
                    )
                )

                self.send_json(
                    200,
                    {
                        "history": history,
                    },
                )

            except Exception as error:
                print(
                    "History error:",
                    error,
                )

                self.send_json(
                    500,
                    {
                        "error": (
                            "Unable to load "
                            "prediction history."
                        ),
                    },
                )

        # -------------------------------------------------
        # USER STATISTICS
        # -------------------------------------------------

        elif path == "/statistics":
            user = (
                self.require_authenticated_user()
            )

            if user is None:
                return

            try:
                statistics = get_statistics(
                    user["id"]
                )

                self.send_json(
                    200,
                    statistics,
                )

            except Exception as error:
                print(
                    "Statistics error:",
                    error,
                )

                self.send_json(
                    500,
                    {
                        "error": (
                            "Unable to load "
                            "statistics."
                        ),
                    },
                )

        # -------------------------------------------------
        # ROUTE NOT FOUND
        # -------------------------------------------------

        else:
            self.send_json(
                404,
                {
                    "error": (
                        "Route not found."
                    ),
                },
            )

    # =====================================================
    # POST REQUESTS
    # =====================================================

    def do_POST(self):
        path = urlparse(
            self.path
        ).path

        print("==========")
        print(
            "POST PATH:",
            repr(path),
        )

        # -------------------------------------------------
        # REGISTER
        # -------------------------------------------------

        if path == "/register":
            try:
                data = self.read_json_body()

                name = str(
                    data.get(
                        "name",
                        "",
                    )
                ).strip()

                email = str(
                    data.get(
                        "email",
                        "",
                    )
                ).strip()

                password = str(
                    data.get(
                        "password",
                        "",
                    )
                )

                if len(name) < 2:
                    raise ValueError(
                        "Name must contain at least "
                        "2 characters."
                    )

                if (
                    "@" not in email
                    or "." not in email
                ):
                    raise ValueError(
                        "Enter a valid email address."
                    )

                if len(password) < 6:
                    raise ValueError(
                        "Password must contain at least "
                        "6 characters."
                    )

                user_id = create_user(
                    name=name,
                    email=email,
                    password=password,
                )

                token = create_session(
                    user_id
                )

                user = get_user_by_token(
                    token
                )

                self.send_json(
                    201,
                    {
                        "message": (
                            "Account created "
                            "successfully."
                        ),
                        "token": token,
                        "user": user,
                    },
                )

            except ValueError as error:
                self.send_json(
                    400,
                    {
                        "error": str(error),
                    },
                )

            except Exception as error:
                print(
                    "Registration error:",
                    error,
                )

                self.send_json(
                    500,
                    {
                        "error": (
                            "Unable to create "
                            "the account."
                        ),
                    },
                )

            return

        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        if path == "/login":
            try:
                data = self.read_json_body()

                email = str(
                    data.get(
                        "email",
                        "",
                    )
                ).strip()

                password = str(
                    data.get(
                        "password",
                        "",
                    )
                )

                if not email or not password:
                    raise ValueError(
                        "Email and password "
                        "are required."
                    )

                user = authenticate_user(
                    email=email,
                    password=password,
                )

                if user is None:
                    self.send_json(
                        401,
                        {
                            "error": (
                                "Incorrect email "
                                "or password."
                            ),
                        },
                    )

                    return

                token = create_session(
                    user["id"]
                )

                self.send_json(
                    200,
                    {
                        "message": (
                            "Login successful."
                        ),
                        "token": token,
                        "user": user,
                    },
                )

            except ValueError as error:
                self.send_json(
                    400,
                    {
                        "error": str(error),
                    },
                )

            except Exception as error:
                print(
                    "Login error:",
                    error,
                )

                self.send_json(
                    500,
                    {
                        "error": (
                            "Unable to log in."
                        ),
                    },
                )

            return

        # -------------------------------------------------
        # LOGOUT
        # -------------------------------------------------

        if path == "/logout":
            token = (
                self.get_authorization_token()
            )

            if token:
                delete_session(
                    token
                )

            self.send_json(
                200,
                {
                    "message": (
                        "Logged out successfully."
                    ),
                },
            )

            return

        # -------------------------------------------------
        # PREDICTION ROUTE CHECK
        # -------------------------------------------------

        if path != "/predict":
            self.send_json(
                404,
                {
                    "error": (
                        "Route not found."
                    ),
                },
            )

            return

        # -------------------------------------------------
        # REQUIRE LOGIN FOR PREDICTION
        # -------------------------------------------------

        user = (
            self.require_authenticated_user()
        )

        if user is None:
            return

        # -------------------------------------------------
        # READ MULTIPART IMAGE
        # -------------------------------------------------

        content_type = self.headers.get(
            "Content-Type",
            "",
        )

        content_length_header = (
            self.headers.get(
                "Content-Length"
            )
        )

        if not content_length_header:
            self.send_json(
                411,
                {
                    "error": (
                        "Content-Length header "
                        "is required."
                    ),
                },
            )

            return

        try:
            content_length = int(
                content_length_header
            )

        except ValueError:
            self.send_json(
                400,
                {
                    "error": (
                        "Invalid Content-Length "
                        "header."
                    ),
                },
            )

            return

        if content_length <= 0:
            self.send_json(
                400,
                {
                    "error": (
                        "The request body is empty."
                    ),
                },
            )

            return

        if content_length > (
            MAX_FILE_SIZE
            + (1024 * 1024)
        ):
            self.send_json(
                413,
                {
                    "error": (
                        "The uploaded file is too "
                        "large. Maximum size is 10 MB."
                    ),
                },
            )

            return

        if not content_type.startswith(
            "multipart/form-data"
        ):
            self.send_json(
                400,
                {
                    "error": (
                        "The request must use "
                        "multipart/form-data."
                    ),
                },
            )

            return

        try:
            request_body = self.rfile.read(
                content_length
            )

            raw_message = (
                b"Content-Type: "
                + content_type.encode(
                    "utf-8"
                )
                + b"\r\n"
                + b"MIME-Version: 1.0"
                + b"\r\n\r\n"
                + request_body
            )

            message = BytesParser(
                policy=default
            ).parsebytes(
                raw_message
            )

            uploaded_file = None
            file_name = None
            file_type = None

            for part in message.iter_parts():
                content_disposition = (
                    part.get(
                        "Content-Disposition",
                        "",
                    )
                )

                field_name = (
                    part.get_param(
                        "name",
                        header=(
                            "Content-Disposition"
                        ),
                    )
                )

                if (
                    "form-data"
                    in content_disposition
                    and field_name == "file"
                ):
                    uploaded_file = (
                        part.get_payload(
                            decode=True
                        )
                    )

                    file_name = (
                        part.get_filename()
                        or "uploaded_image"
                    )

                    file_type = (
                        part.get_content_type()
                    )

                    break

            if uploaded_file is None:
                self.send_json(
                    400,
                    {
                        "error": (
                            "No image was uploaded. "
                            "Use the form field name "
                            "'file'."
                        ),
                    },
                )

                return

            if not uploaded_file:
                self.send_json(
                    400,
                    {
                        "error": (
                            "The uploaded image "
                            "is empty."
                        ),
                    },
                )

                return

            if len(uploaded_file) > MAX_FILE_SIZE:
                self.send_json(
                    413,
                    {
                        "error": (
                            "The uploaded file is "
                            "too large. Maximum size "
                            "is 10 MB."
                        ),
                    },
                )

                return

            if file_type not in ALLOWED_TYPES:
                self.send_json(
                    415,
                    {
                        "error": (
                            "Unsupported image type. "
                            "Upload JPG, PNG or WEBP."
                        ),
                    },
                )

                return

            safe_file_name = Path(
                file_name
            ).name

            result = predict_image(
                uploaded_file
            )

            prediction_id = save_prediction(
                user_id=user["id"],
                file_name=safe_file_name,
                predicted_class=result[
                    "predicted_class"
                ],
                confidence=result[
                    "confidence"
                ],
                recommendation=result[
                    "recommendation"
                ],
                top_predictions=result[
                    "top_predictions"
                ],
            )

            result["id"] = prediction_id
            result["file_name"] = safe_file_name

            self.send_json(
                200,
                result,
            )

        except ValueError as error:
            self.send_json(
                400,
                {
                    "error": str(error),
                },
            )

        except Exception as error:
            print(
                "Prediction error:",
                error,
            )

            self.send_json(
                500,
                {
                    "error": (
                        "An internal server error "
                        "occurred while processing "
                        "the image."
                    ),
                },
            )

    # =====================================================
    # DELETE REQUESTS
    # =====================================================

    def do_DELETE(self):
        path = urlparse(
            self.path
        ).path

        print("==========")
        print(
            "DELETE PATH:",
            repr(path),
        )

        user = (
            self.require_authenticated_user()
        )

        if user is None:
            return

        # -------------------------------------------------
        # CLEAR CURRENT USER HISTORY
        # -------------------------------------------------

        if path == "/history":
            try:
                clear_prediction_history(
                    user["id"]
                )

                self.send_json(
                    200,
                    {
                        "message": (
                            "Prediction history "
                            "cleared successfully."
                        ),
                    },
                )

            except Exception as error:
                print(
                    "Clear history error:",
                    error,
                )

                self.send_json(
                    500,
                    {
                        "error": (
                            "Unable to clear "
                            "prediction history."
                        ),
                    },
                )

            return

        # -------------------------------------------------
        # DELETE ONE CURRENT USER PREDICTION
        # -------------------------------------------------

        if path.startswith(
            "/history/"
        ):
            prediction_id_text = (
                path.replace(
                    "/history/",
                    "",
                    1,
                )
            )

            try:
                prediction_id = int(
                    prediction_id_text
                )

            except ValueError:
                self.send_json(
                    400,
                    {
                        "error": (
                            "Invalid prediction ID."
                        ),
                    },
                )

                return

            try:
                deleted = delete_prediction(
                    user_id=user["id"],
                    prediction_id=prediction_id,
                )

                if deleted:
                    self.send_json(
                        200,
                        {
                            "message": (
                                "Prediction deleted "
                                "successfully."
                            ),
                        },
                    )

                else:
                    self.send_json(
                        404,
                        {
                            "error": (
                                "Prediction record "
                                "was not found."
                            ),
                        },
                    )

            except Exception as error:
                print(
                    "Delete prediction error:",
                    error,
                )

                self.send_json(
                    500,
                    {
                        "error": (
                            "Unable to delete the "
                            "prediction record."
                        ),
                    },
                )

            return

        self.send_json(
            404,
            {
                "error": (
                    "Route not found."
                ),
            },
        )

    # =====================================================
    # CUSTOM SERVER LOGGING
    # =====================================================

    def log_message(
        self,
        format_string,
        *args,
    ):
        print(
            f"[Backend] "
            f"{self.address_string()} - "
            f"{format_string % args}"
        )


# =========================================================
# START SERVER
# =========================================================

def run_server():
    server = ThreadingHTTPServer(
        (HOST, PORT),
        WasteRequestHandler,
    )

    print(
        f"Custom backend running at "
        f"http://{HOST}:{PORT}"
    )

    print(
        "Authentication is enabled."
    )

    print(
        "Press Ctrl+C to stop the backend."
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print(
            "\nStopping custom backend..."
        )

    finally:
        server.server_close()

        print(
            "Custom backend stopped."
        )


if __name__ == "__main__":
    run_server()