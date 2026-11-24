from django.db import models
from .deelnemer import Deelnemer
from survey.models import Category
from datetime import datetime
from django.utils import timezone

class HoofdDoel(models.Model):
    category = models.OneToOneField(Category, on_delete=models.CASCADE, primary_key=True, related_name="categorie")  