#  Importing Required Module

from flask import Flask, render_template,request,flash, redirect, session
import json
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import date as d
import os
from werkzeug.utils import secure_filename
from sqlalchemy import or_

local_server = True


app = Flask(__name__)
app.secret_key = 'super-secret-key'


# Opening the Configrion json file
with open('config.json', 'r') as c:
    params = json.load(c)["params"]


# Database Configruation

if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']

else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Contact Mail Configruation

app.config.update(
        MAIL_SERVER = "smtp.gmail.com" ,
        MAIL_PORT = "465" ,
        MAIL_USE_SSL= True ,
        MAIL_USERNAME = params['gmail-user'],
        MAIL_PASSWORD = params['gmail-password'] )

mail = Mail(app)


# Movielist Database Class  

class Movieslist(db.Model):

    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  nullable=False)
    slug = db.Column(db.String(12),  nullable=False)
    imdb_score = db.Column(db.String(120), nullable=False)
    genre = db.Column(db.String(12))
    releaseyear = db.Column(db.String(12))
    img_file = db.Column(db.String(12))
    director = db.Column(db.String(80),  nullable=False)
    popularity = db.Column(db.String(80),  nullable=False)
    description = db.Column(db.String(12))

# Databse class for Contact 

class Contacts(db.Model):

    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  nullable=False)
    phone_num = db.Column(db.String(12),  nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20))
    email = db.Column(db.String(20),  nullable=False)

#  User Registration 

class Registration(db.Model):
    name = db.Column(db.String(80) )
    email   = db.Column(db.String(80) , nullable=True, primary_key=True)
    password = db.Column(db.String(80) , nullable = False)


# Home page and Seaching movie using post method 

@app.route('/', methods=['GET', 'POST'], defaults={"page": 1})
@app.route('/<int:page>', methods=['GET', 'POST'])
def index_r(page):

    page = page
    pages = 5
    movieslist = Movieslist.query.order_by(Movieslist.sno.asc()).paginate(page,error_out=False)  #desc()

    if request.method == 'POST' and 'tag' in request.form:

        tag = request.form["tag"]
        if tag=="":
            flash("Please enter something")
            return render_template('index.html',params=params, valid =0)

        search = "%{}%".format(tag)

        movieslist = Movieslist.query.filter(or_(Movieslist.genre.like(search),Movieslist.name.like(search),Movieslist.director.like(search))).paginate(page,per_page=pages, error_out=False) # LIKE: query.filter(User.name.like('%ednalan%'))
        product_count = movieslist.query.count()
        if product_count==0:
            flash("No Movie related to this Keyword, Try again!")


        return render_template('index.html', movieslist=movieslist, tag=tag,params = params, product_count= product_count)


    return render_template('index.html',params=params, data=movieslist,valid =0)


# >>>>> About Section >>>>>>>>>>

@app.route('/about')
def  about():
    return render_template('about.html',params = params)

# >>>>>USer Registration Section >>>>>>>>>>

@app.route("/signup")
def signup():
    return render_template('signup.html',params=params)



@app.route("/signup" , methods = ['GET','POST'])
def signup_post():
        # '''Add entry to DB'''
    if request.method=='POST':
        name = request.form.get('name')
        email= request.form.get('email')
        password = request.form.get('pass')

        email_exist = Registration.query.filter_by(email=email).first()


        if email_exist:
            flash("Email already exists!")
            return redirect('/signup')
        else:
            entry = Registration(name=name ,password=password, email = email)
            db.session.add(entry)
            db.session.commit()
            flash("You are Succefully Registered!")
            return redirect('/login')

    return redirect('/signup')


# >>>>>USer Logout >>>>>>>>>>

@app.route("/logout")
def logout():
    if 'user' in session and session['user']==params['admin_user']:
        session['user']= False
    else:
        session['logged_in'] = False
    return redirect("/")


# User Login
@app.route('/login')
def login():
    return render_template('login.html',params=params)

@app.route("/login" , methods = ['POST'])
def login_post():
    '''Add entry to DB'''
    if request.method=='POST':
        session['email'] =  request.form.get('uname')
        session['password'] =  request.form.get('pass')
        user = Registration.query.filter_by(email=session['email'] ).first()

    if not user  :
        flash('Please check your login details and try again.')
        return redirect('/login')
    elif not user.password==session['password']:
        flash('Please check your login details and try again.')
        return redirect('/login')

    session['name'] = Registration.query.filter_by(email =session['email']).first().name

    session['logged_in'] = True
    return redirect('/')



