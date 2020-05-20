from flask import *
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField , validators
from passlib.hash import sha256_crypt
from functools import wraps

from data import Articles
from flask_mail import *
from random import *


app=Flask(__name__)
#Setting up secret key
app.secret_key='secret123456'





#Config MySQL
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='Gurudev#123'
app.config['MYSQL_DB']='consultmydoc'
app.config['MYSQL_CURSORCLASS']='DictCursor'

#init MySQL
mysql=MySQL(app)




#Email verification
mail=Mail(app)

app.config["MAIL_SERVER"]='smtp.gmail.com'
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = 'gurudevssutar@gmail.com'
app.config['MAIL_PASSWORD'] =
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
otp = randint(000000,999999)


@app.route('/validate',methods=["POST"])
def validate():
    user_otp = request.form['otp']
    email=request.form['email']
    if otp == int(user_otp):
        session['email']=email
        return redirect(url_for('fill_form'))
    flash("Please enter correct OTP",'danger')
    return redirect(url_for('register'))


#Index
@app.route("/")
def index():
    return render_template("home.html")

#About
@app.route("/about")
def about():
    return render_template("about.html")



#Registration form class created
class RegisterForm2(Form):
    email=StringField("Email",[validators.Length(min=6,max=50)])
    name=StringField("Name",[validators.Length(min=1,max=50)])
    username=StringField("Username",[validators.Length(min=4,max=50)])
    password=PasswordField("Password",[
        validators.DataRequired(),
        validators.EqualTo("confirm",message="Passwords do not match")
    ])
    confirm=PasswordField("Confirm Password")


class RegisterForm1(Form):
    email=StringField("Email",[validators.Length(min=6,max=50)])

#User Register route
@app.route("/register",methods=["POST","GET"])
def register():
    form=RegisterForm1(request.form)

    if(request.method=="POST" and form.validate()):
        email=form.email.data
        msg = Message('OTP',sender = 'gurudevssutar@gmail.com', recipients = [email])
        msg.body = str(otp)
        mail.send(msg)
        flash('One-time password has been sent to the email id. Please check the email for the verification.','success')
        return render_template('verify.html',email=email)
    return render_template("register.html",form=form)



@app.route("/fill_form",methods=['POST','GET'])
def fill_form():
    email=session.get('email')
    form=RegisterForm2(request.form)
    if(request.method=="POST" and form.validate()):
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))
        #create cursor
        cur=mysql.connection.cursor()
        #cursor is acting as bridge between the data and the mysql database

        #Execute query
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s, %s, %s, %s)", (name,email,username,password))


        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('You are now registered and can log in','success')
        return redirect(url_for('login'))
    return render_template("fill_form.html",form=form,email=email)



# User login route
@app.route("/login",methods=['POST','GET'])
def login():
    if request.method=='POST':
        #Get Form Fields
        username=request.form['username']
        password_candidate=request.form['password']
        #Create cursor
        cur=mysql.connection.cursor()

        #Get user by Username
        result=cur.execute("SELECT * FROM users WHERE username=%s",[username])

        if result>0:
            #Get stored hash
            data=cur.fetchone()
            password=data['password']
            userrole=data['userrole']
            name=data['name']
            #Compare passwords
            if sha256_crypt.verify(password_candidate,password):
                #Passed and session created
                session['logged_in']=True
                session['username']=username
                session['name']=name
                flash('You are now logged in.','success')
                if userrole=='D':
                    session['userrole']=True
                else:
                    session['userrole']=False
                return redirect(url_for('dashboard'))
            else:
                error="Invalid login. Please enter correct password."
                return render_template('login.html',error=error)
            #Close connection
            cur.close()
        else:
            error="Username not found. Please register first."
            return render_template('login.html',error=error)

    return render_template('login.html')


#Check if user is logged in(using flask-decorator)
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized, Please login.','danger')
            return redirect(url_for('login'))
    return wrap


#Logout
@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out.','success')
    return redirect(url_for('login'))

# Dashboard route
@app.route("/dashboard",methods=['GET','POST'])
@is_logged_in
def dashboard():
    if request.method=='GET':
        #Create cursor
        cur=mysql.connection.cursor()

        #Get articles
        result=cur.execute("SELECT * FROM articles Where type='Public'")

        articles=cur.fetchall()

        if result>0:
            return render_template("dashboard.html",articles=articles)
        else:
            msg='No questions found'
            return render_template("dashboard.html",msg=msg)
        # Close connection
        cur.close()
    else:
        cur=mysql.connection.cursor()
        search=request.form['search']
        #Execute
        result=cur.execute("SELECT * from users WHERE id=%s or username=%s",(search,search))

        mysql.connection.commit()
        searchuser=cur.fetchall()
        if result>0:
            return render_template("profile.html",searchuser=searchuser)
        else:
            msg='No Users found'
            return render_template("dashboard.html",msg=msg)

        #Close connection
        cur.close()



# All articles
@app.route("/articles")
@is_logged_in
def articles():
    # articles=Articles()
    # return render_template("articles.html",articles=articles)

    #Create cursor
    cur=mysql.connection.cursor()

    #Get articles
    result=cur.execute("SELECT * FROM articles WHERE type='Public'")

    articles=cur.fetchall()
    if result>0:
        return render_template("articles.html",articles=articles)
    else:
        msg='No questions found'
        return render_template("articles.html",msg=msg)
    # Close connection
    cur.close()


