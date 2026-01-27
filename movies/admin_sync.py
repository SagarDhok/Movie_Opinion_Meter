from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.core.management import call_command

@staff_member_required
def sync_tmdb(request):
    call_command("sync_tmdb_movies")
    call_command("sync_tmdb_cast")
    return HttpResponse("TMDB movies & cast synced successfully")
