from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from .models import Emprunt

def retourner_livre(request, emprunt_id):
    emprunt = get_object_or_404(Emprunt, pk=emprunt_id)
    # Marquer l'emprunt comme retourné et mettre à jour la date de retour effective
    emprunt.est_en_retard = False
    emprunt.date_retour_effectif = timezone.now()
    emprunt.save()
    # Incrémenter le nombre d'exemplaires du livre
    emprunt.livre.nombre_exemplaires += 1
    emprunt.livre.save()
    return redirect('mes_emprunts')
