from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('ministry', '0002_policy_complaint'),
        ('products', '0003_seed_product_types'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeasonalPriceRange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('season', models.CharField(choices=[
                    ('spring', '🌸 Spring  (Mar–May)'),
                    ('summer', '☀️ Summer  (Jun–Aug)'),
                    ('autumn', '🍂 Autumn  (Sep–Nov)'),
                    ('winter', '❄️ Winter  (Dec–Feb)'),
                ], max_length=10)),
                ('min_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('max_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product_type', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='price_ranges',
                    to='products.producttype',
                )),
            ],
            options={'ordering': ['product_type__name', 'season'], 'unique_together': {('product_type', 'season')}},
        ),
    ]
