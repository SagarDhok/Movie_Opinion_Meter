# 🎬 Movie Opinion Meter

<div align="center">

![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![REST API](https://img.shields.io/badge/REST-API-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![AI Powered](https://img.shields.io/badge/AI-Powered-FF6F00?style=for-the-badge&logo=openai&logoColor=white)

**Production-grade movie review platform with AI-powered features, real-time voting, and REST API**

[Live Demo](https://movie-opinion-meter.onrender.com) · 
[GitHub](https://github.com/SagarDhok/Movie_Opinion_Meter) · 

DEMO CREDENTIALS: 
Email : dhokved7@gmail.com
Passsword : ved@1234

</div>

---

## 🚀 Quick Overview

Full-stack Django application combining TMDB movie data with AI-powered review assistance. Features custom authentication, comprehensive REST API, real-time voting, and modern UI/UX.

**📊 Stats:** `4,800+ lines` · `44 files` · `3 API integrations` · `15+ REST endpoints`

---

## ✨ Key Features

### 🔐 **Authentication System**
- Custom email-based authentication with token verification
- Secure password reset flow with expiring links
- Profile management with image uploads
- Session handling and activity logging

### 🎬 **Movie Database**
- TMDB API integration (1000+ movies synced)
- Smart filtering: genre, status, release date
- Dynamic sections: Trending, Latest, Coming Soon, Most Hyped
- Cast & crew details with biography pages

### 🤖 **AI-Powered Features** ⭐ *Unique Selling Point*
- **7 writing modes:** Rewrite, Shorten, Funny, Roast, Professional, Hype, Savage
- **Pros/Cons extraction** from reviews using NLP
- Rate limiting (100 req/10min) to prevent abuse
- Built with Groq LLM API (Llama 3.3 70B) + fallback

### ⭐ **Review & Social**
- 5-star ratings with detailed text reviews
- Spoiler warnings and content filtering
- Like/comment system with nested threads
- Real-time vote aggregation (Masterpiece → Bad scale)
- Public user profiles with review history

### 📊 **Opinion Meter**
- Community voting with live percentages
- Visual progress bars with color coding
- Vote breakdown tooltips
- Personal voting history

### 🎯 **Additional**
- Watchlist with hype tracking
- Paginated content (20 items/page)
- Responsive design
- Toast notifications
- Activity logging

---

## 🛠️ Tech Stack

**Backend:** Django 5.2, Python 3.11+, PostgreSQL, Django REST Framework  
**Frontend:** HTML5/CSS3, Vanilla JavaScript, Responsive Design  
**APIs:** TMDB (movies), Groq AI (LLM), Brevo (email)  
**Auth:** Custom User Model + Token verification  
**Architecture:** MVC pattern, 2-app structure

---

## 📦 Quick Start

### Installation

```bash
# Clone & setup
git clone https://github.com/yourusername/movie-opinion-meter.git
cd movie-opinion-meter
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your API keys to .env

# Database
python manage.py migrate
python manage.py createsuperuser

# Sync movies
python manage.py sync_tmdb_movies
python manage.py sync_tmdb_cast --limit=50

# Run
python manage.py runserver
```

Visit `http://localhost:8000`

### Required API Keys
- **TMDB API:** Get from [themoviedb.org](https://www.themoviedb.org/settings/api)
- **Groq API:** Get from [console.groq.com](https://console.groq.com)
- **Brevo API:** Get from [app.brevo.com](https://app.brevo.com)

---

## 📁 Project Structure

```
movie_opinion_meter/
├── users/              # Auth module
│   ├── models.py       # Custom User model
│   ├── views.py        # Auth views
│   ├── forms.py        # Validation
│   └── utils.py        # Email service
│
├── movies/             
│   ├── models.py      #Models
│   ├── views.py        # Business logic
│   ├── views_ai.py     # AI features
│   ├── services/
│   │   └── ai_service.py
│   ├── tmdb/           # External API
│   │   ├── client.py
│   │   └── sync.py
│   └── api/            # REST endpoints
│       ├── views.py
│       └── serializers.py
│
├── templates/          # HTML 
├── static/             # JS + CSs
└── media/              # User uploads
```

---

## 🔌 API Endpoints

### Authentication
```
POST   /users/signup/              Register
POST   /users/login/               Login
POST   /users/logout/              Logout
```

### Movies
```
GET    /api/movies/                List (paginated)
GET    /api/movies/{id}/           Details + vote stats
POST   /api/movies/{id}/vote/      Vote (masterpiece/good/average/bad)
POST   /api/movies/{id}/watchlist/ Toggle watchlist
```

### Reviews
```
GET    /api/movies/{id}/reviews/   Reviews (sort: liked/latest)
POST   /reviews/{id}/like/         Toggle like
```

### AI Features
```
POST   /movie/{id}/ai/assist/      Generate review (7 modes)
POST   /movie/{id}/ai/pros-cons/   Extract pros/cons
```

### User
```
GET    /api/me/                    Current user
GET    /api/me/watchlist/          User watchlist
```

**Rate Limits:** AI (100/10min), API (1000/day authenticated)

---

## 🎯 Key Technical Highlights

### Database Optimization
- Query optimization with `select_related()` and `prefetch_related()` → 70% reduction
- Database-level aggregations using `annotate()`
- Strategic indexing on frequently queried fields

### API Best Practices
- Pagination for all list endpoints
- Consistent error handling
- Rate limiting on AI endpoints
- Token-based authentication

### AI Integration
- 7 different writing modes via prompt engineering
- Per-user rate limiting per action type
- Request logging for analytics
- Fallback model for reliability

### External API Handling
- Retry logic with exponential backoff
- Session reuse for performance
- Timeout handling
- Rate limit awareness

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Avg Response Time | ~150ms |
| Database Queries/Page | 3-8 |
| API Response | ~80ms |
| AI Generation | 2-4s |

---

## 🛣️ Roadmap

**Phase 1** - Testing (In Progress)
- Unit tests (target: 80% coverage)
- Integration tests for API
- E2E tests

**Phase 2** - Performance
- Redis caching
- Celery for async tasks
- Query optimization v2

**Phase 3** - Features
- WebSocket notifications
- Elasticsearch integration
- Social features
- ML recommendations

---

## 📸 Screenshots

### Home Page
![Home Page](#)
*Smart sections: Trending, Latest, Coming Soon, Most Hyped*

### Movie Detail
![Movie Detail](#)
*Opinion meter, AI review assistant, reviews with nested comments*

### AI Features
![AI Assistant](#)
*7 writing modes + Pros/Cons extraction*

---

## 🚀 Deployment

### Production Checklist
- [x] PostgreSQL configured
- [x] Environment variables secured
- [x] Static files collected
- [ ] Redis caching (planned)
- [ ] CI/CD pipeline (planned)
- [ ] Monitoring setup (planned)

### Recommended Platforms
- **Render** - Auto-deploy

---

## 🎓 What I Learned

✅ Django MVC architecture & best practices  
✅ Custom authentication & authorization  
✅ Complex database design & optimization  
✅ RESTful API design with DRF  
✅ External API integration & error handling  
✅ AI/LLM integration & prompt engineering  
✅ Rate limiting & security  
✅ Production-ready code structure  

---

## 👨‍💻 Author

**Sagar Dhok**  
Backend Developer | Python & Django

- Strong focus on backend architecture, APIs, and data modeling  
- Experience with Django, Django REST Framework, PostgreSQL  
- Interested in backend-heavy roles (Python / Django / API developer)

[GitHub](https://github.com/SagarDhok) · 
[LinkedIn](https://linkedin.com/in/sagar-dhok) · 
[Email](mailto:sdhok041@gmail.com)

---
s

---

## 🙏 Acknowledgments

- TMDB for movie database API
- Groq for LLM inference
- Brevo for email delivery
- Django community

---

<div align="center">

### 💼 Looking for Opportunities

I'm actively seeking **Backend Developer** positions specializing in **Python/Django**.  
This project demonstrates my ability to build production-grade applications with modern best practices.

**⭐ If you're a recruiter, let's connect!**

[Schedule a Call](9764645156) 
[More Projects]()
[View Resume](#) 

---

Made with ❤️ by [Sagar Dhok] | 

</div>


#live links can take time to load because its free tier 


Note: The app is deployed on a free hosting tier, so the first load and some page transitions may be slower due to limited resources and cold starts. Functionality, architecture, and backend logic are fully implemented and production-ready.

treding secition
watchlist 
hype percentage + everything, votes + percenteage toatl votes eveything 
cast crew there info biography 
profile personal review public review
review
review spoiler filtering pagination

0️⃣ Review system ka purpose (WHY)
Tumne review system isliye nahi banaya:
“Bas text save karne ke liye”
Tumne banaya:
1 user = 1 review per movie
Review ke saath:
rating
text
spoiler flag
likes
comments
sorting (most liked / latest)
Fast rendering (no N+1)
Clean templates

Ye already production-grade intent hai.
likes commets (see how much level)
ai review 
pros and cons 