@app.route("/profile/<string:name>")
def profile(name):
    return render_template('profile.html',params=params,name=session['name'])

@app.route("/profile/<string:name>" , methods = ['POST'])
def profile_post(name):
        # '''Add entry to DB'''
    if request.method=='POST':
        email= request.form.get('email')
        email_exist = Registration.query.filter_by(email=email).first()

        if email_exist:
            flash(email_exist)
            flash(" Email already exists!")

        else:
            user = Registration.query.filter_by(email = session['email']).first()
            user.email = email; session['email']= email
            db.session.commit()
            flash("Succefully Updated!")
            return redirect('/')
        return redirect('/profile')



@app.route("/contact" , methods = ['GET' , 'POST'])
def contact():
    if request.method=='POST':

        '''Add entry to DB'''
        name = request.form.get('name')
        email= request.form.get('email')
        phone  = request.form.get('phone')
        message= request.form.get('message')

        entry = Contacts(name=name , phone_num = phone , msg = message , date= d.today(), email = email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from learn2_cod' + name ,
                    sender = email ,
                    recipients = [params['gmail-user']] ,
                    body = message +  "\n"  + phone
                    )
        flash(" Message Sent Successfully !")

    return render_template('contact.html' , params = params)


@app.route("/movieslist")
def movieslist():
    if 'logged_in' in session and session['logged_in']:

        data = Movieslist.query.all()
        return render_template("movieslist.html",data=data,params=params)
    else:
        return redirect('/login')


@app.route("/dashboard" , methods=['GET' , 'POST'])
def dashboard():
    if ('user' in session and session['user']==params['admin_user']):
        posts = Movieslist.query.all()

        return render_template('dashboard.html' , params = params , posts = posts)

    if request.method=='POST':
        username  = request.form.get('uname')
        userpass  = request.form.get('pass')

        if (username == params['admin_user'] and userpass == params['admin_password']):
            #set the session variable
            session['user'] = username
            posts = Movieslist.query.all()
            return render_template('dashboard.html' , params = params , posts = posts)

        else:
            flash('Wrong Username or Password')
            return render_template('admin.html' , params= params)

    else:
        return render_template('admin.html' , params = params)



@app.route("/edit/<string:sno>" , methods = ['GET' , 'POST'])
def edit(sno):
    if ('user' in session and session['user']==params['admin_user']):
        if request.method == 'POST':


    # director = db.Column(db.String(80),  nullable=False)
    # popularity = db.Column(db.String(80),  nullable=False)
            name= request.form.get('title')
            imdb_score = request.form.get('tline')
            slug = request.form.get('slug')
            genre= request.form.get('genre')
            img_file = request.form.get('img_file')
            releaseyear = request.form.get('year')
            popularity = request.form.get('pop')
            director = request.form.get('director')
            description = request.form.get('description')



            if sno =="0":
                movieslist = Movieslist(description=description,popularity = popularity,name = name , slug = slug , imdb_score = imdb_score, genre = genre ,img_file = img_file , releaseyear = releaseyear,director = director)
                db.session.add(movieslist)
                db.session.commit()

            else:
                movieslist = Movieslist.query.filter_by(sno = sno).first()
                movieslist.name  = name
                movieslist.slug  = slug
                movieslist.imdb_score = imdb_score
                movieslist.genre = genre
                movieslist.img_file = img_file
                movieslist.releaseyear = releaseyear
                movieslist.description = description
                db.session.commit()
                return redirect('/edit/' + sno)

        movieslist = Movieslist.query.filter_by(sno = sno).first()
        return render_template('edit.html' , params = params ,  sno= sno , movieslist = movieslist)
    else:

        return dashboard()



@app.route("/uploader" , methods = ['GET' , 'POST'])
def uploader():
    if ('user' in session and session['user']==params['admin_user']):

        if(request.method == 'POST'):
            f= request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'] , secure_filename(f.filename)))
            return "Uploaded Successfully!"



@app.route("/delete/<string:sno>" , methods = ['GET' , 'POST'])
def delete(sno):
    if ('user' in session and session['user']==params['admin_user']):
        post = Movieslist.query.filter_by(sno = sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')



if __name__=='__main__':
    app.run(debug=True)