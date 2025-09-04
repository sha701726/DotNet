from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from datetime import datetime
import logging
import re
from typing import Dict, Any, Optional, List
import requests
import time

# Optional: Gemini (Google Generative AI)
try:
    import google.generativeai as genai
except Exception:
    genai = None

# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# App and Env
# ----------------------------------------------------------------------------
load_dotenv()
app = Flask(__name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip().strip('"').strip("'")
SUPABASE_URL = os.getenv('SUPABASE_URL', '').strip()
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '').strip()

# ----------------------------------------------------------------------------
# Gemini setup (prefer free-tier friendly model)
# ----------------------------------------------------------------------------
# Default to flash to maximize free access; you can change MODEL_NAME via env
MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
model = None

if genai and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Sanity check against flash
        _sanity = genai.GenerativeModel('gemini-2.0-flash')
        _ = _sanity.generate_content('ping')
        # Main model
        model = genai.GenerativeModel(MODEL_NAME, generation_config={
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40,
            'max_output_tokens': 2048,
        })
        logger.info(f'Gemini model ready: {MODEL_NAME}')
    except Exception as e:
        logger.warning(f'Gemini disabled: {e}')
else:
    if not GEMINI_API_KEY:
        logger.warning('GEMINI_API_KEY missing; AI answers will be limited')
    if not genai:
        logger.warning('google-generativeai not installed; AI answers disabled')

# ----------------------------------------------------------------------------
# Conversation state (simple in-memory)
# ----------------------------------------------------------------------------
conversation_history: Dict[str, List[Dict[str, Any]] ] = {}

# ----------------------------------------------------------------------------
# Intent helpers and handlers
# ----------------------------------------------------------------------------
class AmLIExpert:
    def analyze_user_intent(self, message: str) -> Dict[str, Any]:
        text = (message or '').lower().strip()
        intents = {
            'greeting': any(w in text for w in ['hello', 'hi ', ' hi', 'hey', 'namaste', 'good morning', 'good evening']),
            'thanks': any(w in text for w in ['thanks', 'thank you', 'thx', 'tysm']),
            'goodbye': any(w in text for w in ['bye', 'goodbye', 'see you']),
            'small_talk': any(p in text for p in ['how are you', 'who are you', 'what can you do']),
            'amli_info': ('amli' in text) or any(p in text for p in ['services', 'about amli', 'amli services']),
            'support_issue': any(p in text for p in ['issue', 'problem', 'not working', 'failed to fetch', 'error']),
            'job_application': any(w in text for w in ['job', 'internship', 'apply', 'application', 'career']),
            'certificate_search': any(w in text for w in ['certificate', 'document', 'offer letter', 'enrollment', 'password', 'search']),
            'time_date': any(w in text for w in ['time', 'date', 'today', 'now']) and len(text) <= 50,
            'simple_math': bool(re.fullmatch(r"[\d\s\+\-\*\/\(\)\.]+", text)) and any(op in text for op in ['+', '-', '*', '/'])
        }
        enrollment_match = re.search(r'\b\d{6}\b', message or '')
        enrollment_no = enrollment_match.group() if enrollment_match else None
        primary_intent = 'general'
        for key in ['greeting','thanks','goodbye','small_talk','amli_info','support_issue','job_application','certificate_search','time_date','simple_math']:
            if intents.get(key):
                primary_intent = key
                break
        return {
            'primary_intent': primary_intent,
            'enrollment_no': enrollment_no,
        }


def make_prompt(user_message: str, history: List[Dict[str, Any]], file_context: str = '') -> str:
    ctx = ''
    if history:
        last = history[-5:]
        for m in last:
            role = 'User' if m.get('isUser') else 'Assistant'
            ctx += f"\n{role}: {m.get('content','')}"
    return (
        "You are AmLI Assistant. Be accurate, concise, and helpful."
        " Provide actionable steps when possible."
        f"\n\nUser message: {user_message}{file_context}\n{ctx}"
        "\n\nAnswer:"
    )


