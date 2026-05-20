from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0002_alter_equipment_wilaya_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipment',
            name='name_ar',
            field=models.CharField(blank=True, help_text='Arabic name (optional)', max_length=200),
        ),
        migrations.AddField(
            model_name='equipment',
            name='price_per_day',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Rental price per day (DA)', max_digits=10),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='wilaya',
            field=models.CharField(blank=True, help_text='Wilaya where the equipment is available', max_length=100),
        ),
    ]
