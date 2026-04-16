# Generated manually for Daraja B2C wage payouts

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MpesaPayout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('phone', models.CharField(max_length=12)),
                ('month', models.IntegerField()),
                ('year', models.IntegerField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('queued', 'Queued'), ('success', 'Success'), ('failed', 'Failed')], db_index=True, default='pending', max_length=20)),
                ('conversation_id', models.CharField(blank=True, max_length=100)),
                ('originator_conversation_id', models.CharField(blank=True, max_length=100)),
                ('result_code', models.CharField(blank=True, max_length=32)),
                ('result_desc', models.TextField(blank=True)),
                ('transaction_id', models.CharField(blank=True, max_length=64)),
                ('receipt', models.CharField(blank=True, max_length=64)),
                ('raw_result', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('initiated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mpesa_payouts_initiated', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mpesa_payouts', to=settings.AUTH_USER_MODEL)),
                ('wage_summary', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mpesa_payouts', to='attendance.WageSummary')),
            ],
            options={
                'db_table': 'mpesa_payout',
                'ordering': ['-created_at'],
            },
        ),
    ]
