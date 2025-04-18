from django.contrib.auth.models import User
from django.db import models
from datetime import datetime

class Realtor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='realtor', null=True, blank=True)
    name = models.CharField(max_length=200)
    photo = models.ImageField(upload_to='photo/%Y/%m/%d')
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(max_length=50, unique=True)
    is_mvp = models.BooleanField(default=False)
    hire_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name
