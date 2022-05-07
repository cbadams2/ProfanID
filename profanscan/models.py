from django.db import models

class BadWord(models.Model):
    badword = models.CharField(max_length=100)

    EXPLICIT   = 'X'
    Q_EXPLICIT = 'Q'
    SEVERITY_CHOICES = [
        (EXPLICIT, 'Explicit'),
        (Q_EXPLICIT, 'Questionably Explicit'),
    ]

    severity = models.CharField(
        max_length=2,
        blank=True,
        choices=SEVERITY_CHOICES,
        default=EXPLICIT,
    )

    def __str__(self):
        return self.badword