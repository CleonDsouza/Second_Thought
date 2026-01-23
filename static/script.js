function showModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
} 

function showReflection(decisionId) {
    document.getElementById('reflectionId').value = decisionId;
    showModal('reflectionModal');
}

async function submitDecision() {
    const data = {
        title: document.getElementById('title').value,
        context: document.getElementById('context').value,
        decision: document.getElementById('decision').value,
        full_reasoning: document.getElementById('fullReasoning').value,
        expected_outcome: document.getElementById('expectedOutcome').value,
        stakes: document.getElementById('stakes').value
    };

    if (!data.title || !data.context || !data.decision || !data.full_reasoning || !data.expected_outcome) {
        alert('Please fill in all required fields marked with *');
        return;
    }

    try {
        const response = await fetch('/add_decision', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });


        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            console.error('Server returned non-JSON response');
            const text = await response.text();
            console.error('Response body:', text);
            alert('Server error. Please check the console and try again.');
            return;
        }

        const result = await response.json();

        if (result.success) {
            location.reload();
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Request error:', error);
        alert('Error submitting decision: ' + error.message);
    }
}

async function submitReflection() {
    const decisionId = document.getElementById('reflectionId').value;
    const data = {
        actual_outcome: document.getElementById('actualOutcome').value,
        revised_perspective: document.getElementById('revisedPerspective').value,
        lessons_learned: document.getElementById('lessonsLearned').value,
        would_decide_same: document.getElementById('wouldDecideSame').value
    };

    if (!data.actual_outcome || !data.revised_perspective || !data.would_decide_same) {
        alert('Please fill in all required fields marked with *');
        return;
    }

    try {
        const response = await fetch(`/add_reflection/${decisionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            location.reload();
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Request error:', error);
        alert('Error submitting reflection: ' + error.message);
    }
}


window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}


document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
    }
});


async function getAIAdvice() {
    const question = document.getElementById('adviceQuestion').value.trim();

    if (!question) {
        alert('Please enter your question');
        return;
    }

    const btn = document.getElementById('getAdviceBtn');
    const loading = document.getElementById('adviceLoading');
    const result = document.getElementById('adviceResult');

    btn.disabled = true;
    btn.textContent = 'Analyzing...';
    loading.style.display = 'block';
    result.style.display = 'none';

    try {
        const response = await fetch('/get_advice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });

        const data = await response.json();

        if (data.success) {
            document.getElementById('adviceText').textContent = data.advice;
            document.getElementById('adviceMeta').textContent =
                `✓ Analyzed ${data.decisions_analyzed} of your past decisions`;

            result.style.display = 'block';
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Advice request error:', error);
        alert('Error getting advice: ' + error.message);
    } finally {
        loading.style.display = 'none';
        btn.disabled = false;
        btn.textContent = 'Get Advice';
    }
}