# 🏠 House Price Prediction Web-App

## 📌 Overview

This project is a machine learning powered web application that predicts house prices based on features such as **location, square-footage, number of BHK, and number of bathrooms**.  
The backend uses a trained **Linear Regression model** built with Scikit-learn, while the frontend is a responsive web interface powered by **HTML, CSS, JavaScript, and jQuery**.  
The Flask API connects the ML model with the frontend, delivering instant predictions.

---

## ✨ Features

- **Responsive Web UI**: Simple and user-friendly interface for inputting house details.  
- **Instant Predictions**: Real-time house price estimation served by Flask API.  
- **Data-Driven**: Model trained on the **‘Real Estate Data V21’ Kaggle dataset**.  
- **AJAX Integration**: Smooth request handling without page reloads.  
- **Error Handling**: Provides validation for missing or incorrect inputs.  

---

## 📁 Project Structure

.
├── server.py # Flask backend to handle API requests
├── util.py # Helper functions for model loading & predictions
├── templates/
│ └── WebApp.html # Frontend HTML file
├── static/
│ ├── WebApp.css # Stylesheet
│ └── WebApp.js # Frontend JavaScript (AJAX requests)
├── model/
│ └── Columnsnew.json # Stores model feature columns
├── data/
│ └── Real Estate Data V21.pickle # Serialized dataset/model artifacts
├── notebooks/
│ └── HousePricePredictions.ipynb # Jupyter Notebook for training & analysis
├── requirements.txt # Python dependencies
└── README.md # This file

---

## 🚀 Getting Started

1. Install dependencies:pip install -r requirements.txt
2. Ensure model and data files are present:
i. Columnsnew.json
ii. Real Estate Data V21.pickle

---

## How to Run the Application

1. Start the Flask server: python server.py
2. Access the Web App -> Open your browser and go to: http://127.0.0.1:5000

---

⚙️ How It Works

User Input: The frontend form collects location, square-footage, BHK, and bathroom count.

AJAX Request: The inputs are sent to the Flask backend via an API call.

Model Loading: Flask uses util.py to load the trained Linear Regression model and feature columns.

Prediction: The model generates the estimated house price.

Result Display: The result is sent back to the frontend and displayed instantly.

---

👩‍🔬 Model Training Details

Dataset: ‘Real Estate Data V21’ from Kaggle

Preprocessing: Feature encoding, handling missing values, and scaling

Algorithm: Linear Regression (Scikit-learn)

Notebook: See HousePricePredictions.ipynb for complete training workflow
