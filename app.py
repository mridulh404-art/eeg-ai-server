from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import traceback
import requests
import json

app = Flask(__name__)
CORS(app)

# Groq is FREE - no credit card needed!
# Get your free API key from: https://console.groq.com
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', 'gsk_free_key_placeholder')
USE_AI = os.environ.get('USE_AI', 'true').lower() == 'true'

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'service': 'EEG AI Analysis Server',
        'version': '2.0.0',
        'ai_provider': 'Groq (FREE)',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'ai_configured': bool(GROQ_API_KEY and GROQ_API_KEY != 'gsk_free_key_placeholder'),
        'ai_enabled': USE_AI,
        'ai_provider': 'Groq'
    })

@app.route('/api/test')
def api_test():
    return jsonify({
        'status': 'ok',
        'groq_api_key_set': bool(GROQ_API_KEY and GROQ_API_KEY != 'gsk_free_key_placeholder'),
        'use_ai': USE_AI,
        'ai_provider': 'Groq (FREE)',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_eeg():
    """Analyze EEG data using FREE Groq AI"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        attention_history = data.get('attentionHistory', [])
        meditation_history = data.get('meditationHistory', [])
        blink_history = data.get('blinkHistory', [])
        
        if not attention_history or not meditation_history:
            return jsonify({'error': 'Missing EEG data'}), 400
        
        # Use Groq AI if configured, otherwise local analysis
        if USE_AI and GROQ_API_KEY and GROQ_API_KEY != 'gsk_free_key_placeholder':
            result = analyze_with_groq(attention_history, meditation_history, blink_history)
        else:
            result = analyze_local(attention_history, meditation_history, blink_history)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Analysis error: {e}")
        traceback.print_exc()
        # Always fallback to local
        avg_att = sum(attention_history) / len(attention_history)
        avg_med = sum(meditation_history) / len(meditation_history)
        avg_blink = sum(blink_history) / len(blink_history) if blink_history else 0
        return jsonify(analyze_local_simple(avg_att, avg_med, avg_blink))

@app.route('/api/question', methods=['POST'])
def ask_question():
    """Answer questions using FREE Groq AI"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Use Groq AI if configured
        if USE_AI and GROQ_API_KEY and GROQ_API_KEY != 'gsk_free_key_placeholder':
            answer = answer_with_groq(question)
        else:
            answer = answer_local(question)
        
        return jsonify({'answer': answer})
        
    except Exception as e:
        print(f"Question error: {e}")
        traceback.print_exc()
        return jsonify({'answer': answer_local(question)})

def analyze_with_groq(attention_history, meditation_history, blink_history):
    """Analyze using FREE Groq AI (llama-3.3-70b)"""
    try:
        avg_attention = sum(attention_history) / len(attention_history)
        avg_meditation = sum(meditation_history) / len(meditation_history)
        avg_blink = sum(blink_history) / len(blink_history) if blink_history else 0
        
        prompt = f"""You are an EEG brainwave analysis expert. Analyze this data and provide insights:

EEG Data Summary:
- Average Attention: {int(avg_attention)}%
- Average Meditation: {int(avg_meditation)}%
- Average Blink Rate: {int(avg_blink)}%
- Attention Range: {min(attention_history)}-{max(attention_history)}%
- Meditation Range: {min(meditation_history)}-{max(meditation_history)}%
- Data Points: {len(attention_history)} seconds

Provide your analysis in EXACTLY this format:

Mental State: [Choose ONE: Stressed/Relaxed/Happy/Sad/Focused/Tired/Neutral]
Analysis: [2-3 sentences explaining the brainwave patterns and what they mean]
Recommendation: [One specific actionable recommendation to improve mental state]

Be supportive and specific. Focus on practical insights."""

        response = call_groq_api(prompt)
        
        # Parse response
        lines = response.strip().split('\n')
        mental_state = "Neutral"
        analysis = ""
        recommendation = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith("Mental State:"):
                mental_state = line.replace("Mental State:", "").strip()
            elif line.startswith("Analysis:"):
                analysis = line.replace("Analysis:", "").strip()
            elif line.startswith("Recommendation:"):
                recommendation = line.replace("Recommendation:", "").strip()
        
        # If parsing failed, extract from full response
        if not analysis:
            analysis = response[:250]
        if not recommendation:
            recommendation = "Continue monitoring your brainwaves regularly."
        
        stress_level = calculate_stress_level(avg_attention, avg_meditation)
        
        return {
            'mentalState': mental_state,
            'analysis': analysis,
            'recommendation': recommendation,
            'stressLevel': stress_level
        }
        
    except Exception as e:
        print(f"Groq AI error: {e}")
        traceback.print_exc()
        # Fallback to local
        avg_att = sum(attention_history) / len(attention_history)
        avg_med = sum(meditation_history) / len(meditation_history)
        avg_blink = sum(blink_history) / len(blink_history) if blink_history else 0
        return analyze_local_simple(avg_att, avg_med, avg_blink)

def answer_with_groq(question):
    """Answer questions using FREE Groq AI"""
    try:
        prompt = f"""You are a helpful EEG brain-computer interface assistant. 

User question: {question}

Provide a brief, friendly, and informative answer in 2-3 sentences. Be supportive and practical."""

        return call_groq_api(prompt)
        
    except Exception as e:
        print(f"Groq question error: {e}")
        return answer_local(question)

def call_groq_api(prompt):
    """Call Groq API - FREE and FAST!"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",  # FREE model!
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    print(f"Calling Groq API...")
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    print(f"Groq response status: {response.status_code}")
    
    if response.status_code != 200:
        error_text = response.text
        print(f"Groq API error: {error_text}")
        raise Exception(f"Groq API error ({response.status_code}): {error_text}")
    
    result = response.json()
    return result['choices'][0]['message']['content']

def analyze_local(attention_history, meditation_history, blink_history):
    """Smart local analysis (fallback)"""
    avg_attention = sum(attention_history) / len(attention_history)
    avg_meditation = sum(meditation_history) / len(meditation_history)
    avg_blink = sum(blink_history) / len(blink_history) if blink_history else 0
    
    att_variance = calculate_variance(attention_history)
    
    if avg_attention > 70 and avg_meditation < 40:
        mental_state = "Stressed"
        analysis = f"Your attention is very high ({int(avg_attention)}%) while meditation is low ({int(avg_meditation)}%). This indicates mental stress or intense focus without relaxation. Your mind is working hard but needs rest."
        recommendation = "Take a 5-10 minute break. Try deep breathing: inhale for 4 seconds, hold for 4, exhale for 4. This reduces stress while maintaining alertness."
        
    elif avg_attention < 40 and avg_meditation > 70:
        mental_state = "Relaxed"
        analysis = f"High meditation ({int(avg_meditation)}%) with lower attention ({int(avg_attention)}%). You're in a deeply relaxed, calm state - perfect for stress relief and mindfulness."
        recommendation = "Great relaxation! To shift toward focus, gently increase activity. To maintain calm, continue with mindful breathing or meditation."
        
    elif avg_attention > 60 and avg_meditation > 60:
        mental_state = "Focused"
        analysis = f"Excellent balance! Both attention ({int(avg_attention)}%) and meditation ({int(avg_meditation)}%) are high. This is the optimal 'flow state' - focused yet relaxed."
        recommendation = "You're in peak mental performance! Maintain this by staying on task. Take 5-minute breaks every 25-30 minutes to sustain flow."
        
    elif avg_attention < 30 and avg_meditation < 30:
        mental_state = "Tired"
        analysis = f"Both attention ({int(avg_attention)}%) and meditation ({int(avg_meditation)}%) are low, indicating mental fatigue. Your brain needs rest or stimulation."
        recommendation = "Take a 15-20 minute power nap, get fresh air, or do light exercise. Stay hydrated and eat a healthy snack to boost energy."
        
    else:
        mental_state = "Neutral"
        analysis = f"Balanced neutral state. Attention: {int(avg_attention)}%, Meditation: {int(avg_meditation)}%. Neither highly focused nor deeply relaxed - a flexible middle ground."
        recommendation = "You can shift toward focus (tackle a challenging task) or relaxation (take a mindful break) as needed. Stay flexible!"
    
    stress_level = calculate_stress_level(avg_attention, avg_meditation)
    
    return {
        'mentalState': mental_state,
        'analysis': analysis,
        'recommendation': recommendation,
        'stressLevel': stress_level
    }

def analyze_local_simple(avg_attention, avg_meditation, avg_blink):
    """Simplified local analysis"""
    if avg_attention > 70 and avg_meditation < 40:
        mental_state = "Stressed"
        analysis = "High attention, low meditation indicates stress."
        recommendation = "Take a break and practice deep breathing."
    elif avg_attention < 40 and avg_meditation > 70:
        mental_state = "Relaxed"
        analysis = "High meditation shows a relaxed state."
        recommendation = "Maintain this calm or gently increase focus."
    elif avg_attention > 60 and avg_meditation > 60:
        mental_state = "Focused"
        analysis = "Balanced high levels - optimal flow state."
        recommendation = "Keep going! Take breaks every 25-30 minutes."
    elif avg_attention < 30 and avg_meditation < 30:
        mental_state = "Tired"
        analysis = "Low levels indicate fatigue."
        recommendation = "Rest or light exercise needed."
    else:
        mental_state = "Neutral"
        analysis = "Balanced neutral state."
        recommendation = "Shift to focus or relaxation as needed."
    
    stress_level = calculate_stress_level(avg_attention, avg_meditation)
    
    return {
        'mentalState': mental_state,
        'analysis': analysis,
        'recommendation': recommendation,
        'stressLevel': stress_level
    }

def answer_local(question):
    """Local knowledge base"""
    question = question.lower()
    
    if any(word in question for word in ['hi', 'hello', 'hey']):
        return "Hello! I'm your EEG assistant. I can help you understand brainwaves, stress levels, focus, and how to use this app. What would you like to know?"
    
    if any(word in question for word in ['attention', 'focus']):
        return "Attention measures your mental focus (0-100%). Higher values = better concentration. It reflects beta wave activity. Track it to improve focus during work or study!"
    
    if any(word in question for word in ['meditation', 'calm', 'relax']):
        return "Meditation measures mental calmness (0-100%). Higher = more relaxed. Reflects alpha waves. Great for stress monitoring and mindfulness practice!"
    
    if any(word in question for word in ['stress', 'stressed']):
        return "Stress is calculated from attention/meditation balance. High attention + low meditation = high stress. Reduce it with breaks, breathing exercises, and regular monitoring!"
    
    if any(word in question for word in ['blink', 'eye']):
        return "Blink strength (0-100%) measures eye blink intensity. Use strong blinks for control commands - a natural way to interact with devices!"
    
    if any(word in question for word in ['how', 'use', 'work']):
        return "Wear the EEG headset and this app reads your brainwaves in real-time. It analyzes mental state, tracks focus, monitors stress, and lets you control devices. Explore the features!"
    
    if any(word in question for word in ['improve', 'better']):
        return "To improve: Practice 10-15 mins daily, stay relaxed, recalibrate weekly, work in quiet spaces, stay hydrated. Your brain gets stronger with practice!"
    
    return "That's interesting! I can tell you about: attention, meditation, stress, blinks, app usage, or mental training. What would you like to know?"

def calculate_variance(data):
    """Calculate standard deviation"""
    if not data or len(data) < 2:
        return 0
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    return variance ** 0.5

def calculate_stress_level(avg_attention, avg_meditation):
    """Calculate stress level (0-100)"""
    if avg_attention > 70 and avg_meditation < 40:
        return 75
    elif avg_attention < 40 and avg_meditation > 70:
        return 25
    elif avg_attention > 60 and avg_meditation > 60:
        return 30
    else:
        return 50

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
```
