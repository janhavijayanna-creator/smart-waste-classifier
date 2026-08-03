const API_URL = "https://smart-waste-classifier-production-580f.up.railway.app";


/* =========================================================
   PAGE ELEMENTS
========================================================= */

const imageInput =
    document.getElementById("imageInput");

const previewImage =
    document.getElementById("previewImage");

const predictButton =
    document.getElementById("predictButton");

const prediction =
    document.getElementById("prediction");

const confidence =
    document.getElementById("confidence");

const recommendation =
    document.getElementById("recommendation");

const topPredictions =
    document.getElementById("topPredictions");

const progressBar =
    document.getElementById("progressBar");


/* =========================================================
   CAMERA ELEMENTS
========================================================= */

const openCameraBtn =
    document.getElementById("openCameraBtn");

const captureBtn =
    document.getElementById("captureBtn");

const closeCameraBtn =
    document.getElementById("closeCameraBtn");

const camera =
    document.getElementById("camera");

const canvas =
    document.getElementById("canvas");


/* =========================================================
   INTERACTIVE UI ELEMENTS
========================================================= */

const dropZone =
    document.getElementById("dropZone");

const previewOverlay =
    document.getElementById("previewOverlay");

const uploadMessage =
    document.getElementById("uploadMessage");

const resultCard =
    document.querySelector(".result-card");

const resultIcon =
    document.getElementById("resultIcon");


/* =========================================================
   STATE
========================================================= */

let selectedFile = null;
let cameraStream = null;
let previewObjectUrl = null;


/* =========================================================
   DRAG AND DROP
========================================================= */

if (dropZone) {
    [
        "dragenter",
        "dragover"
    ].forEach(eventName => {
        dropZone.addEventListener(
            eventName,
            event => {
                event.preventDefault();
                event.stopPropagation();

                dropZone.classList.add(
                    "drag-over"
                );
            }
        );
    });

    [
        "dragleave",
        "drop"
    ].forEach(eventName => {
        dropZone.addEventListener(
            eventName,
            event => {
                event.preventDefault();
                event.stopPropagation();

                dropZone.classList.remove(
                    "drag-over"
                );
            }
        );
    });

    dropZone.addEventListener(
        "drop",
        event => {
            const files =
                event.dataTransfer.files;

            if (!files || files.length === 0) {
                return;
            }

            handleSelectedFile(
                files[0]
            );
        }
    );
}


/* =========================================================
   FILE INPUT
========================================================= */

if (imageInput) {
    imageInput.addEventListener(
        "change",
        event => {
            handleSelectedFile(
                event.target.files[0]
            );
        }
    );
}


/* =========================================================
   HANDLE SELECTED FILE
========================================================= */

function handleSelectedFile(file) {
    if (!file) {
        return;
    }

    if (!file.type.startsWith("image/")) {
        showUploadMessage(
            "Please select a valid image file.",
            true
        );

        return;
    }

    const maximumSize =
        10 * 1024 * 1024;

    if (file.size > maximumSize) {
        showUploadMessage(
            "Image is too large. Maximum size is 10 MB.",
            true
        );

        return;
    }

    selectedFile = file;

    if (previewObjectUrl) {
        URL.revokeObjectURL(
            previewObjectUrl
        );
    }

    previewObjectUrl =
        URL.createObjectURL(file);

    previewImage.src =
        previewObjectUrl;

    previewImage.style.display =
        "block";

    resetPredictionResult();

    showUploadMessage(
        "Image ready for prediction.",
        false
    );

    closeCamera();
}


/* =========================================================
   OPEN CAMERA
========================================================= */

if (openCameraBtn) {
    openCameraBtn.addEventListener(
        "click",
        async () => {
            try {
                if (
                    !navigator.mediaDevices ||
                    !navigator.mediaDevices
                        .getUserMedia
                ) {
                    throw new Error(
                        "Camera access is not supported in this browser."
                    );
                }

                cameraStream =
                    await navigator.mediaDevices
                        .getUserMedia({
                            video: {
                                facingMode:
                                    "environment"
                            },
                            audio: false
                        });

                camera.srcObject =
                    cameraStream;

                camera.style.display =
                    "block";

                previewImage.style.display =
                    "none";

                openCameraBtn.style.display =
                    "none";

                captureBtn.style.display =
                    "inline-block";

                closeCameraBtn.style.display =
                    "inline-block";

                showUploadMessage(
                    "Camera opened. Position the waste item and capture the image.",
                    false
                );

            } catch (error) {
                console.error(
                    "Camera error:",
                    error
                );

                showUploadMessage(
                    error.message ||
                    "Unable to open the camera. Please allow camera permission.",
                    true
                );
            }
        }
    );
}


