from flask import Flask, request, jsonify
import argparse
import os
import google.generativeai as genai
from dotenv import load_dotenv

app = Flask(__name__)

try:
    # API token for authentication
    gemini_api_key = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_api_key)
except KeyError:
    # If the key is not set, the service will not start.
    raise RuntimeError("GEMINI_API_KEY environment variable not set.") from None

model = genai.GenerativeModel('gemini-2.5-flash')
@app.route('/predict', methods=['POST'])
def predict():
    """Receives a query and returns a response from the Gemini API."""
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    try:
        # --- Call the Gemini API ---
        response = model.generate_content(query)

        # Return the model's response text directly.
        return jsonify({'response': response.text})

    except Exception as e:
        # Log the error for debugging.
        print(f"An error occurred: {e}")
        # Return a generic error message to the user.
        return jsonify({'error': 'Failed to get a response from the LLM service.'}), 500


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Flask server.')
    parser.add_argument('--port', type=int, default=5001)
    args = parser.parse_args()

    app.run(debug=True, host='0.0.0.0', port=args.port)