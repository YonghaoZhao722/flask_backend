import os
from functools import wraps
import pytz
from flask import current_app
from sqlalchemy import desc
from app.models import User

def convert_to_timezone(datetime_obj, timezone_str='Asia/Shanghai'):
    """
    Convert UTC datetime to specified timezone (default: Asia/Shanghai)
    Returns formatted datetime string in 'YYYY-MM-DD HH:MM' format
    """
    if not datetime_obj.tzinfo:
        datetime_obj = pytz.UTC.localize(datetime_obj)
    target_timezone = pytz.timezone(timezone_str)
    converted_datetime = datetime_obj.astimezone(target_timezone)
    return converted_datetime.strftime('%Y-%m-%d %H:%M')

def check_email(email):
    """
    Check if email already exists in database
    Returns True if email exists, False otherwise
    """
    return User.query.filter_by(email=email).first() is not None

def combine_index_post(posts):
    """
    Process and combine post information for homepage display
    Extracts essential post data including title, images, and author info
    Returns list of formatted post dictionaries
    """
    result = []
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
    Check and delete image files with specified ID prefix
    Args:
        id: File ID prefix to match
        mainPath: Directory path to search for files
    Returns:
        True if file was found and deleted, False otherwise
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
    Perform pagination on database query
    Args:
        query: SQLAlchemy query object
        offset: Starting position
        limit: Number of items per page (default: 3)
    Returns:
        List of query results for requested page
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
    Retrieve paginated user post information
    Includes post metadata like dates, likes, comments etc.
    Returns list of formatted post dictionaries
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
    Retrieve paginated user profile information
    Includes user stats like followers, following count etc.
    Returns list of formatted user dictionaries
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
    Check if uploaded file has allowed image extension
    Returns True if file extension is in allowed list, False otherwise
    """
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_IMAGE_EXTENSIONS']

def save_file(file, folder, id_prefix):
    """
    Save uploaded file to specified folder with ID prefix
    Args:
        file: File object to save
        folder: Target folder name
        id_prefix: Prefix to add to filename
    Returns:
        Path to saved file or None if save failed
    """
    if file and allowed_file(file.filename):
        filename = f"{id_prefix}-{file.filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
        file.save(filepath)
        return os.path.join('/static/img', folder, filename)
    return None

def handle_error(f):
    """
    Decorator for handling function errors
    Catches exceptions and returns error response
    Logs error details to application logger
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Error in {f.__name__}: {str(e)}")
            return {'error': 'Internal Server Error'}, 500
    return decorated_function