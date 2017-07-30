# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from myapp.models import UserModel,PostModel,CommentModel,LikeModel,UpvoteModel


admin.site.register(UserModel)
admin.site.register(PostModel)
admin.site.register(CommentModel)
admin.site.register(LikeModel)
admin.site.register(UpvoteModel)

# Register your models here.
