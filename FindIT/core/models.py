from django.db import models
from django.contrib.auth.models import User


class FoundItem(models.Model):
	CATEGORY_CHOICES = [
		('electronics', 'Electronics'),
		('clothing', 'Clothing & Accessories'),
		('documents', 'IDs & Documents'),
		('keys', 'Keys'),
		('other', 'Other'),
	]

	LOCATION_CHOICES = [
		('library', 'Main Library'),
		('cafeteria', 'Cafeteria'),
		('gym', 'Gymnasium'),
		('parking', 'Parking Lot A'),
		('lobby', 'Main Lobby'),
		('other', 'Other'),
	]

	CONDITION_CHOICES = [
		('new', 'New'),
		('good', 'Good'),
		('damaged', 'Damaged'),
	]

	reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='found_items')
	item_name = models.CharField(max_length=120)
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
	location_found = models.CharField(max_length=20, choices=LOCATION_CHOICES)
	date_found = models.DateField()
	condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
	is_valuable = models.BooleanField(default=False)
	description = models.TextField()
	image = models.FileField(upload_to='found_items/')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'found_items'
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.item_name} ({self.get_category_display()})'


class LostItem(models.Model):
	CATEGORY_CHOICES = [
		('electronics', 'Electronics'),
		('clothing', 'Clothing'),
		('accessories', 'Accessories'),
		('documents', 'Documents'),
		('other', 'Other'),
	]

	CONDITION_CHOICES = [
		('new', 'Like New'),
		('good', 'Good'),
		('fair', 'Fair (Scratched)'),
		('poor', 'Damaged'),
	]

	LOCATION_CHOICES = [
		('library', 'Main Library'),
		('cafeteria', 'Student Cafeteria'),
		('gym', 'Sports Gym'),
		('hall_a', 'Lecture Hall A'),
		('dorm', 'Dormitory Block'),
		('other', 'Other'),
	]

	searched_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lost_items')
	item_name = models.CharField(max_length=120)
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
	condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
	location_lost = models.CharField(max_length=20, choices=LOCATION_CHOICES)
	date_lost = models.DateField()
	description = models.TextField()
	image = models.FileField(upload_to='lost_items/')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'lost_items'
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.item_name} ({self.get_category_display()})'
