from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from timetable.models import Lecturer, Lesson, UserProfile

class Command(BaseCommand):
    help = 'Fix permissions for all lecturers so they can access admin panel'

    def handle(self, *args, **options):
        # Get or create lesson permissions
        lesson_content_type = ContentType.objects.get_for_model(Lesson)
        lesson_permissions = Permission.objects.filter(
            content_type=lesson_content_type,
            codename__in=['view_lesson', 'add_lesson', 'change_lesson', 'delete_lesson']
        )
        
        # Process all lecturers
        lecturers = Lecturer.objects.filter(user__isnull=False)
        count = 0
        
        for lecturer in lecturers:
            user = lecturer.user
            
            # Ensure user is marked as staff
            if not user.is_staff:
                user.is_staff = True
                user.is_active = True
                user.save()
                self.stdout.write(f"✓ Marked {user.username} as staff")
            
            # Ensure user has lesson permissions
            missing_perms = []
            for perm in lesson_permissions:
                if not user.user_permissions.filter(pk=perm.pk).exists():
                    user.user_permissions.add(perm)
                    missing_perms.append(perm.codename)
            
            if missing_perms:
                self.stdout.write(f"✓ Added permissions to {user.username}: {', '.join(missing_perms)}")
            
            # Ensure UserProfile exists and is set to LECTURER
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'user_type': 'LECTURER'}
            )
            if profile.user_type != 'LECTURER':
                profile.user_type = 'LECTURER'
                profile.save()
                self.stdout.write(f"✓ Updated {user.username} profile to LECTURER")
            
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Fixed permissions for {count} lecturer(s)')
        )
