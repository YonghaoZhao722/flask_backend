from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Comment, Post
from app.utils.file_handlers import handle_error, convert_to_timezone, paginate_query

comment_bp = Blueprint('comment', __name__)


@comment_bp.route('/', methods=['POST'])
@jwt_required()
@handle_error
def do_comment():
    user_id = get_jwt_identity()
    data = request.json
    post_id = data.get('post_id')
    content = data.get('content')
    parent_comment_id = data.get('parent_comment_id')

    # 验证帖子是否存在
    post = Post.query.get_or_404(post_id)

    try:
        comment = Comment(
            user_id=user_id,
            post_id=post_id,
            content=content,
            parent_id=parent_comment_id
        )
        db.session.add(comment)
        db.session.commit()

        return jsonify({
            'info': '评论已发送！',
            'id': comment.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@comment_bp.route('/main/', methods=['POST'])
@handle_error
def get_comment():
    data = request.json
    post_id = data.get('id')
    offset = int(data.get('offset', 0))

    # 获取主评论（没有parent_id的评论）
    main_comments = Comment.query.filter_by(
        post_id=post_id,
        parent_id=None
    )

    comments = paginate_query(main_comments, offset)

    return jsonify({
        'info': [{
            'id': comment.id,
            'content': comment.content,
            'createTime': convert_to_timezone(comment.created_at),
            'user': {
                'id': comment.author.id,
                'username': comment.author.username,
                'avatar': comment.author.avatar
            },
            'replyCount': comment.replies.count(),
            'replies': []  # 保持响应式，初始为空列表
        } for comment in comments]
    })


@comment_bp.route('/reply/', methods=['POST'])
@handle_error
def load_reply():
    data = request.json
    comment_id = data.get('id')  # 主评id
    offset = int(data.get('offset', 0))

    # 获取指定评论的回复
    comment = Comment.query.get_or_404(comment_id)
    replies = paginate_query(comment.replies, offset)

    return jsonify({
        'info': [{
            'id': reply.id,
            'content': reply.content,
            'createTime': convert_to_timezone(reply.created_at),
            'user': {
                'id': reply.author.id,
                'username': reply.author.username,
                'avatar': reply.author.avatar
            }
        } for reply in replies],
        'count': len(replies)
    })