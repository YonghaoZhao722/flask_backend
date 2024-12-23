from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from ..utils.jwt_auth import create_token
from app.models import db, User, Image, Post
from app.utils.file_handlers import (
    handle_error, check_email, save_file
)

# 创建独立路由蓝图
independent_bp = Blueprint('independent', __name__)

@independent_bp.route('/login/', methods=['POST'])
@handle_error
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        is_valid = check_password_hash(user.password_hash, password)

        if is_valid:
            # Creating a token
            token = create_token(user)

            # Constructing return data
            response_data = {
                "id": user.id,
                "username": user.username,
                "avatar": user.avatar,
                "signature": user.signature or "No bio yet~",
                "token": token
            }

            return jsonify(response_data), 200
        else:
            return jsonify({"error": "Wrong password"}), 401
    else:
        return jsonify({"error": "User not found"}), 401

@independent_bp.route('/register/', methods=['POST'])
@handle_error
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if check_email(email):
        return jsonify({'error': 'This email address has been registered'}), 401

    try:
        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password_hash=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({'info': 'User created successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"User creation failed: {str(e)}")
        return jsonify({'error': 'Failed to create user'}), 401


@independent_bp.route('/change-password/', methods=['POST'])
@handle_error
@jwt_required()
def change_password():
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    # 获取当前用户ID
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"error": "User not found"}), 401

    # 验证旧密码
    if not check_password_hash(current_user.password_hash, old_password):
        return jsonify({"error": "Current password is incorrect"}), 401

    try:
        # Generate a hash of the new password
        new_password_hash = generate_password_hash(new_password)

        # Update Password
        current_user.password_hash = new_password_hash
        db.session.commit()

        return jsonify({"message": "Password updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password update failed: {str(e)}")
        return jsonify({"error": "Failed to update password"}), 500

@independent_bp.route('/index/', methods=['POST'])
@handle_error
def query_user_index():
    user_id = request.json.get('id')
    user = User.query.get_or_404(user_id)

    return jsonify({
        'data': {
            'user': {
                'id': user.id,
                'username': user.username,
                'avatar': user.avatar,
                'signature': user.signature,
                'fans': user.followers.count(),
                'focusOn': user.following.count(),
                'postsCount': user.posts.count()
            }
        }
    })

@independent_bp.route('/focus/', methods=['POST'])
@jwt_required()
@handle_error
def focus_on():
    user_id = get_jwt_identity()
    target_id = request.json.get('id')

    if user_id == target_id:
        return jsonify({'error': '不能关注自己'}), 400

    user = User.query.get_or_404(user_id)
    target_user = User.query.get_or_404(target_id)

    if target_user not in user.following:
        user.following.append(target_user)
        db.session.commit()
        return jsonify({'info': '成功关注'})
    return jsonify({'error': '已经关注该用户'}), 400

# 帖子相关
@independent_bp.route('/upload/', methods=['POST', 'GET'])
@jwt_required()
@handle_error
def upload_post():
    post_id = request.form.get('id')
    if 'file' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400

    file = request.files['file']
    if not file:
        return jsonify({'error': '文件为空'}), 400

    filepath = save_file(file, 'post', post_id)
    if not filepath:
        return jsonify({'error': '文件上传失败'}), 400

    try:
        # 只存储相对路径
        image = Image(
            post_id=post_id,
            image_path=filepath,
            height=0,
            width=0
        )
        db.session.add(image)
        db.session.commit()

        # 返回完整 URL 给前端
        full_path = f"{request.host_url.rstrip('/')}{filepath}"
        return jsonify({'data': 'success', 'filepath': full_path})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Image save failed: {str(e)}")
        return jsonify({'error': '保存图片信息失败'}), 400

@independent_bp.route('/upload/info/', methods=['POST', 'GET'])
@jwt_required()
@handle_error
def upload_post_info():
    user_id = get_jwt_identity()
    data = request.json

    # 验证用户身份
    if str(user_id) != str(data.get('user_id')):
        return jsonify({'error': '用户身份验证失败'}), 401

    try:
        post = Post(
            user_id=user_id,
            title=data.get('title'),
            content=data.get('content', '')
        )
        db.session.add(post)
        db.session.commit()
        return jsonify({
            'data': 'success',
            'info': post.id
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Post creation failed: {str(e)}")
        return jsonify({'error': '创建帖子失败'}), 400