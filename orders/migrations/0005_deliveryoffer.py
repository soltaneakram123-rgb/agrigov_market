from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_order_shipping_approval'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryOffer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proposed_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(
                    choices=[
                        ('pending',  'Pending Buyer Approval'),
                        ('accepted', 'Accepted by Buyer'),
                        ('rejected', 'Rejected by Buyer'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('delivery', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='offers',
                    to='orders.delivery',
                )),
                ('transporter', models.ForeignKey(
                    limit_choices_to={'role': 'transporter'},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='delivery_offers',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['proposed_price'],
                'unique_together': {('delivery', 'transporter')},
            },
        ),
    ]
