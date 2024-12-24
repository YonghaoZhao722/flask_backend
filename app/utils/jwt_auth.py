import logging
from datetime import timedelta
from functools import wraps

from flask import jsonify
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    verify_jwt_in_request
)

logging.basicConfig(level=logging.DEBUG)

def create_token(user):
    """
    Create a JWT token for the user
    """
    expires = timedelta(days=5, hours=12)
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
    Decorator for validating JWT tokens
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
                    return jsonify({"error": "Login expired"}), 401
                elif "invalid" in error_msg.lower():
                    return jsonify({"error": "Illegal token"}), 401
                else:
                    return jsonify({"error": "jwt authentication failed"}), 401

        return wrapper

    return decorator


def get_current_user():
    """
    Get the information of the currently logging in user
    """
    return get_jwt_identity()
