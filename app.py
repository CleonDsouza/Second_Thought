from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import sqlite3
import json
import re
import requests
import firebase_admin
from firebase_admin import credentials, auth

app = Flask(__name__)
app.secret_key = "second_thought_secret_key_123"
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)


def rule_based_analysis(text):
    lower = text.lower()
    words = lower.split()
    word_count = len(words)

    emotional_keywords = ['feel', 'felt', 'feeling', 'excited', 'worried', 'fear', 'afraid',
                          'happy', 'sad', 'anxious', 'nervous', 'passionate', 'love', 'hate',
                          'scared', 'thrilled', 'upset', 'angry', 'frustrated', 'stressed',
                          'emotional', 'gut', 'heart', 'instinct', 'sense', 'vibe', 'overwhelmed',
                          'hope', 'hopeful', 'dread', 'comfort', 'uncomfortable']

    logical_keywords = ['because', 'therefore', 'thus', 'hence', 'data', 'evidence', 'fact',
                        'research', 'study', 'analysis', 'analyze', 'statistics', 'numbers',
                        'proven', 'demonstrate', 'shows', 'indicates', 'suggests', 'conclude',
                        'reason', 'rationale', 'logical', 'objective', 'measured', 'quantify',
                        'decided', 'decide', 'chosen', 'selected', 'needs', 'requirements',
                        'scalable', 'fast', 'efficient', 'performance', 'reliable', 'technology',
                        'solution', 'approach', 'method', 'system', 'implement', 'architecture',
                        'database', 'api', 'framework', 'platform']

    intellectual_keywords = ['strategy', 'strategic', 'future', 'long-term', 'learning', 'learn',
                             'growth', 'grow', 'insight', 'understand', 'wisdom', 'perspective',
                             'consider', 'contemplate', 'reflect', 'philosophy', 'principle',
                             'framework', 'concept', 'theory', 'develop', 'evolve', 'vision',
                             'planning', 'design', 'architecture', 'thinking', 'thought',
                             'building', 'creating', 'maintain', 'maintainability', 'quality']

    emotional_matches = [w for w in emotional_keywords if w in lower]
    logical_matches = [w for w in logical_keywords if w in lower]
    intellectual_matches = [w for w in intellectual_keywords if w in lower]

    emotional_score = min(100, (len(emotional_matches) * 20) + 10)
    logical_score = min(100, (len(logical_matches) * 12) + 15)
    intellectual_score = min(100, (len(intellectual_matches) * 12) + 15)

    decision_patterns = ['i decided', 'decided to', 'chose to', 'selected', 'picked',
                         'will use', 'going with', 'opted for']
    if any(pattern in lower for pattern in decision_patterns):
        logical_score = min(100, logical_score + 15)

    technical_patterns = ['building', 'application', 'app', 'web', 'software', 'code',
                          'system', 'platform', 'stack', 'technology', 'tool']
    if any(pattern in lower for pattern in technical_patterns):
        intellectual_score = min(100, intellectual_score + 15)

    reasoning_words = ['because', 'since', 'therefore', 'thus', 'so', 'as a result']
    reasoning_count = sum(1 for word in reasoning_words if word in lower)
    logical_score = min(100, logical_score + (reasoning_count * 10))

    if word_count > 30:
        logical_score = min(100, logical_score + 10)
        intellectual_score = min(100, intellectual_score + 10)

    if word_count > 50:
        intellectual_score = min(100, intellectual_score + 10)

    scores = [emotional_score, logical_score, intellectual_score]
    if max(scores) - min(scores) < 15:
        if len(logical_matches) > len(emotional_matches):
            logical_score = min(100, logical_score + 15)
        if len(intellectual_matches) > len(emotional_matches):
            intellectual_score = min(100, intellectual_score + 15)

    biases = []
    if any(w in lower for w in ['everyone', 'everybody', 'all my friends', 'people are', 'most people']):
        biases.append('Bandwagon Effect')
    if any(w in lower for w in ['missing out', 'fomo', 'before it', "don't want to miss", 'left behind']):
        biases.append('FOMO')
    if any(w in lower for w in ['always', 'never', 'every time', 'constantly', 'all the time']):
        biases.append('Overgeneralization')
    if any(w in lower for w in ['proves my', 'confirms', 'i was right', 'i knew', 'validates']):
        biases.append('Confirmation Bias')
    if any(w in lower for w in ['obviously', 'clearly', 'definitely will', 'certain', 'sure thing', 'no doubt']):
        biases.append('Overconfidence')
    if any(w in lower for w in ['recent', 'just heard', 'just saw', 'lately', 'trending']):
        biases.append('Recency Bias')
    if any(w in lower for w in ['status quo', 'keep doing', 'stick with', 'current approach']):
        biases.append('Status Quo Bias')

    scores_dict = {
        'emotional': emotional_score,
        'logical': logical_score,
        'intellectual': intellectual_score
    }
    dominant = max(scores_dict, key=scores_dict.get)

    confidence_words = ['certain', 'sure', 'confident', 'definitely', 'absolutely', 'convinced', 'decided']
    uncertainty_words = ['maybe', 'might', 'perhaps', 'unsure', 'uncertain', 'possibly', 'thinking about']

    confidence = 50
    confidence += sum(8 for w in confidence_words if w in lower)
    confidence -= sum(10 for w in uncertainty_words if w in lower)

    if 'decided' in lower or 'decided to' in lower:
        confidence += 15

    confidence = max(25, min(100, confidence))

    return {
        "emotional": {
            "score": emotional_score,
            "keywords": emotional_matches[:5],
            "summary": f"Shows {emotional_score}% emotional influence" + (
                f" with keywords: {', '.join(emotional_matches[:3])}" if emotional_matches else "")
        },
        "logical": {
            "score": logical_score,
            "keywords": logical_matches[:5],
            "summary": f"Contains {logical_score}% logical reasoning" + (
                f" including: {', '.join(logical_matches[:3])}" if logical_matches else "")
        },
        "intellectual": {
            "score": intellectual_score,
            "keywords": intellectual_matches[:5],
            "summary": f"Demonstrates {intellectual_score}% intellectual depth" + (
                f" with: {', '.join(intellectual_matches[:3])}" if intellectual_matches else "")
        },
        "confidence": confidence,
        "dominantMode": dominant,
        "biasIndicators": biases
    }


