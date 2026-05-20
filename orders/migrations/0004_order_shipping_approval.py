from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_delivery_shipping_price_order_shipping_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='shipping_approval',
            field=models.CharField(
                choices=[
                    ('pending',  'Awaiting Buyer Approval'),
                    ('approved', 'Approved by Buyer'),
                    ('rejected', 'Rejected by Buyer'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
