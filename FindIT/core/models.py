from django.db import models
from django.contrib.auth.models import User


class FoundItem(models.Model):
	CLAIM_STATUS_CHOICES = [
		('open', 'Open'),
		('claimed', 'Claimed'),
	]

	CATEGORY_CHOICES = [
		('electronics', 'Electronics'),
		('clothing', 'Clothing'),
		('stationery', 'Stationery'),
		('jewellery', 'Jewellery'),
		('bottle', 'Bottle'),
		('wallet', 'Wallet'),
		('bags', 'Bags'),
		('documents', 'Documents'),
		('keys', 'Keys'),
		('other', 'Other'),
	]

	LOCATION_CHOICES = [
		('cafeteria', 'Cafeteria'),
		('classroom', 'Classroom'),
		('lecture_hall', 'Lecture Hall'),
		('parking', 'Parking Lot A'),
		('library', 'Library'),
		('playground', 'Playground'),
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
	claim_status = models.CharField(max_length=20, choices=CLAIM_STATUS_CHOICES, default='open')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'found_items'
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.item_name} ({self.get_category_display()})'


class LostItem(models.Model):
	CLAIM_STATUS_CHOICES = [
		('open', 'Open'),
		('claimed', 'Claimed'),
	]

	CATEGORY_CHOICES = [
		('electronics', 'Electronics'),
		('clothing', 'Clothing'),
		('stationery', 'Stationery'),
		('jewellery', 'Jewellery'),
		('bottle', 'Bottle'),
		('wallet', 'Wallet'),
		('bags', 'Bags'),
		('documents', 'Documents'),
		('keys', 'Keys'),
		('other', 'Other'),
	]

	CONDITION_CHOICES = [
		('new', 'New'),
		('good', 'Good'),
		('damaged', 'Damaged'),
	]

	LOCATION_CHOICES = [
		('cafeteria', 'Cafeteria'),
		('classroom', 'Classroom'),
		('lecture_hall', 'Lecture Hall'),
		('parking', 'Parking Lot A'),
		('library', 'Library'),
		('playground', 'Playground'),
	]

	searched_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lost_items')
	item_name = models.CharField(max_length=120)
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
	condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
	location_lost = models.CharField(max_length=20, choices=LOCATION_CHOICES)
	date_lost = models.DateField()
	description = models.TextField()
	image = models.FileField(upload_to='lost_items/')
	claim_status = models.CharField(max_length=20, choices=CLAIM_STATUS_CHOICES, default='open')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'lost_items'
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.item_name} ({self.get_category_display()})'


class FoundItemClaim(models.Model):
	found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, related_name='claims')
	claimed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='found_item_claims')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'found_item_claims'
		ordering = ['-created_at']
		constraints = [
			models.UniqueConstraint(fields=['found_item', 'claimed_by'], name='unique_found_item_claim_per_user')
		]

	def __str__(self):
		return f'{self.found_item.item_name} claimed by {self.claimed_by.username}'


class ClaimVerification(models.Model):
	VERIFICATION_STATUS_CHOICES = [
		('unverified', 'Unverified'),
		('verified', 'Verified'),
		('rejected', 'Rejected'),
		('closed', 'Closed'),
	]

	claim = models.OneToOneField(FoundItemClaim, on_delete=models.CASCADE, related_name='verification')
	found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, related_name='verifications')
	claimed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claim_verifications')
	description = models.TextField()
	proof_image = models.FileField(upload_to='claim_verifications/', blank=True, null=True)
	status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='unverified')
	admin_message = models.TextField(blank=True)
	reviewed_by = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='reviewed_claim_verifications',
	)
	reviewed_at = models.DateTimeField(blank=True, null=True)
	submitted_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'claim_verification'
		ordering = ['-submitted_at']

	def __str__(self):
		return f'Verification for {self.found_item.item_name} by {self.claimed_by.username}'
