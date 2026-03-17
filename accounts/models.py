from django.db import models
from django.contrib.auth.models import User



class Profile(models.Model):

    USER_TYPE_CHOICES = (
        ('freelancer', 'Freelancer'),
        ('recruiter', 'Recruiter'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)

    # Freelancer fields
    education = models.CharField(max_length=255, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    cv = models.FileField(upload_to='cv/', blank=True, null=True)

    # Recruiter fields
    company_name = models.CharField(max_length=255, blank=True, null=True)

    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username



# -------------------------
# JOB MODEL
# -------------------------
class Job(models.Model):

    EXPERIENCE_LEVELS = (
        ('junior', 'Junior'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior'),
    )

    recruiter = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    description = models.TextField()

    skills_required = models.CharField(max_length=255)
    tech_stack = models.CharField(max_length=255)

    pay_per_hour = models.DecimalField(max_digits=10, decimal_places=2)

    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVELS
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# -------------------------
# JOB APPLICATION
# -------------------------
class JobApplication(models.Model):

    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE)

    freelancer = models.ForeignKey(User, on_delete=models.CASCADE)

    cover_letter = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='applied'
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'freelancer')

    def __str__(self):
        return f"{self.freelancer.username} - {self.job.title}"
    


class JobInterest(models.Model):

    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE)

    message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.freelancer.username} -> {self.job.title}"