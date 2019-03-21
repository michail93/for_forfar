from django.db import models
from django.contrib.postgres.fields import JSONField

# Create your models here.


CHECK_TYPE_CHOICES = [
        ("kitchen", "kitchen"),
        ("client", "client")
    ]

CHECK_STATUS_CHOICES = [
    ("new", "new"),
    ("rendered", "rendered"),
    ("printed", "printed"),
]


class Printer(models.Model):
    name = models.CharField(max_length=15)
    api_key = models.CharField(max_length=10, unique=True)
    check_type = models.CharField(choices=CHECK_TYPE_CHOICES, max_length=7)
    point_id = models.IntegerField()

    def __str__(self):
        return "point id {}; type {} ".format(self.point_id, self.check_type)


class Check(models.Model):
    printer_id = models.ForeignKey("Printer", on_delete=models.CASCADE,)
    type = models.CharField("Type of check", choices=CHECK_TYPE_CHOICES, max_length=7)
    order = JSONField()
    status = models.CharField("Status of check", choices=CHECK_STATUS_CHOICES, max_length=8)
    pdf_file = models.FileField(max_length=300)
