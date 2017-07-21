# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from Project3.settings import BASE_DIR
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect
from forms import SignUpForm, LoginForm, LikeForm, CommentForm, PostForm, CategoryForm
from models import UserModel, SessionToken, PostModel, LikeModel, CommentModel
from imgurpython import ImgurClient
from clarifai.rest import ClarifaiApp
from past.builtins import basestring
import sendgrid
from sendgrid.helpers.mail import *


YOUR_CLIENT_ID="cd0d6498059a791"
YOUR_CLIENT_SECRET="261784d575ae95822cc066a47adb14b353436d40"
app = ClarifaiApp(api_key='bf44b536a5b24b6e818a246e24051bc2')
sg_key="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"

def signup_views(request):
    if request.method == 'GET':
        form = SignUpForm()
    elif request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = UserModel(name=name, password=make_password(password), email=email, username=username)
            user.save()
            # sg = sendgrid.SendGridAPIClient(apikey=sg_key)
            # from_email = Email("jahnveesharma@gmail.com")
            # to_email = Email(user.email)
            # subject = "Sending with SendGrid is Fun"
            # content = Content("text/plain", "and easy to do anywhere, even with Python")
            # mail = Mail(from_email, subject, to_email, content)
            # response = sg.client.mail.send.post(request_body=mail.get())
            # print(response.status_code)
            # print(response.body)
            # print(response.headers)
            return render(request, 'success.html')
    return render(request, 'index.html', {'form': form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = UserModel.objects.filter(username=username).first()

            if user:
                if check_password(password, user.password):
                    token = SessionToken(user=user)
                    token.create_token()
                    token.save()
                    response = redirect('feed/')
                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
                else:
                    print 'User Or Password is invalid'
    elif request.method == "GET":
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def check_validation(request):
  if request.COOKIES.get('session_token'):
    session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
    if session:
      return session.user
  else:
    return None




def post_view(request):
    user = check_validation(request)
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
                post.save()
                path = str(BASE_DIR + post.image.url)
                client = ImgurClient(YOUR_CLIENT_ID, YOUR_CLIENT_SECRET)
                post.image_url = client.upload_from_path(path, anon=True)['link']
                post.save()
                model = app.models.get('general-v1.3')
                response = model.predict_by_url(url=post.image_url)
                category = response["outputs"][0]["data"]["concepts"][0]["name"]
                post.category = category
                post.save()
                return redirect('/feed/')
        else:
            return redirect('/login/')


def feed_view(request):
     user = check_validation(request)
     if user:
            posts = PostModel.objects.all().order_by('created_on')
            for post in posts:
                existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
                if existing_like:
                    post.has_liked = True
            return render(request, 'feed.html', {'posts': posts})

     else:
        return redirect('/login/')


def like_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = LikeForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
            if not existing_like:
                LikeModel.objects.create(post_id=post_id, user=user)
            else:
                existing_like.delete()
            return redirect('/feed/')
    else:
        return redirect('/login/')


def comment_view(request):
    user = check_validation(request)
    if user and request.method=='POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id=form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()
            return redirect('/feed/')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')

def category_view(request):
    user = check_validation(request)

    if user and request.method=="GET":
        posts = PostModel.objects.all().order_by('created_on')
        return render(request, 'categories.html', {'posts': posts})
    elif request.method=="POST":
        form=CategoryForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data.get('category')
            posts = PostModel.objects.filter(category=category)
            return render(request, 'feed.html', {'posts': posts})

        else:
            return redirect('/feed/')

    return redirect('/login/')


def logout_view(request):
    user = check_validation(request)
    if user:
        token = SessionToken(user=user)
        token.delete()
        return redirect('/login/')
    else:
        return redirect('/index/')