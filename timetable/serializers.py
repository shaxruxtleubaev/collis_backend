from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from datetime import datetime
from .models import (
    Course, Group, Room,
    Lecturer, Student, UserProfile,
    Lesson, Notification
)

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['course_code', 'title', 'credits', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class GroupSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'intake', 'student_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_student_count(self, obj):
        return obj.students.count()

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'building', 'hall', 'capacity', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class LecturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lecturer
        fields = ['lecturer_id', 'fullname', 'email', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class StudentSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = Student
        fields = ['student_id', 'fullname', 'email', 'group', 'group_name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    fullname = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'user_type', 'user_type_display', 'fullname', 'user_id', 'group_name']
        read_only_fields = ['id']
    
    def get_fullname(self, obj):
        """Get fullname from Lecturer or Student"""
        if obj.user_type == 'LECTURER' and hasattr(obj.user, 'lecturer'):
            return obj.user.lecturer.fullname
        elif obj.user_type == 'STUDENT' and hasattr(obj.user, 'student'):
            return obj.user.student.fullname
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
    
    def get_user_id(self, obj):
        """Get lecturer_id or student_id"""
        if obj.user_type == 'LECTURER' and hasattr(obj.user, 'lecturer'):
            return obj.user.lecturer.lecturer_id
        elif obj.user_type == 'STUDENT' and hasattr(obj.user, 'student'):
            return obj.user.student.student_id
        return None
    
    def get_group_name(self, obj):
        """Get student's group name"""
        if obj.user_type == 'STUDENT' and hasattr(obj.user, 'student'):
            if obj.user.student.group:
                return obj.user.student.group.name
        return None

class LessonSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.course_code', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    lecturer_name = serializers.CharField(source='lecturer.fullname', read_only=True)
    lecturer_id = serializers.CharField(source='lecturer.lecturer_id', read_only=True)
    group_names = serializers.SerializerMethodField()
    room_details = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'course_code', 'course_title', 
            'lecturer', 'lecturer_id', 'lecturer_name', 
            'groups', 'group_names', 
            'room', 'room_details', 
            'lesson_type', 'date', 'starting_time', 'ending_time', 'duration',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_room_details(self, obj):
        return f'{obj.room.building} - {obj.room.hall} (Capacity: {obj.room.capacity})'

    def get_group_names(self, obj):
        return [g.name for g in obj.groups.all()]
    
    def get_duration(self, obj):
        """Return lesson duration in minutes"""
        start_dt = datetime.combine(datetime.today(), obj.starting_time)
        end_dt = datetime.combine(datetime.today(), obj.ending_time)
        duration = (end_dt - start_dt).total_seconds() / 60
        return int(duration)

    def validate(self, data):
        # Get data from instance if updating, otherwise from validated data
        date = data.get('date') or (self.instance.date if self.instance else None)
        starting_time = data.get('starting_time') or (self.instance.starting_time if self.instance else None)
        ending_time = data.get('ending_time') or (self.instance.ending_time if self.instance else None)

        # Validate time logic
        if starting_time >= ending_time:
            raise serializers.ValidationError({"ending_time": "Lesson ending time must be after starting time."})

        # Calculate and validate duration
        start_dt = datetime.combine(datetime.today(), starting_time)
        end_dt = datetime.combine(datetime.today(), ending_time)
        duration = (end_dt - start_dt).total_seconds() / 60  # minutes
        
        if duration < 30:
            raise serializers.ValidationError({"ending_time": "Lesson must be at least 30 minutes long."})
        if duration > 240:  # 4 hours
            raise serializers.ValidationError({"ending_time": "Lesson cannot exceed 4 hours."})

        # Get objects for conflict checking
        room = data.get('room') or (self.instance.room if self.instance else None)
        lecturer = data.get('lecturer') or (self.instance.lecturer if self.instance else None)
        groups = data.get('groups') or (list(self.instance.groups.all()) if self.instance else [])

        # Validate room capacity
        if groups:
            total_students = sum(g.students.count() for g in groups)
            if total_students > room.capacity:
                raise serializers.ValidationError({
                    "room": f"Room capacity ({room.capacity}) exceeded. Total students from selected groups: {total_students}"
                })

        # Build overlap queryset
        overlap_queryset = Lesson.objects.filter(date=date)
        if self.instance:
            overlap_queryset = overlap_queryset.exclude(pk=self.instance.pk)

        # Time overlap condition
        time_overlap_condition = Q(starting_time__lt=ending_time) & Q(ending_time__gt=starting_time)

        # Check room conflict
        if overlap_queryset.filter(Q(room=room) & time_overlap_condition).exists():
            raise serializers.ValidationError({"room": "This room is already occupied during this time slot."})

        # Check lecturer conflict
        if overlap_queryset.filter(Q(lecturer=lecturer) & time_overlap_condition).exists():
            raise serializers.ValidationError({"lecturer": "This lecturer is already busy during this time slot."})
            
        # Check group conflict
        if overlap_queryset.filter(Q(groups__in=groups) & time_overlap_condition).exists():
            raise serializers.ValidationError({"groups": "One or more of the selected groups already has a lesson during this time slot."})
            
        return data

class NotificationSerializer(serializers.ModelSerializer):
    lesson_details = serializers.SerializerMethodField()
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'lesson', 'lesson_details',
            'course_code', 'course_title', 'lesson_date', 'lesson_time', 'group_names',
            'message_type', 'message_type_display', 'message_text', 
            'is_sent', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'lesson_details', 'message_type_display', 'is_read']
    
    def get_lesson_details(self, obj):
        """Return lesson details if lesson still exists, otherwise use stored data"""
        if obj.lesson:
            return {
                'id': obj.lesson.id,
                'course_code': obj.lesson.course.course_code,
                'course_title': obj.lesson.course.title,
                'date': obj.lesson.date,
                'time': obj.lesson.starting_time,
                'room': f"{obj.lesson.room.building} - {obj.lesson.room.hall}",
                'lecturer': obj.lesson.lecturer.fullname,
            }
        else:
            # Lesson was deleted, return stored data
            return {
                'id': None,
                'course_code': obj.course_code,
                'course_title': obj.course_title,
                'date': obj.lesson_date,
                'time': obj.lesson_time,
                'deleted': True
            }
    
    def get_is_read(self, obj):
        """Check if current user has read this notification"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        from .models import NotificationRead
        return NotificationRead.objects.filter(
            notification=obj,
            user=request.user
        ).exists()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user