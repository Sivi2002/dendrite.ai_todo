import stripe
import os
from flask import Flask, render_template, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from models import db, Todo, User
from forms import TodoForm
from auth import auth
from sqlalchemy import exc



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key',
app.config['STRIPE_PUBLIC_KEY'] = 'pk_test_51PmpagRuXetyKR4mMeojOPntF6egO4f1kIbeXnI7BGl2kD2ec2A1v3S2EYJb349v09nJZ9xm2gBaR3qJfNaopnqO00YpQQEwfJ'
app.config['STRIPE_SECRET_KEY'] = 'sk_test_51PmpagRuXetyKR4mFdRtl9qwJL5B4fwIWFSz38En12jtiRfiB0cpJ9T90PuzczCD7SfTgOMVZU8LzQetf8mDjV1c00aETVXQVp'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
stripe.api_key = 'sk_test_51PmpagRuXetyKR4mFdRtl9qwJL5B4fwIWFSz38En12jtiRfiB0cpJ9T90PuzczCD7SfTgOMVZU8LzQetf8mDjV1c00aETVXQVp' 


db.init_app(app)


# Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

app.register_blueprint(auth)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = TodoForm()
    todos = Todo.query.filter_by(user_id=current_user.id).all()

    if form.validate_on_submit():
        image = form.image.data
        filename = None
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        todo = Todo(
            title=form.title.data,
            description=form.description.data,
            image=filename,
            time=form.time.data,  # Save the DateTime data
            user_id=current_user.id
            
        )
        db.session.add(todo)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('index.html', form=form, todos=todos)

@app.route('/delete/<int:todo_id>', methods=['POST'])
@login_required
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    if todo.user_id != current_user.id:
        flash("You do not have permission to delete this item.")
        return redirect(url_for('index'))
    if todo.image:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], todo.image))
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:todo_id>', methods=['GET', 'POST'])
@login_required
def edit_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    if todo.user_id != current_user.id:
        flash("You do not have permission to edit this item.")
        return redirect(url_for('index'))
    
    form = TodoForm(obj=todo)  # Pre-fill the form with the todo data

    if form.validate_on_submit():
        todo.title = form.title.data
        todo.description = form.description.data
        if form.image.data:
            # Handle image upload if a new image is provided
            image = form.image.data
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            todo.image = filename

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_todo.html', form=form, todo=todo)

# Initialize Stripe
stripe.api_key = app.config['STRIPE_SECRET_KEY']

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Pro License',
                        },
                        'unit_amount': 1000,  # e.g., $10.00
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=url_for('payment_success', _external=True),  # Use the correct route
            cancel_url=url_for('cancel', _external=True),
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify(error=str(e)), 400


@app.route('/payment_success')
@login_required
def payment_success():
    # Grant the user access to pro features (e.g., update their status in the database)
    current_user.has_pro_license = True  # Assuming you have this field in your User model
    db.session.commit()
    return render_template('payment_success.html')  # Render a success template


@app.route('/cancel')
def cancel():
    return "Payment cancelled."


if __name__ == '__main__':
    app.run(debug=True)