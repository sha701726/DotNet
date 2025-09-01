from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Warning: GEMINI_API_KEY not found in .env file!")
    print("Please create a .env file with: GEMINI_API_KEY=your_api_key_here")

genai.configure(api_key=api_key)

# Initialize Gemini model
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("Gemini model loaded successfully")
except Exception as e:
    print(f"Error loading Gemini model: {e}")
    exit(1)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Please enter a message'}), 400

        # Build context-aware prompt
        context_prompt = f"""You are a helpful humanoid AI assistant. 

Current user message: {user_message}

Guidelines:
- Be friendly and conversational
- Provide accurate and helpful information
- Use a natural, human-like tone
- Ask follow-up questions when appropriate
- Be empathetic and understanding

Assistant:"""

        # Generate response
        response = model.generate_content(context_prompt)

        # Safely extract response
        ai_response = None
        if hasattr(response, "text") and response.text:
            ai_response = response.text
        else:
            ai_response = response.candidates[0].content.parts[0].text

        return jsonify({
            'response': ai_response, 
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
