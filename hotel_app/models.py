from django.db import models

# Create your models here.

class Hotel(models.Model):
    image = models.ImageField(upload_to='hotels/', blank=True, null=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    country = models.CharField(max_length=50)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name
