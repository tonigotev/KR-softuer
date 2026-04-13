from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_info(_request):
    return JsonResponse({
        'message': 'GP Visits Scheduling API',
        'version': '1.0',
        'current_api_version': 'v1',
        'endpoints': {
            'admin': '/admin/',
            'health': '/health/',
            'v1': {
                'authentication': '/v1/auth/',
                'scheduling': '/v1/scheduling/'
            }
        }
    })


def healthcheck(_request):
    return JsonResponse({"status": "ok"})


v1_patterns = [
    path('auth/', include('authentication.urls')),
    path('scheduling/', include('scheduling.urls')),
]

urlpatterns = [
    path('', api_info, name='api_info'),
    path('health/', healthcheck, name='health'),
    path('admin/', admin.site.urls),
    path('v1/', include(v1_patterns)),
]
