from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import re
import requests
from datetime import datetime

app = Flask(__name__) 

# test change

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
                "model": "phi3",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            },
            timeout=60
        )

        data = response.json()
        ai_text = data["message"]["content"]

        print("\n--- RAW AI OUTPUT START ---")
        print(ai_text)
        print("--- RAW AI OUTPUT END ---\n")

        parsed = parse_ai_response(ai_text, reasoning_text)
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
    c.execute('''create table if not exists decisions (id integer primary key autoincrement, title text not null, context text not null, decision text not null, full_reasoning text not null, expected_outcome text not null, stakes text not null, date_created timestamp default current_timestamp, initial_analysis text, has_reflection boolean default 0)''')
    c.execute('''create table if not exists reflections (id integer primary key autoincrement, decision_id integer not null, actual_outcome text not null, revised_perspective text not null, lessons_learned text, would_decide_same text not null, date_created timestamp default current_timestamp, reflection_analysis text, foreign key (decision_id) references decisions(id))''')
    conn.commit()
    conn.close()


init_db()


def parse_ai_response(ai_text, reasoning_text):

    try:
        print(f"Parsing AI text: {ai_text[:200]}...")

        emotional_match = re.search(r'Emotional[:\s]*[=]?\s*<?\s*(\d+)\s*>?', ai_text, re.I)
        logical_match = re.search(r'Logical[:\s]*[=]?\s*<?\s*(\d+)\s*>?', ai_text, re.I)
        intellectual_match = re.search(r'Intellectual[:\s]*[=]?\s*<?\s*(\d+)\s*>?', ai_text, re.I)
        confidence_match = re.search(r'Confidence[:\s]*[=]?\s*<?\s*(\d+)\s*>?', ai_text, re.I)

        if not all([emotional_match, logical_match, intellectual_match, confidence_match]):
            print(
                f"Missing matches: E:{bool(emotional_match)} L:{bool(logical_match)} I:{bool(intellectual_match)} C:{bool(confidence_match)}")
            return None

        emotional = int(emotional_match.group(1))
        logical = int(logical_match.group(1))
        intellectual = int(intellectual_match.group(1))
        confidence = int(confidence_match.group(1))

        print(f"Parsed scores - E:{emotional} L:{logical} I:{intellectual} C:{confidence}")

        if not all(0 <= score <= 100 for score in [emotional, logical, intellectual, confidence]):
            print("Scores out of range!")
            return None

        mode_match = re.search(r'Mode[:\s]*[=]?\s*(\w+)', ai_text, re.I)
        mode = mode_match.group(1).lower() if mode_match else 'logical'
        if mode not in ['emotional', 'logical', 'intellectual']:
            mode = 'logical'

        biases_match = re.search(r'Biases[:\s]*[=]?\s*(.+?)(?:\n|$)', ai_text, re.I | re.DOTALL)
        biases = []
        if biases_match:
            bias_text = biases_match.group(1).strip()
            if 'none' not in bias_text.lower():
                biases = [b.strip() for b in re.split(r'[,;.\n]', bias_text) if b.strip() and len(b.strip()) > 2]
                biases = biases[:5]

        print(f"Successfully parsed! Mode: {mode}, Biases: {biases}")

        return {
            "emotional": {"score": emotional, "keywords": [], "summary": f"AI Analysis: {emotional}% emotional influence detected"},
            "logical": {"score": logical, "keywords": [], "summary": f"AI Analysis: {logical}% logical reasoning present"},
            "intellectual": {"score": intellectual, "keywords": [], "summary": f"AI Analysis: {intellectual}% intellectual depth identified"},
            "confidence": confidence,
            "dominantMode": mode,
            "biasIndicators": biases
        }

    except Exception as e:
        print(f"Parse error: {e}")
        return None


@app.route('/')
def index():
    conn = sqlite3.connect('decisions.db')
    c = conn.cursor()
    c.execute('''select d.*, r.actual_outcome, r.revised_perspective, r.lessons_learned, r.would_decide_same, r.reflection_analysis from decisions d left join reflections r on d.id = r.decision_id order by d.date_created desc''')
    rows = c.fetchall()
    conn.close()

    decisions = []
    for row in rows:
        d = {
            'id': row[0], 'title': row[1], 'context': row[2], 'decision': row[3],
            'full_reasoning': row[4], 'expected_outcome': row[5], 'stakes': row[6],
            'date_created': row[7], 'initial_analysis': json.loads(row[8]) if row[8] else None,
            'has_reflection': bool(row[9]), 'reflection': None
        }
        if row[10]:
            d['reflection'] = {
                'actual_outcome': row[10], 'revised_perspective': row[11],
                'lessons_learned': row[12], 'would_decide_same': row[13],
                'reflection_analysis': json.loads(row[14]) if row[14] else None
            }
        decisions.append(d)

    return render_template('index.html', decisions=decisions)


@app.route('/add_decision', methods=['POST'])
def add_decision():
    data = request.json
    analysis = analyze_with_local_ai(data['full_reasoning'])

    conn = sqlite3.connect('decisions.db')
    c = conn.cursor()
    c.execute('''insert into decisions (title, context, decision, full_reasoning, expected_outcome, stakes, initial_analysis) values (?, ?, ?, ?, ?, ?, ?)''',
              (data['title'], data['context'], data['decision'], data['full_reasoning'],
               data['expected_outcome'], data['stakes'], json.dumps(analysis)))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/add_reflection/<int:decision_id>', methods=['POST'])
def add_reflection(decision_id):
    data = request.json
    combined = f"{data['actual_outcome']} {data['revised_perspective']}"
    analysis = analyze_with_local_ai(combined)

    conn = sqlite3.connect('decisions.db')
    c = conn.cursor()
    c.execute('''insert into reflections (decision_id, actual_outcome, revised_perspective, lessons_learned, would_decide_same, reflection_analysis) values (?, ?, ?, ?, ?, ?)''',
              (decision_id, data['actual_outcome'], data['revised_perspective'],
               data.get('lessons_learned', ''), data['would_decide_same'], json.dumps(analysis)))
    c.execute('''update decisions set has_reflection = 1 where id = ?''', (decision_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


if __name__ == '__main__':
    print("Second Thought - FREE AI Analysis")
    print("http://localhost:5000")
    app.run(debug=True, port=5000)
