from django.db import models
from django.contrib.auth.models import User
from cloudinary_storage.storage import RawMediaCloudinaryStorage


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
    cv = models.FileField(
        upload_to='cv/',
        storage=RawMediaCloudinaryStorage(),
        blank=True,
        null=True
    )
    about = models.TextField(blank=True, null=True)

    # Recruiter fields
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_location = models.CharField(max_length=255, blank=True, null=True)
    company_website = models.CharField(max_length=255, blank=True, null=True)
    company_about = models.TextField(blank=True, null=True)
    recruiter_skills = models.TextField(blank=True, null=True)

    is_complete = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.user_type == "freelancer":
            self.is_complete = all([
                self.education,
                self.skills,
                self.experience,
                self.cv
            ])
        elif self.user_type == "recruiter":
            self.is_complete = bool(self.company_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username


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
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class JobApplication(models.Model):

    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE)
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'freelancer')

    def __str__(self):
        return f"{self.freelancer.username} - {self.job.title}"


class JobInterest(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("shortlisted", "Shortlisted"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"{self.freelancer.username} -> {self.job.title}"


class Notification(models.Model):

    NOTIF_TYPES = [
        ('interest_sent', 'Interest Sent'),
        ('shortlisted',   'Shortlisted'),
        ('accepted',      'Accepted'),
        ('rejected',      'Rejected'),
        ('new_interest',  'New Interest Received'),
        ('job_closed',    'Job Closed'),
    ]

    recipient  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=30, choices=NOTIF_TYPES)
    title      = models.CharField(max_length=255)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    job        = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notif_type}] → {self.recipient.username}"