def _is_quota_error(err: str) -> bool:
    if not err:
        return False
    lowered = err.lower()
    return (' 429 ' in f' {err} ' or 'quota' in lowered or 'rate limit' in lowered)


def generate_ai_response(message: str, session_id: str, data: dict) -> Dict[str, Any]:
    if not model:
        logger.warning("AI requested but model is not configured")
        return {
            'response': "AI responses are temporarily unavailable. You can still use job application and certificate search features.",
            'timestamp': datetime.now().isoformat(),
            'type': 'service_unavailable'
        }
    attempts = 3
    backoff = 0.8
    last_err = ''
    for i in range(attempts):
        try:
            file_context = ''
            if data.get('has_file') and data.get('file_analysis'):
                file_context = f"\n\nFile analysis: {data.get('file_analysis')}"
            prompt = make_prompt(message, conversation_history.get(session_id, []), file_context)
            logger.info(f"Invoking Gemini {MODEL_NAME} (attempt {i+1}) with prompt length {len(prompt)}")
            res = model.generate_content(prompt)
            logger.info("Gemini responded successfully")
            text = ''
            if hasattr(res, 'text') and res.text:
                text = res.text.strip()
            elif hasattr(res, 'candidates') and res.candidates:
                text = res.candidates[0].content.parts[0].text.strip()
            if not text:
                text = "I'm sorry, I couldn't generate a response right now. Please try again."
            return {
                'response': text,
                'timestamp': datetime.now().isoformat(),
                'type': 'general_response'
            }
        except Exception as e:
            last_err = str(e)
            logger.warning(f'Gemini call failed (attempt {i+1}): {last_err}')
            if i < attempts - 1:
                time.sleep(backoff)
                backoff *= 2
                continue
    if _is_quota_error(last_err):
        return {
            'response': "I've reached my API quota limit. Please try again later. Job applications and certificate searches still work.",
            'timestamp': datetime.now().isoformat(),
            'type': 'quota_exceeded'
        }
    return {
        'response': "I encountered an error while answering. Please try again shortly.",
        'timestamp': datetime.now().isoformat(),
        'type': 'error'
    }

# ---------- Intent Handlers (rule-based, no AI needed) ----------

def handle_greeting() -> Dict[str, Any]:
    return {
        'response': "Hello! How can I assist you today? You can ask about jobs, certificates, or general AmLI info.",
        'timestamp': datetime.now().isoformat(),
        'type': 'greeting'
    }


def handle_thanks() -> Dict[str, Any]:
    return {
        'response': "You're welcome! If you need anything else, just ask.",
        'timestamp': datetime.now().isoformat(),
        'type': 'ack'
    }


def handle_goodbye() -> Dict[str, Any]:
    return {
        'response': "Goodbye! Have a great day.",
        'timestamp': datetime.now().isoformat(),
        'type': 'goodbye'
    }


def handle_small_talk(message: str) -> Dict[str, Any]:
    if 'how are you' in (message or '').lower():
        text = "I'm doing great and ready to help!"
    elif 'who are you' in (message or '').lower():
        text = "I'm the AmLI Assistant. I help with jobs, certificates, and general queries."
    else:
        text = "I'm here to help with AmLI services and your questions."
    return {
        'response': text,
        'timestamp': datetime.now().isoformat(),
        'type': 'small_talk'
    }


def handle_amli_info() -> Dict[str, Any]:
    return {
        'response': (
            "AmLI (Adaptive Monitoring Layered Intelligence) offers:\n"
            "• Job applications and internships\n"
            "• Certificate/offer letter search\n"
            "• Student and employee support\n"
            "• Educational consulting and development\n\n"
            "Ask me to apply for a job or search your certificate to begin."
        ),
        'timestamp': datetime.now().isoformat(),
        'type': 'amli_info'
    }


