# Gmail SMTP Setup for FINDIT

This project already uses Django's password reset flow. To send real reset emails through Gmail, configure SMTP and set the required environment variables.

## 1. Create a Gmail App Password

1. Turn on 2-Step Verification for the Gmail account you want to send from.
2. Go to Google Account settings.
3. Open Security -> App passwords.
4. Create a new app password for Mail.
5. Copy the 16-character password Google gives you.

Use that value as `EMAIL_HOST_PASSWORD`. Do not use your normal Gmail password.

## 2. Set environment variables

Create a local `.env` file from `.env.example` and fill in the real values:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=yourgmailaddress@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=yourgmailaddress@gmail.com
PASSWORD_RESET_TIMEOUT=3600
```

If you are not loading `.env` automatically, export the same variables in your terminal before starting Django.

## 3. Confirm Django settings

The project settings in [FindIT/settings.py](FindIT/settings.py) already read these values with `os.environ`.

The important ones are:

`EMAIL_BACKEND`
`EMAIL_HOST`
`EMAIL_PORT`
`EMAIL_USE_TLS`
`EMAIL_HOST_USER`
`EMAIL_HOST_PASSWORD`
`DEFAULT_FROM_EMAIL`

## 4. Run the project

From the project root:

```bash
source "/Users/arpannepal/Documents/Islington/FYP/System Application/.venv/bin/activate"
cd "/Users/arpannepal/Documents/Islington/FYP/System Application/FindIT"
python manage.py runserver
```

## 5. Test the forgot password flow

1. Open the login page.
2. Click `Forgot password?`.
3. Enter a registered email address.
4. Check the Gmail inbox.
5. Open the reset link and set a new password.

## 6. Common issues

If email sending fails, check:

1. The Gmail account has 2-Step Verification enabled.
2. The app password is correct.
3. `EMAIL_USE_TLS=true` and `EMAIL_PORT=587` are set.
4. The server is using the same environment variables you edited.
5. The account has not triggered Google security blocking.

If you want to keep secrets out of the shell, use a `.env` loader or set the variables in your IDE run configuration.
