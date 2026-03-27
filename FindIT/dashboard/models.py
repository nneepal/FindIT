from django.db import models


class AdminManagedItem(models.Model):
	title = models.CharField(max_length=120)
	category = models.CharField(max_length=80)
	location = models.CharField(max_length=120)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.title
