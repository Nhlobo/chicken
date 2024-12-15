from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField
from wtforms.validators import InputRequired, Email, Length
import hashlib
import smtplib
from email.mime.text import MIMEText

# Initialize the Flask app and database
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    orders = db.relationship('Order', backref='user', lazy=True)

# Order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    items = db.Column(db.String(500), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')  # Could be 'Pending', 'Processing', 'Shipped'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Form for user login and registration
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    phone_number = StringField('Phone Number', validators=[InputRequired(), Length(min=10)])

# Route to handle user login
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('menu'))
        flash('Login unsuccessful. Please check your email and password.', 'danger')
    return render_template('login.html', form=form)

# Route for user logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Route to handle user registration
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, password=form.password.data, phone_number=form.phone_number.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Route to view menu (products)
@app.route("/menu")
@login_required
def menu():
    items = ["Whole Chicken", "Chicken Wings", "Chicken Thighs", "Chicken Breasts"]
    return render_template('menu.html', items=items)

# Route to add item to cart (simplified example)
@app.route("/add_to_cart/<item>")
@login_required
def add_to_cart(item):
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(item)
    session.modified = True
    flash(f"{item} added to your cart", 'success')
    return redirect(url_for('menu'))

# Route to checkout
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty!', 'danger')
        return redirect(url_for('menu'))
    
    total_price = len(session['cart']) * 100  # For simplicity, let's assume each item is 100 units
    if request.method == 'POST':
        order = Order(items=str(session['cart']), total_price=total_price, user_id=current_user.id)
        db.session.add(order)
        db.session.commit()
        session['cart'] = []  # Clear the cart after order is placed
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))

    return render_template('checkout.html', cart=session['cart'], total_price=total_price)

# Route for order confirmation and tracking
@app.route("/order_confirmation/<int:order_id>")
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('order_confirmation.html', order=order)

# Route for order tracking
@app.route("/track_order")
@login_required
def track_order():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('track_order.html', orders=orders)

# Initialize the database (run only once)
@app.before_first_request
def create_tables():
    db.create_all()

# Function to send confirmation email to customer
def send_confirmation_email(customer_email, order_details):
    msg = MIMEText(f"Thank you for your order: {order_details}")
    msg['Subject'] = 'Your Chicken Order Confirmation'
    msg['From'] = 'yourbusiness@example.com'
    msg['To'] = customer_email

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('your_email@example.com', 'your_email_password')
        server.sendmail('your_email@example.com', customer_email, msg.as_string())

# Route to view user profile and orders
@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html', user=current_user)

if __name__ == "__main__":
    app.run(debug=True)
