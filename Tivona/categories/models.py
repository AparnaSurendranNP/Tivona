from django.db import models
from django.utils.text import slugify

# Create your models here.

class Category(models.Model):
    name=models.CharField(max_length=25)
    image=models.ImageField(upload_to='category_image/',blank=False,null=False)
    product_count=models.PositiveIntegerField(default=0)
    description=models.TextField()
    url_name=models.CharField(max_length=20,unique=True,default=None)
    is_listed=models.BooleanField(default=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self) :
        return self.name
    