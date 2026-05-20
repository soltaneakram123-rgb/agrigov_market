from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_transporterprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_approved',
            field=models.BooleanField(
                default=False,
                help_text='Must be approved by admin before login is allowed'
            ),
        ),
    ]
