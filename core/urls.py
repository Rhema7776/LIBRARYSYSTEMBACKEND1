from django.urls import path
from .views import (
    RegisterAPI, LoginAPIView, BookListAPI,
    BorrowBookAPI, ReturnBookAPI, UserTransactionHistoryAPI,
    PayFineAPI, BookCreateAPI, BookUpdateAPI, BookDeleteAPI,
    UserDashboardAPI, OverdueBooksAPI, ExtendDueDateAPI,
    borrowed_transactions
)

urlpatterns = [
    path('register/', RegisterAPI.as_view(), name='api-register'),
    path('login/', LoginAPIView.as_view(), name='api-login'),
    path('books/', BookListAPI.as_view(), name='api-books'),
    path('books/create/', BookCreateAPI.as_view(), name='api-book-create'),
    path('books/<int:pk>/update/', BookUpdateAPI.as_view(), name='api-book-update'),
    path('books/<int:pk>/delete/', BookDeleteAPI.as_view(), name='api-book-delete'),
    path('borrow/', BorrowBookAPI.as_view(), name='api-borrow'),
    path('return/', ReturnBookAPI.as_view(), name='api-return'),
    path('transactions/borrowed/', borrowed_transactions, name='borrowed-transactions'),
    path('transactions/', UserTransactionHistoryAPI.as_view(), name='api-transactions'),
    path('pay-fine/', PayFineAPI.as_view(), name='api-pay-fine'),
    path('dashboard/', UserDashboardAPI.as_view(), name='api-dashboard'),
    path('overdue/', OverdueBooksAPI.as_view(), name='api-overdue'),
    path('extend-due-date/', ExtendDueDateAPI.as_view(), name='api-extend-due-date'),
]