#Single article
@app.route("/article/<string:id>/")
@is_logged_in
def article(id):
    #Create cursor
    cur=mysql.connection.cursor()
    #Get article
    result=cur.execute("SELECT * FROM articles WHERE id=%s",[id])

    article=cur.fetchone()
    isanswered=article['answered']
    if isanswered=="Not Answered":
        session.isanswered=False
        return render_template("article.html",article=article)
    else:
        session.isanswered=True
        result2 = cur.execute("SELECT * FROM answers WHERE question_id=%s",[id])
        doctorans=cur.fetchall()
        return render_template("article.html",article=article,doctorans=doctorans)

 #Personalarticles
@app.route("/personalarticles")
@is_logged_in
def personalarticles():
    # articles=Articles()
    # return render_template("articles.html",articles=articles)

    #Create cursor
    cur=mysql.connection.cursor()

    #Get articles
    if session['userrole']:
        result=cur.execute("SELECT * FROM articles Where type='Personal'")
    else:
        result=cur.execute("SELECT * FROM articles WHERE author=%s",[session['username']])

    personalarticles=cur.fetchall()
    if result>0:
        return render_template("personalarticles.html",personalarticles=personalarticles)
    else:
        msg='No Questions found'
        return render_template("personalarticles.html",msg=msg)
    # Close connection
    cur.close()

#Article form class
class ArticleForm(Form):
    title=StringField("Title",[validators.Length(min=1,max=200)])
    body=TextAreaField("Body",[validators.Length(min=30)])

# Add article route
@app.route("/add_article",methods=["GET","POST"])
@is_logged_in
def add_article():
    form=ArticleForm(request.form)
    if request.method=='POST' and form.validate():
        title=form.title.data
        body=form.body.data
        type=request.form['type']
        # Create cursor
        cur=mysql.connection.cursor()

        #Execute
        if type=="Personal":
            cur.execute("INSERT INTO articles(title,body,author,type) VALUES(%s,%s,%s,%s)", (title,body,session['username'],type))
        else:
            cur.execute("INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)", (title,body,session['username']))
        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()
        flash('Question created','success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html',form=form)

# Edit article route
@app.route("/edit_article/<string:id>/",methods=["GET","POST"])
@is_logged_in
def edit_article(id):
    #Create cursor
    cur=mysql.connection.cursor()

    #Get the article
    result=cur.execute("SELECT * FROM articles WHERE id=%s",[id])

    article=cur.fetchone()
    cur.close()

    #Get Form
    form=ArticleForm(request.form)

    #Populate article form
    #form.title.data=article['title']
    #form.body.data=article['body']

    if request.method=='POST':
        #title=request.form['title']
        body=request.form['body']

        # Create cursor
        cur=mysql.connection.cursor()

        #Execute
        cur.execute("UPDATE articles SET answered=%s WHERE id=%s", ("Answered",id))

        #Commit to DB
        mysql.connection.commit()
        cur.close()

        cur=mysql.connection.cursor()
        result=cur.execute("Select * from articles where id=%s",[id])
        article=cur.fetchone()
        author=article['author']
        title=article['title']
        typed=article['type']
        cur.close()

        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO `answers`(`question_id`, `author`, `questiontitle`, `ans_body`, `Doctor_username`,`type`) VALUES(%s,%s,%s,%s,%s,%s)",(id,author,title,body,session['username'],typed))
        mysql.connection.commit()
        #Close connection
        cur.close()

        flash('Answer uploaded','success')
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html',form=form)


#Delete article
@app.route("/delete_article/<string:id>",methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur=mysql.connection.cursor()

    #Execute
    cur.execute("DELETE from articles WHERE id=%s",[id])

    #Commit to DB
    mysql.connection.commit()
    cur.execute("DELETE FROM answers WHERE question_id=%s",[id])
    mysql.connection.commit()
    #Close connection
    cur.close()

    flash('Question deleted','success')
    return redirect(url_for('dashboard'))

#User Search
@app.route("/profile/",methods=['GET','POST'])
@is_logged_in
def search_user():
    cur=mysql.connection.cursor()
    search=request.form['search']
    #Execute
    result=cur.execute("SELECT * from users WHERE id=%s or username=%s",(search,search))
    searchuser=cur.fetchall()

    #Close connection
    cur.close()
    if result>0:
        return render_template("profile.html",searchuser=searchuser)
    else:
        msg='No Users found'
        return render_template("profile.html",msg=msg)

#Single User
@app.route('/user/<string:username>/')
@is_logged_in
def user(username):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

    userg = cur.fetchone()
    result1 = cur.execute("SELECT * FROM articles WHERE author = %s and type='Public'", [username])
    userarticle=cur.fetchall()
    result2 =   cur.execute("SELECT * FROM articles WHERE author = %s and type='Personal'", [username])
    userpersonalarticle=cur.fetchall()
    result3 = cur.execute("SELECT * FROM answers WHERE Doctor_username = %s and type='Public'", [username])
    doctorans=cur.fetchall()
    result4 = cur.execute("SELECT * FROM answers WHERE Doctor_username = %s and type='Personal'", [username])
    doctoranspersonal=cur.fetchall()
    return render_template('user.html', userg=userg,userarticle=userarticle,userpersonalarticle=userpersonalarticle,doctorans=doctorans,doctoranspersonal=doctoranspersonal)


if __name__=='__main__':
    app.debug=True
    app.run()
