from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import WalletTransaction,HeroCarousel
User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'phone_number')

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            phone_number=validated_data.get('phone_number')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
class UserProfileSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone_number', 'balance','is_staff','is_superuser','first_name','last_name')
        read_only_fields = ('id', 'balance')

    def get_balance(self, obj):
        return obj.balance  # dynamic balance from WalletTransaction

class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ["amount", "type", "proof"]

    def validate(self, data):
        if data["amount"] <= 0:
            raise serializers.ValidationError("Invalid amount")

        if data["type"] not in ["manual_lumicash","manual_mpesa","manual_safaricom", "crypto"]:
            raise serializers.ValidationError("Invalid deposit type")

        return data
class WalletTransactionSerializer(serializers.ModelSerializer):
    user=UserProfileSerializer(read_only=True)
    class Meta:
        model=WalletTransaction
        fields=('id','amount','user','type','status','proof','reference','created_at')
        def get_proof(self, obj):
            request = self.context.get("request")

            if obj.proof:
                return request.build_absolute_uri(obj.proof.url)

            return None
class UserSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()
    class Meta:
        model=User
        fields = ('id', 'username', 'email', 'phone_number', 'balance','is_staff','is_superuser','first_name','last_name')
    def get_balance(self, obj):
        return obj.balance  # dynamic balance from WalletTransaction
class HeroCarouselSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroCarousel
        fields = "__all__"
class AdminUserSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone_number', 'balance','is_staff','is_superuser','first_name','last_name','password')
        read_only_fields = ('id', 'balance')

    def get_balance(self, obj):
        return obj.balance  # dynamic balance from WalletTransaction
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)  # hash the password properly
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance