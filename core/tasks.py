from background_task import background
from datetime import date, timedelta
from django.core.mail import send_mail
from .models import Transaction

@background(schedule=60)  # 60 seconds later for testing
def send_due_reminders():
    today = date.today()
    reminder_date = today + timedelta(days=2)  # 2 days before due date
    transactions = Transaction.objects.filter(return_date__isnull=True, due_date=reminder_date)
    
    for t in transactions:
        send_mail(
            subject=f"Reminder: Book Due Soon - {t.book.title}",
            message=f"Hello {t.member.user.username},\n\n"
                    f"Your borrowed book '{t.book.title}' is due on {t.due_date}.\n"
                    "Please return it to avoid fines.",
            from_email="library@yourdomain.com",
            recipient_list=[t.member.user.email],
        )
