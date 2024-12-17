from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from app.models import db, User, Post
from app.utils.file_handlers import (
    handle_error, check_email, save_file,
    get_user_info, get_user_post_info, combine_index_post
)
from app.utils.jwt_auth import create_token, auth_required

user_bp = Blueprint('user', __name__)


@user_bp.route('/focus/', methods=['GET'])
# @jwt_required()
@auth_required()
def get_user_focus():
    user_id = get_jwt_identity()

    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401

    user = User.query.get_or_404(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # 添加异常处理
    try:
        response_data = {
            'follow': [u.id for u in user.following.all()],  # 添加 .all()
            'collected': [p.id for p in user.collected.all()],
            'favorites': [p.id for p in user.favorites.all()]
        }
        print(response_data)
        return jsonify(response_data)
    except Exception as e:
        print("Error:", str(e))  # 打印具体错误
        return jsonify({'error': str(e)}), 500


@user_bp.route('/avatar/', methods=['POST'])
@jwt_required()
@handle_error
def update_avatar():
    user_id = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400

    file = request.files['file']
    if not file:
        return jsonify({'error': '文件为空'}), 400

    filepath = save_file(file, 'avatar', user_id)
    if not filepath:
        return jsonify({'error': '文件上传失败'}), 400

    user = User.query.get_or_404(user_id)
    user.avatar = f"http://localhost:8000{filepath}"
    db.session.commit()

    return jsonify({
        'filename': file.filename,
        'filepath': user.avatar
    })


@user_bp.route('update/', methods=['POST'])
@jwt_required()
@handle_error
def update_user_info():
    user_id = get_jwt_identity()
    data = request.json

    user = User.query.get_or_404(user_id)
    if 'signature' in data:
        user.signature = data['signature']
    if 'username' in data:
        user.username = data['username']

    db.session.commit()
    return jsonify({'info': '修改成功'})


@user_bp.route('/unfollow/', methods=['POST'])
@jwt_required()
@handle_error
def unfollow():
    user_id = get_jwt_identity()
    target_id = request.json.get('id')

    user = User.query.get_or_404(user_id)
    target_user = User.query.get_or_404(target_id)

    if target_user in user.following:
        user.following.remove(target_user)
        db.session.commit()
        return jsonify({'info': '成功取消关注'})
    return jsonify({'error': '未关注该用户'}), 400


@user_bp.route('/remove/fan/', methods=['POST'])
@jwt_required()
@handle_error
def remove_fans():
    user_id = get_jwt_identity()
    fan_id = request.json.get('id')

    user = User.query.get_or_404(user_id)
    fan = User.query.get_or_404(fan_id)

    if user in fan.following:
        fan.following.remove(user)
        db.session.commit()
        return jsonify({'info': '成功移除粉丝'})
    return jsonify({'error': '该用户不是你的粉丝'}), 400


@user_bp.route('/post/', methods=['POST'])
@handle_error
def query_user_index_post():
    # 类型映射字典
    type_mapping = {
        '帖子': 'posts',
        '点赞': 'favorites',
        '收藏': 'collected',
    }

    data = request.json
    user_id = data.get('user_id')
    types = data.get('types')
    offset = data.get('offset')

    # 查询用户
    user = User.query.filter_by(id=user_id).first()

    if user and types in type_mapping:
        # 获取对应的属性（posts/favorites/collected）
        field_name = type_mapping[types]
        post_query = getattr(user, field_name)

        # 分页查询，限制10条
        posts = post_query.offset(offset).limit(10).all()

        if posts:
            return jsonify({
                'info': combine_index_post(posts)
            })
        return jsonify({'info': []})

    return jsonify({'error': '错误访问'}), 404

@user_bp.route('/post/control/', methods=['POST'])
@jwt_required()
@handle_error
def user_control_index():
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
        return jsonify({'error': '无效的类型'}), 400

    return jsonify({
        'info': info,
        'total': items.count()
    })