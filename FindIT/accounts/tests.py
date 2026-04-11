import re

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import PasswordResetRequest


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPass123!',
        )

    def test_password_reset_end_to_end(self):
        response = self.client.post(
            reverse('accounts:password_reset'),
            {'email': self.user.email},
            follow=True,
        )

        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password Reset Link', mail.outbox[0].subject)

        reset_request = PasswordResetRequest.objects.latest('requested_at')
        self.assertTrue(reset_request.sent_successfully)
        self.assertEqual(reset_request.email, self.user.email)
        self.assertEqual(reset_request.user, self.user)

        match = re.search(
            r'/accounts/password-reset-confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z\-]+)/',
            mail.outbox[0].body,
        )
        self.assertIsNotNone(match)
        reset_url = match.group(0)

        confirm_get = self.client.get(reset_url, follow=True)
        self.assertEqual(confirm_get.status_code, 200)
        self.assertContains(confirm_get, 'Set New Password')
        set_password_url = confirm_get.request['PATH_INFO']

        confirm_post = self.client.post(
            set_password_url,
            {
                'new_password1': 'BrandNewPass123!',
                'new_password2': 'BrandNewPass123!',
            },
            follow=True,
        )
        self.assertRedirects(confirm_post, reverse('accounts:password_reset_complete'))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('BrandNewPass123!'))

    def test_password_reset_unknown_email_shows_error_and_logs_attempt(self):
        response = self.client.post(
            reverse('accounts:password_reset'),
            {'email': 'unknown@example.com'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No active account found with this email address.')
        self.assertEqual(len(mail.outbox), 0)

        reset_request = PasswordResetRequest.objects.latest('requested_at')
        self.assertFalse(reset_request.sent_successfully)
        self.assertEqual(reset_request.email, 'unknown@example.com')
        self.assertIsNone(reset_request.user)
