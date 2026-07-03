# AI Career Advisor

AI Career Advisor is a Flask web application that helps students explore career paths, analyze resumes, and receive personalized recommendations based on their skills and interests.

## Features
- User registration and login
- Career prediction and roadmap guidance
- Resume analysis support
- Course suggestions and interview preparation resources

## Tech Stack
- Python
- Flask
- SQLite
- HTML/CSS/JavaScript
- pdfplumber
- python-docx

## Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   py -m pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   py app.py
   ```
4. Open your browser and visit:
   ```text
   http://127.0.0.1:5000/
   ```

## Project Structure
- app.py - Main Flask application
- templates/ - HTML pages
- static/ - CSS and static assets
- uploads/ - Uploaded resume files
- users.db - SQLite database

## Notes
- The app uses SQLite for storing user accounts.
- Uploaded files are stored in the uploads folder.

## License
This project is for educational and personal use.
