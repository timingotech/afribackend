import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    django.setup()
    from apps.users.models import OTP
    from django.utils import timezone
    email = 'taonuga01@gmail.com'
    print('Inspecting OTPs for', email)
    q = OTP.objects.filter(email=email).order_by('-created_at')[:10]
    for o in q:
        print('id=', o.pk, 'code=', o.code, 'created_at=', o.created_at, 'sent_at=', o.sent_at, 'send_result=', o.send_result, 'send_error=', bool(o.send_error))
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
