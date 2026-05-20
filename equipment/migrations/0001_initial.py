from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('category', models.CharField(
                    choices=[
                        ('tractor',    'جرار زراعي'),
                        ('harvester',  'آلة حصاد'),
                        ('plow',       'محراث'),
                        ('seeder',     'بذارة'),
                        ('sprayer',    'آلة رش'),
                        ('irrigation', 'نظام ري'),
                        ('baler',      'آلة تبن'),
                        ('other',      'أخرى'),
                    ],
                    default='other', max_length=30,
                )),
                ('description', models.TextField(blank=True)),
                ('image_url', models.URLField(blank=True)),
                ('quantity_available', models.PositiveIntegerField(default=1)),
                ('wilaya', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['category', 'name']},
        ),
        migrations.CreateModel(
            name='EquipmentRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('reason', models.TextField()),
                ('status', models.CharField(
                    choices=[
                        ('pending',  'في الانتظار'),
                        ('approved', 'مقبول'),
                        ('rejected', 'مرفوض'),
                        ('returned', 'مُعاد'),
                    ],
                    default='pending', max_length=20,
                )),
                ('admin_note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('equipment', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='requests', to='equipment.equipment',
                )),
                ('farmer', models.ForeignKey(
                    limit_choices_to={'role': 'farmer'},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='equipment_requests',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
