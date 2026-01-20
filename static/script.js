
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
//esc
document.addEventListener('keydown', function(event) {

    if (event.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
    }
});