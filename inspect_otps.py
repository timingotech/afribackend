import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend_project.settings')
django.setup()
from apps.users.models import OTP

def show(email):
    q=OTP.objects.filter(email__iexact=email).order_by('-created_at')[:5]
    print('\n===', email, 'COUNT=', len(q))
    for o in q:
        print(o.pk, o.code, o.created_at, o.sent_at, o.send_result, repr(o.send_error))

show('adebolaaaaa@gmail.com')
show('oyenugaridwan@gmail.com')
