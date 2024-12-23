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

    user = User.query.get_or_404(user_id)

    # 删除旧头像（修正路径处理）
    if user.avatar:
        # 如果是完整 URL，提取相对路径
        old_path = user.avatar.replace('http://localhost:8000', '')
        try:
            old_file = os.path.join(current_app.root_path, old_path.lstrip('/'))
            if os.path.exists(old_file) and 'defaultAvatar' not in old_file:
                os.remove(old_file)
        except OSError:
            pass  # 忽略删除失败的错误

    # 保存新头像
    filepath = save_file(file, 'avatar', user_id)
    if not filepath:
        return jsonify({'error': '文件上传失败'}), 400

    # 存储相对路径
    user.avatar = filepath
    db.session.commit()

    # 返回完整 URL 给前端
    full_path = f"{request.host_url.rstrip('/')}{filepath}"
    return jsonify({
        'filename': file.filename,
        'filepath': full_path
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


PAGE_SIZE=10

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
        'Posts': 'posts',
        'Likes': 'favorites',
        'Collections': 'collected',
    }

    data = request.json
    user_id = data.get('user_id')
    types = data.get('types')
    offset = data.get('offset', 0)  # 提供默认值0
    print(data)
    # 查询用户
    user = User.query.filter_by(id=user_id).first()
    print(user)
    print(type_mapping)
    print(types)
    if user and types in type_mapping:
        print(111)
        # 获取对应的属性（posts/favorites/collected）
        field_name = type_mapping[types]
        post_query = getattr(user, field_name)

        # 获取总数，用于判断是否还有更多数据
        total_count = post_query.count()

        # 分页查询
        posts = post_query.offset(offset).limit(PAGE_SIZE).all()

        # 判断是否还有更多数据
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