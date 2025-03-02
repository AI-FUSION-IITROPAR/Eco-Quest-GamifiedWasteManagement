import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import pandas as pd
import numpy as np
import plotly.express as px
from PIL import Image
import geocoder
import folium
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import json
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Initialize session state for points and achievements
if 'user_points' not in st.session_state:
    st.session_state.user_points = 0
if 'achievements' not in st.session_state:
    st.session_state.achievements = []
if 'user_level' not in st.session_state:
    st.session_state.user_level = 1
if 'analyses_completed' not in st.session_state:
    st.session_state.analyses_completed = 0
if 'locations_found' not in st.session_state:
    st.session_state.locations_found = 0
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Achievement definitions
ACHIEVEMENTS = {
    'first_analysis': {'name': ' First Analysis', 'points': 50, 'description': 'Complete your first waste analysis'},
    'location_master': {'name': ' Location Master', 'points': 100, 'description': 'Find disposal locations 5 times'},
    'eco_warrior': {'name': ' Eco Warrior', 'points': 200, 'description': 'Complete 10 waste analyses'},
    'green_expert': {'name': ' Green Expert', 'points': 500, 'description': 'Reach level 5'},
    'climate_conscious': {'name': ' Climate Conscious', 'points': 100, 'description': 'Calculate your carbon footprint'}
}

# Points system
POINTS_SYSTEM = {
    'analysis': 20,
    'location_search': 15,
    'daily_login': 10,
    'achievement': 50
}

