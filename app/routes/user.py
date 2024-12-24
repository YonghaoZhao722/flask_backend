import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, User
from app.utils.file_handlers import (
    handle_error, save_file,
    get_user_info, get_user_post_info, combine_index_post
)
from app.utils.jwt_auth import auth_required

user_bp = Blueprint('user', __name__)


@user_bp.route('/focus/', methods=['GET'])
@auth_required()
def get_user_focus():
    """
    Get user's following, collected posts, and favorites
    Returns:
        JSON containing lists of followed users, collected posts, and liked posts
    """
    user_id = get_jwt_identity()

    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401

    user = User.query.get_or_404(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Add error handling
    try:
        response_data = {
            'follow': [u.id for u in user.following.all()],
            'collected': [p.id for p in user.collected.all()],
            'favorites': [p.id for p in user.favorites.all()]
        }
        print(response_data)
        return jsonify(response_data)
    except Exception as e:
        print("Error:", str(e))  # Print specific error
        return jsonify({'error': str(e)}), 500


@user_bp.route('/avatar/', methods=['POST'])
@jwt_required()
@handle_error
def update_avatar():
    """
    Update user's avatar
    Handles file upload, deletes old avatar, and saves new one
    Returns:
        JSON with new avatar file information
    """
    user_id = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file:
        return jsonify({'error': 'Empty file'}), 400

    user = User.query.get_or_404(user_id)

    # Delete old avatar (fix path handling)
    if user.avatar:
        # Extract relative path if full URL
        old_path = user.avatar.replace('http://localhost:8000', '')
        try:
            old_file = os.path.join(current_app.root_path, old_path.lstrip('/'))
            if os.path.exists(old_file) and 'defaultAvatar' not in old_file:
                os.remove(old_file)
        except OSError:
            pass  # Ignore deletion failures

    # Save new avatar
    filepath = save_file(file, 'avatar', user_id)
    if not filepath:
        return jsonify({'error': 'File upload failed'}), 400

    # Store relative path
    user.avatar = filepath
    db.session.commit()

    # Return full URL to frontend
    full_path = f"{request.host_url.rstrip('/')}{filepath}"
    return jsonify({
        'filename': file.filename,
        'filepath': full_path
    })


@user_bp.route('update/', methods=['POST'])
@jwt_required()
@handle_error
def update_user_info():
    """
    Update user profile information
    Allows updating signature and username
    """
    user_id = get_jwt_identity()
    data = request.json

    user = User.query.get_or_404(user_id)
    if 'signature' in data:
        user.signature = data['signature']
    if 'username' in data:
        user.username = data['username']

    db.session.commit()
    return jsonify({'info': 'Update successful'})


@user_bp.route('/unfollow/', methods=['POST'])
@jwt_required()
@handle_error
def unfollow():
    """
    Unfollow another user
    """
    user_id = get_jwt_identity()
    target_id = request.json.get('id')

    user = User.query.get_or_404(user_id)
    target_user = User.query.get_or_404(target_id)

    if target_user in user.following:
        user.following.remove(target_user)
        db.session.commit()
        return jsonify({'info': 'Successfully unfollowed'})
    return jsonify({'error': 'Not following this user'}), 400


PAGE_SIZE = 10


@user_bp.route('/remove/fan/', methods=['POST'])
@jwt_required()
@handle_error
def remove_fans():
    """
    Remove a follower from user's followers list
    """
    user_id = get_jwt_identity()
    fan_id = request.json.get('id')

    user = User.query.get_or_404(user_id)
    fan = User.query.get_or_404(fan_id)

    if user in fan.following:
        fan.following.remove(user)
        db.session.commit()
        return jsonify({'info': 'Successfully removed follower'})
    return jsonify({'error': 'This user is not your follower'}), 400


@user_bp.route('/post/', methods=['POST'])
@handle_error
def query_user_index_post():
    """
    Query user's posts based on type (Posts/Likes/Collections)
    Implements pagination and returns paginated results
    """
    # Type mapping dictionary
    type_mapping = {
        'Posts': 'posts',
        'Likes': 'favorites',
        'Collections': 'collected',
    }

    data = request.json
    user_id = data.get('user_id')
    types = data.get('types')
    offset = data.get('offset', 0)  # Default value 0

    # Query user
    user = User.query.filter_by(id=user_id).first()

    if user and types in type_mapping:
        # Get corresponding attribute (posts/favorites/collected)
        field_name = type_mapping[types]
        post_query = getattr(user, field_name)

        # Get total count for pagination
        total_count = post_query.count()

        # Paginated query
        posts = post_query.offset(offset).limit(PAGE_SIZE).all()

        # Check if more data exists
        has_more = (offset + len(posts)) < total_count

        if posts:
            return jsonify({
                'info': combine_index_post(posts),
                'has_more': has_more
            })
        return jsonify({
            'info': [],
            'has_more': False
        })

    return jsonify({'error': 'Invalid access'}), 404


@user_bp.route('/post/control/', methods=['POST'])
@jwt_required()
@handle_error
def user_control_index():
    """
    Control panel for user's posts, collections, favorites, and social connections
    Handles different types of content with pagination
    """
    data = request.json
    offset = int(data.get('offset', 0))
    types = data.get('types')
    user_id = get_jwt_identity()

    user = User.query.get_or_404(user_id)

    if types == 'posts':
        items = user.posts
        info = get_user_post_info(items, offset)
    elif types in ['collected', 'favorites']:
        items = user.collected if types == 'collected' else user.favorites
        info = get_user_post_info(items, offset)
    elif types in ['fans', 'follow']:
        items = user.followers if types == 'fans' else user.following
        info = get_user_info(items, offset)
    else:
        return jsonify({'error': 'Invalid type'}), 400

    return jsonify({
        'info': info,
        'total': items.count()
    })