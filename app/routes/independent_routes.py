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

# 用户相关
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
            # 创建token
            token = create_token(user)

            # 构建返回数据
            response_data = {
                "id": user.id,
                "username": user.username,
                "avatar": user.avatar,
                "signature": user.signature or "暂时没有个性签名~",
                "token": token
            }

            return jsonify(response_data), 200
        else:
            return jsonify({"error": "Invalid password"}), 401
    else:
        return jsonify({"error": "User not found"}), 401

@independent_bp.route('/register/', methods=['POST'])
@handle_error
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 检查邮箱是否已被注册
    if check_email(email):
        return jsonify({'error': '该邮箱已被注册'}), 401

    try:
        # 对密码进行加密
        hashed_password = generate_password_hash(password)

        # 创建用户对象，并将加密后的密码存储
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password  # 存储加密后的密码
        )

        # 将用户信息保存到数据库
        db.session.add(user)
        db.session.commit()

        return jsonify({'info': '创建用户成功'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"User creation failed: {str(e)}")
        return jsonify({'error': '创建用户失败'}), 401

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
        image = Image(
            post_id=post_id,
            image_path=f"http://localhost:8000{filepath}",
            # TODO: 获取图片尺寸
            height=0,
            width=0
        )
        db.session.add(image)
        db.session.commit()
        return jsonify({'data': 'success'})
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