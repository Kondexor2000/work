# Eduwork

Eduwork helps you generate content ideas up to 5× faster.
 
    For content creators
        Share ideas on bios, posts, and messages in seconds instead of hours.

    For inspiration seekers
        Save up to 70% of brainstorming time and never run out of ideas.

---

## Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Functions](#functions)
- [Tech stack](#tech-stack)
- [Additional comments](#additional-comments)
- [Contact](#contact)

## Installation

```bash
git clone https://github.com/Kondexor2000/work.git
cd work
```

## Configuration

```bash
mkdir requirements.txt
pip freeze > requirements.txt
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Functions

- Content management by admin
- Add ideas
- Search ideas

## Tech stack

- Python
- Django
- PostgreSQL
- HTML, CSS, JS
- tools with import in code

## Additional comments
- AI: python manage.py ai
      python chat.py
- Cryptography: python manage.py secure_backup
- Certificate Security: python manage.py generate_cert
- Adding Google Login API or Facebook Login API is suggested
- class SearchPortfolioView is created according to business value by search

## Contact

- If you have any questions or suggestions, get in touch with us on e-mail address: k.kosciecha20@gmail.com
