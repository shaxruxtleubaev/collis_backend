# Generated migration for NotificationRead model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('timetable', '0003_notification_course_code_notification_course_title_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationRead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('read_at', models.DateTimeField(auto_now_add=True)),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reads', to='timetable.notification')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_reads', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('notification', 'user')},
            },
        ),
        migrations.AddIndex(
            model_name='notificationread',
            index=models.Index(fields=['user', 'read_at'], name='timetable_n_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationread',
            index=models.Index(fields=['notification'], name='timetable_n_notif_idx'),
        ),
    ]
