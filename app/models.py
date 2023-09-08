from django.contrib.auth.models import AbstractUser
from django.db import models


class Courses(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title
    
class User(AbstractUser):
    progress = models.DecimalField(max_digits=3, decimal_places=0, default=0)

    def __str__(self):
        return self.username

class LearningPath(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ManyToManyField(Courses, related_name='learning_paths')
    recommended_path = models.TextField()
    # Add any other attributes for the learning path

    def __str__(self):
        return f"{self.user}'s Learning Path"
