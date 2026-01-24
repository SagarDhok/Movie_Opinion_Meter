# users/views.py - FIXED VERSION
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from .utils import send_brevo_email
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from movies.models import Watchlist, MovieReview, MovieVote
from django.db.models import Prefetch
from .models import User
from .forms import SignupForm, LoginForm, ProfileUpdateForm, ForgotPasswordForm, ResetPasswordForm


def signup_view(request):
    """
    Handle user registration using Django forms.
    
    Validates user input server-side, creates user account,
    and sends email verification link via Brevo API.
    """
    if request.method == "POST":
        form = SignupForm(request.POST)
        
        if form.is_valid():
            # Create user with validated data
            user = User.objects.create_user(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )

            # Generate email verification token
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verify_url = request.build_absolute_uri(
                reverse("verify-email", kwargs={"uid": uid, "token": token})
            )

            # Send verification email
            send_brevo_email(
                to_email=user.email,
                subject="Verify your email – Movie Opinion Meter",
                text_content=f"""
Hi {user.first_name},

Please verify your email address to activate your Movie Opinion Meter account.

Verification link:
{verify_url}

This link expires in 24 hours.
If you did not sign up, you can safely ignore this email.

– Movie Opinion Meter Team
"""
            )

            messages.success(
                request, 
                "Registration successful! Please check your email to verify your account."
            )
            return redirect('verify-email-success')
    else:
        form = SignupForm()
    
    return render(request, "users/signup.html", {"form": form})


def verify_email(request, uid, token):
    """
    Verify user email from token link.
    
    Decodes user ID from URL, validates token, and marks email as verified.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.save()
        messages.success(request, "Email verified successfully. You can now login.")
    else:
        messages.error(request, "Verification link is invalid or expired.")

    return redirect("login")


def verify_email_success(request):
    """Display verification email sent confirmation page."""
    return render(request, "users/verify_email_success.html")


def login_view(request):
    """
    Handle user login using Django forms.
    
    Authenticates user credentials and creates session.
    Checks for email verification before allowing login.
    """
    if request.method == "POST":
        form = LoginForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Authenticate user
            user = authenticate(request, email=email, password=password)

            if user is None:
                form.add_error(None, 'Invalid email or password')
            elif not user.is_email_verified:
                form.add_error('email', 'Please verify your email before logging in')
            else:
                # Login successful
                login(request, user)
                messages.success(
                    request,
                    f"Welcome {user.first_name} {user.last_name}! Login successful 🎉"
                )
                
                # Redirect to 'next' parameter or home
                next_url = request.GET.get("next")
                if next_url:
                    return redirect(next_url)
                
                return redirect("movies-home")
    else:
        form = LoginForm()

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    """
    Handle user logout.
    
    Destroys user session and redirects to home page.
    """
    logout(request)
    messages.info(request, "You have been logged out successfully")
    return redirect("movies-home")


def forgot_password_view(request):
    """
    Handle forgot password request.
    
    Sends password reset link to user's email if account exists.
    Always shows success message for security (prevents user enumeration).
    """
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None

            # Send email only if user exists (but always show success)
            if user:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                reset_url = request.build_absolute_uri(
                    reverse("reset-password", kwargs={"uid": uid, "token": token})
                )

                send_brevo_email(
                    to_email=user.email,
                    subject="Reset your password – Movie Opinion Meter",
                    text_content=f"""
Hi {user.first_name},

You requested a password reset.

Reset link:
{reset_url}

This link expires in 24 hours.
If you didn't request this, ignore this email.

– Movie Opinion Meter Team
"""
                )

            # Always show this message (security best practice)
            messages.success(
                request,
                "If an account exists with this email, a password reset link has been sent."
            )
            return redirect("login")
    else:
        form = ForgotPasswordForm()

    return render(request, "users/forgot_password.html", {"form": form})


def reset_password_view(request, uid, token):
    """
    Handle password reset from token link.
    
    Validates token and allows user to set new password.
    Uses Django's password validation.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if not user or not default_token_generator.check_token(user, token):
        messages.error(request, "Reset link is invalid or expired.")
        return redirect("login")

    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        
        if form.is_valid():
            # Set new password
            user.set_password(form.cleaned_data['password'])
            user.save()

            messages.success(request, "Password reset successful. You can now login.")
            return redirect("login")
    else:
        form = ResetPasswordForm()

    return render(request, "users/reset_password.html", {"form": form})


@login_required
def profile_view(request):
    """
    Display and handle user profile updates.
    
    Allows users to update name and profile image.
    Uses Django forms for validation.
    """
    if request.method == "POST":
        
        # Handle profile image removal
        if request.POST.get("remove_image") == "1":
            if request.user.profile_image:
                request.user.profile_image.delete(save=False)
                request.user.profile_image = None
                request.user.save()
            messages.success(request, "Profile photo removed")
            return redirect("profile")

        # Handle profile update
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            # Delete old image if new one uploaded
            if 'profile_image' in request.FILES and request.user.profile_image:
                request.user.profile_image.delete(save=False)
            
            form.save()
            messages.success(request, "Profile updated successfully")
            return redirect("profile")
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    # Get user statistics
    watchlist_movies = Watchlist.objects.filter(
        user=request.user
    ).select_related("movie")
    
    review_count = MovieReview.objects.filter(user=request.user).count()
    
    context = {
        "watchlist_count": watchlist_movies.count(),
        "watchlist_movies": watchlist_movies,
        "review_count": review_count,
    }
    
    return render(request, "users/profile.html", context)


def public_profile(request, user_id):
    """
    Display public profile of a user.
    
    Shows user's reviews and their votes on reviewed movies.
    All data fetched server-side with optimized queries.
    """
    user_obj = get_object_or_404(User, id=user_id)

    # Fetch reviews with related data (optimized query)
    reviews = (
        MovieReview.objects
        .filter(user=user_obj)
        .select_related("movie")
        .prefetch_related(
            Prefetch(
                "movie__votes",
                queryset=MovieVote.objects.filter(user=user_obj),
                to_attr="user_vote_list"
            )
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "users/public_profile.html",
        {
            "user_obj": user_obj,
            "reviews": reviews,
        }
    )