from functools import wraps
from datetime import datetime, timedelta
from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    verify_jwt_in_request,
    jwt_required
)
import logging

logging.basicConfig(level=logging.DEBUG)

def create_token(user):
    """
    为用户创建JWT token
    """
    expires = timedelta(days=5, hours=12)  # 设置为5天12小时，对应原来的时间
    additional_claims = {
        'username': user.username
    }
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims,
        expires_delta=expires
    )
    return access_token


def auth_required():
    """
    验证JWT token的装饰器
    """

    def decorator(fn):
        print("Inside auth_required")

        @wraps(fn)
        def wrapper(*args, **kwargs):
            print("Inside auth_required")
            try:
                verify_jwt_in_request()
                return fn(*args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                print(error_msg)
                if "expired" in error_msg.lower():
                    return jsonify({"error": "登录身份过期"}), 401
                elif "invalid" in error_msg.lower():
                    return jsonify({"error": "非法的token"}), 401
                else:
                    return jsonify({"error": "jwt认证失败"}), 401

        return wrapper

    return decorator


def get_current_user():
    """
    获取当前登录用户的信息
    """
    return get_jwt_identity()
