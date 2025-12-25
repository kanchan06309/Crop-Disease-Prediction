from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import mysql.connector
import tensorflow as tf
from tensorflow import keras
import pandas as pd
import numpy as np
from PIL import Image
import requests
import io
import json
import os
from mysql.connector import Error
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Your OpenWeatherMap API key
API_KEY = 'OPENWEATHER_API_KEY'  # Replace with your actual API key
WEATHER_URL = 'https://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'

# Major cities in Madhya Pradesh
MP_CITIES = {
    'Bhopal': {'lat': 23.2599, 'lon': 77.4126},
    'Indore': {'lat': 22.7196, 'lon': 75.8577},
    'Jabalpur': {'lat': 23.1815, 'lon': 79.9864},
    'Gwalior': {'lat': 26.2183, 'lon': 78.1828},
    'Ujjain': {'lat': 23.1765, 'lon': 75.7885},
    'Sagar': {'lat': 23.8388, 'lon': 78.7378},
    'Dewas': {'lat': 22.9676, 'lon': 76.0534},
    'Satna': {'lat': 24.6005, 'lon': 80.8322},
    'Ratlam': {'lat': 23.3315, 'lon': 75.0367},
    'Rewa': {'lat': 24.5364, 'lon': 81.2961}
}

def calculate_irrigation_advisory(weather_data, forecast_data):
    """Calculate irrigation advisory based on weather conditions"""
    
    # Extract data
    rain_today = weather_data.get('rain', {}).get('1h', 0)
    humidity = weather_data['main']['humidity']
    temperature = weather_data['main']['temp']
    
    # Get rain forecast for next 24 hours
    rain_forecast_24h = 0
    for forecast in forecast_data['list'][:8]:  # Next 24 hours (3-hour intervals)
        rain_forecast_24h += forecast.get('rain', {}).get('3h', 0)
    
    advisory = {
        'status': '',
        'recommendation': '',
        'reasons': [],
        'data': {
            'rain_today': round(rain_today, 1),
            'rain_forecast_24h': round(rain_forecast_24h, 1),
            'humidity': humidity,
            'temperature': round(temperature, 1)
        }
    }
    
    # STEP 1: Check Rainfall
    if rain_today >= 5 or rain_forecast_24h >= 5:
        advisory['status'] = '❌ Not Required'
        advisory['recommendation'] = 'Do not irrigate today'
        if rain_today >= 5:
            advisory['reasons'].append(f'Current rainfall: {round(rain_today, 1)} mm (sufficient moisture)')
        if rain_forecast_24h >= 5:
            advisory['reasons'].append(f'Expected rainfall: {round(rain_forecast_24h, 1)} mm in next 24 hours')
        return advisory
    
    # STEP 2: Check Humidity
    if humidity >= 75:
        advisory['status'] = '⚠️ Reduce Irrigation'
        advisory['recommendation'] = 'Minimal irrigation recommended'
        advisory['reasons'].append(f'High humidity ({humidity}%) reduces evaporation')
        advisory['reasons'].append('Soil retains moisture longer in humid conditions')
        return advisory
    
    # STEP 3: Check Temperature
    if temperature >= 35 and humidity < 60:
        advisory['status'] = '🚿 Increase Irrigation'
        advisory['recommendation'] = 'Extra irrigation required'
        advisory['reasons'].append(f'High temperature ({round(temperature, 1)}°C) increases water loss')
        advisory['reasons'].append(f'Low humidity ({humidity}%) accelerates evaporation')
        return advisory
    
    # STEP 4: Default Case
    advisory['status'] = '✅ Normal Irrigation'
    advisory['recommendation'] = 'Regular irrigation recommended'
    advisory['reasons'].append('Normal weather conditions')
    advisory['reasons'].append('Maintain regular irrigation schedule')
    
    return advisory

