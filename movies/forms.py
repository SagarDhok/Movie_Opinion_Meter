# movies/forms.py
from django import forms
from .models import MovieReview


class MovieReviewForm(forms.ModelForm):    
    class Meta:
        model = MovieReview
        fields = ['rating', 'review_text', 'contains_spoiler']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, i) for i in range(1, 6)],
                attrs={'class': 'star-rating'}
            ),
            'review_text': forms.Textarea(attrs={
                'placeholder': 'Write your review...',
                'maxlength': 1000,
                'rows': 5,
                'class': 'review-textarea'
            }),
            'contains_spoiler': forms.CheckboxInput(attrs={
                'class': 'spoiler-checkbox'
            })
        }
        labels = {
            'rating': '',
            'review_text': '',
            'contains_spoiler': 'Contains Spoilers'
        }

    def clean_review_text(self):
        text = self.cleaned_data.get('review_text')
        
        if not text or not text.strip():
            raise forms.ValidationError("Review cannot be empty")
        
        if len(text) > 1000:
            raise forms.ValidationError("Review must be under 1000 characters")
        
        return text.strip()

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        
        if not rating or rating < 1 or rating > 5:
            raise forms.ValidationError("Please select a rating between 1 and 5")
        
        return rating
