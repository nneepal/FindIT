from django.db import connection


def set_auth_user_full_name(user_id, full_name):
    normalized_full_name = (full_name or '').strip()
    with connection.cursor() as cursor:
        cursor.execute(
            'UPDATE auth_user SET full_name = %s WHERE id = %s',
            [normalized_full_name, user_id],
        )
