from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('freelancer', 'Freelancer'),
        ('recruiter', 'Recruiter'),
    ]

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    email = models.EmailField(unique=True)