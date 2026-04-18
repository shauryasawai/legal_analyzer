from django.db import models
import uuid


class DocumentAnalysis(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('error', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    full_text = models.TextField(blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.filename


class Clause(models.Model):
    RISK_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    ]

    document = models.ForeignKey(DocumentAnalysis, on_delete=models.CASCADE, related_name='clauses')
    title = models.CharField(max_length=255)
    original_text = models.TextField()
    simplified_text = models.TextField()
    eli5_text = models.TextField(blank=True)   # Explain Like I'm 10
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES, default='low')
    risk_reason = models.TextField(blank=True)
    clause_type = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.document.filename} — {self.title}"
