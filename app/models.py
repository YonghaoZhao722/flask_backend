from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# User follow-up relationship association table
followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )

# User favorite posts association table
favorites = db.Table('favorites',
                     db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('post_id', db.Integer, db.ForeignKey('post.id'))
                     )

# User collections posts association table
collections = db.Table('collections',
                       db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                       db.Column('post_id', db.Integer, db.ForeignKey('post.id'))
                       )


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(32), unique=True, nullable=False, default='123@123.com')
    username = db.Column(db.String(32), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar = db.Column(db.String(256), nullable=False,
                       default='/static/img/avatar/defaultAvatar.png')
    signature = db.Column(db.String(64), default='No bio yet~')

    # User following relationship
    following = db.relationship('User',
                                secondary=followers,
                                primaryjoin=(followers.c.follower_id == id),
                                secondaryjoin=(followers.c.followed_id == id),
                                backref=db.backref('followers', lazy='dynamic'),
                                lazy='dynamic'
                                )

    # user likes
    favorites = db.relationship('Post',
                                secondary=favorites,
                                backref=db.backref('favorited_by', lazy='dynamic'),
                                lazy='dynamic'
                                )

    # user collects
    collected = db.relationship('Post',
                                secondary=collections,
                                backref=db.backref('collected_by', lazy='dynamic'),
                                lazy='dynamic'
                                )

    # user posts/comments
    posts = db.relationship('Post', backref='author', lazy='dynamic',
                            cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic',
                               cascade='all, delete-orphan')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    content = db.Column(db.Text(), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # post pics
    images = db.relationship('Image', backref='post', lazy='dynamic',
                             cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='post', lazy='dynamic',
                               cascade='all, delete-orphan')


class Image(db.Model):
    __tablename__ = 'image'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    image_path = db.Column(db.String(256), nullable=False)
    height = db.Column(db.Integer, default=0)
    width = db.Column(db.Integer, default=0)


class Comment(db.Model):
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))

    # reply relationship
    replies = db.relationship('Comment',
                              backref=db.backref('parent', remote_side=[id]),
                              lazy='dynamic', cascade='all, delete-orphan')