from django.db import migrations


ADD_COLUMN_SQL = "ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS full_name varchar(150) NOT NULL DEFAULT ''"
DROP_COLUMN_SQL = "ALTER TABLE auth_user DROP COLUMN IF EXISTS full_name"


def backfill_auth_user_full_name(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        for user in User.objects.all().iterator():
            profile, _ = UserProfile.objects.get_or_create(user_id=user.id)
            full_name = (profile.full_name or '').strip()
            if not full_name:
                full_name = (user.username or '').strip()
            cursor.execute(
                'UPDATE auth_user SET full_name = %s WHERE id = %s',
                [full_name, user.id],
            )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_sync_full_name_and_clear_auth_names'),
    ]

    operations = [
        migrations.RunSQL(ADD_COLUMN_SQL, reverse_sql=DROP_COLUMN_SQL),
        migrations.RunPython(backfill_auth_user_full_name, migrations.RunPython.noop),
    ]
