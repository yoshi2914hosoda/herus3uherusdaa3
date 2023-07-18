from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
import openai

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.db')
app.config['SECRET_KEY'] = 'secret-key'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class HealthCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    blood_pressure_high = db.Column(db.Integer)
    blood_pressure_low = db.Column(db.Integer)
    blood_sugar = db.Column(db.Float)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()


@app.route('/new_healthcheck', methods=['GET', 'POST'])
@login_required
def new_healthcheck():
    user = current_user
    if request.method == 'POST':
        height = request.form['height']
        weight = request.form['weight']
        blood_pressure_high = request.form['blood_pressure_high']
        blood_pressure_low = request.form['blood_pressure_low']
        blood_sugar = request.form['blood_sugar']
        healthcheck = HealthCheck(user_id=user.id, height=height, weight=weight, blood_pressure_high=blood_pressure_high, blood_pressure_low=blood_pressure_low, blood_sugar=blood_sugar)
        db.session.add(healthcheck)
        db.session.commit()
        return redirect(url_for('user_healthcheck'))
    return render_template('new_healthcheck.html', user=user)
    
# APIキーの設定
openai.api_key = ""

@app.route('/', methods=['GET'])
@login_required
def index():
    return redirect(url_for('user_healthcheck'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username is None or password is None:
            return jsonify({"error": "missing username or password"}), 400
        if User.query.filter_by(username=username).first() is not None:
            return jsonify({"error": "existing user"}), 400
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    if request.method == 'POST':
        user = User(username=request.form['username'])
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('user'))
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/healthcheck', methods=['GET', 'POST'])
@login_required
def healthcheck():
    if request.method == 'POST':
        healthcheck = HealthCheck(user_id=request.form['user_id'], height=request.form['height'], weight=request.form['weight'], blood_pressure_high=request.form['blood_pressure_high'], blood_pressure_low=request.form['blood_pressure_low'], blood_sugar=request.form['blood_sugar'])
        db.session.add(healthcheck)
        db.session.commit()
        return redirect(url_for('healthcheck'))
    healthchecks = HealthCheck.query.all()
    return render_template('healthchecks.html', healthchecks=healthchecks)

@app.route('/user/healthcheck', methods=['GET', 'POST'])
@login_required
def user_healthcheck():
    user = current_user
    healthcheck = HealthCheck.query.filter_by(user_id=user.id).order_by(HealthCheck.id.desc()).first()
    if request.method == 'POST':
        if 'menu' in request.form:
            # データベースから最新のユーザーの身長、体重、血圧、血糖値を取得
            latest_healthcheck = HealthCheck.query.filter_by(user_id=user.id).order_by(HealthCheck.id.desc()).first()
            height = latest_healthcheck.height
            weight = latest_healthcheck.weight
            blood_pressure_high = latest_healthcheck.blood_pressure_high
            blood_pressure_low = latest_healthcheck.blood_pressure_low
            blood_sugar = latest_healthcheck.blood_sugar

            # OpenAI GPT-3.5 APIを呼び出す
            prompt = f"身長は {height} cm、体重は {weight} kg、血圧は {blood_pressure_high}/{blood_pressure_low}、血糖値は {blood_sugar} mg/dL です。朝、昼、晩のおすすめメニューを教えてください。"
            messages = [
                {"role": "system", "content": "あなたをサポートする健康食事アシスタントです。"},
                {"role": "user", "content": prompt}
            ]
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            if 'choices' in response and len(response['choices']) > 0 and 'message' in response['choices'][0]:
                menu = response['choices'][0]['message']['content']
                menu_lines = menu.split("\n")
                menu_formatted = "<br>".join(menu_lines)
            else:
                menu_formatted = "メニューのおすすめを生成できませんでした。"

            return render_template('user_healthcheck.html', user=user, healthcheck=healthcheck, menu=menu_formatted)

        elif 'healthcheck' in request.form:
            height = request.form['height']
            weight = request.form['weight']
            blood_pressure_high = request.form['blood_pressure_high']
            blood_pressure_low = request.form['blood_pressure_low']
            blood_sugar = request.form['blood_sugar']
            healthcheck = HealthCheck(user_id=user.id, height=height, weight=weight, blood_pressure_high=blood_pressure_high, blood_pressure_low=blood_pressure_low, blood_sugar=blood_sugar)
            db.session.add(healthcheck)
            db.session.commit()
            return redirect(url_for('user_healthcheck'))
    return render_template('user_healthcheck.html', user=user, healthcheck=healthcheck)



if __name__ == '__main__':
    app.run(debug=True)
