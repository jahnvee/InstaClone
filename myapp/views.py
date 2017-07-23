# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from Project3.settings import BASE_DIR #import base path
from django.contrib.auth.hashers import make_password, check_password  #make_password to convert password in hash code
# check_password to compare the entered password and hashed password from database
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.shortcuts import render, redirect #render to send only data and redirect to completly switching to redirected page
from forms import SignUpForm, LoginForm, LikeForm, CommentForm, PostForm, CategoryForm
from models import UserModel, SessionToken, PostModel, LikeModel, CommentModel
from imgurpython import ImgurClient
from clarifai.rest import ClarifaiApp
from myapp.data import YOUR_CLIENT_ID, YOUR_CLIENT_SECRET, app
from past.builtins import basestring
import sendgrid
from sendgrid.helpers.mail import *
from sgkey import sg_key



#view function for the user signup page
def signup_views(request):
    if request.method == 'GET': #when request is get
        form = SignUpForm() #empty form in "form"
    elif request.method == "POST":#when request is post
        form = SignUpForm(request.POST)#post request as argument
        if form.is_valid():#validate SignUpForm
            # cleaned data is used for security purpose
            username = form.cleaned_data['username']#take username from the field of template whose name is "username"
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = UserModel(name=name, password=make_password(password), email=email, username=username) #enter the above data to database model
            user.save()#save the data in model
            sg = sendgrid.SendGridAPIClient(apikey=(sg_key))
            from_email = Email("jahnveesharma@gmail.com")
            to_email = Email(email)
            subject = "SignUp to InstaClone"
            content = Content("text/plain", "You have been Successfully registered on InstaClone")
            mail = Mail(from_email, subject, to_email, content)
            response = sg.client.mail.send.post(request_body=mail.get())
            print(response.status_code)
            print(response.body)
            print(response.headers)
            return redirect("/login/") #redirect to login page when signup is successful

    return render(request, 'index.html', {'form': form}) #send data in the index.html from "form"


#view function for user login
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = UserModel.objects.filter(username=username).first() #pass only the fisrt user from the databse with provided username

            if user:
                if check_password(password, user.password): #comapare actual entered and hashed password
                    token = SessionToken(user=user) #object of SessionToken Model
                    token.create_token() #call create_token functiont to generate token
                    token.save() #save token
                    response = redirect('feed/')
                    response.set_cookie(key='session_token', value=token.session_token) #save session token in cookies
                    return response
                else:
                    print 'User Or Password is invalid'
    elif request.method == "GET":
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


#function declaration to check the validity of session token
def check_validation(request):
  if request.COOKIES.get('session_token'):
    session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
    if session:
      return session.user
  else:
    return None


#view function to make a post by user
def post_view(request):
    user = check_validation(request) #check validity of session token of current user
    if user:
        if request.method == 'GET':
            form = PostForm()
            return render(request, 'post.html', {'form': form})
        elif request.method == 'POST':
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                image = form.cleaned_data.get('image')
                caption = form.cleaned_data.get('caption')
                post = PostModel(user=user, image=image, caption=caption)
                post.save() #save image ,user name and caption
                path = str(BASE_DIR + post.image.url) #append url of image with base directory path
                client = ImgurClient(YOUR_CLIENT_ID, YOUR_CLIENT_SECRET)
                post.image_url = client.upload_from_path(path, anon=True)['link']#upload to imagur ,the post from provided url
                post.save()  #save post
                model = app.models.get('general-v1.3')  #notify model which we are going to use from clarifai
                response = model.predict_by_url(url=post.image_url)  #pass the url of current image
                category = response["outputs"][0]["data"]["concepts"][0]["name"]  #abstarct category name from json response
                post.category = category  #pass value to postModel
                post.save() #save in category field
                return redirect('/feed/')
        else:
            return redirect('/login/')


#view function to view news feed
def feed_view(request):
     user = check_validation(request)
     if user:
            posts = PostModel.objects.all().order_by('created_on')  #order images on the basis of time they are created
            for post in posts:
                existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first() #check for the likes on post
                if existing_like:
                    post.has_liked = True
            return render(request, 'feed.html', {'posts': posts})

     else:
        return redirect('/login/')


#view function to like a post
def like_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = LikeForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
            if not existing_like: #if post is not liked by current user
                like=LikeModel.objects.create(post_id=post_id, user=user)

                post=PostModel.objects.get(id=post_id)
                email_id=post.user.email
                sg = sendgrid.SendGridAPIClient(apikey=(sg_key))
                from_email = Email("jahnveesharma@gmail.com")
                to_email = Email(email_id)
                subject ="Like on Post"
                text=like.user.username+" liked your post!"
                content = Content("text/plain", text)
                mail = Mail(from_email, subject, to_email, content)
                response = sg.client.mail.send.post(request_body=mail.get())
                print(response.status_code)
                print(response.body)
                print(response.headers)
            else:
                existing_like.delete()  #unlike post
            return redirect('/feed/')
    else:
        return redirect('/login/')


#view function to comment on post
def comment_view(request):
    user = check_validation(request)
    if user and request.method=='POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id=form.cleaned_data.get('post').id #takes id of post on which user has commented
            comment_text = form.cleaned_data.get('comment_text')  #takes comment text as input
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()  #save comment on the model
            return redirect('/feed/')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')


#view function to view post of particular category
def category_view(request):
    user = check_validation(request)

    if user and request.method=="GET":
        posts = PostModel.objects.all().order_by('created_on') #pass all images data when categories are to be displayed
        return render(request, 'categories.html', {'posts': posts})
    elif request.method=="POST":
        form=CategoryForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data.get('category')
            posts = PostModel.objects.filter(category=category) #select only those post which have same category as selected by user
            return render(request, 'feed.html', {'posts': posts})
        else:
            return redirect('/feed/')

    return redirect('/login/')


def logout_view(request):
        logout(request)
        return HttpResponseRedirect('/login/')

