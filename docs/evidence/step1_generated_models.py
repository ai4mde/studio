from django.db import models
from django.contrib.auth.models import AbstractUser
from django.shortcuts import get_object_or_404



class Author(models.Model):
    name = models.CharField(max_length=255, default='', null=True, blank=True)
    nationality = models.CharField(max_length=255, default='', null=True, blank=True)
    


    
    def __str__(self):
        return str(self.name)
    
class Book(models.Model):
    title = models.CharField(max_length=255, default='', null=True, blank=True)
    isbn = models.CharField(max_length=255, default='', null=True, blank=True)
    year = models.IntegerField(default=0, null=True, blank=True)
    
    class Category(models.TextChoices):
        FICTION = 'FICTION', 'FICTION'
        NON_FICTION = 'NON_FICTION', 'NON_FICTION'
        SCIENCE = 'SCIENCE', 'SCIENCE'
        HISTORY = 'HISTORY', 'HISTORY'
        CHILDREN = 'CHILDREN', 'CHILDREN'
        
    category = models.CharField(
        max_length=512,
        choices=Category.choices,
        default=Category.choices[0][0]
    )
    
    Author = models.ForeignKey("Author", on_delete=models.CASCADE)
    


    


    
    def __str__(self):
        return str(self.title)
    
class Customer(models.Model):
    name = models.CharField(max_length=255, default='', null=True, blank=True)
    email = models.CharField(max_length=255, default='', null=True, blank=True)
    


    
    def __str__(self):
        return str(self.name)
    
class Loan(models.Model):
    loan_date = models.CharField(max_length=255, default='', null=True, blank=True)
    due_date = models.CharField(max_length=255, default='', null=True, blank=True)
    return_date = models.CharField(max_length=255, default='', null=True, blank=True)
    
    Customer = models.ForeignKey("Customer", on_delete=models.CASCADE)
    


    


    
    def __str__(self):
        return str(self.loan_date)
    
class BookLoan(models.Model):
    
    Loan = models.ForeignKey("Loan", on_delete=models.CASCADE)
    


    
    Book = models.ForeignKey("Book", on_delete=models.CASCADE)
    


    
    def __str__(self):
        return str(self.Loan)
    
