# AI Fusion: Smart Waste Management & Environmental Analysis

An innovative environmental application that combines AI-powered waste analysis, visual recognition, and climate impact tracking. This interactive platform gamifies waste management while providing educational insights and practical solutions for sustainable living.

## Features

- **Waste Analysis Quest**: 
  - Interactive waste analysis system
  - AI-powered suggestions for proper waste disposal
  - Gamified experience with points and achievements

- **Visual Recognition Challenge**:
  - Image-based waste identification
  - Real-time analysis of recyclable materials
  - Smart disposal recommendations
  - Nearby disposal location finder

- **Climate Impact Tracker**:
  - Carbon footprint calculation
  - Personalized eco-friendly recommendations
  - Environmental impact visualization
  - Progress tracking and metrics

- **Gamification Elements**:
  - Point-based reward system
  - Achievement unlocks
  - Level progression
  - User engagement tracking

- **Smart Location Services**:
  - Nearby waste disposal facility locator
  - Interactive maps using Folium
  - Distance calculations
  - Facility recommendations based on waste type

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-fusion.git
cd ai-fusion
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory and add your API keys:
```
GOOGLE_API_KEY=your_google_api_key_here
```

## Usage

Run the main application:
```bash
streamlit run final_app.py
```

## Project Structure

- `final_app.py`: Main application file
- `ui.py`: User interface components
- `requirements.txt`: Project dependencies
- `.env`: Environment variables (not included in repository)
- `model_cache/`: Directory for cached model data
- `cifar10_model.h5`: Pre-trained model file

## Dependencies

- Python 3.8+
- Streamlit
- Plotly
- Pandas
- NumPy
- Pillow
- Folium
- Geocoder
- Geopy
- Google Generative AI
- Python-dotenv

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
