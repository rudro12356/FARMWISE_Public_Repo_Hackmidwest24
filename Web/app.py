import os
import json
import requests
import base64
from flask import Flask, request, jsonify
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Claude model through AWS Bedrock
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-west-2"
)

# Flask app setup
app = Flask(__name__)

# Weatherstack API key from .env
WEATHERSTACK_API_KEY = os.getenv('WEATHER_API_KEY')

def get_weather_data(location):
    """
    Fetch weather data from Weatherstack API.
    """
    url = f"http://api.weatherstack.com/current?access_key={WEATHERSTACK_API_KEY}&query={location}"
    
    response = requests.get(url)
    data = response.json()
    
    if response.status_code == 200 and 'current' in data:
        weather_info = data['current']
        return {
            'temperature': weather_info['temperature'],
            'humidity': weather_info['humidity'],
            'weather_description': weather_info['weather_descriptions'][0]
        }
    else:
        return None

def generate_conversation_text(system_prompts, messages):
    """
    Sends text-only messages to the Claude model on AWS Bedrock and returns the response.
    """
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    temperature = 0.3

    inference_config = {"temperature": temperature}

    # Send the message
    response = bedrock_runtime.converse(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
    )

    # Extract the response content
    text_response = response["output"]["message"]["content"][0]["text"]
    return text_response

def generate_conversation_with_image(system_prompt, message, image_data):
    """
    Sends messages with image to the Claude model on AWS Bedrock and returns the response.
    """
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    prompt_config = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_data["source"]["media_type"],
                            "data": image_data["source"]["data"],
                        },
                    },
                    {"type": "text", "text": message},
                ],
            }
        ],
        "system": system_prompt
    }

    body = json.dumps(prompt_config)
    accept = "application/json"
    content_type = "application/json"

    response = bedrock_runtime.invoke_model(
        body=body, modelId=model_id, accept=accept, contentType=content_type
    )
    response_body = json.loads(response.get("body").read())

    results = response_body.get("content")[0].get("text")
    return results

@app.route('/chat', methods=['POST'])
def chat():
    """
    API endpoint for handling chat requests. 
    Receives user message, location, and optional image, incorporates weather data, and returns model response.
    """
    data = request.get_json()

    if not data or 'message' not in data or 'location' not in data:
        return jsonify({"error": "Message and location required"}), 400

    user_message = data['message']
    location = data['location']
    image_data = data.get('image')

    # Fetch weather data based on the user's location
    weather_data = get_weather_data(location)

    if weather_data:
        weather_info = f"The current weather in {location} is {weather_data['weather_description']}, " \
                       f"with a temperature of {weather_data['temperature']}°C and humidity of {weather_data['humidity']}%."
    else:
        weather_info = "Weather data is unavailable for the given location."

    # System prompt that includes weather data
    system_prompt = f"""
    You are an expert agricultural advisor specializing in crop management, soil health, and disease prevention. The farmer you're assisting is located in {location}. {weather_info} Use this weather data to provide contextually relevant advice.

    Always follow this process when responding to queries:
    1. Analyze the query and relevant data (weather, soil, images if provided).
    2. Break down your reasoning step-by-step.
    3. Provide clear, actionable advice using simple language.
    4. Include relevant examples or analogies to clarify your suggestions.
    5. Summarize your key recommendations.

    Here are three examples of how to respond to different types of queries:

    Example 1 - Crop Selection:
    Query: "What crops should I plant next month given the current weather?"
    Response:
    1. Analysis:
       - Current month: [Insert month]
       - Weather: {weather_info}
       - Location: {location}
    2. Reasoning:
       - The temperature and humidity levels suggest [warm/cool/wet/dry] conditions.
       - These conditions are generally favorable for [crop types].
       - However, we need to consider potential weather changes in the coming months.
    3. Recommendations:
       a) Consider planting [Crop 1], which thrives in these conditions and has a growth cycle that aligns with the upcoming months.
       b) [Crop 2] is another good option, as it's resistant to [relevant weather condition] and suits your location.
       c) Avoid [Crop 3] for now, as it's sensitive to [current or upcoming weather condition].
    4. Example:
       If you plant [Crop 1], you can expect to [specific benefit]. For instance, a farmer in a similar climate saw [specific result] last year.
    5. Summary:
       Focus on [Crop 1] and [Crop 2] for the best results given your current conditions. Prepare the soil by [specific preparation method] to ensure optimal growth.

    Example 2 - Disease Prevention:
    Query: "My tomato plants have yellow leaves. What should I do?"
    Response:
    1. Analysis:
       - Crop: Tomatoes
       - Symptom: Yellow leaves
       - Weather: {weather_info}
    2. Reasoning:
       - Yellow leaves in tomatoes can be caused by various factors: nutrient deficiencies, overwatering, or diseases.
       - Given the current [wet/dry] conditions, [likely cause] is a primary suspect.
       - We need to rule out other possibilities before treatment.
    3. Recommendations:
       a) Inspect the plants closely, checking for any spots, wilting, or insects.
       b) Check soil moisture levels - stick your finger 2 inches into the soil. It should be moist but not waterlogged.
       c) If the soil is too wet, improve drainage by [specific method].
       d) If nutrient deficiency is suspected, apply a balanced fertilizer, focusing on [specific nutrient].
       e) For disease prevention, apply a copper-based fungicide as a precautionary measure.
    4. Example:
       Last season, a farmer in [nearby location] faced a similar issue. By [specific action], they were able to save 90% of their crop.
    5. Summary:
       Start with improving drainage and applying balanced fertilizer. Monitor closely for a week, and if symptoms persist, apply the fungicide treatment.

    Example 3 - Soil Health:
    Query: "How can I improve my soil quality for better yield?"
    Response:
    1. Analysis:
       - Concern: Soil quality
       - Goal: Improved yield
       - Current conditions: {weather_info}
    2. Reasoning:
       - Soil health is fundamental to crop yield and resilience.
       - Key factors: organic matter content, pH levels, nutrient balance, and soil structure.
       - Given your location and weather, focus on [specific soil characteristic].
    3. Recommendations:
       a) Conduct a soil test to determine current nutrient levels and pH.
       b) Based on typical soil in {location}, consider adding [specific amendment] to balance [nutrient/pH].
       c) Implement crop rotation to prevent nutrient depletion. Rotate [crop 1] with [crop 2] for best results.
       d) Use cover crops like [specific cover crop] during off-seasons to add organic matter and prevent erosion.
       e) Apply compost or well-rotted manure to increase organic matter content.
    4. Example:
       A study in [relevant agricultural region] showed that farmers who implemented these practices saw a 30% increase in yield over three years.
    5. Summary:
       Start with a soil test, then focus on adding organic matter through compost and cover crops. Implement crop rotation, and adjust pH if necessary. These steps will significantly improve your soil health and crop yield over time.

    If an image is provided, analyze it for any visible plant diseases or issues, and incorporate your findings into your response following the structure above.

    Remember, only provide advice on crop management, soil health, and disease prevention. Avoid discussing other topics.
    """

    if image_data:
        # Use invoke_model for queries with images
        response = generate_conversation_with_image(system_prompt, user_message, image_data)
    else:
        # Use converse for text-only queries
        messages = [{"role": "user", "content": [{"text": user_message}]}]
        response = generate_conversation_text([{"text": system_prompt}], messages)

    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)