from django.contrib import admin
from .models import Lecteur, Bibliothecaire, Livre, Emprunt, Amende, Commentaire, Reservation

admin.site.register(Lecteur)
admin.site.register(Bibliothecaire)
admin.site.register(Livre)
admin.site.register(Emprunt)
admin.site.register(Amende)
admin.site.register(Commentaire)
admin.site.register(Reservation)