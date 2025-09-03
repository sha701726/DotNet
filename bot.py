from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import json
import logging
from typing import Dict, Any, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY not found in .env file!")
    logger.error("Please create a .env file with: GEMINI_API_KEY=your_api_key_here")
    raise ValueError("GEMINI_API_KEY is required")

# Configure Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")

genai.configure(api_key=api_key)

# Initialize Gemini model with advanced configuration
try:
    # Use Gemini 1.5 Pro for better reasoning capabilities
    model = genai.GenerativeModel(
        "gemini-1.5-pro",
        generation_config={
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 2048,
        },
        safety_settings=[
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    )
    logger.info("Gemini 1.5 Pro model loaded successfully with advanced configuration")
except Exception as e:
    logger.error(f"Error loading Gemini model: {e}")
    # Fallback to flash model
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("Fallback to Gemini 1.5 Flash model")
    except Exception as e2:
        logger.error(f"Error loading fallback model: {e2}")
        exit(1)

# Enhanced conversation history management
conversation_history = {}

class AmLIExpert:
    """Enhanced AI expert system for AmLI services"""
    
    def __init__(self):
        self.knowledge_base = {
            "amli_info": {
                "name": "AmLI - Adaptive Monitoring Layered Intelligence",
                "services": [
                    "Job applications and internships",
                    "Certificate and offer letter searches", 
                    "Student and employee support",
                    "Educational consulting",
                    "Professional development programs"
                ],
                "contact": "Contact AmLI for professional services and support",
                "website": "AmLI provides comprehensive educational and professional services"
            },
            "job_application": {
                "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSe7kN4IqtYOvWmBBrgBzuu7Kv0oc415UEFPkFN6-6Ezn8XKaA/viewform",
                "requirements": "Open positions for qualified candidates",
                "process": "Submit application → Review → Interview → Selection"
            },
            "certificate_search": {
                "process": "Enrollment Number → Password Verification → Document Access",
                "requirements": "Valid 6-digit enrollment number and password"
            }
        }
    
    def generate_context_prompt(self, user_message: str, conversation_context: list = None, file_context: str = "") -> str:
        """Generate comprehensive context prompt for better AI responses"""
        
        # Build conversation context
        context_str = ""
        if conversation_context:
            context_str = "\n\nRecent conversation:\n"
            for msg in conversation_context[-5:]:  # Last 5 messages
                role = "User" if msg.get('isUser') else "Assistant"
                context_str += f"{role}: {msg.get('content', '')}\n"
        
        # Enhanced system prompt
        system_prompt = f"""You are an expert AI assistant for AmLI (Adaptive Monitoring Layered Intelligence), a comprehensive educational and professional services organization.

CORE CAPABILITIES:
- Job applications and internship opportunities
- Certificate and offer letter document searches
- Student and employee support services
- Educational consulting and guidance
- Professional development programs

RESPONSE GUIDELINES:
1. Be accurate, helpful, and professional
2. Provide specific, actionable information
3. When unsure, ask clarifying questions
4. Reference AmLI services when relevant
5. Keep responses concise but comprehensive (100-200 words)
6. Use clear, professional language
7. Provide step-by-step guidance when appropriate

KNOWLEDGE BASE:
- AmLI offers comprehensive educational and professional services
- Job applications require form submission with proper credentials
- Certificate searches need valid enrollment number and password
- All services are designed to support student and professional growth

Current user message: {user_message}{file_context}{context_str}

Please provide a helpful, accurate response that addresses the user's specific needs while maintaining AmLI's professional standards."""

        return system_prompt
    
    def analyze_user_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user message to determine intent and extract relevant information"""
        
        message_lower = message.lower()
        
        # Intent classification
        intents = {
            'job_application': any(word in message_lower for word in ['job', 'internship', 'apply', 'application', 'position', 'career', 'work']),
            'certificate_search': any(word in message_lower for word in ['certificate', 'document', 'offer letter', 'enrollment', 'password', 'search']),
            'general_info': any(word in message_lower for word in ['what is', 'tell me about', 'information', 'help', 'service']),
            'file_analysis': any(word in message_lower for word in ['analyze', 'review', 'check', 'examine', 'look at']),
            'support': any(word in message_lower for word in ['help', 'support', 'assist', 'problem', 'issue'])
        }
        
        # Extract enrollment number if present
        enrollment_match = re.search(r'\b\d{6}\b', message)
        enrollment_no = enrollment_match.group() if enrollment_match else None
        
        # Determine primary intent
        primary_intent = max(intents.items(), key=lambda x: x[1])[0] if any(intents.values()) else 'general'
        
        return {
            'primary_intent': primary_intent,
            'confidence': intents.get(primary_intent, 0),
            'enrollment_no': enrollment_no,
            'requires_clarification': primary_intent == 'general' and len(message.split()) < 5
        }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Enhanced chat endpoint with better AI responses"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        user_intent = data.get('intent', '')
        session_id = data.get('session_id', 'default')

        if not user_message:
            return jsonify({'error': 'Please enter a message'}), 400

        # Initialize conversation history for session
        if session_id not in conversation_history:
            conversation_history[session_id] = []

        # Add user message to history
        conversation_history[session_id].append({
            'content': user_message,
            'isUser': True,
            'timestamp': datetime.now().isoformat()
        })

        # Initialize AmLI expert
        expert = AmLIExpert()
        
        # Analyze user intent
        intent_analysis = expert.analyze_user_intent(user_message)
        
        # Handle specific intents
        if user_intent == 'job_application' or intent_analysis['primary_intent'] == 'job_application':
            response_data = handle_job_application()
        elif user_intent == 'certificate_search' or intent_analysis['primary_intent'] == 'certificate_search':
            response_data = handle_certificate_search(data, intent_analysis)
        elif user_intent == 'verify_password':
            response_data = handle_password_verification(data)
        else:
            # Generate AI response for general questions
            response_data = generate_ai_response(user_message, conversation_history[session_id], data, expert)

        # Add AI response to history
        conversation_history[session_id].append({
            'content': response_data['response'],
            'isUser': False,
            'timestamp': response_data['timestamp']
        })

        # Limit conversation history to prevent memory issues
        if len(conversation_history[session_id]) > 20:
            conversation_history[session_id] = conversation_history[session_id][-20:]

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': 'An error occurred while processing your request. Please try again.',
            'response': 'I apologize, but I encountered an error. Please rephrase your question or try again in a moment.',
            'timestamp': datetime.now().isoformat(),
            'type': 'error'
        }), 500

def handle_job_application():
    """Handle job application requests"""
    return {
        'response': "Great! You can apply for job roles or internships at AmLI. Here's what you need to know:\n\n"
                   "📋 **Application Process:**\n"
                   "1. Fill out our comprehensive application form\n"
                   "2. Submit your resume and relevant documents\n"
                   "3. Our team will review your application\n"
                   "4. Qualified candidates will be contacted for interviews\n\n"
                   "🔗 **Apply Now:** [Click here to access the application form](https://docs.google.com/forms/d/e/1FAIpQLSe7kN4IqtYOvWmBBrgBzuu7Kv0oc415UEFPkFN6-6Ezn8XKaA/viewform)\n\n"
                   "For any questions about the application process, feel free to ask!",
        'timestamp': datetime.now().isoformat(),
        'type': 'job_form',
        'form_url': 'https://docs.google.com/forms/d/e/1FAIpQLSe7kN4IqtYOvWmBBrgBzuu7Kv0oc415UEFPkFN6-6Ezn8XKaA/viewform'
    }

def handle_certificate_search(data, intent_analysis):
    """Handle certificate search requests"""
    enrollment_no = data.get('enrollment_no') or intent_analysis.get('enrollment_no')
    
    if not enrollment_no:
        return {
            'response': "I can help you search for your certificate or offer letter. To proceed, I need your 6-digit Enrollment Number.\n\n"
                       "📝 **Please provide:**\n"
                       "• Your 6-digit Enrollment Number\n\n"
                       "Once you provide this, I'll guide you through the verification process to access your documents.",
            'timestamp': datetime.now().isoformat(),
            'type': 'request_enrollment'
        }
    
    return {
        'response': f"Thank you! I found enrollment number {enrollment_no}. To access your documents, please provide the 6-digit password code associated with this enrollment.\n\n"
                   "🔐 **Security Verification:**\n"
                   "• Enter your 6-digit password\n"
                   "• This ensures secure access to your personal documents",
        'timestamp': datetime.now().isoformat(),
        'type': 'request_password',
        'enrollment_no': enrollment_no
    }

def handle_password_verification(data):
    """Handle password verification for document access"""
    enrollment_no = data.get('enrollment_no', '')
    password = data.get('password', '')
    
    if not enrollment_no or not password:
        return {
            'error': 'Both enrollment number and password are required',
            'response': 'Please provide both your enrollment number and password to access your documents.',
            'timestamp': datetime.now().isoformat(),
            'type': 'error'
        }
    
    # Search Supabase for documents
    result = search_supabase_documents(enrollment_no, password)
    return result

def generate_ai_response(user_message: str, conversation_context: list, data: dict, expert: AmLIExpert) -> Dict[str, Any]:
    """Generate intelligent AI response using enhanced prompting"""
    try:
        # Prepare file context if available
        file_context = ""
        if data.get('has_file') and data.get('file_analysis'):
            file_context = f"\n\n📎 **File Analysis** ({data.get('file_name', 'Document')}):\n{data.get('file_analysis', '')}"
        
        # Generate comprehensive prompt
        prompt = expert.generate_context_prompt(user_message, conversation_context, file_context)
        
        # Generate response with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                
                # Extract response text safely
                if hasattr(response, "text") and response.text:
                    ai_response = response.text.strip()
                elif hasattr(response, "candidates") and response.candidates:
                    ai_response = response.candidates[0].content.parts[0].text.strip()
                else:
                    raise ValueError("No response text found")
                
                # Validate response
                if len(ai_response) < 10:
                    raise ValueError("Response too short")
                
                return {
                    'response': ai_response,
                    'timestamp': datetime.now().isoformat(),
                    'type': 'general_response'
                }
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise e
                continue
        
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        return {
            'response': "I apologize, but I'm having trouble processing your request right now. Please try rephrasing your question or try again in a moment. If the issue persists, please contact AmLI support.",
            'timestamp': datetime.now().isoformat(),
            'type': 'error'
        }

def search_supabase_documents(enrollment_no: str, password: str) -> Dict[str, Any]:
    """Enhanced Supabase document search with better error handling"""
    try:
        if not supabase_url or not supabase_key:
            return {
                'response': 'I apologize, but the document search service is currently unavailable. Please contact AmLI support for assistance.',
                'timestamp': datetime.now().isoformat(),
                'type': 'service_unavailable'
            }
        
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        query_url = f"{supabase_url}/rest/v1/rpc/search_documents"
        payload = {
            'enrollment_no': enrollment_no,
            'pass_key': password
        }
        
        response = requests.post(query_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                document = data[0]
                return {
                    'response': f"✅ **Document Found Successfully!**\n\n"
                               f"📋 **Your Details:**\n"
                               f"• **Name:** {document.get('name', 'N/A')}\n"
                               f"• **Course:** {document.get('course', 'N/A')}\n"
                               f"• **Status:** {document.get('status', 'N/A')}\n"
                               f"• **Enrollment:** {enrollment_no}\n\n"
                               f"📥 **Download:** Your document is ready for download.",
                    'timestamp': datetime.now().isoformat(),
                    'type': 'document_found',
                    'document': document,
                    'download_url': document.get('file_url', ''),
                    'enrollment_no': enrollment_no
                }
            else:
                return {
                    'response': "❌ **Document Not Found**\n\n"
                               "I couldn't find any documents with the provided credentials. Please verify:\n"
                               "• Your 6-digit enrollment number is correct\n"
                               "• Your 6-digit password is correct\n"
                               "• You're using the right credentials for this service\n\n"
                               "If you continue to have issues, please contact AmLI support.",
                    'timestamp': datetime.now().isoformat(),
                    'type': 'no_document'
                }
        else:
            return {
                'response': "⚠️ **Service Temporarily Unavailable**\n\n"
                           "The document search service is experiencing technical difficulties. Please try again in a few minutes or contact AmLI support if the issue persists.",
                'timestamp': datetime.now().isoformat(),
                'type': 'database_error'
            }
            
    except requests.exceptions.Timeout:
        return {
            'response': "⏱️ **Request Timeout**\n\n"
                       "The search is taking longer than expected. Please try again in a moment.",
            'timestamp': datetime.now().isoformat(),
            'type': 'timeout'
        }
    except Exception as e:
        logger.error(f"Supabase search error: {str(e)}")
        return {
            'response': "🔧 **Technical Error**\n\n"
                       "I encountered an error while searching for your documents. Please try again or contact AmLI support for assistance.",
            'timestamp': datetime.now().isoformat(),
            'type': 'error'
        }

@app.route('/download/<enrollment_no>', methods=['GET'])
def download_document(enrollment_no):
    """Download document for verified enrollment"""
    try:
        return jsonify({
            'message': f'Download initiated for enrollment {enrollment_no}',
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Enhanced file upload processing with better AI analysis"""
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
            
            # Validate file size (max 10MB)
            if len(file_content) > 10 * 1024 * 1024:
                return jsonify({'error': 'File size must be less than 10MB'}), 400
            
            # Process file based on type
            if is_image_file(file.filename):
                analysis = analyze_image_with_gemini(file_content, file.filename, user_message)
            else:
                text_content = extract_text_from_file(file_content, file.filename, file_type)
                analysis = analyze_document_with_gemini(text_content, file.filename, user_message)
            
            return jsonify({
                'message': 'File processed successfully',
                'analysis': analysis,
                'filename': file.filename,
                'type': file_type,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

def analyze_document_with_gemini(text_content: str, filename: str, user_message: str) -> str:
    """Enhanced document analysis with better prompting"""
    try:
        prompt = f"""Analyze this document and provide a comprehensive, professional summary.

📄 **Document:** {filename}
❓ **User Query:** {user_message}

Please provide a detailed analysis covering:

1. **Document Type & Purpose** (2-3 sentences)
2. **Key Content Summary** (3-4 sentences)
3. **Relevance to AmLI Services** (1-2 sentences)
4. **Specific Recommendations** (1-2 sentences)
5. **Next Steps** (1 sentence)

Keep the response professional, accurate, and actionable. Focus on how this document relates to the user's specific question.

**Document Content:**
{text_content[:3000]}"""

        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"Document analysis error: {str(e)}")
        return f"Document analysis error: {str(e)}"

def is_image_file(filename: str) -> bool:
    """Check if file is an image based on extension"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
    file_ext = os.path.splitext(filename.lower())[1]
    return file_ext in image_extensions

def analyze_image_with_gemini(file_content: bytes, filename: str, user_message: str) -> str:
    """Enhanced image analysis with better prompting"""
    try:
        image_part = {
            "mime_type": get_mime_type(filename),
            "data": file_content
        }
        
        prompt = f"""Analyze this image and provide a comprehensive, professional description.

🖼️ **Image:** {filename}
❓ **User Query:** {user_message}

Please provide a detailed analysis covering:

1. **Visual Content** (What you see in the image - 3-4 sentences)
2. **Text/Information** (Any readable text or data - 2-3 sentences)
3. **Relevance to AmLI** (How this relates to AmLI services - 1-2 sentences)
4. **Specific Insights** (Key findings or important details - 2-3 sentences)
5. **Recommendations** (What the user should do next - 1-2 sentences)

Keep the response professional, accurate, and focused on the user's specific question about the image."""

        response = model.generate_content([prompt, image_part])
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}")
        return f"Image analysis error: {str(e)}"

def get_mime_type(filename: str) -> str:
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

def extract_text_from_file(file_content: bytes, filename: str, file_type: str) -> str:
    """Enhanced text extraction from various file types"""
    try:
        # Try to decode as text first
        try:
            text_content = file_content.decode('utf-8', errors='ignore')
            if len(text_content.strip()) > 0:
                return text_content
        except UnicodeDecodeError:
            pass
        
        # Try other encodings
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                text_content = file_content.decode(encoding, errors='ignore')
                if len(text_content.strip()) > 0:
                    return text_content
            except UnicodeDecodeError:
                continue
        
        # If all text decoding fails, return file info
        return f"Binary file: {filename} - Size: {len(file_content)} bytes - Type: {file_type}"
        
    except Exception as e:
        logger.error(f"Text extraction error: {str(e)}")
        return f"File content extraction error: {str(e)}"

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    logger.info("Starting AmLI AI Assistant...")
    logger.info("Server will be available at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
