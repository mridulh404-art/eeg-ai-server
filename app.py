"""
EEG AI Analysis Server
Free cloud-deployable Flask backend for EEG brainwave analysis
Supports both OpenAI GPT and Anthropic Claude APIs
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for Android app

# ✅ API Configuration - Set via environment variables
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
USE_ANTHROPIC = os.environ.get('USE_ANTHROPIC', 'true').lower() == 'true'

# API endpoints
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


@app.route('/', methods=['GET'])
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'EEG AI Analysis Server',
        'version': '1.0',
        'timestamp': datetime.now().isoformat(),
        'ai_provider': 'Anthropic Claude' if USE_ANTHROPIC else 'OpenAI GPT'
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_eeg_data():
    """
    Analyze EEG brainwave data
    
    Expected JSON:
    {
        "attentionHistory": [int, int, ...],
        "meditationHistory": [int, int, ...],
        "blinkHistory": [int, int, ...]
    }
    
    Returns:
    {
        "success": true,
        "mentalState": "Focused",
        "analysis": "...",
        "recommendation": "...",
        "stressLevel": 50
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract EEG data
        attention_history = data.get('attentionHistory', [])
        meditation_history = data.get('meditationHistory', [])
        blink_history = data.get('blinkHistory', [])
        
        # Validate data
        if not attention_history or not meditation_history or not blink_history:
            return jsonify({
                'success': False,
                'error': 'Missing EEG data (attentionHistory, meditationHistory, or blinkHistory)'
            }), 400
        
        # Calculate averages
        avg_attention = sum(attention_history) / len(attention_history)
        avg_meditation = sum(meditation_history) / len(meditation_history)
        avg_blink = sum(blink_history) / len(blink_history)
        
        # Create analysis prompt
        prompt = f"""Analyze this EEG brainwave data collected over the last minute and provide insights:

Average Attention: {int(avg_attention)}%
Average Meditation: {int(avg_meditation)}%
Average Blink Rate: {int(avg_blink)}%

Attention Range: {min(attention_history)}-{max(attention_history)}%
Meditation Range: {min(meditation_history)}-{max(meditation_history)}%

Number of data points: {len(attention_history)}

Please provide:
1. Current mental state (choose ONE: Stressed, Relaxed, Happy, Sad, Focused, Tired, or Neutral)
2. Brief analysis (2-3 sentences explaining the brainwave patterns)
3. One actionable recommendation for the user

Keep the response concise, supportive, and helpful."""
        
        # Call AI API
        if USE_ANTHROPIC and ANTHROPIC_API_KEY:
            ai_response = call_claude_api(prompt)
        elif OPENAI_API_KEY:
            ai_response = call_openai_api(prompt)
        else:
            # Fallback to rule-based analysis
            return jsonify(analyze_offline(attention_history, meditation_history, blink_history))
        
        # Parse AI response
        result = parse_ai_response(ai_response, avg_attention, avg_meditation)
        
        return jsonify({
            'success': True,
            **result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/question', methods=['POST'])
def ask_question():
    """
    Ask AI assistant a question
    
    Expected JSON:
    {
        "question": "What is attention?"
    }
    
    Returns:
    {
        "success": true,
        "answer": "Attention measures..."
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'No question provided'
            }), 400
        
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'Question cannot be empty'
            }), 400
        
        # Create prompt
        prompt = f"""You are a helpful assistant for an EEG brain-computer interface app.
User question: {question}

Provide a brief, friendly answer (2-3 sentences max)."""
        
        # Call AI API
        if USE_ANTHROPIC and ANTHROPIC_API_KEY:
            answer = call_claude_api(prompt)
        elif OPENAI_API_KEY:
            answer = call_openai_api(prompt)
        else:
            # Fallback
            answer = answer_offline(question)
        
        return jsonify({
            'success': True,
            'answer': answer
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def call_claude_api(prompt):
    """Call Anthropic Claude API"""
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
    }
    
    payload = {
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 1000,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }
    
    response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    return data['content'][0]['text']


def call_openai_api(prompt):
    """Call OpenAI GPT API"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }
    
    payload = {
        'model': 'gpt-4',
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'max_tokens': 500,
        'temperature': 0.7
    }
    
    response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    return data['choices'][0]['message']['content']


def parse_ai_response(response, avg_attention, avg_meditation):
    """Parse AI response to extract mental state, analysis, and recommendation"""
    
    # Detect mental state from response
    response_lower = response.lower()
    mental_state = "Neutral"
    
    if "stressed" in response_lower or "stress" in response_lower:
        mental_state = "Stressed"
    elif "relaxed" in response_lower or "calm" in response_lower:
        mental_state = "Relaxed"
    elif "happy" in response_lower or "joyful" in response_lower:
        mental_state = "Happy"
    elif "sad" in response_lower or "down" in response_lower:
        mental_state = "Sad"
    elif "focused" in response_lower or "concentration" in response_lower:
        mental_state = "Focused"
    elif "tired" in response_lower or "fatigue" in response_lower:
        mental_state = "Tired"
    
    # Calculate stress level
    stress_level = 50
    if avg_attention > 70 and avg_meditation < 40:
        stress_level = 75
    elif avg_attention < 40 and avg_meditation > 70:
        stress_level = 25
    elif avg_attention > 60 and avg_meditation > 60:
        stress_level = 30
    
    # Split response into lines
    lines = [line.strip() for line in response.split('\n') if line.strip()]
    
    # Try to extract analysis and recommendation
    analysis = ""
    recommendation = ""
    
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in ['analysis:', 'mental state:', 'patterns:']):
            # Next few lines are analysis
            analysis = ' '.join(lines[i:min(i+3, len(lines))])
        elif any(keyword in line.lower() for keyword in ['recommendation:', 'suggest:', 'try:']):
            # Rest is recommendation
            recommendation = ' '.join(lines[i:])
            break
    
    # Fallback: use whole response as analysis
    if not analysis:
        analysis = ' '.join(lines[:3]) if len(lines) >= 3 else response
    
    if not recommendation:
        recommendation = lines[-1] if lines else "Keep up the good work!"
    
    return {
        'mentalState': mental_state,
        'analysis': analysis.replace('Analysis:', '').replace('Mental state:', '').strip(),
        'recommendation': recommendation.replace('Recommendation:', '').replace('Suggest:', '').strip(),
        'stressLevel': stress_level
    }


def analyze_offline(attention_history, meditation_history, blink_history):
    """Offline rule-based analysis when no API key is available"""
    avg_attention = sum(attention_history) / len(attention_history)
    avg_meditation = sum(meditation_history) / len(meditation_history)
    avg_blink = sum(blink_history) / len(blink_history)
    
    att_variance = max(attention_history) - min(attention_history)
    med_variance = max(meditation_history) - min(meditation_history)
    
    # Determine mental state
    if avg_attention > 70 and avg_meditation < 40:
        mental_state = "Focused"
    elif avg_attention < 40 and avg_meditation > 70:
        mental_state = "Relaxed"
    elif avg_attention > 60 and avg_meditation > 60:
        mental_state = "Happy"
    elif avg_attention < 40 and avg_meditation < 40:
        mental_state = "Tired"
    elif att_variance > 30 or med_variance > 30:
        mental_state = "Stressed"
    else:
        mental_state = "Neutral"
    
    # Calculate stress level
    if avg_attention > 70 and avg_meditation < 40:
        stress_level = 70
    elif avg_attention < 40 and avg_meditation > 70:
        stress_level = 20
    elif att_variance > 40 or med_variance > 40:
        stress_level = 85
    elif avg_attention > 60 and avg_meditation > 60:
        stress_level = 25
    else:
        stress_level = 50
    
    # Generate analysis
    analyses = {
        "Focused": f"Your attention levels are high ({int(avg_attention)}%) while meditation is lower ({int(avg_meditation)}%). You're in a concentrated state, actively engaging with tasks.",
        "Relaxed": f"Your meditation levels are high ({int(avg_meditation)}%) with lower attention ({int(avg_attention)}%). You're in a calm, peaceful state - great for recovery.",
        "Happy": f"Both attention ({int(avg_attention)}%) and meditation ({int(avg_meditation)}%) are balanced and high. You're in an optimal mental state!",
        "Tired": f"Both attention ({int(avg_attention)}%) and meditation ({int(avg_meditation)}%) are low. Your brain may be fatigued and needs rest.",
        "Stressed": f"Your brainwave patterns show high variability (attention range: {min(attention_history)}-{max(attention_history)}%). This indicates mental stress or distraction.",
        "Neutral": f"Your brainwave patterns are relatively stable. Attention at {int(avg_attention)}% and meditation at {int(avg_meditation)}%."
    }
    
    # Generate recommendation
    recommendations = {
        "Focused": "Take short breaks every 25 minutes to prevent burnout. Try the 20-20-20 rule: look at something 20 feet away for 20 seconds.",
        "Relaxed": "Great job relaxing! If you need to focus, try deep breathing exercises or light physical activity to increase alertness.",
        "Happy": "Excellent mental state! Maintain this balance with regular breaks, hydration, and mindful breathing.",
        "Tired": "Consider taking a 15-20 minute power nap, getting fresh air, or doing light stretching to re-energize.",
        "Stressed": "Try 5 minutes of deep breathing: inhale for 4 counts, hold for 4, exhale for 4. Reduce multitasking if possible.",
        "Neutral": "Stay consistent with your current routine. Take breaks when needed and stay hydrated."
    }
    
    return {
        'success': True,
        'mentalState': f"{mental_state} (Offline Mode)",
        'analysis': analyses[mental_state],
        'recommendation': recommendations[mental_state],
        'stressLevel': stress_level
    }


def answer_offline(question):
    """Offline question answering"""
    q_lower = question.lower()
    
    if ("how" in q_lower and ("work" in q_lower or "use" in q_lower)):
        return "This app reads your EEG brainwaves (attention, meditation, blink) and uses them to control devices. Focus or relax to trigger different actions!"
    elif "attention" in q_lower:
        return "Attention measures your mental focus level. Higher values (60-100%) mean you're concentrating well. Try focusing on a single task to increase it."
    elif "meditation" in q_lower:
        return "Meditation measures your relaxation level. Higher values (60-100%) mean you're calm. Try deep breathing or closing your eyes to increase it."
    elif "blink" in q_lower:
        return "Blink strength measures eye muscle activity. Strong blinks can be used as a control signal. Try blinking deliberately to test it."
    elif "stress" in q_lower:
        return "Stress is detected through erratic brainwave patterns. Reduce stress with: deep breathing, regular breaks, meditation, or light exercise."
    elif "hi" in q_lower or "hello" in q_lower:
        return "Hello! I'm your EEG assistant. I can help you understand your brainwaves and how to use this app. What would you like to know?"
    else:
        return "I'm working in offline mode. I can help with basic questions about EEG, attention, meditation, blinks, and app usage. What would you like to know?"


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
