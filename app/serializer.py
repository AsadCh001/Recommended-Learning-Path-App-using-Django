from rest_framework import serializers
from .models import Courses, LearningPath
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ( 'id','username', 'email', 'password','password2')
    extra_kwargs = {
            'password': {'write_only': True}
        }
    def validate(self, data):
        password = data.get('password')
        password2 = data.get('password2')

        if password and password2 and password != password2:
            raise serializers.ValidationError("Passwords do not match.")

        return data
    def create(self, validated_data):
        password = validated_data.pop('password')
        password2 = validated_data.pop('password2')  # Remove 'password2' from validated_data
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        print("user saved")
        return user

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = ['id','title']

    def create(self, validated_data):
        # Extract the 'technology' from the validated data
        technology = validated_data.get('title')

        # Try to get the course with thse given technology title
        course, created = Courses.objects.get_or_create(title=technology)

        return course


class LearningPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPath
        fields = ['id','user', 'course', 'recommended_path']
    def create(self, validated_data):
        user = validated_data['user']
        course = validated_data['course'][0] if validated_data['course'] else None
        recommended_path = validated_data['recommended_path']

        existing_path = LearningPath.objects.filter(user=user, course=course).first()

        if existing_path:
            existing_path.recommended_path = recommended_path
            existing_path.save()
            return existing_path
        else:
            learning_path = LearningPath.objects.create(user=user, recommended_path=recommended_path)
            if course:
                learning_path.course.set([course])
            return learning_path