from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DocumentAnalysis',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('filename', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to='uploads/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(
                    choices=[('pending','Pending'),('processing','Processing'),('done','Done'),('error','Error')],
                    default='pending', max_length=20)),
                ('full_text', models.TextField(blank=True)),
            ],
            options={'ordering': ['-uploaded_at']},
        ),
        migrations.CreateModel(
            name='Clause',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('original_text', models.TextField()),
                ('simplified_text', models.TextField()),
                ('eli5_text', models.TextField(blank=True)),
                ('risk_level', models.CharField(
                    choices=[('low','Low Risk'),('medium','Medium Risk'),('high','High Risk')],
                    default='low', max_length=10)),
                ('risk_reason', models.TextField(blank=True)),
                ('clause_type', models.CharField(blank=True, max_length=100)),
                ('order', models.PositiveIntegerField(default=0)),
                ('document', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='clauses',
                    to='legal_app.documentanalysis')),
            ],
            options={'ordering': ['order']},
        ),
    ]