def calculate_spray_advisory(weather_data, forecast_data):
    """Calculate spray advisory based on weather conditions"""
    
    # Extract data
    wind_speed = weather_data['wind']['speed'] * 3.6  # Convert m/s to km/h
    humidity = weather_data['main']['humidity']
    
    # Check rain forecast for next 12 hours
    rain_forecast_12h = False
    for forecast in forecast_data['list'][:4]:  # Next 12 hours
        if forecast.get('rain', {}).get('3h', 0) > 0:
            rain_forecast_12h = True
            break
    
    # Get current time for optimal spraying time
    current_hour = datetime.now().hour
    is_optimal_time = (6 <= current_hour <= 10) or (16 <= current_hour <= 19)
    
    advisory = {
        'status': '',
        'recommendation': '',
        'reasons': [],
        'optimal_time': 'Early morning (6-10 AM) or Evening (4-7 PM)',
        'data': {
            'wind_speed': round(wind_speed, 1),
            'humidity': humidity,
            'rain_forecast_12h': rain_forecast_12h,
            'current_time_optimal': is_optimal_time
        }
    }
    
    # STEP 1: Check Wind Speed
    if wind_speed >= 15:
        advisory['status'] = '❌ Not Recommended'
        advisory['recommendation'] = 'Do not spray - High wind conditions'
        advisory['reasons'].append(f'Wind speed: {round(wind_speed, 1)} km/h (causes spray drift)')
        advisory['reasons'].append('Chemical drift can damage crops and waste pesticides')
        return advisory
    
    # STEP 2: Check Rain Forecast
    if rain_forecast_12h:
        advisory['status'] = '❌ Not Recommended'
        advisory['recommendation'] = 'Do not spray - Rain expected'
        advisory['reasons'].append('Rain expected within 12 hours')
        advisory['reasons'].append('Rain will wash away chemicals, wasting money and resources')
        return advisory
    
    # STEP 3: Check Humidity
    if humidity >= 85:
        advisory['status'] = '⚠️ Delay Spraying'
        advisory['recommendation'] = 'Avoid spraying or wait for better conditions'
        advisory['reasons'].append(f'Very high humidity ({humidity}%)')
        advisory['reasons'].append('Reduces chemical absorption and increases fungal risk')
        return advisory
    
    # STEP 4: Optimal Conditions
    if wind_speed < 10 and not rain_forecast_12h and 50 <= humidity <= 80:
        advisory['status'] = '✅ Safe to Spray'
        advisory['recommendation'] = 'Good conditions for spraying'
        advisory['reasons'].append(f'Wind speed: {round(wind_speed, 1)} km/h (safe range)')
        advisory['reasons'].append(f'Humidity: {humidity}% (optimal range)')
        advisory['reasons'].append('No rain forecast in next 12 hours')
        if is_optimal_time:
            advisory['reasons'].append('✅ Current time is optimal for spraying')
        else:
            advisory['reasons'].append('⚠️ Consider spraying during morning or evening for best results')
        return advisory
    
    # Moderate conditions
    advisory['status'] = '⚠️ Proceed with Caution'
    advisory['recommendation'] = 'Spraying possible but not ideal'
    advisory['reasons'].append('Conditions are acceptable but not optimal')
    if wind_speed >= 10:
        advisory['reasons'].append(f'Wind speed is moderate ({round(wind_speed, 1)} km/h)')
    if humidity < 50:
        advisory['reasons'].append(f'Humidity is low ({humidity}%)')
    
    return advisory

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Return list of available cities"""
    return jsonify({
        'success': True,
        'cities': list(MP_CITIES.keys())
    })

@app.route('/api/dashboard/<city>', methods=['GET'])
def get_dashboard_data(city):
    """Fetch complete dashboard data for a city"""
    
    if city not in MP_CITIES:
        return jsonify({
            'success': False,
            'error': 'City not found'
        }), 404
    
    try:
        coords = MP_CITIES[city]
        
        # Fetch current weather
        weather_params = {
            'lat': coords['lat'],
            'lon': coords['lon'],
            'appid': API_KEY,
            'units': 'metric'
        }
        weather_response = requests.get(WEATHER_URL, params=weather_params)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        # Fetch forecast data
        forecast_response = requests.get(FORECAST_URL, params=weather_params)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        
        # Extract weather information
        weather_info = {
            'city': city,
            'temperature': round(weather_data['main']['temp'], 1),
            'feels_like': round(weather_data['main']['feels_like'], 1),
            'humidity': weather_data['main']['humidity'],
            'pressure': weather_data['main']['pressure'],
            'wind_speed': round(weather_data['wind']['speed'] * 3.6, 1),
            'wind_direction': weather_data['wind'].get('deg', 0),
            'description': weather_data['weather'][0]['description'].title(),
            'icon': weather_data['weather'][0]['icon'],
            'visibility': round(weather_data.get('visibility', 0) / 1000, 1),
            'clouds': weather_data['clouds']['all'],
            'rainfall': weather_data.get('rain', {}).get('1h', 0),
            'sunrise': weather_data['sys']['sunrise'],
            'sunset': weather_data['sys']['sunset']
        }
        
        # Calculate advisories
        irrigation_advisory = calculate_irrigation_advisory(weather_data, forecast_data)
        spray_advisory = calculate_spray_advisory(weather_data, forecast_data)
        
        return jsonify({
            'success': True,
            'weather': weather_info,
            'irrigation_advisory': irrigation_advisory,
            'spray_advisory': spray_advisory
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch data: {str(e)}'
        }), 500
    except KeyError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid data received: {str(e)}'
        }), 500


# --- FRONTEND ROUTES ---
@app.route("/weather")
def weather():
    return render_template('weather.html')

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/explore")
def explore():
    return render_template('explore.html')

@app.route('/detect')
def detect():
    return render_template('detect.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/smart-farming')
def smart_farming():
    return render_template('smart-farming.html')

@app.route('/global-impact')
def global_impact():
    return render_template('global-impact.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/hi')
def homehi():
    return render_template('index-en.html')

@app.route('/explorehi')
def explorehi():
    return render_template('explore-hi.html')

@app.route('/detecthi')
def detecthi():
    return render_template('detect-hi.html')

@app.route('/contacthi')
def contacthi():
    return render_template('contact-hi.html')

@app.route('/helphi')
def helphi():
    return render_template('help-hi.html')

@app.route('/smart-farming-hi')
def smart_farming_hi():
    return render_template('smart-farming-hi.html')

@app.route('/global-impact-hi')
def global_impact_hi():
    return render_template('global-impact-hi.html')

print("done")

# --- CONFIGURATION & PATH FIXES ---
# Get the absolute path to the folder where this script runs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define paths relative to the script location
MODEL_PATH = os.path.join(BASE_DIR, 'crop_disease_model_best.h5')
LABELS_PATH = os.path.join(BASE_DIR, 'class_labels.json')
IMG_SIZE = 224

# --- LOAD MODEL & LABELS ---
print(f"DEBUG: Looking for model at -> {MODEL_PATH}")
print(f"DEBUG: Looking for labels at -> {LABELS_PATH}")

model = None
class_labels = {}

try:
    # 1. Check if files actually exist before loading
    if not os.path.exists(MODEL_PATH):
        print(f"CRITICAL ERROR: Model file not found at {MODEL_PATH}")
    
    if not os.path.exists(LABELS_PATH):
        print(f"WARNING: Labels file not found at {LABELS_PATH}. Using generic labels.")

    # 2. Load the Model
    if os.path.exists(MODEL_PATH):
        print("Loading model...")
        model = keras.models.load_model(MODEL_PATH)
        print("✅ Model loaded successfully!")
    
    # 3. Load the Labels
    if os.path.exists(LABELS_PATH):
        with open(LABELS_PATH, 'r') as f:
            class_labels = json.load(f)
        print(f"✅ Loaded {len(class_labels)} class labels")
    else:
        # Fallback if JSON is missing (prevents crash)
        print("Using fallback numeric labels.")
        class_labels = {str(i): f"Class {i}" for i in range(10)}

except Exception as e:
    print(f"❌ Error during loading: {e}")

# --- HELPER FUNCTIONS ---

def preprocess_image(image):
    """Preprocess image for prediction"""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize
    image = image.resize((IMG_SIZE, IMG_SIZE))
    
    # Convert to array and normalize
    img_array = np.array(image)
    img_array = img_array / 255.0
    
    # Add batch dimension
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def get_prediction(image):
    """Get prediction from model"""
    if model is None:
        return None, None, None
    
    # Preprocess
    processed_img = preprocess_image(image)
    
    # Predict
    predictions = model.predict(processed_img)
    predicted_class_idx = np.argmax(predictions[0])
    confidence = float(predictions[0][predicted_class_idx])
    
    # Get class name
    # We cast to str() because JSON keys are usually strings
    predicted_class = class_labels.get(str(predicted_class_idx), f"Class {predicted_class_idx}")
    
    # Get top 3 predictions
    top_3_idx = np.argsort(predictions[0])[-3:][::-1]
    top_3_predictions = [
        {
            'class': class_labels.get(str(idx), f"Class {idx}"),
            'confidence': float(predictions[0][idx])
        }
        for idx in top_3_idx
    ]
    
    return predicted_class, confidence, top_3_predictions

# --- ROUTES ---

@app.route('/api/health2', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'model_path_checked': MODEL_PATH,
        'num_classes': len(class_labels)
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """Prediction endpoint"""
    if model is None:
        return jsonify({'error': 'Model not loaded. Check server console for paths.'}), 500
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    try:
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        predicted_class, confidence, top_3 = get_prediction(image)
        
        return jsonify({
            'success': True,
            'prediction': predicted_class,
            'confidence': confidence,
            'top_predictions': top_3
        })
    
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Get all available classes"""
    return jsonify({
        'classes': list(class_labels.values()),
        'num_classes': len(class_labels)
    })

