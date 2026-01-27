from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.core.management import call_command

@staff_member_required
def sync_movies(request):
    call_command("sync_tmdb_movies")
    return HttpResponse("Movies synced successfully")

@staff_member_required
def sync_cast(request):
    call_command("sync_tmdb_cast")
    return HttpResponse("Cast synced successfully")
