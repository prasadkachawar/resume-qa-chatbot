# My Info - Personal Information Management System

A modern web application for managing and displaying personal information, contacts, and profile data.

## Features

- **Personal Profile Management** - Store and update personal details
- **Contact Management** - Organize contacts and relationships  
- **Skills & Experience** - Track professional skills and work history
- **Notes & Documents** - Personal note-taking and document storage
- **Dashboard View** - Clean, organized overview of all information

## Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python Flask
- **Database**: SQLite (development) / PostgreSQL (production)
- **Styling**: Modern CSS with Flexbox/Grid
- **Icons**: Font Awesome

## Project Structure

```
my-info-project/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── contact.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── api.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── profile.html
│   └── static/
│       ├── css/
│       ├── js/
│       └── images/
├── config/
│   └── config.py
├── migrations/
├── tests/
│   └── test_app.py
├── requirements.txt
└── run.py
```

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Initialize database: `flask db upgrade`
3. Run the application: `python run.py`
4. Open http://localhost:5000

## Development

- Run in development mode: `flask run --debug`
- Run tests: `python -m pytest`
- Database migrations: `flask db upgrade`

## License

MIT License - feel free to use and modify as needed.
