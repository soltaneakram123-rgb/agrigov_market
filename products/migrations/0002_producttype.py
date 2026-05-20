from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('name_ar', models.CharField(blank=True, max_length=100)),
                ('category', models.CharField(choices=[('vegetables', 'Vegetables'), ('fruits', 'Fruits'), ('grains', 'Grains & Cereals'), ('herbs', 'Herbs & Spices'), ('legumes', 'Legumes'), ('dairy', 'Dairy'), ('other', 'Other')], default='vegetables', max_length=50)),
                ('image_url', models.URLField(blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='products.producttype'),
        ),
    ]
