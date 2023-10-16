from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about-us')
def about_us():
    return render_template('about-us.html')

@app.route('/my-account')
def my_account():
    return render_template('my-account.html')

@app.route('/shopping-cart')
def shopping_cart():
    return render_template('shopping-cart.html')

@app.route('/coffeeshops', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Todo(content=task_content)

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/coffeeshops')
        except:
            return 'there was an issue adding your task'
    else:
        tasks = Todo.query.order_by(Todo.date_created).all()

        return render_template('shops.html', tasks=tasks)

@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/coffeeshops')
    except:
        return 'There was a problem deleting that task'
    
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task_to_update = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task_to_update.content=request.form['content']

        try:
            db.session.commit()
            return redirect('/coffeeshops')
        except:
            return 'There was an issue updating your task'
    else:
        return render_template('update.html', task=task_to_update)
    

if __name__ == "__main__":
    app.run(debug=True)