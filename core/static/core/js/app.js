function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function () {
    const csrftoken = getCookie('csrftoken');

    // Handle vote buttons (questions and answers)
    document.querySelectorAll('.js-vote-btn').forEach(function (button) {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const type = this.dataset.type;
            const objectId = this.dataset.id;
            const val = this.dataset.value;
            const url = type === 'question' ? '/api/vote/question/' : '/api/vote/answer/';

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: new URLSearchParams({
                    'object_id': objectId,
                    'value': val,
                }),
            })
            .then(function (response) {
                if (response.status === 401) {
                    alert('Please log in to vote.');
                    window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
                    return null;
                }
                if (!response.ok) {
                    return response.json().then(function (err) {
                        alert(err.message || 'Error recording vote.');
                    });
                }
                return response.json();
            })
            .then(function (data) {
                if (!data || !data.success) return;
                const counter = document.getElementById(type + '-rating-' + objectId);
                if (counter) {
                    counter.textContent = data.rating;
                }
                const isUp = (data.user_vote === 1);
                const isDown = (data.user_vote === -1);
                const allUpBtns = document.querySelectorAll('.js-vote-btn[data-type="' + type + '"][data-id="' + objectId + '"][data-value="1"]');
                const allDownBtns = document.querySelectorAll('.js-vote-btn[data-type="' + type + '"][data-id="' + objectId + '"][data-value="-1"]');
                allUpBtns.forEach(function (btn) {
                    btn.classList.toggle('active', isUp);
                    btn.setAttribute('aria-pressed', isUp ? 'true' : 'false');
                });
                allDownBtns.forEach(function (btn) {
                    btn.classList.toggle('active', isDown);
                    btn.setAttribute('aria-pressed', isDown ? 'true' : 'false');
                });
            })
            .catch(function (error) {
                console.error('Vote request failed:', error);
            });
        });
    });

    // Handle marking correct answer
    document.querySelectorAll('.js-correct-checkbox').forEach(function (checkbox) {
        checkbox.addEventListener('change', function (e) {
            const answerId = this.dataset.answerId;
            const self = this;

            fetch('/api/answer/correct/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: new URLSearchParams({
                    'answer_id': answerId,
                }),
            })
            .then(function (response) {
                if (response.status === 401) {
                    alert('Please log in to mark the correct answer.');
                    self.checked = !self.checked;
                    window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
                    return null;
                }
                if (response.status === 403) {
                    alert('Only the author of the question can choose the correct answer.');
                    self.checked = !self.checked;
                    return null;
                }
                if (!response.ok) {
                    self.checked = !self.checked;
                    alert('Failed to update correct answer status.');
                    return null;
                }
                return response.json();
            })
            .then(function (data) {
                if (!data || !data.success) return;
                self.checked = data.is_correct;
            })
            .catch(function (error) {
                console.error('Mark correct request failed:', error);
                self.checked = !self.checked;
            });
        });
    });

    // Smooth scroll to anchor if present (e.g. #answer-123)
    if (window.location.hash) {
        try {
            const target = document.querySelector(window.location.hash);
            if (target) {
                setTimeout(function () {
                    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 100);
            }
        } catch (e) {
            // ignore invalid hash selector
        }
    }
});
