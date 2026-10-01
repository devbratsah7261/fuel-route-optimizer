from django.db import models


class FuelStation(models.Model):
    opis_truckstop_id = models.IntegerField()
    truckstop_name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=5)
    rack_id = models.IntegerField()
    retail_price = models.DecimalField(max_digits =10, decimal_places = 6)


    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)


    def __str__(self):
        return f"{self.truckstop_name} - {self.city}, {self.state}"