# Path to your Excel file
EXCEL_FILE = 'Book1.xlsx'  # Change this to your actual Excel filename

def load_excel_data():
    """Load data from Excel file"""
    try:
        df = pd.read_excel(EXCEL_FILE)
        # Clean column names
        df.columns = df.columns.str.strip()
        print(f"✓ Excel loaded: {len(df)} rows")
        print(f"✓ Columns: {df.columns.tolist()}")
        return df
    except Exception as e:
        print(f"✗ Error loading Excel: {e}")
        return None

@app.route('/api/options', methods=['GET'])
def get_options():
    """Get options for all three dropdowns"""
    try:
        df = load_excel_data()
        if df is None:
            return jsonify({'error': 'Excel file not found'}), 404
        
        # Dropdown 1: States
        if 'states' in df.columns:
            states = df['states'].dropna().unique().tolist()
            dropdown1 = [{'value': state, 'label': state} for state in states]
        else:
            dropdown1 = [{'value': 'MP', 'label': 'Madhya Pradesh (MP)'}]
        
        # Dropdown 2: Priority Regions
        if 'priority_region' in df.columns:
            regions = df['priority_region'].dropna().unique().tolist()
            dropdown2 = [{'value': region, 'label': region} for region in regions]
        else:
            dropdown2 = []
        
        # Dropdown 3: Districts (extract unique districts)
        dropdown3 = []
        if 'district' in df.columns:
            all_districts = set()
            for districts_str in df['district'].dropna():
                # Split by comma and add each district
                districts = [d.strip() for d in str(districts_str).split(',')]
                all_districts.update(districts)
            
            # Sort and create dropdown
            dropdown3 = [{'value': district, 'label': district} 
                        for district in sorted(all_districts)]
        
        return jsonify({
            'dropdown1': dropdown1,
            'dropdown2': dropdown2,
            'dropdown3': dropdown3
        })
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search():
    """Search data based on dropdown selections"""
    try:
        df = load_excel_data()
        if df is None:
            return jsonify({'error': 'Excel file not found'}), 404
        
        data = request.get_json()
        state = data.get('value1', '').strip()
        region = data.get('value2', '').strip()
        district = data.get('value3', '').strip()
        
        print(f"\n{'='*60}")
        print(f"Search - State: '{state}', Region: '{region}', District: '{district}'")
        
        filtered_df = df.copy()
        
        # Filter by state if selected
        if state and 'states' in df.columns:
            filtered_df = filtered_df[filtered_df['states'].str.strip() == state]
            print(f"After state filter: {len(filtered_df)} rows")
        
        # Filter by priority region if selected
        if region and 'priority_region' in df.columns:
            filtered_df = filtered_df[filtered_df['priority_region'].str.strip() == region]
            print(f"After region filter: {len(filtered_df)} rows")
        
        # Filter by district if selected (check if district appears in the district column)
        if district and 'district' in df.columns:
            # Filter rows where the district column contains the selected district
            filtered_df = filtered_df[
                filtered_df['district'].astype(str).str.contains(district, case=False, na=False)
            ]
            print(f"After district filter: {len(filtered_df)} rows")
        
        print(f"Final results: {len(filtered_df)} rows")
        print(f"{'='*60}\n")
        
        # Convert to items format
        items = []
        for _, row in filtered_df.iterrows():
            items.append({
                'state': str(row.get('states', 'N/A')),
                'priority_region': str(row.get('priority_region', 'N/A')),
                'priority_level': str(row.get('priority_level', 'N/A')),
                'district': str(row.get('district', 'N/A')),
                'target_crops': str(row.get('Target_crops', 'N/A')),
                'main_problem': str(row.get('main problem', 'N/A')),
                'notes': str(row.get('Notes', 'N/A'))
            })
        
        return jsonify({
            'success': True,
            'items': items,
            'count': len(items)
        })
    except Exception as e:
        print(f"✗ Error in search: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# --- NEW CONFIGURATION LOGIC ---
db_url = os.getenv('DATABASE_URL')

# Check if we are on Render (Cloud) or Local (Laptop)
if db_url:
    # We are on Render! Parse the long Aiven URL
    url = urlparse(db_url)
    DB_CONFIG = {
        'host': url.hostname,
        'user': url.username,
        'password': url.password,
        'database': url.path[1:],  # Removes the leading '/'
        'port': url.port or 3306
    }
else:
    # We are on your Laptop! Use your old local settings
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'kanmysql'),
        'database': os.getenv('DB_NAME', 'crop_disease_db')
    }

