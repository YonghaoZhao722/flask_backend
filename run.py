from app import create_app

app = create_app()
app.config["JWT_COOKIE_CSRF_PROTECT"] = False

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)