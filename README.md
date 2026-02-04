# EEG AI Analysis Server

Cloud-based AI analysis backend for EEG brainwave monitoring Android app.

## Features

- ✅ Analyzes 1-minute EEG data (attention, meditation, blink patterns)
- ✅ AI-powered mental state detection (Stressed, Happy, Focused, Relaxed, Tired, Sad, Neutral)
- ✅ Personalized recommendations based on brainwave patterns
- ✅ Question answering about EEG and brainwaves
- ✅ Supports both Anthropic Claude and OpenAI GPT
- ✅ Offline fallback with rule-based analysis
- ✅ CORS enabled for Android app access
- ✅ Free tier deployable (Render, Railway, Heroku)

## API Endpoints

### GET /
Health check endpoint
```json
{
  "status": "ok",
  "service": "EEG AI Analysis Server",
  "version": "1.0",
  "ai_provider": "Anthropic Claude"
}
```

### POST /api/analyze
Analyze EEG data

**Request:**
```json
{
  "attentionHistory": [60, 65, 70, 75, 80, ...],
  "meditationHistory": [40, 45, 50, 55, 60, ...],
  "blinkHistory": [20, 25, 30, 35, 40, ...]
}
```

**Response:**
```json
{
  "success": true,
  "mentalState": "Focused",
  "analysis": "Your attention levels are high (72%) while meditation is lower (48%). You're in a concentrated state...",
  "recommendation": "Take short breaks every 25 minutes to prevent burnout...",
  "stressLevel": 70
}
```

### POST /api/question
Ask AI assistant a question

**Request:**
```json
{
  "question": "What is attention?"
}
```

**Response:**
```json
{
  "success": true,
  "answer": "Attention measures your mental focus level. Higher values (60-100%) mean you're concentrating well..."
}
```

## Environment Variables

Required:
- `ANTHROPIC_API_KEY` - Your Anthropic API key (OR)
- `OPENAI_API_KEY` - Your OpenAI API key
- `USE_ANTHROPIC` - Set to `true` for Claude, `false` for GPT (default: `true`)

Optional:
- `PORT` - Server port (default: 5000)

## Deployment

See `DEPLOYMENT_GUIDE.md` for complete instructions.

Quick deploy to Render.com:
1. Fork this repository
2. Go to https://render.com
3. New Web Service → Connect repository
4. Add environment variables
5. Deploy!

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your-key-here"
export USE_ANTHROPIC="true"

# Run server
python app.py
```

Server will run on http://localhost:5000

## Tech Stack

- **Flask** - Web framework
- **Flask-CORS** - CORS handling
- **Requests** - HTTP client
- **Gunicorn** - Production server

## License

MIT License - Feel free to use and modify!

## Support

For issues and questions, see `DEPLOYMENT_GUIDE.md` troubleshooting section.
