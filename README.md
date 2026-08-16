♻️ AI-Based Smart Waste Classification & Recycling Recommendation System

An AI-powered web application that classifies waste using a fine-tuned 8-class deep-learning model and provides recycling recommendations to encourage proper waste segregation and disposal.

📌 Project Overview

The Smart Waste Classifier allows a user to upload a waste image or capture one using a webcam. The image is sent to the deployed Python backend, processed by the trained Keras model, and returned with the predicted waste category, confidence score, top predictions, and a recycling recommendation.

The final application also includes authentication, user-specific prediction history, dashboard analytics, SQLite storage, low-confidence handling, and public deployment on Railway.

🚀 Features

📷 Webcam image capture

📁 Image upload and drag-and-drop input

🤖 AI-based waste classification

🎯 Confidence score and top predictions

⚠️ Uncertain result for low-confidence predictions

♻️ Recycling recommendations

🔐 User registration and login

📝 User-specific prediction history

📊 Dashboard statistics and category counts

📈 Waste distribution and category charts

💾 SQLite database storage

☁️ Frontend and backend deployed on Railway

🧠 AI Model

Deployed model: best_final_8class_finetuned.keras

Model type: Fine-tuned deep-learning image classification model

Input: 224 × 224 RGB image

Best validation accuracy: 94.95%

94.95% is the best validation accuracy recorded during fine-tuning. It is not presented as a separately measured independent test-set accuracy.

Final 8 Waste Classes

Broken Toys

Cardboard

E-Waste

Glass

Metal

Organic

Paper

Plastic

If the highest prediction confidence is below the configured threshold, the application returns Uncertain rather than forcing the image into one of the eight trained classes.

🛠 Technologies Used

Frontend

HTML5

CSS3

JavaScript

Chart.js

Backend

Python

HTTP-based backend/API

SQLite

AI / Image Processing

TensorFlow

Keras

NumPy

Pillow

Development & Deployment

Git

GitHub

Railway

🔄 Application Flow

User registers or logs in.

User opens the prediction page.

An image is uploaded, dropped, or captured using the camera.

The frontend sends the image and authentication token to the backend.

The backend validates the session and preprocesses the image.

The final fine-tuned model performs inference.

The backend returns the class, confidence, top predictions, and recycling recommendation.

The prediction is stored in the authenticated user's history.

Dashboard statistics are calculated from that user's prediction records.

📂 Project Structure

smart-waste-classifier/
├── backend/          # Authentication, prediction, history, statistics and database logic
├── frontend/         # HTML, CSS and JavaScript user interface
├── model_training/   # Training/fine-tuning scripts and class information
└── .gitignore

⚙️ Run Locally

1. Start the backend

From the project root:

python -m backend.custom_server

The local backend runs at:

http://127.0.0.1:8000

You can verify it using:

http://127.0.0.1:8000/health

2. Start the frontend

Open another terminal:

cd frontend
python -m http.server 3000

Then open:

http://127.0.0.1:3000

🌐 Live Deployment

The project is deployed on Railway as separate frontend and backend services.

Live website:

https://frontend-production-5c347.up.railway.app

Backend health/API service:

https://smart-waste-classifier-production-580f.up.railway.app/health

The deployed website works independently of the local VS Code development servers.

📊 Final Model Performance

Metric

Value

Best Validation Accuracy

94.95%

Trained Waste Classes

8

Input Size

224 × 224 RGB

Low-Confidence Handling

Uncertain

Deployment

Railway

🔌 Main Backend Endpoints

Endpoint

Purpose

/health

Checks backend, model and database availability

/register

Creates a user account

/login

Authenticates an existing user

/predict

Classifies an uploaded image

/history

Returns/manages user-specific prediction history

/statistics

Supplies user-specific dashboard analytics

🔮 Future Improvements

Collect more balanced real-world waste images

Evaluate the model on a separate independent test set with precision, recall, F1-score and confusion matrix

Add hazardous waste, textiles, batteries and other waste categories

Add password reset and email verification

Use a managed production database for larger deployments

Provide city-specific recycling rules

Add multilingual support

Optimize inference and hosting cost

Integrate the classifier with an IoT smart-bin or automated sorting system

👩‍💻 Developer

Janhavi Jayanna
Computer Science Engineering Student

GitHub: https://github.com/janhavijayanna-creator

⭐ Support

If you find this project useful, consider giving the repository a ⭐.
