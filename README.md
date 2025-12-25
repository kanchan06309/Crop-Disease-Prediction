🌾 Smart Crop Disease Detection & Farmer Support System (Madhya Pradesh Focus)

An AI-powered agriculture assistant designed to help farmers in Madhya Pradesh prevent crop losses, manage diseases, get smart advisory, and access bilingual support.
This system integrates computer vision, weather intelligence, smart advisory, region-based crop management, and AI chatbot assistance to deliver a complete digital agriculture solution.

🚀 Key Features:

🔍 Crop Disease Detection
Upload or capture an image of the crop → the system detects disease and provides:
- Disease name
- Confidence level

🌐 Bilingual Support (English + हिंदी)
Designed for accessibility and inclusiveness.
- Full app support in English
- Full app support in Hindi
- Easy toggle for language switching

🤖 AI Chatbot Support
Integrated smart chatbot to answer farmer queries such as,
- Crop health doubts
- Disease symptoms & treatment
- General farming support

🌱 Explore Diseases by Crop
Users can browse diseases.
- Crop-wise structured categories
- Clear disease descriptions
- Symptoms breakdown
- Treatment recommendations

🗺 Agricultural Priority Regions – Madhya Pradesh
Special focus on Madhya Pradesh agriculture ecosystem:
- Region-wise agricultural insights
- Priority crops per district
- Region-based advisory
- Supports local farming ecosystem planning

💧 Smart Irrigation & Spray Advisory
The system provides:
- Smart irrigation schedule suggestions
- Spray advisory based on crop condition
- Preventive suggestion to reduce risk
- Helps optimize resources and reduce cost

☁️ Weather Intelligence
Integrated weather support:
- Real-time weather report
- Temperature, humidity, rainfall insights
- Helps farmers make better cultivation decisions

Note - The machine Learning model is not trained for all crop diseases. You can find the dataset used for this in the datasets folder.

MySql Database Schema: Used to store data of
- 6 sample crops with images from Unsplash
- 8 treatment methods with detailed information
- 12 diseases linking crops to treatments

Database name - crop_disease_db

Tables - disease, treatment, and crops

-- Table 1: crops

CREATE TABLE crops (
    crop_id INT PRIMARY KEY AUTO_INCREMENT,
    crop_name VARCHAR(100) NOT NULL,
    crop_image_url VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: treatment

CREATE TABLE treatment (
    treatment_id INT PRIMARY KEY AUTO_INCREMENT,
    treatment_name VARCHAR(150) NOT NULL,
    dosage VARCHAR(100),
    application_method TEXT,
    precautions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 3: disease (with foreign keys to crops and treatment)

CREATE TABLE disease (
    disease_id INT PRIMARY KEY AUTO_INCREMENT,
    disease_name VARCHAR(150) NOT NULL,
    crop_id INT NOT NULL,
    treatment_id INT NOT NULL,
    symptoms TEXT,
    prevention TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crop_id) REFERENCES crops(crop_id) ON DELETE CASCADE,
    FOREIGN KEY (treatment_id) REFERENCES treatment(treatment_id) ON DELETE CASCADE
);
