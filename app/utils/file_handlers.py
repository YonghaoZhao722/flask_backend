import os
import pytz
from datetime import datetime
from functools import wraps
from flask import current_app
from sqlalchemy import desc
from app.models import User, Post


def convert_to_timezone(datetime_obj, timezone_str='Asia/Shanghai'):
    """
    转换时间为指定时区
    """
    if not datetime_obj.tzinfo:
        datetime_obj = pytz.UTC.localize(datetime_obj)
    target_timezone = pytz.timezone(timezone_str)
    converted_datetime = datetime_obj.astimezone(target_timezone)
    return converted_datetime.strftime('%Y-%m-%d %H:%M')


def check_email(email):
    """
    检查邮箱是否已存在
    """
    return User.query.filter_by(email=email).first() is not None


def combine_index_post(posts):
    """
    整合首页帖子信息
    """
    result = []  # 用于存储最终的结果
    for post in posts:
        imgs = post.images.all()
        if not imgs:
            continue

        result.append({
            'title': post.title,
            'id': post.id,
            'img': imgs[0].image_path,
            'img_info': {
                'height': imgs[0].height,
                'width': imgs[0].width,
            },
            'load': False,
            'user': {
                'id': post.author.id,
                'username': post.author.username,
                'avatar': post.author.avatar
            }
        })
    return result



def check_and_delete(*, id, mainPath):
    """
    检查和删除图片文件
    """
    try:
        file_list = os.listdir(mainPath)
        for file_name in file_list:
            if file_name.startswith(f'{id}-'):
                file_path = os.path.join(mainPath, file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
        return False
    except Exception as e:
        current_app.logger.error(f"Error deleting file: {str(e)}")
        return False


def paginate_query(query, offset, limit=3):
    """
    分页查询
    """
    try:
        offset = int(offset)
        total = query.count()
        if 0 <= offset < total:
            return query.order_by(desc('id')).offset(offset).limit(limit).all()
        return []
    except (ValueError, TypeError):
        return []


def get_user_post_info(posts, offset):
    """
    获取用户帖子信息
    """
    paginated_posts = paginate_query(posts, offset, 10)
    return [{
        'date': convert_to_timezone(post.created_at),
        'title': post.title,
        'likeCount': post.favorited_by.count(),
        'collectCount': post.collected_by.count(),
        'commentCount': post.comments.count(),
        'content': post.content,
        'id': post.id,
        'username': post.author.username,
    } for post in paginated_posts if post]


def get_user_info(users, offset):
    """
    获取用户信息
    """
    paginated_users = paginate_query(users, offset, 10)
    return [{
        'username': user.username,
        'avatar': user.avatar,
        'id': user.id,
        'fans': user.followers.count(),
        'follow': user.following.count(),
        'note': user.posts.count()
    } for user in paginated_users]


def allowed_file(filename):
    """
    检查文件类型是否允许
    """
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_IMAGE_EXTENSIONS']


def save_file(file, folder, id_prefix):
    """
    保存文件
    """
    if file and allowed_file(file.filename):
        filename = f"{id_prefix}-{file.filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
        file.save(filepath)
        return os.path.join('/static/img', folder, filename)
    return None


def handle_error(f):
    """
    错误处理装饰器
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Error in {f.__name__}: {str(e)}")
            return {'error': '服务器内部错误'}, 500

    return decorated_function