from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, Post, User
from app.utils.file_handlers import (
    handle_error, convert_to_timezone,
    combine_index_post, check_and_delete
)
from app.utils.jwt_auth import auth_required

post_bp = Blueprint('post', __name__)

PAGE_SIZE = 10


def paginate_query(query, offset):
    """
    Perform pagination on database query
    Args:
        query: SQLAlchemy query object
        offset: Number of records to skip
    Returns:
        List of paginated query results
    """
    return query.offset(offset).limit(PAGE_SIZE).all()


# Implementation of KMP search algorithm
def build_next(pattern):
    """
    Build the next array for KMP algorithm
    Args:
        pattern: String pattern to build next array for
    Returns:
        List containing the next array values
    """
    next_array = [0]
    prefix = 0
    i = 1

    while i < len(pattern):
        if pattern[prefix] == pattern[i]:
            prefix += 1
            next_array.append(prefix)
            i += 1
        elif prefix == 0:
            next_array.append(0)
            i += 1
        else:
            prefix = next_array[prefix - 1]

    return next_array


def kmp_search(text, pattern):
    """
    Perform KMP string search algorithm
    Args:
        text: Source text to search in
        pattern: Pattern to search for
    Returns:
        Starting index of pattern if found, -1 otherwise
    """
    if not pattern or not text:
        return -1

    next_array = build_next(pattern)
    i = 0  # text pointer
    j = 0  # pattern pointer

    while i < len(text) and j < len(pattern):
        if text[i] == pattern[j]:
            i += 1
            j += 1
        elif j == 0:
            i += 1
        else:
            j = next_array[j - 1]

    return i - j if j == len(pattern) else -1


@post_bp.route('/detail/', methods=['POST', 'GET'])
@handle_error
def get_post_detail():
    """
    Get detailed information for a specific post
    Returns:
        JSON object containing post details including title, images, author info,
        timestamps, and engagement metrics
    """
    post_id = request.json.get('id')
    post = Post.query.get_or_404(post_id)

    return jsonify({
        'info': {
            'title': post.title,
            'id': post.id,
            'imgs': [img.image_path for img in post.images],
            'user': {
                'id': post.author.id,
                'username': post.author.username,
                'avatar': post.author.avatar
            },
            'createTime': convert_to_timezone(post.created_at),
            'likeCount': post.favorited_by.count(),
            'collectCount': post.collected_by.count(),
            'commentCount': post.comments.count(),
            'content': post.content or ''
        }
    })


@post_bp.route('/', methods=['POST', 'GET'])
@handle_error
def query_post_index():
    """
    Query posts with optional search and pagination
    Returns:
        JSON object containing list of posts and pagination info
    """
    offset = int(request.json.get('offset', 0))
    search_query = request.json.get('query', '').lower()

    # Get posts ordered by creation time descending
    posts = Post.query.order_by(Post.created_at.desc())

    if search_query:
        all_posts = posts.all()
        filtered_posts = [
            post for post in all_posts
            if kmp_search(post.title.lower(), search_query) != -1
        ]

        total_count = len(filtered_posts)
        paginated_posts = filtered_posts[offset:offset + PAGE_SIZE]
    else:
        total_count = posts.count()
        paginated_posts = paginate_query(posts, offset)

    result_posts = list(combine_index_post(paginated_posts))

    has_more = (offset + len(result_posts)) < total_count

    return jsonify({
        'info': result_posts,
        'has_more': has_more
    })


@post_bp.route('/control/', methods=['POST', 'GET'])
@jwt_required()
@handle_error
def control_like_collect():
    """
    Handle post like and collection operations
    Returns:
        JSON response indicating success or failure of the operation
    """
    user_id = get_jwt_identity()
    data = request.json
    post_id = data.get('post_id')
    operator = data.get('operator')
    type_ = data.get('type')

    user = User.query.get_or_404(user_id)
    post = Post.query.get_or_404(post_id)

    try:
        if type_ == 'like':
            if operator:  # Remove like
                if post in user.favorites:
                    user.favorites.remove(post)
                    msg = 'Unliked Successfully'
            else:  # Add like
                if post not in user.favorites:
                    user.favorites.append(post)
                    msg = 'Liked Successfully'
        elif type_ == 'collect':
            if operator:  # Remove from collection
                if post in user.collected:
                    user.collected.remove(post)
                    msg = 'Successfully removed from collection'
            else:  # Add to collection
                if post not in user.collected:
                    user.collected.append(post)
                    msg = 'Successfully added to collection'
        else:
            return jsonify({'error': 'Invalid operation type'}), 400

        db.session.commit()
        return jsonify({'info': msg})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Post control failed: {str(e)}")
        return jsonify({'error': 'Operation failed'}), 400


@post_bp.route('/delete/', methods=['POST', 'GET'])
@auth_required()
@handle_error
def post_delete():
    """
    Delete a post and its associated images
    Returns:
        JSON response indicating success or failure of deletion
    """
    user_id = get_jwt_identity()
    post_id = request.json.get('id')

    post = Post.query.get_or_404(post_id)

    print(f"Post user_id: {post.user_id}, Current user_id: {user_id}")
    print(type(post.user_id), type(user_id))
    if post.user_id != int(user_id):
        return jsonify({'error': 'Unauthorized to delete this post'}), 403

    try:
        # Delete associated image files
        path = current_app.config['UPLOAD_FOLDER'] + '/post/'
        check_and_delete(id=post_id, mainPath=path)

        # Delete post and related data
        db.session.delete(post)
        db.session.commit()
        return jsonify({'success': 'Post deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Post deletion failed: {str(e)}")
        return jsonify({'error': 'Deletion failed'}), 400