def handle_support_issue() -> Dict[str, Any]:
    return {
        'response': (
            "Let's fix this. Please try:\n"
            "1) Reload the page at http://localhost:5000\n"
            "2) Ensure the server is running\n"
            "3) If you uploaded a file, keep it under 10MB\n"
            "4) If error persists, share the exact error message"
        ),
        'timestamp': datetime.now().isoformat(),
        'type': 'support'
    }


def handle_time_date() -> Dict[str, Any]:
    now = datetime.now()
    return {
        'response': f"Current date/time: {now.strftime('%Y-%m-%d %H:%M:%S')}",
        'timestamp': now.isoformat(),
        'type': 'time_date'
    }


def safe_eval_math(expr: str) -> Optional[float]:
    if not re.fullmatch(r"[\d\s\+\-\*\/\(\)\.]+", expr or ''):
        return None
    try:
        return float(eval(expr, {"__builtins__": {}}, {}))
    except Exception:
        return None


def handle_simple_math(message: str) -> Dict[str, Any]:
    val = safe_eval_math((message or '').strip())
    text = f"Result: {val}" if val is not None else "I couldn't evaluate that expression. Please use only numbers and + - * / ( )."
    return {
        'response': text,
        'timestamp': datetime.now().isoformat(),
        'type': 'math'
    }

# ----------------------------------------------------------------------------
# Supabase integration
# ----------------------------------------------------------------------------

