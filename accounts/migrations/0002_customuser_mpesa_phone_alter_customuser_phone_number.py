# Generated manually for M-Pesa payout integration

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='mpesa_phone',
            field=models.CharField(
                blank=True,
                help_text='Number registered on M-Pesa for salary payouts (2547XXXXXXXX).',
                max_length=12,
                validators=[
                    django.core.validators.RegexValidator(
                        message='M-Pesa number must be 2547XXXXXXXX or 2541XXXXXXXX.',
                        regex=r'^$|^254[17]\d{8}$',
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='phone_number',
            field=models.CharField(
                blank=True,
                help_text='Contact phone (e.g. 0712345678).',
                max_length=15,
                validators=[
                    django.core.validators.RegexValidator(
                        message='Enter a valid Kenyan phone (e.g. 0712345678 or +254712345678).',
                        regex=r'^\+?254\d{9}$|^0\d{9}$|^$',
                    )
                ],
            ),
        ),
    ]
