from app import db, create_app
from app.models import User, Image


def update_image_paths():
    try:
        # 更新用户头像路径
        users = User.query.all()
        for user in users:
            if user.avatar and 'http://localhost:8000' in user.avatar:
                # 从路径中移除域名部分
                user.avatar = user.avatar.replace('http://localhost:8000', '')

        # 更新帖子图片路径
        images = Image.query.all()
        for image in images:
            if image.image_path and 'http://localhost:8000' in image.image_path:
                # 从路径中移除域名部分
                image.image_path = image.image_path.replace('http://localhost:8000', '')

                # 修复 Windows 风格路径
                image.image_path = image.image_path.replace('\\', '/')

        # 提交所有更改
        db.session.commit()
        print("Successfully updated all image paths.")

    except Exception as e:
        # 如果出现错误，回滚更改
        db.session.rollback()
        print(f"Error updating image paths: {str(e)}")
        raise


# 执行更新
if __name__ == '__main__':
    # 创建 Flask 应用并设置上下文
    app = create_app()  # 确保 create_app 是您项目中用于创建 Flask 应用的工厂函数
    with app.app_context():
        update_image_paths()
