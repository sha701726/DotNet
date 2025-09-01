# AmLI - Adaptive Monitoring Layered Intelligence Chatbot

An intelligent AI assistant specifically designed to help users access AmLI services including job applications, certificate searches, and offer letter downloads.

## Features

- **Job Application Support**: Direct links to AmLI job/internship application forms
- **Certificate Search**: Search for certificates using enrollment number and password
- **Offer Letter Access**: Find and download offer letters with secure authentication
- **AmLI-Specific AI**: Trained to understand and assist with AmLI services
- **Browser Storage**: All conversations stored locally in browser cache
- **Voice Support**: Text-to-speech functionality for accessibility

## Quick Actions

- **Apply for Job/Internship**: Direct access to application forms
- **Search Certificate**: Find certificates using enrollment number
- **Find Offer Letter**: Access offer letters with secure login
- **AmLI Information**: Get details about AmLI services

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in the root directory with:

```bash
# Google Gemini AI API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

### 2. Install Dependencies

   ```bash
   pip install -r requirements.txt
   ```

### 3. Run the Application

   ```bash
   python bot.py
   ```

The application will be available at `http://localhost:5000`

## Supabase Database Setup

### Required Table Structure

```sql
-- Create a function to search documents
CREATE OR REPLACE FUNCTION search_documents(enrollment_no TEXT, pass_key TEXT)
RETURNS TABLE (
    name TEXT,
    course TEXT,
    status TEXT,
    file_url TEXT,
    enrollment_no TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.name,
        d.course,
        d.status,
        d.file_url,
        d.enrollment_no
    FROM documents d
    WHERE d.enrollment_no = search_documents.enrollment_no 
    AND d.pass_key = search_documents.pass_key;
END;
$$ LANGUAGE plpgsql;
```

### Documents Table

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    enrollment_no TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    course TEXT,
    status TEXT,
    file_url TEXT,
    pass_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Deployment on Render

1. **Connect your GitHub repository**
2. **Set environment variables** in Render dashboard
3. **Build command**: `pip install -r requirements.txt`
4. **Start command**: `python bot.py`
5. **No database setup required** - uses browser storage

## How It Works

1. **User Intent Detection**: AI identifies what service the user needs
2. **Job Applications**: Direct links to Google Forms
3. **Document Search**: Secure enrollment number + password verification
4. **Supabase Integration**: Searches database for documents
5. **Download Options**: Secure file access for verified users

## Security Features

- 6-digit enrollment number validation
- 6-digit password authentication
- Secure Supabase database queries
- No sensitive data stored on server

## Browser Compatibility

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Support

For technical support or questions about AmLI services, please contact the AmLI team.

---

**AmLI - Adaptive Monitoring Layered Intelligence**
*Empowering students and professionals with intelligent service access*