/* =========================================================
   CAPTURE CAMERA IMAGE
========================================================= */

if (captureBtn) {
    captureBtn.addEventListener(
        "click",
        () => {
            if (
                !camera.videoWidth ||
                !camera.videoHeight
            ) {
                showUploadMessage(
                    "Camera is still loading. Please wait a moment.",
                    true
                );

                return;
            }

            canvas.width =
                camera.videoWidth;

            canvas.height =
                camera.videoHeight;

            const context =
                canvas.getContext("2d");

            context.drawImage(
                camera,
                0,
                0,
                canvas.width,
                canvas.height
            );

            canvas.toBlob(
                blob => {
                    if (!blob) {
                        showUploadMessage(
                            "Unable to capture the image.",
                            true
                        );

                        return;
                    }

                    const capturedFile =
                        new File(
                            [blob],
                            "camera-capture.jpg",
                            {
                                type: "image/jpeg"
                            }
                        );

                    selectedFile =
                        capturedFile;

                    if (previewObjectUrl) {
                        URL.revokeObjectURL(
                            previewObjectUrl
                        );
                    }

                    previewObjectUrl =
                        URL.createObjectURL(
                            blob
                        );

                    previewImage.src =
                        previewObjectUrl;

                    previewImage.style.display =
                        "block";

                    resetPredictionResult();

                    showUploadMessage(
                        "Camera image captured successfully.",
                        false
                    );

                    closeCamera();
                },
                "image/jpeg",
                0.95
            );
        }
    );
}


/* =========================================================
   CLOSE CAMERA BUTTON
========================================================= */

if (closeCameraBtn) {
    closeCameraBtn.addEventListener(
        "click",
        closeCamera
    );
}


/* =========================================================
   CLOSE CAMERA
========================================================= */

function closeCamera() {
    if (cameraStream) {
        cameraStream
            .getTracks()
            .forEach(track => {
                track.stop();
            });

        cameraStream = null;
    }

    if (camera) {
        camera.srcObject = null;
        camera.style.display =
            "none";
    }

    if (previewImage) {
        previewImage.style.display =
            "block";
    }

    if (openCameraBtn) {
        openCameraBtn.style.display =
            "inline-block";
    }

    if (captureBtn) {
        captureBtn.style.display =
            "none";
    }

    if (closeCameraBtn) {
        closeCameraBtn.style.display =
            "none";
    }
}


/* =========================================================
   PREDICT BUTTON
========================================================= */

if (predictButton) {
    predictButton.addEventListener(
        "click",
        async () => {
            if (!selectedFile) {
                showUploadMessage(
                    "Please upload an image or capture one using the camera.",
                    true
                );

                return;
            }

            const token =
                localStorage.getItem(
                    "authToken"
                );

            if (!token) {
                window.location.href =
                    "login.html";

                return;
            }

            setPredictingState(true);

            const formData =
                new FormData();

            formData.append(
                "file",
                selectedFile
            );

            try {
                const response =
                    await fetch(
                        `${API_URL}/predict`,
                        {
                            method: "POST",

                            headers: {
                                Authorization:
                                    `Bearer ${token}`
                            },

                            body: formData
                        }
                    );

                const data =
                    await response.json();

                if (
                    response.status === 401
                ) {
                    clearStoredSession();

                    window.location.href =
                        "login.html";

                    return;
                }

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        "Prediction failed."
                    );
                }

                showPredictionResult(
                    data
                );

                showUploadMessage(
                    "Prediction completed successfully.",
                    false
                );

            } catch (error) {
                console.error(
                    "Prediction error:",
                    error
                );

                showPredictionError(
                    error.message
                );

            } finally {
                setPredictingState(
                    false
                );
            }
        }
    );
}


/* =========================================================
   PREDICTING STATE
========================================================= */

function setPredictingState(isPredicting) {
    predictButton.disabled =
        isPredicting;

    predictButton.textContent =
        isPredicting
            ? "Predicting..."
            : "Predict Waste";

    if (previewOverlay) {
        previewOverlay.style.display =
            isPredicting
                ? "flex"
                : "none";
    }

    if (isPredicting) {
        prediction.textContent =
            "Predicting...";

        confidence.textContent =
            "--";

        recommendation.textContent =
            "Please wait while the AI analyses the image.";

        progressBar.style.width =
            "0%";

        topPredictions.innerHTML = `
            <p class="empty-message">
                Analysing image...
            </p>
        `;
    }
}


/* =========================================================
   SHOW PREDICTION RESULT
========================================================= */

