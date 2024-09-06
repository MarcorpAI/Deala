from django.db import models

# Create your models here.


class UserQuery(models.Model):
    query  = models.TextField(max_length=1000)
    date_created = models.DateTimeField(auto_now_add=True)



class Waitlist(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    
    def __str__(self):
        return self.name
    