print("Database Configured for:", DB_CONFIG['host'])


print("done")

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.route('/api/explore', methods=['GET'])
def get_diseases():
    """
    Fetch all crop diseases with related crop and treatment information
    Returns JSON with joined data from crops, disease, and treatment tables
    """
    connection = get_db_connection()
    
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # SQL Query joining all three tables
        query = """
            SELECT 
                d.disease_id,
                d.disease_name,
                d.symptoms,
                d.prevention,
                c.crop_id,
                c.crop_name,
                c.crop_image_url,
                c.description as crop_description,
                t.treatment_id,
                t.treatment_name,
                t.dosage,
                t.application_method,
                t.precautions
            FROM disease d
            INNER JOIN crops c ON d.crop_id = c.crop_id
            INNER JOIN treatment t ON d.treatment_id = t.treatment_id
            ORDER BY c.crop_name, d.disease_name
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'count': len(results),
            'data': results
        }), 200
        
    except Error as e:
        print(f"Error executing query: {e}")
        if connection:
            connection.close()
        return jsonify({'error': f'Query execution failed: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def check():
    """Health check endpoint to verify API is running"""
    connection = get_db_connection()
    
    if connection:
        connection.close()
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    else:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected'
        }), 500

@app.route('/api/crops', methods=['GET'])
def get_crops():
    """Get all crops"""
    connection = get_db_connection()
    
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM crops ORDER BY crop_name")
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'count': len(results),
            'data': results
        }), 200
        
    except Error as e:
        if connection:
            connection.close()
        return jsonify({'error': f'Query failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    print(f"Database config: {DB_CONFIG['host']} / {DB_CONFIG['database']}")
    print("Make sure to set environment variables: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME")
    app.run(debug=True, host='0.0.0.0', port=8000)
