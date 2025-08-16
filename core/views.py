from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import Book, Transaction, Member
from .serializers import *
from rest_framework.permissions import IsAuthenticated, IsAdminUser
# from .serializers import TransactionSerializer, TransactionDetailSerializer
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_framework import status
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework import generics
from django.contrib.auth.models import User
from .serializers import RegisterSerializer

from rest_framework import status

from .models import Member
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from background_task import background

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import date, timedelta
from .models import Book, Member, Transaction

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate

from rest_framework.generics import ListAPIView
from .serializers import TransactionDetailSerializer
from django.utils import timezone


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def borrowed_transactions(request):
    user = request.user
    member = get_object_or_404(Member, user=user)
    transactions = Transaction.objects.filter(member=member, return_date__isnull=True)

    serializer = TransactionDetailSerializer(transactions, many=True)
    return Response(serializer.data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def borrow_book(request, book_id):
    user = request.user
    member = get_object_or_404(Member, user=user)
    book = get_object_or_404(Book, id=book_id)

    # Check availability
    if book.available_copies <= 0:
        return Response({"error": "Book not available"}, status=400)

    # Check member's max_books
    borrowed_count = Transaction.objects.filter(member=member, return_date__isnull=True).count()
    if borrowed_count >= member.max_books:
        return Response({"error": "Reached max borrowed books"}, status=400)

    # Create transaction
    Transaction.objects.create(
        member=member,
        book=book,
        borrow_date=date.today(),
        due_date=date.today() + timedelta(days=14)
    )

    # Reduce available copies
    book.available_copies -= 1
    book.save()

    return Response({"success": "Book borrowed successfully"})


class RegisterAPI(APIView):
    permission_classes = [AllowAny]  # ✅ crucial

    def post(self, request):
        username = request.data.get("username", "").strip()
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")

        if not username:
            return Response({"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already in use"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password)
        except ValidationError as e:
            return Response({"error": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        Member.objects.create(user=user)  # Also create member record
        return Response({"message": "Account created successfully"}, status=status.HTTP_201_CREATED)


# List all borrowed books (active transactions)
class StaffBorrowedBooksAPI(ListAPIView):
    queryset = Transaction.objects.filter(return_date__isnull=True)
    serializer_class = TransactionDetailSerializer
    permission_classes = [IsAdminUser]

# Send reminder alert (dummy implementation)
class StaffSendAlertAPI(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, transaction_id):
        try:
            transaction = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)

        # Example: Mark alert sent
        transaction.alert_sent = True
        transaction.save()

        # In future: integrate real email notification
        return Response({"message": f"Reminder sent to {transaction.member.user.username}"})


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "username": user.username,
                "is_staff": user.is_staff
            })
        return Response({"error": "Invalid credentials"}, status=400)
    


# Book List
class BookListAPI(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'author', 'isbn']

# Borrow / Return logic coming next

# Borrow API
class BorrowBookAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        book_id = request.data.get("book_id")
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=404)

        if book.available_copies < 1:
            return Response({"error": "Book not available"}, status=400)

        member = Member.objects.get(user=request.user)

        # Check if already borrowed
        if Transaction.objects.filter(member=member, book=book, return_date__isnull=True).exists():
            return Response({"error": "You already borrowed this book"}, status=400)

        # Check limit
        current_borrowed = Transaction.objects.filter(member=member, return_date__isnull=True).count()
        if current_borrowed >= member.max_books:
            return Response({"error": "Borrowing limit reached"}, status=400)

        # Borrow
        transaction = Transaction.objects.create(
            member=member,
            book=book,
            borrow_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=14),
        )
        book.available_copies -= 1
        book.save()

        return Response(TransactionSerializer(transaction).data, status=201)

# Return API
class ReturnBookAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        transaction_id = request.data.get("transaction_id")
        try:
            transaction = Transaction.objects.get(id=transaction_id, member__user=request.user)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)

        if transaction.return_date:
            return Response({"error": "Book already returned"}, status=400)

        # Calculate fine and update
        transaction.return_date = timezone.now().date()
        late_days = (transaction.return_date - transaction.due_date).days
        if late_days > 0:
            transaction.fine = late_days * 10  # e.g., 10 units per day

        transaction.save()

        # Update book availability
        book = transaction.book
        book.available_copies += 1
        book.save()

        return Response({"message": "Book returned", "fine": transaction.fine}, status=200)

# Transaction History API
class UserTransactionHistoryAPI(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionDetailSerializer

    def get_queryset(self):
        member = Member.objects.get(user=self.request.user)
        return Transaction.objects.filter(member=member).order_by('-borrow_date')

class PayFineAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        transaction_id = request.data.get("transaction_id")

        try:
            transaction = Transaction.objects.get(id=transaction_id, member__user=request.user)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)

        if transaction.fine <= 0:
            return Response({"message": "No fine to pay"}, status=400)

        transaction.fine = 0
        transaction.save()

        return Response({"message": "Fine paid successfully"}, status=200)

class UserDashboardAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        member = Member.objects.get(user=request.user)
        borrowed = Transaction.objects.filter(member=member, return_date__isnull=True)
        total_fines = Transaction.objects.filter(member=member).aggregate(total=models.Sum("fine"))['total'] or 0

        return Response({
            "username": request.user.username,
            "max_books": member.max_books,
            "currently_borrowed": borrowed.count(),
            "total_fines": total_fines
        })

class OverdueBooksAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        member = Member.objects.get(user=request.user)
        today = timezone.now().date()
        overdue = Transaction.objects.filter(
            member=member,
            return_date__isnull=True,
            due_date__lt=today
        )
        serializer = TransactionDetailSerializer(overdue, many=True)
        return Response(serializer.data)

class BookCreateAPI(generics.CreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class BookUpdateAPI(generics.RetrieveUpdateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class BookDeleteAPI(generics.DestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class PayFineAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        transaction_id = request.data.get("transaction_id")

        try:
            transaction = Transaction.objects.get(id=transaction_id, member__user=request.user)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)

        if transaction.fine <= 0:
            return Response({"message": "No fine to pay"}, status=400)

        transaction.fine = 0
        transaction.save()

        return Response({"message": "Fine paid successfully"}, status=200)

class ExtendDueDateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        transaction_id = request.data.get("transaction_id")
        try:
            transaction = Transaction.objects.get(id=transaction_id, member__user=request.user)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)

        if transaction.return_date:
            return Response({"error": "Book already returned"}, status=400)

        if transaction.extended:
            return Response({"error": "Due date has already been extended"}, status=400)

        if transaction.due_date < timezone.now().date():
            return Response({"error": "Book is already overdue"}, status=400)

        # Extend the due date
        transaction.due_date += timedelta(days=7)
        transaction.extended = True
        transaction.save()

        return Response({"message": "Due date extended", "new_due_date": transaction.due_date}, status=200)

