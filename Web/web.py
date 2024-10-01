import streamlit as st
import requests
import json
import base64
from PIL import Image
import io

# Custom CSS for better styling and earthy look
st.markdown("""
    <style>
    /* Hide Streamlit branding */
    .css-1y0tads {display: none;}
    footer {visibility: hidden;}

    /* Main Body Background with Leaf Watermark */
    body {
        background: url('https://www.transparenttextures.com/patterns/leaf.png'); /* Leaf watermark */
        background-color: #f2efe6; /* Light earthy background */
        background-size: 200px; /* Size of the leaf pattern */
    }

    /* Main Chat Pane Styling */
    .main-pane {
        padding: 20px;
        background-color: #faf8f0; /* Light beige for natural tone */
        border-radius: 15px;
        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        color: #333; /* Dark text for visibility */
    }

    /* Sidebar Styling (Dark Earthy Color) */
    [data-testid="stSidebar"] {
        background-color: #4B3B30; /* Dark earthy color */
        color: white;
        padding-top: 20px;
    }

    /* Message Bubbles */
    .user-message {
        background-color: #e8f5e9; /* Soft green for user input */
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        color: #2e7d32;
        border: 2px solid #aed581; /* Border for more definition */
    }

    .assistant-message {
        background-color: #fffde7; /* Pale yellow for assistant response */
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        color: #827717;
        border: 2px solid #ffd54f;
    }

    /* Input Box Styling */
    .stTextInput>div>div>input {
        border-radius: 10px;
        padding: 10px;
        border: 2px solid #4caf50; /* Green input borders */
        background-color: #f0f4c3; /* Soft yellow background */
        color: #333; /* Dark text for visibility */
    }

    /* Button Styling for 'Get Answer' */
    .stButton>button {
        background-color: #8bc34a; /* Light green button */
        color: white;
        border-radius: 8px;
        padding: 10px;
        border: none;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #689f38;
    }

    /* Custom Font Styling */
    h1, h2, h3, p, div {
        color: #180; /* Dark text for all elements */
    }
    </style>
""", unsafe_allow_html=True)

# Function to convert PIL image to base64 string
def pil_to_base64(image, format="png"):
    """
    Converts a PIL image to a base64 encoded string.

    This function takes an image in PIL format and converts it into a base64 string representation, which can be used for embedding images in web applications or APIs. The output format can be specified, with PNG as the default.

    Args:
        image (PIL.Image): The image to be converted.
        format (str): The format to save the image in (default is "png").

    Returns:
        str: The base64 encoded string of the image.

    """

    with io.BytesIO() as buffer:
        image.save(buffer, format)
        return base64.b64encode(buffer.getvalue()).decode()

# Side pane for future features, useful tips, or links
with st.sidebar:
    # Image section wrapped with custom styling
    st.markdown("""
        <div style="text-align: center;">
            <img src="https://img.freepik.com/premium-vector/farmer-using-smartphone-app-that-integrates-ai-technology-weather-data-alert-them-any_216520-124477.jpg" class="chat-image" style="border-radius: 15px; box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.2);" />
            <p style="color: white;">Let FARMWISE Handle All Your Farming Worries!</p>
        </div>
    """, unsafe_allow_html=True)

    st.title("FARMWISE: CULTIVATE SMARTER, GROW BETTER!")
    st.write("Ask any farming-related questions, and get expert advice.")
    st.write("- Crop Diseases")
    st.write("- Farming Recommendations")

# Title of the app
st.markdown("<h1 style='color:#4e342e;'>FARMWISE: THE SOLUTION TO YOUR FARMING QUESTIONS!</h1>", unsafe_allow_html=True)

# Placeholder for chat interface
st.markdown("<div class='main-pane'>", unsafe_allow_html=True)

# User input field
user_query = st.text_input("Ask me anything about farming:")

user_location = st.text_input("Enter your location (e.g., 'Lawrence, Kansas'):")

# User image input
uploaded_image = st.file_uploader("Upload an image of your crop (optional for disease detection):", type=["png", "jpg", "jpeg"])

# Button to get response
if st.button("Get Answer"):
    if user_query and user_location:
        # Payload for the API request
        api_url = "http://localhost:3000/chat"
        payload = {
            "message": user_query,
            "location": user_location
        }
        
        # If an image is uploaded, convert it to base64 and add it to the payload
        if uploaded_image is not None:
            image = Image.open(uploaded_image)
            image_base64 = pil_to_base64(image)
            payload["image"] = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",  # Adjust media type based on image type
                    "data": image_base64
                }
            }
        
        try:
            # Make a POST request to the Flask API
            response = requests.post(api_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                st.markdown(f"<div class='user-message'>{user_query}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='assistant-message'>{data['response']}</div>", unsafe_allow_html=True)
            else:
                st.error(f"Error: {response.status_code}")
        except Exception as e:
            st.error(f"Failed to connect to the API: {str(e)}")
    else:
        st.warning("Please enter both a query and a location.")

st.markdown("</div>", unsafe_allow_html=True)