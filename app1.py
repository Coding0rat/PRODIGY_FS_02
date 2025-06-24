from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SubmitField
from wtforms.validators import InputRequired, Length, Email, NumberRange
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = '12345'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'employee_db'

mysql = MySQL(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id_, username):
        self.id = id_
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM user WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    if user:
        return User(user['id'], user['username'])
    return None


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=4)])
    submit = SubmitField('Login')


class EmployeeForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email()])
    job_title = StringField('Job Title', validators=[InputRequired()])
    salary = FloatField('Salary', validators=[InputRequired(), NumberRange(min=0)])
    submit = SubmitField('Submit')


@app.route('/')
@login_required
def dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM employee')
    employees = cursor.fetchall()
    return render_template('dashboard.html', employees=employees)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE username = %s AND password = %s',
                    (form.username.data, form.password.data))
        user = cursor.fetchone()
        if user:
            user_obj = User(user['id'], user['username'])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    form = EmployeeForm()
    if form.validate_on_submit():
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO employee (name, email, job_title, salary) VALUES (%s, %s, %s, %s)',
                       (form.name.data, form.email.data, form.job_title.data, form.salary.data))
        mysql.connection.commit()
        flash('Employee added successfully!')
        return redirect(url_for('dashboard'))
    return render_template('add_employee.html', form=form)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    form = EmployeeForm()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM employee WHERE id = %s', (id,))
    employee = cursor.fetchone()
    if request.method == 'GET':
        form.name.data = employee['name']
        form.email.data = employee['email']
        form.job_title.data = employee['job_title']
        form.salary.data = employee['salary']
    if form.validate_on_submit():
        cursor.execute('UPDATE employee SET name = %s, email = %s, job_title = %s, salary = %s WHERE id = %s',
                       (form.name.data, form.email.data, form.job_title.data, form.salary.data, id))
        mysql.connection.commit()
        flash('Employee updated successfully!')
        return redirect(url_for('dashboard'))
    return render_template('edit_employee.html', form=form)


@app.route('/delete/<int:id>', methods=['GET'])
@login_required
def delete_employee(id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM employee WHERE id = %s', (id,))
    mysql.connection.commit()
    flash('Employee deleted successfully!')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
