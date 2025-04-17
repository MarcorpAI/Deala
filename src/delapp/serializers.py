from rest_framework import serializers
from .models import UserQuery, CustomUser




class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuery
        fields = ["id", "user", "query"]
        read_only_fields = ['id', 'user']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user   
        return super().create(validated_data)










class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user

