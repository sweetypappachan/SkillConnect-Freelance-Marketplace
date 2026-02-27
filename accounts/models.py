from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20)

    # Freelancer fields
    education = models.CharField(max_length=255, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    cv = models.FileField(upload_to='cv/', blank=True, null=True)

    # Recruiter fields
    company_name = models.CharField(max_length=255, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    job_description = models.TextField(blank=True, null=True)
    salary = models.CharField(max_length=100, blank=True, null=True)

    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    # 🔥 PROFILE COMPLETION METHOD
    def profile_completion(self):
        total_fields = 4
        completed = 0

        if self.education:
            completed += 1
        if self.skills:
            completed += 1
        if self.experience:
            completed += 1
        if self.cv:
            completed += 1

        return int((completed / total_fields) * 100)