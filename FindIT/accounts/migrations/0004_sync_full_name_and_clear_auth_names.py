from django.db import migrations


def sync_full_name_and_clear_auth_names(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')

    for user in User.objects.all().iterator():
        profile, _ = UserProfile.objects.get_or_create(user_id=user.id)

        profile_name = (profile.full_name or '').strip()
        auth_name = f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip()

        if not profile_name and auth_name:
            profile.full_name = auth_name
            profile.save(update_fields=['full_name'])

        if user.first_name or user.last_name:
            user.first_name = ''
            user.last_name = ''
            user.save(update_fields=['first_name', 'last_name'])


def noop_reverse(apps, schema_editor):
    # Names were intentionally consolidated into accounts_userprofile.full_name.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_passwordresetrequest'),
    ]

    operations = [
        migrations.RunPython(sync_full_name_and_clear_auth_names, noop_reverse),
    ]
