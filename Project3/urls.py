from django.conf.urls import url
from django.contrib import admin
from myapp.views import signup_views, login_view, feed_view, like_view, comment_view, post_view, category_view, logout_view

urlpatterns = [


    url('post/', post_view),
    url('categories/',category_view),
    url('Logout/', logout_view),
    url('feed/', feed_view),
    url('like/', like_view),
    url('comment/', comment_view),

    url('admin/', admin.site.urls),
    url('login/', login_view),

    url('', signup_views),
]
