# movies/forms.py
from django import forms
from django.core.validators import MaxLengthValidator
from .models import MovieReview, ReviewComment


class MovieReviewForm(forms.ModelForm):
    """
    Django form for movie reviews
    Handles server-side validation for ratings and review text
    """
    
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
        """Validate review text length and content"""
        text = self.cleaned_data.get('review_text')
        
        if not text or not text.strip():
            raise forms.ValidationError("Review cannot be empty")
        
        if len(text) > 1000:
            raise forms.ValidationError("Review must be under 1000 characters")
        
        return text.strip()

    def clean_rating(self):
        """Validate rating is between 1 and 5"""
        rating = self.cleaned_data.get('rating')
        
        if not rating or rating < 1 or rating > 5:
            raise forms.ValidationError("Please select a rating between 1 and 5")
        
        return rating

#not using 
# class ReviewCommentForm(forms.ModelForm):
#     """
#     Django form for review comments
#     Validates comment length
#     """
    
#     class Meta:
#         model = ReviewComment
#         fields = ['text']
#         widgets = {
#             'text': forms.Textarea(attrs={
#                 'placeholder': 'Write a comment...',
#                 'maxlength': 500,
#                 'rows': 3,
#                 'class': 'comment-textarea'
#             })
#         }
#         labels = {
#             'text': ''
#         }

#     def clean_text(self):
#         """Validate comment text"""
#         text = self.cleaned_data.get('text')
        
#         if not text or not text.strip():
#             raise forms.ValidationError("Comment cannot be empty")
        
#         if len(text) > 500:
#             raise forms.ValidationError("Comment must be under 500 characters")
        
#         return text.strip()