def analyze_with_local_ai(reasoning_text):
    try:
        prompt = f"""Rate the decision reasoning below.

Return ONLY numbers.

Emotional: <0-100>
Logical: <0-100>
Intellectual: <0-100>
Confidence: <0-100>
Mode: emotional|logical|intellectual
Biases: comma-separated or none

Reasoning:
{reasoning_text}
"""

        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.2:3b",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            },
            timeout=60
        )

        data = response.json()
        ai_text = data["message"]["content"]

        parsed = parse_ai_response(ai_text)
        if parsed:
            parsed["analysis_source"] = "ai"
            parsed["raw_ai_output"] = ai_text
            return parsed

    except Exception as e:
        print("Local AI error:", e)

    fallback = rule_based_analysis(reasoning_text)
    fallback["analysis_source"] = "rule-based"
    fallback["raw_ai_output"] = ""
    return fallback

def init_db():
    conn = sqlite3.connect('decisions.db')
    c = conn.cursor()

    c.execute(
        'create table if not exists decisions (id integer primary key autoincrement, user_id text not null, title text not null, context text not null, decision text not null, full_reasoning text not null, expected_outcome text not null, stakes text not null, date_created timestamp default current_timestamp, initial_analysis text, has_reflection boolean default 0)')

    c.execute(
        'create table if not exists reflections (id integer primary key autoincrement, decision_id integer not null, user_id text not null, actual_outcome text not null, revised_perspective text not null, lessons_learned text, would_decide_same text not null, date_created timestamp default current_timestamp, reflection_analysis text)')

    conn.commit()
    conn.close()


init_db()


def parse_ai_response(ai_text):
    try:
        emotional = int(re.search(r'Emotional[:\s]*([0-9]+)', ai_text, re.I).group(1))
        logical = int(re.search(r'Logical[:\s]*([0-9]+)', ai_text, re.I).group(1))
        intellectual = int(re.search(r'Intellectual[:\s]*([0-9]+)', ai_text, re.I).group(1))
        confidence = int(re.search(r'Confidence[:\s]*([0-9]+)', ai_text, re.I).group(1))

        mode_match = re.search(r'Mode[:\s]*([a-zA-Z]+)', ai_text, re.I)
        mode = mode_match.group(1).lower() if mode_match else "logical"

        biases_match = re.search(r'Biases[:\s]*(.+)', ai_text, re.I)
        biases = []
        if biases_match and "none" not in biases_match.group(1).lower():
            biases = [b.strip() for b in re.split(r'[,;\n]', biases_match.group(1)) if b.strip()]

        return {
            "emotional": {"score": emotional},
            "logical": {"score": logical},
            "intellectual": {"score": intellectual},
            "confidence": confidence,
            "dominantMode": mode,
            "biasIndicators": biases
        }

    except Exception as e:
        print("Parse error:", e)
        return None

@app.route('/login', methods=['POST'])
def firebase_login():
    token = request.json.get('token')
    decoded = auth.verify_id_token(token)
    session['uid'] = decoded['uid']
    session['user_email'] = decoded.get('email')
    return jsonify(success=True)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/')