function showPredictionResult(data) {
    const predictedClass =
        data.predicted_class ||
        "unknown";

    const confidenceValue =
        Number(
            data.confidence || 0
        );

    prediction.textContent =
        formatClassName(
            predictedClass
        );

    confidence.textContent =
        `${confidenceValue.toFixed(2)}%`;

    progressBar.style.width =
        `${Math.min(
            confidenceValue,
            100
        )}%`;

    recommendation.textContent =
        data.recommendation ||
        "No recommendation available.";

    renderTopPredictions(
        data.top_predictions
    );

    if (resultIcon) {
        resultIcon.textContent =
            getResultIcon(
                predictedClass
            );
    }

    if (resultCard) {
        resultCard.classList.add(
            "has-result",
            "result-updated"
        );

        window.setTimeout(
            () => {
                resultCard.classList.remove(
                    "result-updated"
                );
            },
            600
        );
    }
}


/* =========================================================
   SHOW PREDICTION ERROR
========================================================= */

function showPredictionError(message) {
    prediction.textContent =
        "Prediction Failed";

    confidence.textContent =
        "0%";

    progressBar.style.width =
        "0%";

    recommendation.textContent =
        message ||
        "Unable to complete the prediction.";

    topPredictions.innerHTML = `
        <p class="empty-message">
            No prediction result available.
        </p>
    `;

    showUploadMessage(
        message ||
        "Unable to complete the prediction.",
        true
    );
}


/* =========================================================
   RENDER TOP PREDICTIONS
========================================================= */

function renderTopPredictions(items) {
    topPredictions.innerHTML =
        "";

    if (
        !Array.isArray(items) ||
        items.length === 0
    ) {
        topPredictions.innerHTML = `
            <p class="empty-message">
                No top predictions available.
            </p>
        `;

        return;
    }

    items.forEach(item => {
        const itemElement =
            document.createElement(
                "div"
            );

        itemElement.className =
            "class-count-item";

        const className =
            formatClassName(
                item.class
            );

        const itemConfidence =
            Number(
                item.confidence || 0
            );

        itemElement.innerHTML = `
            <span class="class-name">
                ${escapeHtml(
                    className
                )}
            </span>

            <span class="class-value">
                ${itemConfidence.toFixed(2)}%
            </span>
        `;

        topPredictions.appendChild(
            itemElement
        );
    });
}


/* =========================================================
   RESET RESULT
========================================================= */

function resetPredictionResult() {
    prediction.textContent =
        "—";

    confidence.textContent =
        "0%";

    progressBar.style.width =
        "0%";

    recommendation.textContent =
        "Click Predict Waste to analyse the selected image.";

    topPredictions.innerHTML = `
        <p class="empty-message">
            No prediction yet.
        </p>
    `;

    if (resultIcon) {
        resultIcon.textContent =
            "♻";
    }

    if (resultCard) {
        resultCard.classList.remove(
            "has-result",
            "result-updated"
        );
    }
}


/* =========================================================
   UPLOAD MESSAGE
========================================================= */

function showUploadMessage(
    message,
    isError
) {
    if (!uploadMessage) {
        return;
    }

    uploadMessage.textContent =
        message;

    uploadMessage.className =
        isError
            ? "form-message error-message"
            : "form-message success-message";
}


/* =========================================================
   RESULT ICON
========================================================= */

function getResultIcon(value) {
    const icons = {
        broken_toys: "🧸",
        cardboard: "📦",
        glass: "🫙",
        human: "🧍",
        metal: "🥫",
        paper: "📄",
        plastic: "🧴",
        trash: "🗑️",
        uncertain: "❓"
    };

    return icons[value] || "♻";
}


/* =========================================================
   FORMAT CLASS NAME
========================================================= */

function formatClassName(value) {
    if (!value) {
        return "Unknown";
    }

    return String(value)
        .replaceAll(
            "_",
            " "
        )
        .replace(
            /\b\w/g,
            letter =>
                letter.toUpperCase()
        );
}


/* =========================================================
   ESCAPE HTML
========================================================= */

function escapeHtml(value) {
    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}


/* =========================================================
   CLEAR SESSION
========================================================= */

function clearStoredSession() {
    localStorage.removeItem(
        "authToken"
    );

    localStorage.removeItem(
        "authUser"
    );
}


/* =========================================================
   STOP CAMERA WHEN LEAVING PAGE
========================================================= */

window.addEventListener(
    "beforeunload",
    () => {
        closeCamera();

        if (previewObjectUrl) {
            URL.revokeObjectURL(
                previewObjectUrl
            );
        }
    }
);