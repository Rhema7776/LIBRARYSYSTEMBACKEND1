# core/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Book, Member, Transaction



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    # ✅ Add this create method here
    def create(self, validated_data):
        # Check if username already exists
        if User.objects.filter(username=validated_data['username']).exists():
            raise serializers.ValidationError({"error": "Username already exists"})
        # Check if email already exists
        if User.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError({"error": "Email already registered"})
        
        # Create the user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        # Also create a related Member record
        Member.objects.create(user=user)
        return user

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class TransactionDetailSerializer(serializers.ModelSerializer):
    book = BookSerializer()
    member = serializers.StringRelatedField()  # or MemberSerializer()

    class Meta:
        model = Transaction
        fields = '__all__'
