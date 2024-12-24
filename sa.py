from app import db, create_app
from app.models import User, Image


def update_image_paths():
    try:
        users = User.query.all()
        for user in users:
            if user.avatar and 'http://localhost:8000' in user.avatar:
                user.avatar = user.avatar.replace('http://localhost:8000', '')

        images = Image.query.all()
        for image in images:
            if image.image_path and 'http://localhost:8000' in image.image_path:
                image.image_path = image.image_path.replace('http://localhost:8000', '')

                image.image_path = image.image_path.replace('\\', '/')

        db.session.commit()
        print("Successfully updated all image paths.")

    except Exception as e:
        db.session.rollback()
        print(f"Error updating image paths: {str(e)}")
        raise


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        update_image_paths()
