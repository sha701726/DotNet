from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import json

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Warning: GEMINI_API_KEY not found in .env file!")
    print("Please create a .env file with: GEMINI_API_KEY=your_api_key_here")

# Configure Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")

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
        user_intent = data.get('intent', '')

        if not user_message:
            return jsonify({'error': 'Please enter a message'}), 400

        # Handle specific AmLI intents
        if user_intent == 'job_application':
            return jsonify({
                'response': "Great! You can apply for job roles or internships at AmLI using our application form. Here's the link: https://docs.google.com/forms/d/e/1FAIpQLSe7kN4IqtYOvWmBBrgBzuu7Kv0oc415UEFPkFN6-6Ezn8XKaA/viewform",
                'timestamp': datetime.now().isoformat(),
                'type': 'job_form',
                'form_url': 'https://docs.google.com/forms/d/e/1FAIpQLSe7kN4IqtYOvWmBBrgBzuu7Kv0oc415UEFPkFN6-6Ezn8XKaA/viewform'
            })
        
        elif user_intent == 'certificate_search':
            enrollment_no = data.get('enrollment_no', '')
            if not enrollment_no:
                return jsonify({
                    'response': "Please provide your 6-digit Enrollment Number to search for your certificate or offer letter.",
                    'timestamp': datetime.now().isoformat(),
                    'type': 'request_enrollment'
                })
            
            return jsonify({
                'response': f"Please enter the 6-digit password code for enrollment number {enrollment_no} to access your documents.",
                'timestamp': datetime.now().isoformat(),
                'type': 'request_password',
                'enrollment_no': enrollment_no
            })
        
        elif user_intent == 'verify_password':
            enrollment_no = data.get('enrollment_no', '')
            password = data.get('password', '')
            
            if not enrollment_no or not password:
                return jsonify({
                    'error': 'Both enrollment number and password are required'
                }), 400
            
            # Verify password and search Supabase
            result = search_supabase_documents(enrollment_no, password)
            return jsonify(result)

        # Check if there's file analysis to include
        file_context = ""
        if data.get('has_file') and data.get('file_analysis'):
            file_context = f"\n\nFile Analysis ({data.get('file_name', 'Document')}):\n{data.get('file_analysis', '')}"
        
        # Default AI response for general AmLI questions
        context_prompt = f"""You are an AI assistant specifically for AmLI (ADAPTIVE MONITORING LAYERED INTELLIGENCE). 

Your role is to help users with AmLI-specific services including:
- Job applications and internships
- Certificate and offer letter searches
- General information about AmLI services
- Student and employee support

Current user message: {user_message}{file_context}

Guidelines:
- Be specific to AmLI services and offerings
- If someone asks about job applications, guide them to the application form
- If someone asks about certificates/offer letters, ask for their enrollment number
- Be helpful, professional, and AmLI-focused
- Provide clear next steps for any service requests
- Keep responses concise and professional (under 100 words)
- If a file is attached, reference the analysis in your response

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
            'timestamp': datetime.now().isoformat(),
            'type': 'general_response'
        })

    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

def search_supabase_documents(enrollment_no, password):
    """Search for documents in Supabase database"""
    try:
        if not supabase_url or not supabase_key:
            return {
                'error': 'Supabase configuration not found',
                'response': 'Database connection not configured. Please contact support.'
            }
        
        # Search for the enrollment number and verify password
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Query to find enrollment and verify password
        query_url = f"{supabase_url}/rest/v1/rpc/search_documents"
        
        payload = {
            'enrollment_no': enrollment_no,
            'pass_key': password
        }
        
        response = requests.post(query_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                document = data[0]
                return {
                    'response': f"Document found! Here are your details:\n\nName: {document.get('name', 'N/A')}\nCourse: {document.get('course', 'N/A')}\nStatus: {document.get('status', 'N/A')}",
                    'timestamp': datetime.now().isoformat(),
                    'type': 'document_found',
                    'document': document,
                    'download_url': document.get('file_url', ''),
                    'enrollment_no': enrollment_no
                }
            else:
                return {
                    'response': "No documents found with the provided enrollment number and password. Please verify your credentials.",
                    'timestamp': datetime.now().isoformat(),
                    'type': 'no_document'
                }
        else:
            return {
                'response': "Unable to search database at the moment. Please try again later.",
                'timestamp': datetime.now().isoformat(),
                'type': 'database_error'
            }
            
    except Exception as e:
        return {
            'response': f"Error searching database: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'type': 'error'
        }

@app.route('/download/<enrollment_no>', methods=['GET'])
def download_document(enrollment_no):
    """Download document for verified enrollment"""
    try:
        # This would typically verify the session and then serve the file
        # For now, return a message
        return jsonify({
            'message': f'Download initiated for enrollment {enrollment_no}',
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads and process them with Gemini AI"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_type = request.form.get('type', 'document')
        user_message = request.form.get('message', '')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file:
            # Read file content
            file_content = file.read()
            
            # Check if it's an image file
            if is_image_file(file.filename):
                # Use Gemini Vision API for images
                analysis = analyze_image_with_gemini(file_content, file.filename, user_message)
            else:
                # Process as text document
                text_content = extract_text_from_file(file_content, file.filename, file_type)
                analysis = analyze_document_with_gemini(text_content, file.filename, user_message)
            
            return jsonify({
                'message': 'File processed successfully',
                'analysis': analysis,
                'filename': file.filename,
                'type': file_type
            })
            
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500



def analyze_document_with_gemini(text_content, filename, user_message):
    """Analyze document text using Gemini API with professional, precise responses"""
    try:
        prompt = f"""Analyze this document and provide a professional, concise summary.
        
        Document: {filename}
        User Query: {user_message}
        
        Provide a brief, precise analysis covering:
        1. Document type and key content (2-3 sentences)
        2. Relevant information for AmLI services (1-2 sentences)
        3. Specific recommendations or next steps (1 sentence)
        
        Keep response under 100 words. Be professional and actionable.
        
        Document content:
        {text_content[:2000]}"""
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"Document analysis error: {str(e)}"

def is_image_file(filename):
    """Check if file is an image based on extension"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
    file_ext = os.path.splitext(filename.lower())[1]
    return file_ext in image_extensions

def analyze_image_with_gemini(file_content, filename, user_message):
    """Analyze image using Gemini Vision API"""
    try:
        # Create image part for Gemini Vision
        image_part = {
            "mime_type": get_mime_type(filename),
            "data": file_content
        }
        
        prompt = f"""Analyze this image and provide a professional, concise description.
        
        Image: {filename}
        User Query: {user_message}
        
        Provide a brief, precise analysis covering:
        1. What you see in the image (2-3 sentences)
        2. Any relevant text or information visible
        3. How this relates to AmLI services (1 sentence)
        4. Specific recommendations based on the image (1 sentence)
        
        Keep response under 100 words. Be professional and actionable.
        Focus on the user's specific question about the image."""
        
        response = model.generate_content([prompt, image_part])
        return response.text
        
    except Exception as e:
        return f"Image analysis error: {str(e)}"

def get_mime_type(filename):
    """Get MIME type based on file extension"""
    ext = os.path.splitext(filename.lower())[1]
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml'
    }
    return mime_types.get(ext, 'image/jpeg')

def extract_text_from_file(file_content, filename, file_type):
    """Extract text content from various file types"""
    try:
        # Try to decode as text first
        try:
            return file_content.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            # If it's a binary file, try to extract basic info
            return f"Binary file: {filename} - Size: {len(file_content)} bytes"
    except Exception as e:
        return f"File content extraction error: {str(e)}"

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
