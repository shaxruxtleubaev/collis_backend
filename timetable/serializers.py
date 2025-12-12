from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q # Imported for complex query construction
from .models import (
    Course, Group, Room,
    Lecturer, Student, UserProfile,
    Lesson, Device, Notification
)

# --- Foundation Serializers ---

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'course_code', 'credits']
        read_only_fields = ['id']

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'intake']
        read_only_fields = ['id']

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'building', 'hall', 'capacity']
        read_only_fields = ['id']

# --- User Serializers ---

class UserProfileSerializer(serializers.ModelSerializer):
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'user_type', 'user_type_display']
        read_only_fields = ['id', 'user']

class LecturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lecturer
        fields = ['id', 'user_profile', 'fullname']
        read_only_fields = ['id']

class StudentSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'user_profile', 'fullname', 'group', 'group_name']
        read_only_fields = ['id']

class UserRegistrationSerializer(serializers.Serializer):
    """
    Handles the registration process for new users (Student or Lecturer).
    """
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    fullname = serializers.CharField(max_length=255)
    user_type = serializers.ChoiceField(choices=['STUDENT', 'LECTURER'])
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), 
        required=False, 
        allow_null=True
    )

    def validate(self, data):
        # 1. Validate if username/email already exists
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "This email is already registered."})

        # 2. Validate Student group requirement
        if data['user_type'] == 'STUDENT' and not data.get('group_id'):
            raise serializers.ValidationError({"group_id": "Students must be assigned to a group."})
             
        return data

    def create(self, validated_data):
        with transaction.atomic():
            # Create Django User
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password']
            )

            # Create UserProfile
            user_profile = UserProfile.objects.create(
                user=user,
                user_type=validated_data['user_type']
            )

            # Create Student or Lecturer record
            if validated_data['user_type'] == 'STUDENT':
                Student.objects.create(
                    user_profile=user_profile,
                    fullname=validated_data['fullname'],
                    group=validated_data['group_id']
                )
            elif validated_data['user_type'] == 'LECTURER':
                Lecturer.objects.create(
                    user_profile=user_profile,
                    fullname=validated_data['fullname']
                )
            
            return user

# --- Scheduling Serializers ---

class LessonSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.course_code', read_only=True)
    lecturer_name = serializers.CharField(source='lecturer.fullname', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    room_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'course_code', 'lecturer', 'lecturer_name', 
            'group', 'group_name', 'room', 'room_details', 'lesson_type', 
            'date', 'starting_time', 'ending_time'
        ]
        read_only_fields = ['id', 'course_code', 'lecturer_name', 'group_name', 'room_details']

    def get_room_details(self, obj):
        return f'{obj.room.building} - {obj.room.hall}'

    def validate(self, data):
        # Determine the final values for date and time (handling both create and update)
        date = data.get('date') or (self.instance.date if self.instance else None)
        starting_time = data.get('starting_time') or (self.instance.starting_time if self.instance else None)
        ending_time = data.get('ending_time') or (self.instance.ending_time if self.instance else None)

        # 1. Check for time validity (Start time must be before End time)
        if starting_time >= ending_time:
            raise serializers.ValidationError("Lesson ending time must be after starting time.")

        # 2. Get resources to check
        room = data.get('room') or (self.instance.room if self.instance else None)
        lecturer = data.get('lecturer') or (self.instance.lecturer if self.instance else None)
        group = data.get('group') or (self.instance.group if self.instance else None)

        # 3. Build the base overlap query
        overlap_queryset = Lesson.objects.filter(date=date)
        
        # Exclude the current lesson being updated
        if self.instance:
            overlap_queryset = overlap_queryset.exclude(pk=self.instance.pk)

        # Overlap condition: (Existing Start Time < New End Time) AND (Existing End Time > New Start Time)
        time_overlap_condition = Q(starting_time__lt=ending_time) & Q(ending_time__gt=starting_time)

        # 4. Check for conflicts on each resource (Room, Lecturer, Group)

        # --- Room Conflict Check ---
        room_conflict = overlap_queryset.filter(
            Q(room=room) & time_overlap_condition
        ).select_related('course').first()
        
        if room_conflict:
            raise serializers.ValidationError({
                "room": f"Room {room.building}-{room.hall} is already booked for '{room_conflict.course.title}' from {room_conflict.starting_time.strftime('%H:%M')} to {room_conflict.ending_time.strftime('%H:%M')} on {date.strftime('%Y-%m-%d')}."
            })

        # --- Lecturer Conflict Check ---
        lecturer_conflict = overlap_queryset.filter(
            Q(lecturer=lecturer) & time_overlap_condition
        ).select_related('course').first()
        
        if lecturer_conflict:
            raise serializers.ValidationError({
                "lecturer": f"Lecturer {lecturer.fullname} is already scheduled for '{lecturer_conflict.course.title}' from {lecturer_conflict.starting_time.strftime('%H:%M')} to {lecturer_conflict.ending_time.strftime('%H:%M')} on {date.strftime('%Y-%m-%d')}."
            })
            
        # --- Group Conflict Check ---
        group_conflict = overlap_queryset.filter(
            Q(group=group) & time_overlap_condition
        ).select_related('course').first()
        
        if group_conflict:
            raise serializers.ValidationError({
                "group": f"Group {group.name} is already scheduled for '{group_conflict.course.title}' from {group_conflict.starting_time.strftime('%H:%M')} to {group_conflict.ending_time.strftime('%H:%M')} on {date.strftime('%Y-%m-%d')}."
            })
            
        return data

# --- Notification Serializers ---

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'user_profile', 'platform', 'registration_id', 'created_at']
        read_only_fields = ['id', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    lesson_details = LessonSerializer(source='lesson', read_only=True)
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'lesson', 'lesson_details', 
            'message_type', 'message_type_display', 'message_text', 
            'is_sent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'lesson_details', 'message_type_display']