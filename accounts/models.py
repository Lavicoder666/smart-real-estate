from django.db import models
from django.contrib.auth.models import User
import uuid

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    verification_code = models.CharField(max_length=6, editable=False)
    is_verified = models.BooleanField(default=False)
