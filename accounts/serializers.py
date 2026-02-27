from rest_framework import serializers
from .models import User


class FreelancerRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    agree_terms = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'password',
            'confirm_password',
            'country',
            'agree_terms'
        ]

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")

        if not data['agree_terms']:
            raise serializers.ValidationError("You must agree to terms.")

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists.")

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data.pop('agree_terms')

        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            country=validated_data['country'],
            user_type='freelancer',
            is_active=False
        )

        return user


class RecruiterRegisterSerializer(FreelancerRegisterSerializer):

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data.pop('agree_terms')

        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            country=validated_data['country'],
            user_type='recruiter',
            is_active=False
        )

        return user