# Function to update user points and check achievements
def update_points_and_achievements(action_type):
    # Add points
    points = POINTS_SYSTEM.get(action_type, 0)
    st.session_state.user_points += points
    
    # Update level (every 200 points = 1 level)
    st.session_state.user_level = (st.session_state.user_points // 200) + 1
    
    # Check for achievements
    if action_type == 'analysis':
        st.session_state.analyses_completed += 1
        if st.session_state.analyses_completed == 1 and 'first_analysis' not in st.session_state.achievements:
            st.session_state.achievements.append('first_analysis')
            st.balloons()
            st.success(f" Achievement Unlocked: {ACHIEVEMENTS['first_analysis']['name']}")
        elif st.session_state.analyses_completed == 10 and 'eco_warrior' not in st.session_state.achievements:
            st.session_state.achievements.append('eco_warrior')
            st.balloons()
            st.success(f" Achievement Unlocked: {ACHIEVEMENTS['eco_warrior']['name']}")
    
    elif action_type == 'location_search':
        st.session_state.locations_found += 1
        if st.session_state.locations_found == 5 and 'location_master' not in st.session_state.achievements:
            st.session_state.achievements.append('location_master')
            st.balloons()
            st.success(f" Achievement Unlocked: {ACHIEVEMENTS['location_master']['name']}")
    
    if st.session_state.user_level >= 5 and 'green_expert' not in st.session_state.achievements:
        st.session_state.achievements.append('green_expert')
        st.balloons()
        st.success(f" Achievement Unlocked: {ACHIEVEMENTS['green_expert']['name']}")

# Initialize Gemini API
def initialize_gemini():
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            st.error("Please set your Google API key in the environment variables as GOOGLE_API_KEY")
            return None, None
        
        genai.configure(api_key=api_key)
        text_model = genai.GenerativeModel('gemini-pro')
        vision_model = genai.GenerativeModel('gemini-pro-vision')
        return text_model, vision_model
    except Exception as e:
        st.error(f"Error initializing Gemini API: {str(e)}")
        return None, None

# Initialize models in session state if not already done
if 'text_model' not in st.session_state or 'vision_model' not in st.session_state:
    st.session_state.text_model, st.session_state.vision_model = initialize_gemini()

def generate_response(prompt):
    try:
        if st.session_state.text_model is None:
            return "Text model not initialized. Please check your API key."
        
        response = st.session_state.text_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

def analyze_image(image, prompt="Analyze this image and identify any waste or recyclable materials present. What type of waste is it and how should it be disposed of?"):
    try:
        if st.session_state.vision_model is None:
            return "Vision model not initialized. Please check your API key."
        
        # Convert PIL Image to bytes
        import io
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format if image.format else 'PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        response = st.session_state.vision_model.generate_content([prompt, img_byte_arr])
        return response.text
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def generate_suggestions(prompt, waste_type=None):
    try:
        if waste_type:
            prompt = f"As a waste management expert, provide detailed suggestions for disposing of {waste_type}. {prompt}"
        else:
            prompt = f"As a waste management expert, analyze this waste and provide disposal suggestions: {prompt}"
        
        response = generate_response(prompt)
        return response
    except Exception as e:
        return f"Error generating suggestions: {str(e)}"

# Function to clean up repetitive text in captions
def clean_caption(text):
    # Split into words and remove duplicates while maintaining order
    words = text.split()
    seen = set()
    cleaned_words = []
    for word in words:
        if word.lower() not in seen:
            cleaned_words.append(word)
            seen.add(word.lower())
    return ' '.join(cleaned_words)

# Function to get nearby waste disposal locations
def get_nearby_disposal_locations(lat, lon, waste_type):
    # This is a mock database of waste disposal locations
    # In a production environment, this should be replaced with a real database or API
    disposal_locations = {
        "Plastic": [
            {"name": "City Recycling Center", "lat": lat + 0.02, "lon": lon + 0.01},
            {"name": "Green Earth Recyclers", "lat": lat - 0.01, "lon": lon + 0.02}
        ],
        "Electronic": [
            {"name": "E-Waste Solutions", "lat": lat + 0.03, "lon": lon - 0.01},
            {"name": "Tech Recycling Hub", "lat": lat - 0.02, "lon": lon - 0.02}
        ],
        "Organic": [
            {"name": "Community Composting", "lat": lat + 0.01, "lon": lon + 0.03},
            {"name": "Garden Waste Center", "lat": lat - 0.03, "lon": lon + 0.01}
        ]
    }
    
    # Get locations for the specific waste type
    locations = disposal_locations.get(waste_type, [])
    # Sort by distance
    locations.sort(key=lambda x: geodesic((lat, lon), (x["lat"], x["lon"])).miles)
    return locations

# Climate analysis helper functions
def calculate_carbon_footprint(waste_type, weight):
    # Carbon footprint factors (kg CO2e per kg of waste)
    factors = {
        'plastic': 6.0,
        'paper': 2.5,
        'metal': 4.0,
        'glass': 0.9,
        'organic': 1.2,
        'electronic': 20.0
    }
    return factors.get(waste_type.lower(), 3.0) * weight

def get_eco_tips(carbon_footprint):
    if carbon_footprint > 50:
        return [
            "Consider recycling more of your waste",
            "Try composting organic waste",
            "Reduce single-use plastic consumption",
            "Choose products with less packaging"
        ]
    elif carbon_footprint > 20:
        return [
            "You're doing well! Here are some additional tips:",
            "Buy products with recyclable packaging",
            "Start a small compost bin"
        ]
    else:
        return [
            "Great job keeping your carbon footprint low!",
            "Share your eco-friendly practices with others",
            "Consider joining local environmental initiatives"
        ]

# Custom CSS for enhanced UI
st.markdown("""
    <style>
    /* Modern Color Scheme */
    :root {
        --primary-color: #2E7D32;
        --secondary-color: #4CAF50;
        --background-color: #FFFFFF;
        --text-color: #333333;
        --accent-color: #81C784;
    }
    
    /* Global Styles */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Cards */
    .eco-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border: 1px solid #E0E0E0;
        transition: transform 0.2s ease-in-out;
    }
    
    .eco-card:hover {
        transform: translateY(-2px);
    }
    
    /* Progress Bar */
    .progress-bar {
        height: 10px;
        background-color: #E0E0E0;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .progress-bar-fill {
        height: 100%;
        background-color: var(--primary-color);
        border-radius: 5px;
        transition: width 0.3s ease-in-out;
    }
    
    /* Achievements */
    .achievement {
        background-color: #F5F5F5;
        padding: 0.8rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 4px solid var(--primary-color);
    }
    
    .achievement.locked {
        opacity: 0.7;
        border-left-color: #9E9E9E;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: var(--secondary-color);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Leaderboard */
    .leaderboard-item {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem;
        border-radius: 4px;
        margin-bottom: 0.3rem;
        background-color: #F5F5F5;
    }
    
    .leaderboard-item:nth-child(1) {
        background-color: #FFD700;
        color: #333;
    }
    
    .leaderboard-item:nth-child(2) {
        background-color: #C0C0C0;
        color: #333;
    }
    
    .leaderboard-item:nth-child(3) {
        background-color: #CD7F32;
        color: #333;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar with User Profile and Achievements
with st.sidebar:
    st.markdown("""
        <div class='eco-card'>
            <h2 style='color: #2E7D32;'> EcoQuest Profile</h2>
        </div>
    """, unsafe_allow_html=True)
    
    # User Level and Points
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            <div class='eco-card' style='text-align: center;'>
                <h3 style='color: #2E7D32;'>Level {st.session_state.user_level}</h3>
                <p> {st.session_state.user_points} pts</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class='eco-card' style='text-align: center;'>
                <h3 style='color: #2E7D32;'>Rank</h3>
                <p> {min(st.session_state.user_level * 10, 100)}</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Progress to next level
    points_to_next_level = (st.session_state.user_level * 200) - st.session_state.user_points
    progress_percentage = ((200 - points_to_next_level) / 200) * 100
    st.markdown(f"""
        <div class='eco-card'>
            <p style='margin-bottom: 0.5rem;'>Progress to Level {st.session_state.user_level + 1}</p>
            <div class='progress-bar'>
                <div class='progress-bar-fill' style='width: {progress_percentage}%;'></div>
            </div>
            <p style='text-align: right; font-size: 0.8rem;'>{points_to_next_level} points needed</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Achievements
    st.markdown("""
        <div class='eco-card'>
            <h3 style='color: #2E7D32; margin-bottom: 1rem;'> Achievements</h3>
        </div>
    """, unsafe_allow_html=True)
    
    for achievement_id, achievement in ACHIEVEMENTS.items():
        is_unlocked = achievement_id in st.session_state.achievements
        st.markdown(f"""
            <div class='achievement {"" if is_unlocked else "locked"}'>
                <strong>{achievement['name']}</strong><br>
                <small>{achievement['description']}</small><br>
                <small>{" Unlocked" if is_unlocked else " Locked"} • {achievement['points']} pts</small>
            </div>
        """, unsafe_allow_html=True)

# Main Content Area
st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='color: #2E7D32;'> EcoQuest: Gamified Waste Management</h1>
        <p style='color: #666;'>Turn your waste management journey into an exciting quest for a greener planet!</p>
    </div>
""", unsafe_allow_html=True)

# Create tabs with icons
tab1, tab2, tab3 = st.tabs([" Waste Analysis Quest", " Visual Recognition Challenge", " Climate Impact"])

with tab1:
    st.markdown("""
        <div class='eco-card'>
            <h3 style='color: #2E7D32; margin-bottom: 1rem;'> Waste Analysis Mission</h3>
            <p style='color: #666; margin-bottom: 1.5rem;'>
                Complete waste analysis missions to earn points and unlock achievements!
                <br>• Each analysis: +20 points
                <br>• Location search: +15 points
                <br>• Special achievements: +50 points
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # User input section with enhanced UI
    with st.container():
        st.markdown("<div class='eco-card'>", unsafe_allow_html=True)
        user_input = st.text_area(
            " Mission Objective:",
            placeholder="Describe the waste item(s) to analyze",
            height=100,
            key="waste_description",
            help="Provide details about the waste items you want to analyze"
        )
        
        # Location input with modern design
        location_col1, location_col2 = st.columns([3, 1])
        with location_col1:
            location_input = st.text_input(
                " Mission Location:",
                "",
                key="location_input",
                help="Enter your city, address, or coordinates"
            )
        with location_col2:
            get_location = st.button(
                " Detect Location",
                help="Automatically detect your current location"
            )

        if get_location:
            try:
                g = geocoder.ip('me')
                if g.latlng:
                    st.session_state['lat'], st.session_state['lon'] = g.latlng
                    geolocator = Nominatim(user_agent="waste_analyzer")
                    location = geolocator.reverse((st.session_state['lat'], st.session_state['lon']))
                    location_input = location.address
                    st.success(" Location detected! +5 points")
                    update_points_and_achievements('location_search')
            except Exception as e:
                st.error(" Mission Update: Could not detect location. Please enter manually.")
        
        analyze_button = st.button(" Complete Mission")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if analyze_button and user_input:
            update_points_and_achievements('analysis')
            with st.spinner(" Mission in progress..."):
                # Generate suggestions
                suggestions = generate_suggestions(user_input)
                
                # Display suggestions with enhanced UI
                st.markdown(f"""
                    <div class='eco-card'>
                        <h4 style='color: #2E7D32; margin-bottom: 0.5rem;'> Mission Accomplished!</h4>
                        <p style='color: #1B5E20; margin-bottom: 1rem;'>{suggestions}</p>
                        <p style='color: #666;'>+20 points awarded for completing the analysis!</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # If location is provided, show nearby disposal locations
                if location_input:
                    try:
                        geolocator = Nominatim(user_agent="waste_analyzer")
                        location = geolocator.geocode(location_input)
                        if location:
                            st.markdown("""
                                <div class='eco-card'>
                                    <h4 style='color: #2E7D32; margin-bottom: 1rem;'> Disposal Locations Found!</h4>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Create a map with modern styling
                            m = folium.Map(
                                location=[location.latitude, location.longitude],
                                zoom_start=13,
                                tiles='CartoDB positron'
                            )
                            
                            # Add user location marker
                            folium.Marker(
                                [location.latitude, location.longitude],
                                popup="Your Location",
                                icon=folium.Icon(color='red', icon='info-sign')
                            ).add_to(m)
                            
                            # Get and display nearby locations
                            nearby_locations = get_nearby_disposal_locations(location.latitude, location.longitude, "General")
                            for loc in nearby_locations:
                                folium.Marker(
                                    [loc["lat"], loc["lon"]],
                                    popup=loc["name"],
                                    icon=folium.Icon(color='green')
                                ).add_to(m)
                            
                            # Display the map in a card
                            st.markdown("<div class='eco-card'>", unsafe_allow_html=True)
                            components.html(m._repr_html_(), height=400)
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            # List the locations with enhanced UI
                            st.markdown("<div class='eco-card'>", unsafe_allow_html=True)
                            for i, loc in enumerate(nearby_locations, 1):
                                distance = geodesic(
                                    (location.latitude, location.longitude),
                                    (loc["lat"], loc["lon"])
                                ).miles
                                st.markdown(f"""
                                    <div style='background-color: #F5F5F5; padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;'>
                                        <strong> {loc['name']}</strong><br>
                                        <small> Distance: {distance:.1f} miles</small>
                                    </div>
                                """, unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            update_points_and_achievements('location_search')
                            st.success(" Bonus Mission Complete: +15 points for finding disposal locations!")
                        else:
                            st.error(" Location not found. Please try a different address.")
                    except Exception as e:
                        st.error(f" Error finding disposal locations: {str(e)}")
                        st.error("Please try a different location or try again later.")

with tab2:
    st.markdown("""
        <div class='eco-card'>
            <h3 style='color: #2E7D32; margin-bottom: 1rem;'> Visual Recognition Challenge</h3>
            <p style='color: #666; margin-bottom: 1.5rem;'>
                Upload an image of waste items for instant classification, hazard assessment, 
                and recycling recommendations.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create two columns for upload and results
    upload_col, result_col = st.columns([1, 1])
    
    with upload_col:
        st.markdown("""
            <div class='upload-section'>
                <h4 style='color: #2E7D32; margin-bottom: 1rem;'>Upload Image</h4>
                <p style='color: #666;'>Supported formats: JPG, JPEG, PNG</p>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload waste image",
            type=['jpg', 'jpeg', 'png'],
            key="visual_analysis",
            label_visibility="collapsed",
            help="Upload an image of waste items for analysis"
        )

    if uploaded_file:
        # Display image and analysis in result column
        with result_col:
            st.markdown("<div class='eco-card'>", unsafe_allow_html=True)
            image = Image.open(uploaded_file)
            st.image(image, caption="Analyzing...", use_container_width=True)
            
            # Analyze image using Gemini Pro Vision model
            with st.spinner("Analyzing image content..."):
                try:
                    caption = analyze_image(image)
                    # Clean up repetitive text
                    caption = clean_caption(caption)
                    st.markdown(f"""
                        <div style='background-color: #E8F5E9; padding: 1rem; border-radius: 8px; margin-top: 1rem;'>
                            <h4 style='color: #2E7D32; margin-bottom: 0.5rem;'> Image Analysis</h4>
                            <p style='color: #1B5E20; margin-bottom: 0;'>{caption}</p>
                        </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error("Error analyzing the image. Please try again.")
                    st.error(f"Error details: {str(e)}")
                    caption = ""
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Analysis results in a separate card below
            st.markdown("<div class='eco-card'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #2E7D32; margin-bottom: 1rem;'>Analysis Results</h4>", unsafe_allow_html=True)
            
            # Initialize waste types with default values if no caption is available
            if not caption:
                waste_types = {
                    "Plastic": {"confidence": 0.2, "recyclable": True, "hazard_level": "Medium"},
                    "Paper": {"confidence": 0.2, "recyclable": True, "hazard_level": "Low"},
                    "Metal": {"confidence": 0.2, "recyclable": True, "hazard_level": "Low"},
                    "Glass": {"confidence": 0.2, "recyclable": True, "hazard_level": "Medium"},
                    "Organic": {"confidence": 0.2, "recyclable": True, "hazard_level": "Low"}
                }
            else:
                # Use the caption to determine waste type probabilities
                waste_types = {
                    "Plastic": {"confidence": 0.0, "recyclable": True, "hazard_level": "Medium"},
                    "Paper": {"confidence": 0.0, "recyclable": True, "hazard_level": "Low"},
                    "Metal": {"confidence": 0.0, "recyclable": True, "hazard_level": "Low"},
                    "Glass": {"confidence": 0.0, "recyclable": True, "hazard_level": "Medium"},
                    "Organic": {"confidence": 0.0, "recyclable": True, "hazard_level": "Low"}
                }
                
                # Simple keyword matching to adjust confidence scores
                caption_lower = caption.lower()
                keywords = {
                    "Plastic": ["plastic", "bottle", "container", "packaging"],
                    "Paper": ["paper", "cardboard", "box", "newspaper"],
                    "Metal": ["metal", "can", "aluminum", "steel"],
                    "Glass": ["glass", "bottle", "jar"],
                    "Organic": ["food", "waste", "organic", "vegetable", "fruit"]
                }
                
                # Calculate confidence scores based on keywords
                for waste_type, related_words in keywords.items():
                    confidence = sum([1 for word in related_words if word in caption_lower]) / len(related_words)
                    waste_types[waste_type]["confidence"] = min(confidence, 0.95)  # Cap at 95% confidence
                
                # Normalize confidence scores
                total_confidence = sum(type_info["confidence"] for type_info in waste_types.values())
                if total_confidence > 0:
                    for waste_type in waste_types:
                        waste_types[waste_type]["confidence"] /= total_confidence
                else:
                    # If no matches, set a small baseline confidence for each type
                    for waste_type in waste_types:
                        waste_types[waste_type]["confidence"] = 0.2
            
            # Display key metrics in a grid
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            top_waste = max(waste_types.items(), key=lambda x: x[1]['confidence'])
            
            with metric_col1:
                st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
                st.metric("Primary Type", top_waste[0])
                st.markdown("</div>", unsafe_allow_html=True)
            
            with metric_col2:
                st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
                st.metric("Confidence", f"{top_waste[1]['confidence']:.1%}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with metric_col3:
                st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
                st.metric("Hazard Level", top_waste[1]['hazard_level'])
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Create detailed analysis chart
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            analysis_data = []
            for waste_type, details in waste_types.items():
                analysis_data.append({
                    'Type': waste_type,
                    'Confidence': details['confidence'],
                    'Recyclable': 'Yes' if details['recyclable'] else 'No',
                    'Hazard Level': details['hazard_level']
                })
            
            df = pd.DataFrame(analysis_data)
            fig = px.bar(df, x='Type', y='Confidence',
                        title='Waste Classification Analysis',
                        color='Hazard Level',
                        color_discrete_map={'Low': '#4CAF50', 'Medium': '#FFA726', 'High': '#EF5350'})
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_font_color='#2E7D32',
                showlegend=True,
                legend_title_text='Hazard Level',
                xaxis_title="Waste Type",
                yaxis_title="Confidence Score"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Recommendations section
            st.markdown("""
                <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 8px; margin-top: 1rem;'>
                    <h4 style='color: #2E7D32; margin-bottom: 0.5rem;'> Recommendations</h4>
                    <ul style='margin-bottom: 0;'>
                        <li>Ensure proper segregation before disposal</li>
                        <li>Check local recycling guidelines</li>
                        <li>Consider reuse options if applicable</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("""
        <div class='eco-card'>
            <h2 style='color: #2E7D32;'> Climate Impact Analysis</h2>
            <p style='color: #666;'>Track your environmental impact and get personalized eco-friendly recommendations.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Carbon Footprint Calculator")
        waste_type = st.selectbox(
            "Select Waste Type",
            ["Plastic", "Paper", "Metal", "Glass", "Organic", "Electronic"],
            help="Choose the type of waste you want to analyze"
        )
        
        waste_weight = st.number_input(
            "Waste Weight (kg)",
            min_value=0.1,
            max_value=1000.0,
            value=1.0,
            step=0.1,
            help="Enter the weight of waste in kilograms"
        )
        
        if st.button("Calculate Impact", help="Calculate your carbon footprint"):
            carbon_footprint = calculate_carbon_footprint(waste_type, waste_weight)
            st.markdown(f"""
                <div class='eco-card result-card'>
                    <h3>Carbon Footprint Results</h3>
                    <p class='impact-number'>{carbon_footprint:.1f} kg CO2e</p>
                    <p>This is equivalent to driving approximately {(carbon_footprint * 4):.1f} km in an average car.</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.subheader("Eco-friendly Tips")
            tips = get_eco_tips(carbon_footprint)
            for tip in tips:
                st.markdown(f"- {tip}")
            
            # Award points for using the calculator
            update_points_and_achievements('climate_conscious')
    
    with col2:
        st.subheader("Historical Impact")
        
        # Using month-end frequency for date range
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='ME')
        monthly_footprint = pd.Series(index=dates, data=np.random.normal(30, 5, len(dates)))
        
        fig = px.line(
            x=dates,
            y=monthly_footprint,
            title='Your Carbon Footprint Over Time',
            labels={'x': 'Month', 'y': 'Carbon Footprint (kg CO2e)'}
        )
        fig.update_layout(
            showlegend=False,
            hovermode='x',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig)
        
        # Display total impact
        total_impact = monthly_footprint.sum()
        st.markdown(f"""
            <div class='eco-card'>
                <h4>Total Impact This Year</h4>
                <p class='impact-number'>{total_impact:.1f} kg CO2e</p>
                <p>That's equivalent to {(total_impact/100):.1f} trees needed for carbon offset</p>
            </div>
        """, unsafe_allow_html=True)

# Add custom CSS for climate analysis tab
st.markdown("""
    <style>
    .impact-number {
        font-size: 24px;
        font-weight: bold;
        color: #2E7D32;
        margin: 10px 0;
    }
    .result-card {
        background-color: #f5f5f5;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)