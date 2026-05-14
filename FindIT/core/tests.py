from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import ClaimVerification, FoundItem, FoundItemClaim


class PendingComplaintsViewTests(TestCase):
	def setUp(self):
		self.reporter = User.objects.create_user(username='reporter', password='password123')
		self.claimant = User.objects.create_user(username='claimant', password='password123')
		self.viewer = User.objects.create_user(username='viewer', password='password123')

		self.found_item = FoundItem.objects.create(
			reported_by=self.reporter,
			item_name='Blue Wallet',
			category='wallet',
			location_found='library',
			date_found='2026-05-01',
			condition='good',
			is_valuable=False,
			description='Blue leather wallet',
			image=SimpleUploadedFile('wallet.jpg', b'fake-image-bytes', content_type='image/jpeg'),
			claim_status='claimed',
		)

		self.claim = FoundItemClaim.objects.create(
			found_item=self.found_item,
			claimed_by=self.claimant,
		)

		ClaimVerification.objects.create(
			claim=self.claim,
			found_item=self.found_item,
			claimed_by=self.claimant,
			description='This wallet is mine.',
			status='closed',
			reviewed_by=self.reporter,
		)

	def test_closed_complaint_is_visible_to_other_users(self):
		self.client.force_login(self.viewer)

		response = self.client.get(reverse('core:pending-complaints'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Blue Wallet')
		self.assertContains(response, 'Complaint Closed')
		self.assertContains(response, 'claimant')
