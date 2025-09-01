# 🤖 Humanoid AI Assistant

A beautiful, modern chatbot web application powered by Google's Gemini AI API. This Flask-based application provides a humanoid AI assistant that can answer any questions with a sleek, responsive interface.

## ✨ Features

- 🤖 **Gemini AI Integration**: Powered by Google's latest Gemini Pro model
- 💬 **Real-time Chat**: Instant responses with typing indicators
- 🎨 **Modern UI**: Beautiful, responsive design with gradient backgrounds
- 📱 **Mobile Friendly**: Works perfectly on all devices
- 💾 **Conversation History**: Keeps track of your chat history
- 🗑️ **Clear History**: Option to clear conversation history
- ⚡ **Fast & Responsive**: Optimized for smooth user experience

## 🛠️ Tech Stack

- **Backend**: Python Flask
- **AI Model**: Google Gemini Pro API
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Custom CSS with gradients and animations
- **Testing**: Python unittest framework
- **Dependencies**: See `requirements.txt`

## 📸 Screenshots

*[Add screenshots of your application here]*

## 🎥 Demo

*[Add a GIF or video demo of your application here]*

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Gemini API key from Google AI Studio

### Installation

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Get your Gemini API key**:
   - Go to [Google AI Studio](https://aistudio.google.com/)
   - Create a new API key
   - Copy the API key

4. **Set up your API key**:
   
   **Option 1: Environment Variable (Recommended)**
   ```bash
   # Windows
   set GEMINI_API_KEY=your_api_key_here
   
   # macOS/Linux
   export GEMINI_API_KEY=your_api_key_here
   ```
   
   **Option 2: Create a .env file**
   ```bash
   # Create a .env file in the project directory
   echo GEMINI_API_KEY=your_api_key_here > .env
   ```

5. **Run the application**:
   ```bash
   python bot.py
   ```

6. **Open your browser**:
   Navigate to `http://localhost:5000`

## 📁 Project Structure

```
humanoid-bot/
├── bot.py              # Main Flask application
├── templates/
│   └── index.html      # Web interface
├── requirements.txt    # Python dependencies
├── test.py            # Unit tests for the application
└── README.md          # This file
```

## 🔧 Configuration

### Environment Variables

- `GEMINI_API_KEY`: Your Gemini API key (required)

### Customization

You can customize the AI's personality by modifying the context in `bot.py`:

```python
context = f"""You are a helpful humanoid AI assistant. You should:
1. Be friendly and conversational
2. Provide accurate and helpful information
3. Use a natural, human-like tone
4. Ask follow-up questions when appropriate
5. Be empathetic and understanding

User: {user_message}
Assistant:"""
```

## 🌐 API Endpoints

- `GET /`: Main chat interface
- `POST /chat`: Send a message and get AI response
- `GET /history`: Get conversation history
- `POST /clear`: Clear conversation history

## 🎨 UI Features

- **Gradient Backgrounds**: Beautiful purple-blue gradients
- **Message Bubbles**: Distinct user and AI message styles
- **Typing Indicators**: Shows when AI is thinking
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Smooth Animations**: Fade-in effects and hover animations
- **Status Indicator**: Shows AI availability with pulsing dot

## 📋 Features in Detail

### 🤖 AI Capabilities
- **Natural Language Processing**: Understands and responds to natural conversation
- **Context Awareness**: Remembers conversation history for coherent responses
- **Multi-turn Conversations**: Handles complex multi-step discussions
- **Knowledge Base**: Access to vast amounts of information across various domains

### 💬 Chat Interface
- **Real-time Messaging**: Instant message delivery and response
- **Message Persistence**: Conversations are saved during the session
- **Clear Functionality**: Easy way to start fresh conversations
- **Error Handling**: Graceful handling of API errors and network issues

### 🎨 User Experience
- **Modern Design**: Clean, professional interface with modern aesthetics
- **Responsive Layout**: Adapts seamlessly to different screen sizes
- **Accessibility**: Designed with accessibility best practices
- **Performance**: Optimized for fast loading and smooth interactions

## 🔒 Security Notes

- Never commit your API key to version control
- Use environment variables for sensitive data
- The application runs on localhost by default

## 🧪 Testing

The project includes unit tests in `test.py`. To run the tests:

```bash
python test.py
```

The tests cover:
- API key validation
- Message processing
- Error handling
- Response formatting

## 🐛 Troubleshooting

### Common Issues

1. **API Key Error**: Make sure your Gemini API key is set correctly
2. **Import Error**: Ensure all dependencies are installed with `pip install -r requirements.txt`
3. **Port Already in Use**: Change the port in `bot.py` or kill the process using port 5000

### Error Messages

- `Error: API key not found`: Set your `GEMINI_API_KEY` environment variable
- `Error: Invalid API key`: Check your API key on Google AI Studio
- `Error: Rate limit exceeded`: Wait a moment and try again

## 📝 Usage Examples

The AI assistant can help with:
- General knowledge questions
- Problem-solving
- Creative writing
- Code explanations
- Math problems
- Language translation
- And much more!

## 🤝 Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Improving the UI/UX
- Adding new AI capabilities
- Writing additional tests

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Google AI for providing the Gemini API
- Flask team for the excellent web framework
- The open-source community for inspiration and tools


# 🧠 Memory System Integration Guide

This guide explains how the memory system works with your Humanoid AI Assistant and how to use it effectively.

## 📋 Overview

The memory system provides:
- **Persistent Storage**: All conversations are saved in SQLite database
- **Context Awareness**: AI remembers previous conversations
- **User Preferences**: Store user settings and preferences
- **Session Management**: Multiple conversation sessions
- **Smart Responses**: AI uses conversation history for better responses

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python bot.py
```

### 3. Test the Memory System
```bash
python test_memory.py
```

## 🔧 How It Works

### Database Structure
The system creates a SQLite database (`chatbot_memory.db`) with these tables:

- **conversations**: Stores conversation sessions
- **messages**: Stores individual messages
- **user_preferences**: Stores user settings
- **context_memory**: Stores context information

### API Endpoints

#### Chat Endpoint
```http
POST /chat
Content-Type: application/json

{
    "message": "Your message here",
    "session_id": "optional_session_id"
}
```

#### Session Management
```http
GET /sessions                    # Get all sessions
GET /session/<session_id>        # Get specific session messages
DELETE /session/<session_id>     # Delete a session
```

#### User Preferences
```http
POST /user/preferences           # Save user preferences
GET /user/preferences/<user_id>  # Get user preferences
```

#### Context Memory
```http
POST /context/<session_id>       # Save context
GET /context/<session_id>        # Get context
```

## 💡 Usage Examples

### 1. Basic Conversation with Memory
```python
import requests

# Start a conversation
response = requests.post('http://localhost:5000/chat', json={
    'message': 'Hello! I want to learn Python',
    'session_id': 'python_learning_001'
})

# Continue the conversation (AI will remember previous context)
response2 = requests.post('http://localhost:5000/chat', json={
    'message': 'What are the basic data types?',
    'session_id': 'python_learning_001'  # Same session ID
})
```

### 2. Save User Preferences
```python
# Save user preferences
requests.post('http://localhost:5000/user/preferences', json={
    'user_id': 'user_123',
    'name': 'John Doe',
    'language': 'en',
    'voice_preference': 'female',
    'theme_preference': 'dark'
})

# Get user preferences
prefs = requests.get('http://localhost:5000/user/preferences/user_123').json()
```

### 3. Save Context Information
```python
# Save context for a session
requests.post('http://localhost:5000/context/python_learning_001', json={
    'key': 'topic',
    'value': 'Python programming'
})

requests.post('http://localhost:5000/context/python_learning_001', json={
    'key': 'user_level',
    'value': 'beginner'
})
```

### 4. Get Conversation History
```python
# Get all sessions
sessions = requests.get('http://localhost:5000/sessions').json()

# Get messages for a specific session
messages = requests.get('http://localhost:5000/session/python_learning_001').json()
```

## 🎯 Frontend Integration

The frontend automatically:
- Creates new sessions when you start chatting
- Loads existing sessions from the sidebar
- Sends session IDs with each message
- Displays conversation history
- Manages session switching

### Session Flow
1. **New Chat**: Creates new session automatically
2. **Continue Chat**: Uses existing session ID
3. **Switch Sessions**: Loads different conversation
4. **Persistent**: Sessions survive page refresh

## 🔍 Advanced Features

### Context-Aware Responses
The AI now uses conversation history to provide better responses:

```python
# The system automatically builds context like this:
context_prompt = f"""
You are a helpful humanoid AI assistant. 

Previous conversation context:
User: Hello! I want to learn Python
AI: Great! Python is an excellent programming language to start with...
User: What are the basic data types?

Current user message: {user_message}

Guidelines:
- Remember the conversation context above
- Be consistent with previous responses
- Build upon previous explanations
"""
```

### User Personalization
Store and use user preferences:

```python
# Save preferences
preferences = {
    'user_id': 'user_123',
    'name': 'John',
    'language': 'en',
    'voice_preference': 'female',
    'theme_preference': 'dark'
}

# Use in responses
if preferences['language'] == 'es':
    # Respond in Spanish
    pass
```

### Session Management
- **Multiple Sessions**: Users can have multiple conversations
- **Session Titles**: Automatically generated from first message
- **Session Switching**: Easy navigation between conversations
- **Session Deletion**: Remove old conversations

## 🛠️ Customization

### Modify Memory System
Edit `memory_system.py` to:
- Add new database tables
- Implement different storage backends
- Add custom context types
- Extend user preferences

### Custom Context Types
```python
# Save custom context
memory.save_context_memory(session_id, "learning_style", "visual")
memory.save_context_memory(session_id, "difficulty_level", "intermediate")
memory.save_context_memory(session_id, "preferred_topics", "web development")
```

### Extend User Preferences
```python
# Add new preference fields
memory.save_user_preference(
    user_id="user_123",
    name="John",
    language="en",
    voice_preference="female",
    theme_preference="dark",
    # Add custom fields here
    notification_preference="email",
    response_length="detailed"
)
```

## 🔧 Troubleshooting

### Common Issues

1. **Database Not Created**
   ```bash
   # Check if chatbot_memory.db exists
   ls -la chatbot_memory.db
   ```

2. **Import Error**
   ```bash
   # Make sure memory_system.py is in the same directory
   python -c "from memory_system import ChatbotMemory"
   ```

3. **Session Not Loading**
   - Check browser console for errors
   - Verify API endpoints are working
   - Check database permissions

### Debug Mode
```python
# Enable debug logging in bot.py
app.run(debug=True, host='0.0.0.0', port=5000)
```

## 📊 Performance Tips

1. **Limit History**: Use `limit` parameter to control memory usage
2. **Clean Old Sessions**: Regularly delete old conversations
3. **Database Optimization**: Use indexes for large datasets
4. **Caching**: Implement Redis for high-traffic applications

## 🚀 Next Steps

1. **Add Authentication**: User login and session management
2. **Multi-User Support**: Separate databases per user
3. **Analytics**: Track conversation patterns
4. **Export/Import**: Backup and restore conversations
5. **Advanced Context**: Sentiment analysis, topic modeling

## 📝 API Reference

Complete API documentation is available in the code comments. Key endpoints:

- `POST /chat` - Send message and get response
- `GET /sessions` - List all sessions
- `GET /session/<id>` - Get session messages
- `POST /user/preferences` - Save user preferences
- `POST /context/<id>` - Save context information

---

**Happy coding! 🚀**

Your chatbot now has a powerful memory system that makes conversations more intelligent and personalized!