def index():
    if 'uid' not in session:
        return redirect(url_for('login_page'))

    user_id = session['uid']
    conn = sqlite3.connect('decisions.db')
    c = conn.cursor()

    c.execute('select d.*, r.actual_outcome, r.revised_perspective, r.lessons_learned, r.would_decide_same, r.reflection_analysis from decisions d left join reflections r on d.id = r.decision_id where d.user_id = ? order by d.date_created desc',(user_id,))

    rows = c.fetchall()
    conn.close()

    decisions = []
    for row in rows:
        d = {
            'id': row[0],
            'title': row[2],
            'context': row[3],
            'decision': row[4],
            'full_reasoning': row[5],
            'expected_outcome': row[6],
            'stakes': row[7],
            'date_created': row[8],
            'initial_analysis': json.loads(row[9]) if row[9] else None,
            'has_reflection': bool(row[10]),
            'reflection': None
        }

        if row[11]:
            d['reflection'] = {
                'actual_outcome': row[11],
                'revised_perspective': row[12],
                'lessons_learned': row[13],
                'would_decide_same': row[14],
                'reflection_analysis': json.loads(row[15]) if row[15] else None
            }

        decisions.append(d)

    return render_template('index.html', decisions=decisions)


@app.route('/add_decision', methods=['POST'])
def add_decision():
    if 'uid' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    try:
        user_id = session['uid']
        data = request.json

        if not data.get('title') or not data.get('full_reasoning'):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        analysis = analyze_with_local_ai(data['full_reasoning'])

        conn = sqlite3.connect('decisions.db')
        c = conn.cursor()
        c.execute('insert into decisions (user_id, title, context, decision, full_reasoning, expected_outcome, stakes, initial_analysis) values (?, ?, ?, ?, ?, ?, ?, ?)',(user_id, data['title'], data['context'], data['decision'], data['full_reasoning'],data['expected_outcome'], data['stakes'], json.dumps(analysis)))
        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error adding decision: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/add_reflection/<int:decision_id>', methods=['POST'])
def add_reflection(decision_id):
    if 'uid' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    try:
        user_id = session['uid']

        conn = sqlite3.connect('decisions.db')
        c = conn.cursor()
        c.execute('select user_id from decisions where id = ?', (decision_id,))
        row = c.fetchone()

        if not row or row[0] != user_id:
            conn.close()
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        data = request.json
        combined = f"{data['actual_outcome']} {data['revised_perspective']}"
        analysis = analyze_with_local_ai(combined)

        c.execute(
            'insert into reflections (decision_id, user_id, actual_outcome, revised_perspective, lessons_learned, would_decide_same, reflection_analysis) values (?, ?, ?, ?, ?, ?, ?)',
            (decision_id, user_id, data['actual_outcome'], data['revised_perspective'], data.get('lessons_learned', ''),
             data['would_decide_same'], json.dumps(analysis)))

        c.execute('update decisions set has_reflection = 1 where id = ?', (decision_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error adding reflection: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/get_advice', methods=['POST'])
def get_advice():
    if 'uid' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    user_id = session['uid']
    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({"success": False, "error": "No question provided"}), 400

    conn = sqlite3.connect('decisions.db')
    c = conn.cursor()

    c.execute('select d.title, d.context, d.decision, d.full_reasoning, d.initial_analysis, d.has_reflection, r.actual_outcome, r.revised_perspective, r.would_decide_same from decisions d left join reflections r on d.id = r.decision_id where d.user_id = ? order by d.date_created desc limit 10',(user_id,))
    rows = c.fetchall()
    conn.close()

    past_decisions_context = ""
    for i, row in enumerate(rows, 1):
        title = row[0]
        decision = row[2]
        reasoning = row[3]
        has_reflection = row[5]

        past_decisions_context += f"\n{i}. Decision: {title}\n   What you decided: {decision}\n   Reasoning: {reasoning[:200]}...\n"

        if has_reflection and row[6]:
            outcome = row[6]
            would_decide_same = row[8]
            past_decisions_context += f"   Outcome: {outcome}\n   Would decide same: {would_decide_same}\n"

    try:
        prompt = f"""You are a wise decision-making advisor. Based on this person's past decision patterns, provide thoughtful advice.

THEIR PAST DECISIONS:
{past_decisions_context}

THEIR CURRENT QUESTION:
{question}

Analyze their past decision patterns (emotional vs logical tendencies, biases, outcomes) and provide:
1. Personalized advice based on their patterns
2. What to watch out for based on their past mistakes
3. Specific recommendation for this question

Keep your response conversational and insightful (200-300 words)."""

        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.2:3b",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            },
            timeout=90
        )

        ai_data = response.json()
        advice_text = ai_data["message"]["content"]

        return jsonify({
            "success": True,
            "advice": advice_text,
            "decisions_analyzed": len(rows)
        })

    except Exception as e:
        print(f"AI Advice Error: {e}")
        return jsonify({
            "success": False,
            "error": "AI service unavailable. Make sure Ollama is running."
        }), 500


@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


if __name__ == '__main__':
    print("Second Thought running on http://localhost:5000")
    app.run(debug=True, port=5000)