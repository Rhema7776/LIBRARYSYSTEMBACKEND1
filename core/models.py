from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, date
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True)
    available_copies = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.title} by {self.author}"

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    max_books = models.PositiveIntegerField(default=3)

    def __str__(self):
        return self.user.username

class Transaction(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrow_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    fine = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    extended = models.BooleanField(default=False)

    def clean(self):
        # Prevent return date before borrow date
        if self.return_date and self.borrow_date and self.return_date < self.borrow_date:
            raise ValidationError("Return date cannot be before borrow date")

    def save(self, *args, **kwargs):
        # Ensure borrow_date is set
        if not self.borrow_date:
            self.borrow_date = date.today()

        # Set default due date if not provided
        if not self.due_date:
            self.due_date = self.borrow_date + timedelta(days=14)

        # Calculate fine if returned
        if self.return_date:
            late_days = (self.return_date - self.due_date).days
            self.fine = max(0, late_days * 10)

        super().save(*args, **kwargs)



