from app import create_app, db

app = create_app('development')

with app.app_context():
    db.create_all()
    print("The database table was created successfully！")