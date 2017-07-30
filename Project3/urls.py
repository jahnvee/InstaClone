from django.conf.urls import url
import patterns
from django.contrib import admin
from django.views.generic import TemplateView
from myapp.views import signup_views, login_view, feed_view, like_view, comment_view, post_view, category_view, \
    search_view, logout_view, upvote_view

urlpatterns =[
    #url(r'^login/feed/(?P<username>\D+)/',search_user_view),


    url('admin/', admin.site.urls),
    url('Logout/', logout_view),
    url('categories/',category_view),
    #url(r'^{UserModel.username}$/',search_view),
    url('search/', search_view),
    url('post/', post_view),
    url('feed/',feed_view),
    url('like/', like_view),
    url('comment/', comment_view),
    url('upvote/', upvote_view),
    url('login/', login_view),
    url('', signup_views),
]
