

document.addEventListener('DOMContentLoaded', function() {
    
    const starLabels = document.querySelectorAll('.star-label input');
    starLabels.forEach(input => {
        input.addEventListener('change', function() {
            const value = parseInt(this.value);
            const labels = document.querySelectorAll('.star-label');
            labels.forEach((label, idx) => {
                label.classList.toggle('active', idx < value);
            });
            const ratingText = document.querySelector('.rating-text');
            if (ratingText) {
                ratingText.textContent = value + '/5';
            }
        });
    });
    
    const textarea = document.querySelector('textarea[name="review_text"]');
    const charCount = document.getElementById('char-count');
    if (textarea && charCount) {
        textarea.addEventListener('input', function() {
            charCount.textContent = this.value.length;
        });
    }
    
    const checkedStar = document.querySelector('.star-label input:checked');
    if (checkedStar) {
        checkedStar.dispatchEvent(new Event('change'));
    }
});

// Spoiler toggle function
function toggleSpoiler(reviewId) {
    const reviewText = document.getElementById('review-' + reviewId);
    const button = event.target;
    
    if (reviewText.classList.contains('revealed')) {
        reviewText.classList.remove('revealed');
        button.textContent = 'Show spoiler';
    } else {
        reviewText.classList.add('revealed');
        button.textContent = 'Hide spoiler';
    }
}