def search_supabase_documents(enrollment_no: str, password: str) -> Dict[str, Any]:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return {
            'response': 'Document search service is not configured. Please contact support.',
            'timestamp': datetime.now().isoformat(),
            'type': 'service_unavailable'
        }
    try:
        headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
            'Content-Type': 'application/json'
        }
        url = f"{SUPABASE_URL}/rest/v1/rpc/search_documents"
        payload = { 'enrollment_no': enrollment_no, 'pass_key': password }
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data:
                doc = data[0]
                return {
                    'response': (
                        "Document Found\n\n"
                        f"Name: {doc.get('name','N/A')}\n"
                        f"Course: {doc.get('course','N/A')}\n"
                        f"Status: {doc.get('status','N/A')}\n"
                        f"Enrollment: {enrollment_no}"
                    ),
                    'timestamp': datetime.now().isoformat(),
                    'type': 'document_found',
                    'document': doc,
                    'download_url': doc.get('file_url',''),
                    'enrollment_no': enrollment_no
                }
            return {
                'response': 'No document found. Please verify your enrollment and password.',
                'timestamp': datetime.now().isoformat(),
                'type': 'no_document'
            }
        return {
            'response': 'Service temporarily unavailable. Please try again later.',
            'timestamp': datetime.now().isoformat(),
            'type': 'database_error'
        }
    except requests.exceptions.Timeout:
        return {
            'response': 'Request timed out. Please try again.',
            'timestamp': datetime.now().isoformat(),
            'type': 'timeout'
        }
    except Exception as e:
        logger.error(f'Supabase error: {e}')
        return {
            'response': 'Technical error while searching documents. Please try again.',
            'timestamp': datetime.now().isoformat(),
            'type': 'error'
        }

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    status = {
        'server': 'ok',
        'model_configured': bool(model),
        'model_name': MODEL_NAME if model else None,
        'supabase_configured': bool(SUPABASE_URL and SUPABASE_ANON_KEY),
        'time': datetime.now().isoformat()
    }
    return jsonify(status)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(force=True)
        message = (data.get('message') or '').strip()
        intent = (data.get('intent') or '').strip()
        session_id = data.get('session_id') or 'default'

        logger.info(f"/chat received | intent='{intent}' | msg='{(message[:120] + '...') if len(message) > 120 else message}' | session='{session_id}'")

        if not message and not intent:
            return jsonify({'error': 'Please enter a message'}), 400

        # init history
        history = conversation_history.setdefault(session_id, [])
        history.append({'content': message or f'Action: {intent}', 'isUser': True, 'timestamp': datetime.now().isoformat()})

        # If a Quick Action intent is explicitly provided, use predefined handlers
        if intent:
            logger.info(f"Routing by explicit intent: {intent}")
            if intent == 'job_application':
                resp = {
                    'response': (
                        "Great! You can apply for jobs or internships at AmLI.\n\n"
                        "Application Steps:\n1) Fill the form\n2) Upload resume\n3) Review\n4) Interview\n\n"
                        "Apply here: https://docs.google.com/forms/d/e/1FAIpQLSe7kN4IqtYOvWmBBrgBzuu7Kv0oc415UEFPkFN6-6Ezn8XKaA/viewform"
                    ),
                    'timestamp': datetime.now().isoformat(),
                    'type': 'job_form',
                    'form_url': 'https://docs.google.com/forms/d/e/1FAIpQLSe7kN4IqtYOvWmBBrgBzuu7Kv0oc415UEFPkFN6-6Ezn8XKaA/viewform'
                }
            elif intent == 'certificate_search':
                enrollment_no = data.get('enrollment_no')
                if not enrollment_no:
                    resp = {
                        'response': (
                            "To search your certificate/offer letter, please provide your 6-digit Enrollment Number."
                        ),
                        'timestamp': datetime.now().isoformat(),
                        'type': 'request_enrollment'
                    }
                else:
                    resp = {
                        'response': (
                            f"Enrollment {enrollment_no} detected. Please provide your 6-digit password to verify."
                        ),
                        'timestamp': datetime.now().isoformat(),
                        'type': 'request_password',
                        'enrollment_no': enrollment_no
                    }
            elif intent == 'verify_password':
                enrollment_no = (data.get('enrollment_no') or '').strip()
                password = (data.get('password') or '').strip()
                if not enrollment_no or not password:
                    resp = {
                        'response': 'Both enrollment number and password are required.',
                        'timestamp': datetime.now().isoformat(),
                        'type': 'error'
                    }
                else:
                    resp = search_supabase_documents(enrollment_no, password)
            elif intent == 'general':
                resp = handle_amli_info()
            else:
                logger.info("Unknown explicit intent; falling back to AI")
                resp = generate_ai_response(message, session_id, data)
        else:
            # No explicit intent provided => infer from message to support Quick Actions
            logger.info("No intent provided; attempting to infer intent from message")
            expert = AmLIExpert()
            inferred = expert.analyze_user_intent(message)
            primary = inferred.get('primary_intent') or 'general'

            if primary == 'job_application':
                resp = {
                    'response': (
                        "Great! You can apply for jobs or internships at AmLI.\n\n"
                        "Application Steps:\n1) Fill the form\n2) Upload resume\n3) Review\n4) Interview\n\n"
                        "Apply here: https://docs.google.com/forms/d/e/1FAIpQLSe7kN4IqtYOvWmBBrgBzuu7Kv0oc415UEFPkFN6-6Ezn8XKaA/viewform"
                    ),
                    'timestamp': datetime.now().isoformat(),
                    'type': 'job_form',
                    'form_url': 'https://docs.google.com/forms/d/e/1FAIpQLSe7kN4IqtYOvWmBBrgBzuu7Kv0oc415UEFPkFN6-6Ezn8XKaA/viewform'
                }
            elif primary == 'certificate_search':
                enrollment_no = inferred.get('enrollment_no')
                if not enrollment_no:
                    resp = {
                        'response': (
                            "To search your certificate/offer letter, please provide your 6-digit Enrollment Number."
                        ),
                        'timestamp': datetime.now().isoformat(),
                        'type': 'request_enrollment'
                    }
                else:
                    resp = {
                        'response': (
                            f"Enrollment {enrollment_no} detected. Please provide your 6-digit password to verify."
                        ),
                        'timestamp': datetime.now().isoformat(),
                        'type': 'request_password',
                        'enrollment_no': enrollment_no
                    }
            elif primary == 'amli_info':
                # Show AmLI information only when explicitly asked
                resp = handle_amli_info()
            else:
                # Fallback to AI for other free-form queries
                logger.info("Inferred intent not a Quick Action; invoking AI")
                resp = generate_ai_response(message, session_id, data)

        # add assistant reply to history
        conversation_history[session_id].append({ 'content': resp['response'], 'isUser': False, 'timestamp': resp['timestamp'] })
        # limit history
        if len(conversation_history[session_id]) > 20:
            conversation_history[session_id] = conversation_history[session_id][-20:]

        return jsonify(resp)
    except Exception as e:
        logger.error(f'Chat error: {e}')
        return jsonify({
            'error': 'An error occurred while processing your request.',
            'response': 'I encountered an error. Please try again in a moment.',
            'timestamp': datetime.now().isoformat(),
            'type': 'error'
        }), 500

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        f = request.files['file']
        if f.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        content = f.read()
        if len(content) > 10 * 1024 * 1024:
            return jsonify({'error': 'File size must be less than 10MB'}), 400
        file_type = request.form.get('type', 'document')
        user_message = request.form.get('message', '')
        if os.path.splitext((f.filename or '').lower())[1] in {'.jpg','.jpeg','.png','.gif','.bmp','.tiff','.webp','.svg'}:
            analysis = analyze_image_with_gemini(content, f.filename, user_message)
        else:
            text = extract_text_from_file(content, f.filename)
            analysis = analyze_document_with_gemini(text, f.filename, user_message)
        return jsonify({
            'message': 'File processed successfully',
            'analysis': analysis,
            'filename': f.filename,
            'type': file_type,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f'Upload error: {e}')
        return jsonify({'error': f'Error processing file: {e}'}), 500

@app.route('/download/<enrollment_no>', methods=['GET'])
def download(enrollment_no):
    try:
        return jsonify({
            'message': f'Download initiated for enrollment {enrollment_no}',
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f'Download error: {e}')
        return jsonify({'error': str(e)}), 500

# ----------------------------------------------------------------------------
# Document/Image analysis helpers (use current model if present)
# ----------------------------------------------------------------------------

def extract_text_from_file(content: bytes, filename: str) -> str:
    try:
        text = content.decode('utf-8', errors='ignore')
        if text.strip():
            return text
    except Exception:
        pass
    for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
        try:
            text = content.decode(enc, errors='ignore')
            if text.strip():
                return text
        except Exception:
            continue
    return f'Binary file: {filename} - Size: {len(content)} bytes'


def analyze_document_with_gemini(text_content: str, filename: str, user_message: str) -> str:
    if not model:
        return 'Document analysis is unavailable right now.'
    try:
        prompt = (
            f"Analyze this document and summarize key points.\n"
            f"File: {filename}\nUser Query: {user_message}\n\n"
            f"Content:\n{text_content[:3000]}"
        )
        res = model.generate_content(prompt)
        return (getattr(res, 'text', '') or '').strip() or 'No analysis available.'
    except Exception as e:
        logger.error(f'Document analysis error: {e}')
        return f'Document analysis error: {e}'


def analyze_image_with_gemini(content: bytes, filename: str, user_message: str) -> str:
    if not model:
        return 'Image analysis is unavailable right now.'
    try:
        part = { 'mime_type': get_mime_type(filename), 'data': content }
        prompt = (f"Analyze this image. File: {filename}\nUser Query: {user_message}")
        res = model.generate_content([prompt, part])
        return (getattr(res, 'text', '') or '').strip() or 'No analysis available.'
    except Exception as e:
        logger.error(f'Image analysis error: {e}')
        return f'Image analysis error: {e}'


def get_mime_type(filename: str) -> str:
    ext = os.path.splitext((filename or '').lower())[1]
    return {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif',
        '.bmp': 'image/bmp', '.tiff': 'image/tiff', '.webp': 'image/webp', '.svg': 'image/svg+xml'
    }.get(ext, 'application/octet-stream')

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    logger.info('Starting AmLI Assistant...')
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        logger.warning('Supabase not configured; document search limited')
    if not model:
        logger.warning('Gemini model not available; general AI responses limited')
    app.run(debug=True, host='0.0.0.0', port=5000)