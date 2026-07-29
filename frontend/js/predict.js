const API_URL = "http://127.0.0.1:8000";

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


/* Camera Elements */

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


let selectedFile = null;
let cameraStream = null;


/* =========================
   FILE UPLOAD
========================= */

imageInput.addEventListener(
    "change",
    (event) => {

        selectedFile =
            event.target.files[0];

        if (!selectedFile) {
            return;
        }

        previewImage.src =
            URL.createObjectURL(selectedFile);

        closeCamera();
    }
);


/* =========================
   OPEN CAMERA
========================= */

openCameraBtn.addEventListener(
    "click",
    async () => {

        try {

            cameraStream =
                await navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: "environment"
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

        } catch (error) {

            console.error(
                "Camera error:",
                error
            );

            alert(
                "Unable to open the camera. Please allow camera permission in your browser."
            );
        }
    }
);


/* =========================
   CAPTURE IMAGE
========================= */

captureBtn.addEventListener(
    "click",
    () => {

        if (
            !camera.videoWidth ||
            !camera.videoHeight
        ) {
            alert(
                "Camera is still loading. Please wait for a moment."
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
            (blob) => {

                if (!blob) {
                    alert(
                        "Unable to capture the image."
                    );

                    return;
                }

                selectedFile =
                    new File(
                        [blob],
                        "camera-capture.jpg",
                        {
                            type: "image/jpeg"
                        }
                    );

                previewImage.src =
                    URL.createObjectURL(blob);

                previewImage.style.display =
                    "block";

                closeCamera();

            },
            "image/jpeg",
            0.95
        );
    }
);


/* =========================
   CLOSE CAMERA BUTTON
========================= */

closeCameraBtn.addEventListener(
    "click",
    closeCamera
);


/* =========================
   CLOSE CAMERA FUNCTION
========================= */

function closeCamera() {

    if (cameraStream) {

        cameraStream
            .getTracks()
            .forEach(
                track =>
                    track.stop()
            );

        cameraStream = null;
    }

    camera.srcObject = null;

    camera.style.display =
        "none";

    previewImage.style.display =
        "block";

    openCameraBtn.style.display =
        "inline-block";

    captureBtn.style.display =
        "none";

    closeCameraBtn.style.display =
        "none";
}


/* =========================
   PREDICT IMAGE
========================= */

predictButton.addEventListener(
    "click",
    async () => {

        if (!selectedFile) {

            alert(
                "Please upload an image or capture one using the camera."
            );

            return;
        }

        prediction.textContent =
            "Predicting...";

        confidence.textContent =
            "--";

        recommendation.textContent =
            "Please wait...";

        topPredictions.innerHTML =
            "";

        progressBar.style.width =
            "0%";

        predictButton.disabled =
            true;

        predictButton.textContent =
            "Predicting...";

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
                        body: formData
                    }
                );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    data.error ||
                    "Prediction failed."
                );
            }

            prediction.textContent =
                formatClassName(
                    data.predicted_class
                );

            confidence.textContent =
                `${data.confidence}%`;

            progressBar.style.width =
                `${data.confidence}%`;

            recommendation.textContent =
                data.recommendation;

            topPredictions.innerHTML =
                "";

            if (
                Array.isArray(
                    data.top_predictions
                )
            ) {

                data.top_predictions.forEach(
                    item => {

                        const div =
                            document.createElement(
                                "div"
                            );

                        div.className =
                            "class-count-item";

                        div.innerHTML = `
                            <span class="class-name">
                                ${formatClassName(item.class)}
                            </span>

                            <span class="class-value">
                                ${item.confidence}%
                            </span>
                        `;

                        topPredictions.appendChild(
                            div
                        );
                    }
                );

            } else {

                topPredictions.innerHTML = `
                    <p>
                        No top predictions available.
                    </p>
                `;
            }

        } catch (error) {

            console.error(
                "Prediction error:",
                error
            );

            prediction.textContent =
                "Failed";

            confidence.textContent =
                "0%";

            recommendation.textContent =
                "Unable to complete prediction.";

            progressBar.style.width =
                "0%";

            alert(
                error.message
            );

        } finally {

            predictButton.disabled =
                false;

            predictButton.textContent =
                "Predict Waste";
        }
    }
);


/* =========================
   FORMAT CLASS NAME
========================= */

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


/* =========================
   STOP CAMERA WHEN LEAVING
========================= */

window.addEventListener(
    "beforeunload",
    closeCamera
);