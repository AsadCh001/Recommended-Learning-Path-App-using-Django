from django.contrib import admin
from .models import User,Courses,LearningPath
# Register your models here.

admin.site.register(User),
admin.site.register(Courses),
admin.site.register(LearningPath),
