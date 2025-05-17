from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from .models import Lecteur, Bibliothecaire, Livre, Emprunt, Reservation
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
from datetime import date, timedelta
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from datetime import date
from .models import Emprunt
from django.views.decorators.http import require_POST
from .models import Livre, Commentaire
from django.views.decorators.csrf import csrf_exempt
from library import models
from .forms import LivreForm  # Import du formulaire LivreForm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import urllib.parse
from django.urls import reverse


def liste_livres_admin_view(request):
    # On suppose que tous les livres sont ajoutés par un admin (bibliothécaire)
    livres = Livre.objects.all().order_by('-livre_id')
    
    # Obtenir la liste des catégories uniques
    categories_uniques = Livre.objects.exclude(categorie_livre__isnull=True).exclude(categorie_livre='').values_list('categorie_livre', flat=True).distinct()
    
    # Configuration de la pagination
    paginator = Paginator(livres, 10)  # 10 livres par page
    page = request.GET.get('page', 1)
    
    try:
        livres_pagines = paginator.page(page)
    except PageNotAnInteger:
        livres_pagines = paginator.page(1)
    except EmptyPage:
        livres_pagines = paginator.page(paginator.num_pages)
    
    return render(request, 'library/liste_livres_admin.html', {
        'livres': livres_pagines,
        'categories_uniques': categories_uniques
    })


def liste_emprunts_en_cours_view(request):
    from datetime import date
    today = date.today()
    emprunts = Emprunt.objects.filter(date_retour__gte=today) | Emprunt.objects.filter(date_retour__isnull=True)
    emprunts = emprunts.select_related('livre', 'lecteur').order_by('-date_emprunt')
    return render(request, 'library/liste_emprunts_en_cours.html', {'emprunts': emprunts, 'today': today})


# Page de connexion

# Page d'inscription
def S_inscrire(request):
    return render(request, 'library/S_inscrire.html')


# Inscription (uniquement pour les lecteurs)
def inscription_view(request):
    if request.method == 'POST':
        try:
            prenom = request.POST.get('prenom')
            nom = request.POST.get('nom')
            email = request.POST.get('email')
            mot_de_passe = request.POST.get('password')
            confirm_mot_de_passe = request.POST.get('confirmPassword')

            print(f"Prénom : {prenom}, Nom : {nom}, Email : {email}")

            # Vérifiez que tous les champs sont remplis
            if not prenom or not nom or not email or not mot_de_passe or not confirm_mot_de_passe:
                print("Tous les champs ne sont pas remplis.")
                return render(request, 'library/S_inscrire.html', {
                    'error': "Tous les champs sont obligatoires.",
                    'prenom': prenom,
                    'nom': nom,
                    'email': email,
                })

            # Vérifiez que les mots de passe correspondent
            if mot_de_passe != confirm_mot_de_passe:
                print("Les mots de passe ne correspondent pas.")
                return render(request, 'library/S_inscrire.html', {
                    'error': "Les mots de passe ne correspondent pas.",
                    'prenom': prenom,
                    'nom': nom,
                    'email': email,
                })

            # Vérifiez que l'email n'est pas déjà utilisé
            if Lecteur.objects.filter(email=email).exists() or Bibliothecaire.objects.filter(email=email).exists():
                print("Email déjà utilisé.")
                return render(request, 'library/S_inscrire.html', {
                    'error': "Cet email est déjà utilisé.",
                    'prenom': prenom,
                    'nom': nom,
                    'email': email,
                })

            # Créez le lecteur
            lecteur = Lecteur.objects.create(
                prenom=prenom,
                nom=nom,
                email=email,
                mot_de_passe=make_password(mot_de_passe)  # Hachez le mot de passe
            )
            print(f"Lecteur créé : {lecteur}")

            # Redirigez vers la page de connexion
            messages.success(request, "Inscription réussie ! Vous pouvez maintenant vous connecter.")
            return redirect('connexion')

        except Exception as e:
            print(f"Erreur lors de l'inscription : {str(e)}")
            return render(request, 'library/S_inscrire.html', {
                'error': f"Une erreur est survenue : {str(e)}",
                'prenom': prenom,
                'nom': nom,
                'email': email,
            })

    return render(request, 'library/S_inscrire.html')


# Connexion (pour les lecteurs et bibliothécaires)
def connexion_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('mot_de_passe')

        print(f"=== Tentative de connexion pour {email} ===")

        try:
            # Vérifier d'abord si c'est un bibliothécaire
            if Bibliothecaire.objects.filter(email=email).exists():
                bibliothecaire = Bibliothecaire.objects.get(email=email)
                if check_password(mot_de_passe, bibliothecaire.mot_de_passe):
                    # Connexion réussie
                    request.session['utilisateur_id'] = bibliothecaire.bibliothecaire_id
                    request.session['role'] = 'bibliothecaire'
                    print("=== Connexion bibliothécaire réussie ===")
                    return redirect('dashboard')

            # Si ce n'est pas un bibliothécaire, vérifier si c'est un lecteur
            elif Lecteur.objects.filter(email=email).exists():
                lecteur = Lecteur.objects.get(email=email)
                if check_password(mot_de_passe, lecteur.mot_de_passe):
                    request.session['utilisateur_id'] = lecteur.lecteur_id
                    request.session['role'] = 'lecteur'
                    return redirect('accueil')

            print("=== Échec de la connexion ===")
            messages.error(request, "Email ou mot de passe incorrect")

        except Exception as e:
            print(f"Erreur : {str(e)}")
            messages.error(request, "Une erreur s'est produite")

    return render(request, 'library/Se_connecter.html')


# Page d'accueil pour Lecteurs
def accueil_view(request):
    if 'utilisateur_id' not in request.session:
        return redirect('connexion')

    query = request.GET.get('q', '').strip()
    if query:
        livres = Livre.objects.filter(
            Q(titre_livre__icontains=query) |
            Q(auteur_livre__icontains=query) |
            Q(categorie_livre__icontains=query)
        )
    else:
        # Récupérer les 4 derniers livres ajoutés par ordre décroissant de leur ID
        # L'ID est généralement incrémenté à chaque nouvel ajout, donc plus l'ID est élevé, plus le livre est récent
        livres = Livre.objects.all().order_by('-livre_id')

    context = {
        'livres': livres,
        'query': query,
        'livre_id': request.GET.get('livre_id')
    }
    return render(request, 'library/Accueil.html', context)



# Vue pour ajouter un livre (formulaire admin)
def ajouter_livre_view(request):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour accéder à cette page.")
        return redirect('connexion')
    
    bibliothecaire = Bibliothecaire.objects.get(bibliothecaire_id=request.session['utilisateur_id'])
    
    if request.method == 'POST':
        form = LivreForm(request.POST, request.FILES)
        if form.is_valid():
            # Vérifier si l'ISBN existe déjà
            isbn = form.cleaned_data['isbn'].strip()
            if Livre.objects.filter(isbn=isbn).exists():
                messages.error(request, "Un livre avec cet ISBN existe déjà.")
            else:
                livre = form.save(commit=False)
                livre.bibliothecaire = bibliothecaire
                livre.save()
                messages.success(request, "Le livre a été ajouté avec succès.")
                return redirect('livres_admin')
    else:
        form = LivreForm()
    
    return render(request, 'library/ajouter_livre.html', {
        'form': form,
        'bibliothecaire': bibliothecaire,
        'title': 'Ajouter un livre'
    })

# Vue pour modifier un livre (formulaire admin)
def modifier_livre_view(request, livre_id):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour accéder à cette page.")
        return redirect('connexion')
    
    try:
        livre = Livre.objects.get(livre_id=livre_id)
    except Livre.DoesNotExist:
        messages.error(request, "Le livre n'existe pas.")
        return redirect('livres_admin')
    
    if request.method == 'POST':
        form = LivreForm(request.POST, request.FILES, instance=livre)
        if form.is_valid():
            # Vérifier si l'ISBN est unique (mais on ignore l'ISBN actuel du livre)
            isbn = form.cleaned_data['isbn'].strip()
            if Livre.objects.filter(isbn=isbn).exclude(livre_id=livre_id).exists():
                messages.error(request, "Un autre livre avec cet ISBN existe déjà.")
            else:
                form.save()
                messages.success(request, "Le livre a été modifié avec succès.")
                return redirect('livres_admin')
    else:
        form = LivreForm(instance=livre)
    
    return render(request, 'library/ajouter_livre.html', {
        'form': form, 
        'mode_edition': True,
        'livre': livre
    })

# Ancienne vue pour supprimer un livre (conservée pour référence)
def supprimer_livre_view_old(request, livre_id):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour accéder à cette page.")
        return redirect('connexion')
    
    # Variables pour stocker les informations du livre
    titre_livre = None
    id_livre = livre_id
    
    try:
        # On utilise select_related pour obtenir le bibliothécaire associé en une seule requête
        livre = Livre.objects.select_related('bibliothecaire').get(livre_id=livre_id)
        titre_livre = livre.titre_livre
        
        # Vérification des emprunts en cours - seule condition qui empêche la suppression
        emprunts_en_cours = Emprunt.objects.filter(livre=livre, date_retour__isnull=True).count()
        if emprunts_en_cours > 0:
            messages.error(request, f"Impossible de supprimer '{titre_livre}' car il a {emprunts_en_cours} emprunt(s) en cours.")
            return redirect('livres_admin')
        
        # Approach 1: Suppression par étapes avec gestion explicite des erreurs
        try:
            with transaction.atomic():
                # Supprimer les dépendances dans un ordre précis
                # 1. Réservations
                Reservation.objects.filter(livre_id=livre_id).delete()
                
                # 2. Commentaires
                Commentaire.objects.filter(livre_id=livre_id).delete()
                
                # 3. Tous les emprunts terminés
                Emprunt.objects.filter(livre_id=livre_id, date_retour__isnull=False).delete()
                
                # Approche plus robuste pour supprimer le livre lui-même
                # Utiliser SQL directement pour contourner les problèmes potentiels ORM
                from django.db import connection
                with connection.cursor() as cursor:
                    # Supprimer directement le livre par son ID
                    cursor.execute("DELETE FROM library_livre WHERE livre_id = %s", [livre_id])
                
                # Message de succès
                messages.success(request, f"Le livre '{titre_livre}' a été supprimé avec succès.")
                
        except Exception as atomic_error:
            # Si une erreur se produit, essayons l'approche 2
            with transaction.atomic():
                # Approach 2: Suppression directe et dépendance sur le CASCADE en SQL
                from django.db import connection
                with connection.cursor() as cursor:
                    # Utiliser ON DELETE CASCADE des définitions de tables SQL
                    # Désactiver temporairement les contraintes de clé étrangère pour une suppression forcée
                    cursor.execute("PRAGMA foreign_keys = OFF;")
                    
                    # Supprimer les dépendances explicitement dans l'ordre inverse
                    cursor.execute("DELETE FROM library_commentaire WHERE livre_id = %s", [livre_id])
                    cursor.execute("DELETE FROM library_reservation WHERE livre_id = %s", [livre_id])
                    cursor.execute("DELETE FROM library_emprunt WHERE livre_id = %s", [livre_id])
                    
                    # Supprimer le livre
                    cursor.execute("DELETE FROM library_livre WHERE livre_id = %s", [livre_id])
                    
                    # Réactiver les contraintes
                    cursor.execute("PRAGMA foreign_keys = ON;")
                
                # Message de succès pour la deuxième approche
                messages.success(request, f"Le livre '{titre_livre}' a été supprimé avec succès.")
                
    except Livre.DoesNotExist:
        messages.error(request, f"Le livre avec ID {id_livre} n'existe pas.")
    except Exception as e:
        # Journaliser l'erreur complète pour le débogage
        import traceback
        print(f"ERREUR CRITIQUE DE SUPPRESSION: {str(e)}")
        print(traceback.format_exc())
        
        messages.error(request, f"Erreur lors de la suppression du livre: {str(e)}")
    
    return redirect('livres_admin')

# Suppression de livre simplifiée avec redirection et notification
def supprimer_livre_view(request, livre_id):
    # Vérifier les permissions
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour accéder à cette page.")
        return redirect('connexion')
    
    redirect_to = request.GET.get('redirect', 'liste_livres_admin')
    
    # Récupérer et supprimer le livre
    try:
        livre = get_object_or_404(Livre, livre_id=livre_id)
        titre_livre = livre.titre_livre
        livre.delete()
        
        # Créer un message de succès qui sera affiché via JavaScript (Toast)
        success_message = f'Le livre "{titre_livre}" a été supprimé avec succès'
        encoded_message = urllib.parse.quote(success_message)
        
        # Rediriger avec le message en paramètre URL
        return redirect(f'{reverse(redirect_to)}?success_message={encoded_message}')
        
    except Exception as e:
        messages.error(request, f'Une erreur est survenue lors de la suppression: {str(e)}')
        return redirect(redirect_to)

# Page de confirmation de suppression avec formulaire POST
def confirmer_suppression_livre(request, livre_id):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour accéder à cette page.")
        return redirect('connexion')
    
    try:
        livre = Livre.objects.select_related('bibliothecaire').get(livre_id=livre_id)
        
        # Vérifier si le livre a des emprunts en cours
        emprunts_en_cours = Emprunt.objects.filter(livre=livre, date_retour__isnull=True).count()
        if emprunts_en_cours > 0:
            messages.error(request, f"Impossible de supprimer '{livre.titre_livre}' car il a {emprunts_en_cours} emprunt(s) en cours.")
            return redirect('livres_admin')
        
        # Traitement du formulaire de suppression
        if request.method == 'POST':
            titre_livre = livre.titre_livre
            
            try:
                # Utiliser l'ORM Django de base mais dans une transaction
                with transaction.atomic():
                    # 1. Supprimer manuellement toutes les relations
                    Commentaire.objects.filter(livre=livre).delete()
                    Reservation.objects.filter(livre=livre).delete()
                    Emprunt.objects.filter(livre=livre).delete()
                    
                    # 2. Supprimer le livre lui-même
                    livre.delete()
                    
                    messages.success(request, f"Le livre '{titre_livre}' a été supprimé avec succès.")
                    return redirect('livres_admin')
            except Exception as e:
                import traceback
                print(f"ERREUR DE SUPPRESSION: {str(e)}")
                print(traceback.format_exc())
                messages.error(request, f"Erreur lors de la suppression: {str(e)}")
        
        # Affichage du formulaire de confirmation
        return render(request, 'library/confirm_delete_livre.html', {'livre': livre})
        
    except Livre.DoesNotExist:
        messages.error(request, f"Le livre avec ID {livre_id} n'existe pas.")
        return redirect('livres_admin')
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('livres_admin')

# Vue pour ajouter un emprunt (formulaire admin)
def ajouter_emprunt_view(request):
    from datetime import date
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour ajouter un emprunt.")
        return redirect('connexion')

    lecteurs = Lecteur.objects.all()
    livres = Livre.objects.filter(nombre_exemplaires__gt=0)
    context = {'lecteurs': lecteurs, 'livres': livres}

    if request.method == 'POST':
        lecteur_id = request.POST.get('lecteur')
        livre_id = request.POST.get('livre')
        date_emprunt = request.POST.get('date_emprunt') or date.today()
        date_retour = request.POST.get('date_retour') or None
        context.update({'lecteur_id': lecteur_id, 'livre_id': livre_id, 'date_emprunt': date_emprunt, 'date_retour': date_retour})
        try:
            if not lecteur_id or not livre_id:
                raise ValueError("Veuillez sélectionner un lecteur et un livre.")
            livre = Livre.objects.get(pk=livre_id)
            if livre.nombre_exemplaires <= 0:
                raise ValueError("Ce livre n'est plus disponible.")
            lecteur = Lecteur.objects.get(pk=lecteur_id)
            Emprunt.objects.create(
                livre=livre,
                lecteur=lecteur,
                date_emprunt=date_emprunt,
                date_retour=date_retour
            )
            livre.nombre_exemplaires -= 1
            livre.save()
            messages.success(request, "Emprunt enregistré avec succès !")
            return redirect('ajouter_emprunt')
        except Exception as e:
            messages.error(request, f"Erreur lors de l'enregistrement de l'emprunt : {str(e)}")
            return render(request, 'library/ajouter_emprunt.html', context)
    return render(request, 'library/ajouter_emprunt.html', context)

# Vue pour réserver un livre

def reserver_livre(request, livre_id):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'lecteur':
        messages.error(request, "Vous devez être connecté en tant que lecteur pour réserver un livre.")
        return redirect('connexion')
    try:
        livre = Livre.objects.get(pk=livre_id)
        # Ici, on suppose que le modèle Reservation existe avec les champs livre, lecteur, date_reservation
        from .models import Reservation
        lecteur = Lecteur.objects.get(pk=request.session['utilisateur_id'])
        Reservation.objects.create(livre=livre, lecteur=lecteur)
        messages.success(request, f"Vous avez réservé le livre '{livre.titre_livre}' avec succès !")
    except Exception as e:
        messages.error(request, f"Erreur lors de la réservation : {str(e)}")
    return redirect('catalogue')

# Vue pour ajouter un lecteur (formulaire admin)
def ajouter_lecteur_view(request):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour ajouter un lecteur.")
        return redirect('connexion')

    if request.method == 'POST':
        prenom = request.POST.get('prenom')
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('mot_de_passe')
        confirm_mot_de_passe = request.POST.get('confirm_mot_de_passe')
        context = {
            'prenom': prenom,
            'nom': nom,
            'email': email,
        }
        try:
            if not prenom or not nom or not email or not mot_de_passe or not confirm_mot_de_passe:
                raise ValueError("Tous les champs sont obligatoires.")
            if mot_de_passe != confirm_mot_de_passe:
                raise ValueError("Les mots de passe ne correspondent pas.")
            if Lecteur.objects.filter(email=email).exists() or Bibliothecaire.objects.filter(email=email).exists():
                raise ValueError("Cet email est déjà utilisé.")
            Lecteur.objects.create(
                prenom=prenom,
                nom=nom,
                email=email,
                mot_de_passe=make_password(mot_de_passe)
            )
            messages.success(request, "Lecteur ajouté avec succès !")
            return redirect('ajouter_lecteur')
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout du lecteur : {str(e)}")
            return render(request, 'library/ajouter_lecteur.html', context)
    return render(request, 'library/ajouter_lecteur.html')

# Vue pour ajouter un bibliothécaire (formulaire admin)

def retourner_livre(request, emprunt_id):
    # Vérifier que l'utilisateur est connecté
    if 'utilisateur_id' not in request.session:
        messages.error(request, "Vous devez être connecté pour effectuer cette action.")
        return redirect('connexion')
    
    emprunt = get_object_or_404(Emprunt, pk=emprunt_id)
    livre = emprunt.livre
    
    # Vérifier si le livre était indisponible avant le retour
    etait_indisponible = livre.nombre_exemplaires == 0
    
    # Marquer l'emprunt comme retourné et mettre à jour la date de retour effective
    emprunt.est_en_retard = False
    emprunt.date_retour_effectif = timezone.now()
    emprunt.save()
    
    # Incrémenter le nombre d'exemplaires du livre
    livre.nombre_exemplaires += 1
    livre.save()
    
    # Message de succès
    if etait_indisponible and livre.nombre_exemplaires > 0:
        messages.success(request, f"Le livre '{livre.titre_livre}' a été retourné avec succès et est maintenant disponible pour de nouveaux emprunts.")
    else:
        messages.success(request, f"Le livre '{livre.titre_livre}' a été retourné avec succès. Nombre d'exemplaires disponibles: {livre.nombre_exemplaires}")
    
    # Redirection en fonction du rôle
    if request.session.get('role') == 'bibliothecaire':
        return redirect('emprunts_en_cours')
    else:
        return redirect('mes_emprunts')

def ajouter_bibliothecaire_view(request):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour ajouter un bibliothécaire.")
        return redirect('connexion')

    if request.method == 'POST':
        prenom = request.POST.get('prenom')
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('mot_de_passe')
        confirm_mot_de_passe = request.POST.get('confirm_mot_de_passe')
        context = {
            'prenom': prenom,
            'nom': nom,
            'email': email,
        }
        if mot_de_passe != confirm_mot_de_passe:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'library/ajouter_bibliothecaire.html', context)
        try:
            if Bibliothecaire.objects.filter(email=email).exists():
                messages.error(request, "Un bibliothécaire avec cet email existe déjà.")
                return render(request, 'library/ajouter_bibliothecaire.html', context)
            Bibliothecaire.objects.create(
                prenom=prenom,
                nom=nom,
                email=email,
                mot_de_passe=make_password(mot_de_passe)
            )
            messages.success(request, "Bibliothécaire ajouté avec succès !")
            return redirect('ajouter_bibliothecaire')
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout du bibliothécaire : {str(e)}")
            return render(request, 'library/ajouter_bibliothecaire.html', context)
    return render(request, 'library/ajouter_bibliothecaire.html')

# Dashboard pour Bibliothécaires

def emprunts_en_retard_view(request):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour accéder à cette page.")
        return redirect('connexion')
    today = date.today()
    emprunts_retard = Emprunt.objects.filter(est_en_retard=True).select_related('livre', 'lecteur').order_by('-date_retour')
    return render(request, 'library/liste_emprunts_en_retard.html', {'emprunts': emprunts_retard, 'today': today})
def dashboard_view(request):
    # Récupérer les informations du bibliothécaire si disponible
    bibliothecaire = None
    if 'utilisateur_id' in request.session and request.session.get('role') == 'bibliothecaire':
        try:
            bibliothecaire = Bibliothecaire.objects.get(bibliothecaire_id=request.session['utilisateur_id'])
        except Bibliothecaire.DoesNotExist:
            pass
    
    # Récupérer les statistiques quel que soit l'état de l'authentification
    total_livres = Livre.objects.count()
    total_emprunts = Emprunt.objects.count()  # Total de tous les emprunts (historique complet)
    
    # Pour les retards, vérifions la date de retour par rapport à aujourd'hui
    from datetime import date
    today = date.today()
    total_retard = Emprunt.objects.filter(est_en_retard=True).count()
    
    # Calculer un taux de rotation qui a du sens même sans emprunts actuels
    if total_livres > 0:
        taux_rotation = int((total_emprunts / total_livres) * 100)
    else:
        taux_rotation = 0
    
    # Récupérer les paramètres de recherche et de filtrage
    recherche = request.GET.get('recherche', '').strip()
    statut = request.GET.get('statut', '')
    
    # Base de la requête pour récupérer les emprunts
    emprunts_query = Emprunt.objects.select_related('livre', 'lecteur').order_by('-date_emprunt')
    
    # Filtrer par nom de lecteur si un terme de recherche est fourni
    if recherche:
        emprunts_query = emprunts_query.filter(
            Q(lecteur__nom__icontains=recherche) | 
            Q(lecteur__prenom__icontains=recherche)
        )
    
    # Filtrer par statut si un statut est sélectionné
    if statut:
        if statut == 'En cours':
            emprunts_query = emprunts_query.filter(date_retour__isnull=True, est_en_retard=False)
        elif statut == 'En retard':
            emprunts_query = emprunts_query.filter(est_en_retard=True)
        elif statut == 'Terminé':
            # Le statut est affiché comme "Retourné" dans l'interface mais la valeur reste "Terminé" en interne
            emprunts_query = emprunts_query.filter(date_retour__isnull=False, est_en_retard=False)
    
    # Paginer les résultats
    paginator = Paginator(emprunts_query, 10)  # 10 emprunts par page
    page = request.GET.get('page', 1)
    
    try:
        emprunts_pagines = paginator.page(page)
    except PageNotAnInteger:
        emprunts_pagines = paginator.page(1)
    except EmptyPage:
        emprunts_pagines = paginator.page(paginator.num_pages)
    
    # 1. Données pour le graphique des catégories
    import json
    from django.db.models import Count
    from collections import Counter
    
    # Récupérer les catégories et compter le nombre de livres par catégorie
    categories_data = list(Livre.objects.exclude(categorie_livre__isnull=True)
                        .exclude(categorie_livre='')
                        .values_list('categorie_livre', flat=True))
    
    # Si pas de catégories ou toutes sont vides
    if not categories_data:
        categories_data = ['Non catégorisé']
        categories_counts = [100]
    else:
        # Compter le nombre de livres par catégorie
        category_counter = Counter(categories_data)
        categories_data = list(category_counter.keys())
        # Calculer le pourcentage pour chaque catégorie
        total_books_with_categories = sum(category_counter.values())
        categories_counts = [round((count / total_books_with_categories) * 100, 1) for count in category_counter.values()]
    
    # 2. Données pour le graphique des statuts
    livres_empruntes = Emprunt.objects.filter(date_retour__isnull=True).count()
    livres_reserves = Reservation.objects.count()
    
    # Calcul des pourcentages pour le graphique des statuts
    if total_livres > 0:
        pourcentage_empruntes = round((livres_empruntes / total_livres) * 100, 1)
        pourcentage_reserves = round((livres_reserves / total_livres) * 100, 1)
        pourcentage_disponibles = round(100 - pourcentage_empruntes - pourcentage_reserves, 1)
    else:
        pourcentage_empruntes = 0
        pourcentage_reserves = 0
        pourcentage_disponibles = 100
    
    # S'assurer que les pourcentages n'excèdent pas 100% au total
    if pourcentage_disponibles < 0:
        pourcentage_disponibles = 0
    
    # Récupérer les derniers avis des lecteurs
    from .models import Commentaire
    derniers_avis = Commentaire.objects.select_related('livre', 'lecteur').order_by('-date_creation')[:5]
    
    context = {
        'bibliothecaire': bibliothecaire,
        'derniers_emprunts': emprunts_pagines,
        'total_livres': total_livres,
        'total_emprunts': total_emprunts,
        'total_retard': total_retard,
        'taux_rotation': taux_rotation,
        'recherche': recherche,
        'statut': statut,
        # Ajouter les données JSON pour les graphiques
        'categories_json': json.dumps(categories_data),
        'categories_counts_json': json.dumps(categories_counts),
        'pourcentage_disponibles_json': json.dumps(pourcentage_disponibles),
        'pourcentage_empruntes_json': json.dumps(pourcentage_empruntes),
        'pourcentage_reserves_json': json.dumps(pourcentage_reserves),
        # Ajouter les derniers avis
        'derniers_avis': derniers_avis,
    }
    
    # Vérifier si la requête est une requête AJAX
    if request.GET.get('ajax') == 'true':
        # Pour les requêtes AJAX, on rend seulement le template partiel
        return render(request, 'library/Dashboard.html', context)
    else:
        # Pour les requêtes normales, on rend le template complet
        return render(request, 'library/Dashboard.html', context)




# Déconnexion

def catalogue_view(request):
    query = request.GET.get('q', '').strip()
    ajax = request.GET.get('ajax', None)
    sort = request.GET.get('sort', None)
    
    if query:
        livres = Livre.objects.filter(
            Q(titre_livre__icontains=query) |
            Q(auteur_livre__icontains=query) |
            Q(categorie_livre__icontains=query)
        )
    else:
        livres = Livre.objects.all()
    
    # Tri des livres selon le paramètre sort
    if sort == 'title':
        livres = livres.order_by('titre_livre')
    elif sort == 'author':
        livres = livres.order_by('auteur_livre')
    elif sort == 'price_asc':
        livres = livres.order_by('prix')
    elif sort == 'price_desc':
        livres = livres.order_by('-prix')
    
    if request.method == 'POST':
        livre_id = request.POST.get('livre_id')
        auteur = request.POST.get('auteur')
        texte = request.POST.get('texte')
        if livre_id and auteur and texte:
            livre = Livre.objects.get(pk=livre_id)
            Commentaire.objects.create(livre=livre, auteur=auteur, texte=texte)
    
    # Vérifier si la colonne lecteur_id existe avant de faire prefetch_related
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE library_commentaire")
        columns = [col[0] for col in cursor.fetchall()]
        
        if 'lecteur_id' in columns:
            # Si lecteur_id existe, on peut faire le prefetch_related
            livres = livres.prefetch_related('commentaires').all()
        else:
            # Sinon, on évite de faire le prefetch_related pour commentaires
            livres = livres.all()
    
    role = request.session.get('role', None)
    context = {'livres': livres, 'role': role, 'query': query}
    if ajax:
        from django.template.loader import render_to_string
        html = render_to_string('library/catalogue.html', context, request=request)
        # Extraire juste le HTML des cartes (div .row.g-4)
        import re
        match = re.search(r'<div class="row g-4">([\s\S]*?)</div>', html)
        if match:
            return HttpResponse(f'<div class="row g-4">{match.group(1)}</div>')
        else:
            return HttpResponse('')
    return render(request, 'library/catalogue.html', context)

# Vue pour afficher les emprunts de l'utilisateur
from django.contrib.auth.decorators import login_required
# Suppression du décorateur login_required qui causait une redirection vers /accounts/login/
def mes_emprunts_view(request):
    # Vérifier si l'utilisateur est connecté en utilisant votre système de session personnalisé
    if 'utilisateur_id' not in request.session or 'role' not in request.session:
        return redirect('connexion')
        
    if request.session.get('role') != 'lecteur':
        return redirect('connexion')
    
    lecteur_id = request.session['utilisateur_id']
    emprunts = Emprunt.objects.filter(lecteur_id=lecteur_id).order_by('-date_emprunt')
    return render(request, 'library/mes_emprunts.html', {'emprunts': emprunts})

# Déconnexion
from django.views.decorators.http import require_POST
# Suppression du décorateur require_POST pour permettre les requêtes GET
def deconnexion_view(request):
    # Effacer toutes les données de session
    request.session.clear()
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    # Rediriger vers la page de connexion
    return redirect('connexion')


# Vue pour emprunter un livre

def a_propos_view(request):
    return render(request, 'library/a_propos.html')
def conditions_view(request):
    return render(request, 'library/conditions.html')

# Vue pour télécharger un reçu
def telecharger_reçu(request, emprunt_id):
    try:
        emprunt = Emprunt.objects.get(emprunt_id=emprunt_id)
        
        # Vérifier que l'utilisateur est connecté
        if 'utilisateur_id' not in request.session:
            messages.error(request, "Vous devez être connecté pour accéder à ce reçu.")
            return redirect('connexion')
        
        # Si utilisateur est un lecteur, vérifier qu'il est le propriétaire de l'emprunt
        if request.session.get('role') == 'lecteur':
            try:
                lecteur_id = int(request.session['utilisateur_id'])
                if lecteur_id != emprunt.lecteur.lecteur_id:
                    messages.error(request, "Vous n'avez pas accès à ce reçu.")
                    return redirect('accueil')
            except (ValueError, TypeError):
                messages.error(request, "ID d'utilisateur invalide.")
                return redirect('connexion')
        # Si utilisateur n'est pas un lecteur, vérifier que c'est un bibliothécaire
        elif request.session.get('role') != 'bibliothecaire':
            messages.error(request, "Vous n'avez pas les droits nécessaires pour accéder à ce reçu.")
            return redirect('connexion')
        
        # Vérifier si le fichier existe, sinon le générer
        import os
        from pathlib import Path
        
        file_path = f'media/reçus/reçu_emprunt_{emprunt_id}.pdf'
        if not os.path.exists(file_path):
            # Créer le dossier s'il n'existe pas
            os.makedirs('media/reçus', exist_ok=True)
            
            # Créer le PDF avec un design amélioré
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Chemins des images
            base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            logo_path = os.path.join(base_dir, 'static', 'images', 'booknova_logo.svg')
            stamp_path = os.path.join(base_dir, 'static', 'images', 'booknova_stamp.svg')
            
            # Créer des styles personnalisés avec les couleurs de la charte graphique BookNova
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold', 
                fontSize=24,
                textColor=colors.HexColor('#8B5E3C'),  # Marron principal BookNova
                spaceAfter=20,
                alignment=1  # Centré
            )
            
            subtitle_style = ParagraphStyle(
                'SubtitleStyle',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=18,
                textColor=colors.HexColor('#8B5E3C'),  # Marron principal BookNova
                spaceAfter=15,
                alignment=1  # Centré
            )
            
            section_style = ParagraphStyle(
                'SectionStyle',
                parent=styles['Heading3'],
                fontName='Helvetica-Bold',
                fontSize=14,
                textColor=colors.HexColor('#8B5E3C'),  # Marron principal BookNova
                spaceBefore=15,
                spaceAfter=10,
                borderWidth=1,
                borderColor=colors.HexColor('#D2B48C'),  # Beige BookNova pour la bordure
                borderPadding=5,
                borderRadius=3
            )
            
            info_style = ParagraphStyle(
                'InfoStyle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#6d4c30'),  # Marron foncé pour le texte
                leftIndent=20,
                spaceAfter=5
            )
            
            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#a1887f'),  # Couleur marron claire pour le footer
                alignment=1,  # Centré
                spaceBefore=30
            )
            
            # Préparer les éléments du document
            elements = []
            
            # Logo et en-tête
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=250, height=80)  # Ajustez la taille si nécessaire
                logo.hAlign = 'CENTER'  # Centrer le logo
                elements.append(logo)
            else:
                elements.append(Paragraph("BookNova", title_style))  # Fallback si l'image n'existe pas
            
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("Reçu d'emprunt", subtitle_style))
            elements.append(Spacer(1, 20))
            
            # Ajout d'un encadré coloré pour les informations principales
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib.colors import HexColor
            
            # En-tête avec fond de couleur BookNova
            header_data = [[Paragraph("<b>INFORMATIONS DE L'EMPRUNT</b>", ParagraphStyle(
                'HeaderStyle',
                parent=styles['Heading3'],
                fontName='Helvetica-Bold',
                fontSize=14,
                textColor=colors.white,
                alignment=1
            ))]]
            
            header_table = Table(header_data, colWidths=[480])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#8B5E3C')),  # Marron principal BookNova
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('ROUNDEDCORNERS', [5, 5, 5, 5]),
            ]))
            
            elements.append(header_table)
            elements.append(Spacer(1, 5))
            
            # Tableau d'informations sur l'emprunt
            emprunt_data = [
                [Paragraph("<b>ID Emprunt:</b>", info_style), Paragraph(f"{emprunt.emprunt_id}", info_style)],
                [Paragraph("<b>Livre:</b>", info_style), Paragraph(f"{emprunt.livre.titre_livre}", info_style)],
                [Paragraph("<b>Auteur:</b>", info_style), Paragraph(f"{emprunt.livre.auteur_livre}", info_style)],
                [Paragraph("<b>Prix:</b>", info_style), Paragraph(f"{emprunt.livre.prix} DH", info_style)],
                [Paragraph("<b>Date d'emprunt:</b>", info_style), Paragraph(f"{emprunt.date_emprunt.strftime('%d/%m/%Y')}", info_style)],
            ]
            
            # Gérer le cas où date_retour pourrait être None
            date_retour_str = emprunt.date_retour.strftime('%d/%m/%Y') if emprunt.date_retour else "Non définie"
            emprunt_data.append([Paragraph("<b>Date de retour prévue:</b>", info_style), Paragraph(f"{date_retour_str}", info_style)])
            
            emprunt_table = Table(emprunt_data, colWidths=[150, 330])
            emprunt_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f4ef')),  # Fond beige très clair pour la colonne de gauche
                ('BACKGROUND', (1, 0), (1, -1), HexColor('#fff8f0')),  # Fond blanc cassé pour la colonne de droite
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#D2B48C')),  # Bordure beige BookNova
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(emprunt_table)
            elements.append(Spacer(1, 15))
            
            # En-tête du lecteur
            lecteur_header = [[Paragraph("<b>INFORMATIONS DU LECTEUR</b>", ParagraphStyle(
                'HeaderStyle',
                parent=styles['Heading3'],
                fontName='Helvetica-Bold',
                fontSize=14,
                textColor=colors.white,
                alignment=1
            ))]]
            
            lecteur_header_table = Table(lecteur_header, colWidths=[480])
            lecteur_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#8B5E3C')),  # Marron principal BookNova
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('ROUNDEDCORNERS', [5, 5, 5, 5]),
            ]))
            
            elements.append(lecteur_header_table)
            elements.append(Spacer(1, 5))
            
            # Tableau d'informations sur le lecteur
            lecteur_data = [
                [Paragraph("<b>Nom:</b>", info_style), Paragraph(f"{emprunt.lecteur.nom} {emprunt.lecteur.prenom}", info_style)],
                [Paragraph("<b>Email:</b>", info_style), Paragraph(f"{emprunt.lecteur.email}", info_style)],
            ]
            
            lecteur_table = Table(lecteur_data, colWidths=[150, 330])
            lecteur_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f4ef')),  # Fond beige très clair pour la colonne de gauche
                ('BACKGROUND', (1, 0), (1, -1), HexColor('#fff8f0')),  # Fond blanc cassé pour la colonne de droite
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#D2B48C')),  # Bordure beige BookNova
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(lecteur_table)
            elements.append(Spacer(1, 15))
            
            # Conditions d'emprunt avec fond coloré BookNova
            conditions_header = [[Paragraph("<b>CONDITIONS D'EMPRUNT</b>", ParagraphStyle(
                'HeaderStyle',
                parent=styles['Heading3'],
                fontName='Helvetica-Bold',
                fontSize=14,
                textColor=colors.white,
                alignment=1
            ))]]
            
            conditions_header_table = Table(conditions_header, colWidths=[480])
            conditions_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#8B5E3C')),  # Marron principal BookNova
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('ROUNDEDCORNERS', [5, 5, 5, 5]),
            ]))
            
            elements.append(conditions_header_table)
            elements.append(Spacer(1, 5))
            
            conditions_data = [
                [Paragraph("• Les livres doivent être retournés avant la date de retour prévue.", info_style)],
                [Paragraph("• Des frais de retard peuvent s'appliquer en cas de retour tardif.", info_style)],
                [Paragraph("• Veuillez prendre soin des livres empruntés.", info_style)],
            ]
            
            conditions_table = Table(conditions_data, colWidths=[480])
            conditions_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8f4ef')),  # Fond beige très clair
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#D2B48C')),  # Bordure beige BookNova
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ]))
            
            elements.append(conditions_table)
            elements.append(Spacer(1, 20))
            
            # Cachet incliné
            if os.path.exists(stamp_path):
                stamp = Image(stamp_path, width=150, height=150)
                stamp.hAlign = 'RIGHT'  # Aligner à droite
                stamp.vAlign = 'BOTTOM'  # Aligner en bas
                elements.append(stamp)
            
            # Footer
            elements.append(Spacer(1, 30))  # Espace avant le footer
            elements.append(Paragraph("Merci d'avoir choisi BookNova pour vos lectures !", footer_style))
            elements.append(Paragraph(f"Reçu généré le {date.today().strftime('%d/%m/%Y')}", footer_style))
            
            # Classe pour ajouter le logo et le cachet comme éléments de fond
            from reportlab.platypus.flowables import Flowable
            from reportlab.lib.units import cm
            
            class StampFlowable(Flowable):
                def __init__(self, stamp_path):
                    Flowable.__init__(self)
                    self.stamp_path = stamp_path
                    self.width = 150
                    self.height = 150
                
                def draw(self):
                    # Dessine le cachet incliné en bas à droite de la page
                    if os.path.exists(self.stamp_path):
                        from reportlab.lib.utils import ImageReader
                        self.canv.saveState()
                        self.canv.translate(350, 50)  # Position en bas à droite
                        self.canv.rotate(25)  # Incliner le cachet
                        self.canv.drawImage(ImageReader(self.stamp_path), 0, 0, width=self.width, height=self.height, mask='auto')
                        self.canv.restoreState()
            
            # Classe personnalisée pour ajouter des éléments sur chaque page
            class PageTemplate(SimpleDocTemplate):
                def __init__(self, filename, **kwargs):
                    SimpleDocTemplate.__init__(self, filename, **kwargs)
                    self.stamp_path = kwargs.get('stamp_path')
                
                def build(self, flowables, **kwargs):
                    if 'onFirstPage' not in kwargs:
                        kwargs['onFirstPage'] = self.add_page_elements
                    if 'onLaterPages' not in kwargs:
                        kwargs['onLaterPages'] = self.add_page_elements
                    return SimpleDocTemplate.build(self, flowables, **kwargs)
                
                def add_page_elements(self, canvas, doc):
                    canvas.saveState()
                    if os.path.exists(self.stamp_path):
                        from reportlab.lib.utils import ImageReader
                        # Dessiner le cachet en arrière-plan
                        canvas.saveState()
                        canvas.translate(400, 150)  # Position du cachet
                        canvas.rotate(-25)  # Incliner le cachet (-25 degrés)
                        canvas.drawImage(ImageReader(self.stamp_path), 0, 0, width=150, height=150, mask='auto')
                        canvas.restoreState()
                    canvas.restoreState()
            
            # Utiliser la classe personnalisée pour construire le document
            doc = PageTemplate(file_path, pagesize=A4, stamp_path=stamp_path)
            
            # Construire le document avec le gestionnaire de pages personnalisé
            doc.build(elements)
        
        # Lire le fichier et le renvoyer
        with open(file_path, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reçu_emprunt_{emprunt_id}.pdf"'
            return response
    except Emprunt.DoesNotExist:
        messages.error(request, "Emprunt non trouvé.")
        return redirect('accueil')

def paiement_view(request, livre_id):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'lecteur':
        return redirect('connexion')

    livre = Livre.objects.get(livre_id=livre_id)
    lecteur = Lecteur.objects.get(lecteur_id=request.session['utilisateur_id'])

    if request.method == 'POST':
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        numeroCarte = request.POST.get('numeroCarte')
        nomCarte = request.POST.get('nomCarte')
        dateExpiration = request.POST.get('dateExpiration')
        cvv = request.POST.get('cvv')

        # Validation des données
        if not (nom and email and telephone and numeroCarte and nomCarte and dateExpiration and cvv):
            messages.error(request, 'Veuillez remplir tous les champs.')
            return redirect('paiement', livre_id=livre_id)

        # Création de l'emprunt
        with transaction.atomic():
            emprunt = Emprunt.objects.create(
                lecteur=lecteur,
                livre=livre,
                date_emprunt=date.today(),
                date_retour=date.today() + timedelta(days=14)
            )
            
            # Réduire le nombre d'exemplaires disponibles
            livre.nombre_exemplaires -= 1
            livre.save()

        # Générer et sauvegarder le reçu PDF pour un accès ultérieur
        import os
        os.makedirs('media/reçus', exist_ok=True)
        file_path = f'media/reçus/reçu_emprunt_{emprunt.emprunt_id}.pdf'
        
        # Créer le PDF avec un design amélioré
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Créer des styles personnalisés
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4A6572'),
            spaceAfter=20,
            alignment=1  # Centré
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#344955'),
            spaceAfter=15,
            alignment=1  # Centré
        )
        
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#4A6572'),
            spaceBefore=15,
            spaceAfter=10
        )
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            leftIndent=20,
            spaceAfter=5
        )
        
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            alignment=1,  # Centré
            spaceBefore=30
        )
        
        # Préparer les éléments du document
        elements = []
        
        # Logo et en-tête
        elements.append(Paragraph("BookNova", title_style))
        elements.append(Paragraph("Reçu d'emprunt", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Informations de l'emprunt
        elements.append(Paragraph("Informations de l'emprunt", section_style))
        elements.append(Paragraph(f"<b>ID Emprunt:</b> {emprunt.emprunt_id}", info_style))
        elements.append(Paragraph(f"<b>Livre:</b> {livre.titre_livre}", info_style))
        elements.append(Paragraph(f"<b>Auteur:</b> {livre.auteur_livre}", info_style))
        elements.append(Paragraph(f"<b>Prix:</b> {livre.prix} DH", info_style))
        elements.append(Paragraph(f"<b>Date d'emprunt:</b> {emprunt.date_emprunt.strftime('%d/%m/%Y')}", info_style))
        elements.append(Paragraph(f"<b>Date de retour prévue:</b> {emprunt.date_retour.strftime('%d/%m/%Y')}", info_style))
        
        # Informations du lecteur
        elements.append(Paragraph("Informations du lecteur", section_style))
        elements.append(Paragraph(f"<b>Nom:</b> {lecteur.nom} {lecteur.prenom}", info_style))
        elements.append(Paragraph(f"<b>Email:</b> {lecteur.email}", info_style))
        
        # Informations de paiement
        elements.append(Paragraph("Informations de paiement", section_style))
        elements.append(Paragraph(f"<b>Méthode de paiement:</b> Carte de crédit", info_style))
        elements.append(Paragraph(f"<b>Titulaire de la carte:</b> {nomCarte}", info_style))
        # Masquer le numéro de carte pour la sécurité
        masked_card = "XXXX-XXXX-XXXX-" + numeroCarte[-4:] if len(numeroCarte) >= 4 else "XXXX-XXXX-XXXX-XXXX"
        elements.append(Paragraph(f"<b>Numéro de carte:</b> {masked_card}", info_style))
        
        # Conditions d'emprunt
        elements.append(Paragraph("Conditions d'emprunt", section_style))
        elements.append(Paragraph("• Les livres doivent être retournés avant la date de retour prévue.", info_style))
        elements.append(Paragraph("• Des frais de retard peuvent s'appliquer en cas de retour tardif.", info_style))
        elements.append(Paragraph("• Veuillez prendre soin des livres empruntés.", info_style))
        
        # Footer
        elements.append(Paragraph("Merci d'avoir choisi BookNova pour vos lectures !", footer_style))
        elements.append(Paragraph(f"Reçu généré le {date.today().strftime('%d/%m/%Y')}", footer_style))
        
        # Construire le document
        doc.build(elements)
        
        # Ajouter un message de succès
        messages.success(request, "Paiement effectué avec succès ! Votre emprunt a été enregistré.")
        
        # Rediriger vers la page de paiement avec les informations de l'emprunt
        context = {
            'livre': livre,
            'lecteur': lecteur,
            'emprunt': emprunt,
            'paiement_reussi': True,
            'date_emprunt': emprunt.date_emprunt.strftime('%d/%m/%Y'),
            'date_retour': emprunt.date_retour.strftime('%d/%m/%Y')
        }
        return render(request, 'library/paiement.html', context)
        
    context = {
        'livre': livre,
        'lecteur': lecteur
    }
    return render(request, 'library/paiement.html', context)

def emprunter_livre(request, livre_id):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'lecteur':
        messages.error(request, "Vous devez être connecté en tant que lecteur pour emprunter un livre.")
        return redirect('connexion')

    try:
        livre = Livre.objects.get(livre_id=livre_id)
        lecteur = Lecteur.objects.get(lecteur_id=request.session['utilisateur_id'])

        # Vérifier si le livre est disponible
        if livre.nombre_exemplaires > 0:
            # Créer un nouvel emprunt avec date de retour à 15 jours
            emprunt = Emprunt.objects.create(
                lecteur=lecteur,
                livre=livre,
                date_emprunt=date.today(),
                date_retour=date.today() + timedelta(days=15)  # 15 jours au lieu de 14
            )

            # Mettre à jour le nombre d'exemplaires disponibles
            livre.nombre_exemplaires -= 1
            livre.save()
            
            messages.success(request, f"Vous avez emprunté '{livre.titre}'. La date de retour prévue est le {emprunt.date_retour.strftime('%d/%m/%Y')}.")
        else:
            messages.error(request, f"Désolé, '{livre.titre}' n'est plus disponible pour l'emprunt.")
        
        # Redirection vers mes emprunts
        return redirect('mes_emprunts')
    
    except (Livre.DoesNotExist, Lecteur.DoesNotExist):
        messages.error(request, "Une erreur est survenue lors de l'emprunt du livre.")
        return redirect('catalogue')

def contact(request):
    if request.method == 'POST':
        # Traitement du formulaire si besoin (non implémenté ici)
        pass
    return render(request, 'library/contact.html')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Reservation, Lecteur  # Ajout de Lecteur
from io import BytesIO
from django.http import JsonResponse
from datetime import datetime, date

def get_amendes_notifications(request):
    # Vérifier que l'utilisateur est connecté et que c'est un lecteur
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'lecteur':
        return JsonResponse({'amendes': []})
    
    lecteur_id = request.session['utilisateur_id']
    today = date.today()
    
    amendes = []
    
    # 1. Récupérer les amendes directement de la table Amende
    from .models import Amende
    amendes_db = Amende.objects.filter(lecteur_id=lecteur_id, amende_payee=False)
    
    for amende in amendes_db:
        amendes.append({
            'livre': f'Amende directe',  # On n'a pas le livre associé directement
            'jours_retard': '-',  # Pas applicable pour les amendes directes
            'montant': float(amende.montant_amende)  # Convertir DecimalField en float pour JSON
        })
    
    # 2. Récupérer tous les emprunts en retard pour ce lecteur
    try:
        # Vérifions si le champ livre_rendu existe, sinon on l'ignore
        if hasattr(Emprunt, 'livre_rendu'):
            emprunts_retard = Emprunt.objects.filter(
                lecteur_id=lecteur_id,
                date_retour__lt=today,
                livre_rendu=False
            ).select_related('livre')
        else:
            # Utiliser une requête sans le champ livre_rendu
            emprunts_retard = Emprunt.objects.filter(
                lecteur_id=lecteur_id,
                date_retour__lt=today,
                date_retour__isnull=False
            ).select_related('livre')
        
        for emprunt in emprunts_retard:
            jours_retard = (today - emprunt.date_retour).days
            montant_amende = jours_retard * 5  # 5 DH par jour de retard
            
            amendes.append({
                'livre': emprunt.livre.titre_livre,  # Utiliser le bon attribut
                'jours_retard': jours_retard,
                'montant': montant_amende
            })
    except Exception as e:
        # En cas d'erreur, on la logge mais on continue
        print(f"Erreur lors de la récupération des emprunts en retard: {e}")
    
    return JsonResponse({'amendes': amendes})
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import os
from django.conf import settings
import datetime

# Suppression du décorateur login_required qui causait une redirection vers /accounts/login/
def mes_reservations(request):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'lecteur':
        return redirect('connexion')
    lecteur_id = request.session['utilisateur_id']
    lecteur = Lecteur.objects.get(lecteur_id=lecteur_id)
    reservations = Reservation.objects.filter(lecteur=lecteur)
    return render(request, 'library/mes_reservations.html', {'reservations': reservations})

# Vue pour gérer les réservations (côté administrateur)
def gerer_reservations(request):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour accéder à cette page.")
        return redirect('connexion')
    
    # Récupérer le paramètre de recherche
    query = request.GET.get('q', '')
    
    # Filtrer les réservations selon la recherche
    if query:
        reservations = Reservation.objects.filter(
            Q(livre__titre_livre__icontains=query) |
            Q(lecteur__prenom__icontains=query) |
            Q(lecteur__nom__icontains=query)
        ).select_related('livre', 'lecteur').order_by('-date_reservation')
    else:
        reservations = Reservation.objects.all().select_related('livre', 'lecteur').order_by('-date_reservation')
    
    # Pagination
    paginator = Paginator(reservations, 10)  # 10 réservations par page
    page = request.GET.get('page', 1)
    
    try:
        reservations_page = paginator.page(page)
    except PageNotAnInteger:
        reservations_page = paginator.page(1)
    except EmptyPage:
        reservations_page = paginator.page(paginator.num_pages)
    
    return render(request, 'library/gerer_reservations.html', {
        'reservations': reservations_page,
    })

# Vue pour confirmer une réservation (transformation en emprunt)
def confirmer_reservation(request, reservation_id):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour accéder à cette page.")
        return redirect('connexion')
    
    try:
        # Récupérer la réservation
        reservation = Reservation.objects.select_related('livre', 'lecteur').get(reservation_id=reservation_id)
        
        # Vérifier si le livre a des exemplaires disponibles
        if reservation.livre.nombre_exemplaires <= 0:
            messages.error(request, f"Le livre '{reservation.livre.titre_livre}' n'a plus d'exemplaires disponibles.")
            return redirect('gerer_reservations')
        
        # Créer un nouvel emprunt
        from datetime import date, timedelta
        date_emprunt = date.today()
        date_retour_prevue = date_emprunt + timedelta(days=15)  # Durée d'emprunt de 15 jours
        
        Emprunt.objects.create(
            livre=reservation.livre,
            lecteur=reservation.lecteur,
            date_emprunt=date_emprunt,
            date_retour_prevue=date_retour_prevue
        )
        
        # Mettre à jour le nombre d'exemplaires du livre
        reservation.livre.nombre_exemplaires -= 1
        reservation.livre.save()
        
        # Supprimer la réservation
        reservation.delete()
        
        messages.success(request, f"La réservation pour '{reservation.livre.titre_livre}' a été transformée en emprunt avec succès.")
    except Reservation.DoesNotExist:
        messages.error(request, "La réservation n'existe pas.")
    except Exception as e:
        messages.error(request, f"Une erreur s'est produite : {str(e)}")
    
    return redirect('gerer_reservations')

# Vue pour annuler une réservation
def annuler_reservation(request, reservation_id):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour accéder à cette page.")
        return redirect('connexion')
    
    try:
        # Récupérer et supprimer la réservation
        reservation = Reservation.objects.select_related('livre', 'lecteur').get(reservation_id=reservation_id)
        titre_livre = reservation.livre.titre_livre
        nom_lecteur = f"{reservation.lecteur.prenom} {reservation.lecteur.nom}"
        
        reservation.delete()
        
        messages.success(request, f"La réservation de '{titre_livre}' par {nom_lecteur} a été annulée.")
    except Reservation.DoesNotExist:
        messages.error(request, "La réservation n'existe pas.")
    except Exception as e:
        messages.error(request, f"Une erreur s'est produite : {str(e)}")
    
    return redirect('gerer_reservations')

# Suppression du décorateur login_required qui causait une redirection vers /accounts/login/
def mes_avis(request):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'lecteur':
        return redirect('connexion')
    
    lecteur_id = request.session['utilisateur_id']
    lecteur = Lecteur.objects.get(lecteur_id=lecteur_id)
    
    # Éviter l'erreur en n'utilisant pas Commentaire.objects.filter(lecteur=lecteur)
    # À la place, on utilise une requête SQL brute qui correspond à la structure actuelle de la table
    from django.db import connection
    
    # Vérifier si nous avons le champ 'lecteur_id' ou un autre champ pour le lecteur
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE library_commentaire")
        columns = [col[0] for col in cursor.fetchall()]
        
        # Récupérer les commentaires en utilisant une requête adaptée à la structure de la table
        if 'lecteur_id' in columns:
            # Si lecteur_id existe, utiliser la requête normale
            avis = Commentaire.objects.filter(lecteur=lecteur).order_by('-date_creation')
        else:
            # Si lecteur_id n'existe pas, créer une liste vide
            avis = []
    
    # Récupérer les livres que le lecteur a déjà empruntés
    livres_empruntes = Livre.objects.filter(emprunts__lecteur=lecteur).distinct()
    
    return render(request, 'library/mes_avis.html', {
        'avis': avis,
        'livres_empruntes': livres_empruntes
    })

# Suppression du décorateur login_required qui causait une redirection vers /accounts/login/
def ajouter_avis(request):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'lecteur':
        return redirect('connexion')
    
    if request.method == 'POST':
        livre_id = request.POST.get('livre_id')
        note = request.POST.get('note')
        commentaire = request.POST.get('commentaire')
        
        try:
            from .models import Commentaire
            lecteur = Lecteur.objects.get(lecteur_id=request.session['utilisateur_id'])
            livre = Livre.objects.get(livre_id=livre_id)
            
            # Créer le commentaire
            Commentaire.objects.create(
                livre=livre,
                lecteur=lecteur,
                note=note,
                commentaire=commentaire
            )
            
            messages.success(request, "Votre avis a été publié avec succès !")
        except Exception as e:
            messages.error(request, f"Erreur lors de la publication de votre avis : {str(e)}")
    
    return redirect('mes_avis')

# Suppression du décorateur login_required qui causait une redirection vers /accounts/login/
def modifier_avis(request, avis_id):
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'lecteur':
        return redirect('connexion')
    
    from .models import Commentaire
    try:
        avis = Commentaire.objects.get(commentaire_id=avis_id, lecteur__lecteur_id=request.session['utilisateur_id'])
    except Commentaire.DoesNotExist:
        messages.error(request, "Cet avis n'existe pas ou ne vous appartient pas.")
        return redirect('mes_avis')
    
    if request.method == 'POST':
        note = request.POST.get('note')
        commentaire = request.POST.get('commentaire')
        
        try:
            avis.note = note
            avis.commentaire = commentaire
            avis.save()
            messages.success(request, "Votre avis a été modifié avec succès !")
            return redirect('mes_avis')
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification de votre avis : {str(e)}")
    
    return render(request, 'library/modifier_avis.html', {'avis': avis})


# Suppression du décorateur login_required qui causait une redirection vers /accounts/login/
def supprimer_avis(request, avis_id):
    if 'utilisateur_id' not in request.session:
        messages.error(request, "Vous devez être connecté pour supprimer un avis.")
        return redirect('connexion')
    
    avis = get_object_or_404(Commentaire, commentaire_id=avis_id)
    if avis.utilisateur_id != request.session['utilisateur_id'] or request.session.get('role') != 'lecteur':
        messages.error(request, "Vous ne pouvez pas supprimer cet avis.")
        return redirect('mes_avis')
    
    avis.delete()
    messages.success(request, "Votre avis a été supprimé avec succès.")
    return redirect('mes_avis')


# Fonction pour exporter le dashboard en PDF
def exporter_dashboard_pdf(request):
    # Vérification de l'authentification
    if 'utilisateur_id' not in request.session or request.session.get('role') != 'bibliothecaire':
        messages.error(request, "Vous devez être connecté en tant que bibliothécaire pour exporter le rapport.")
        return redirect('connexion')
    
    # Récupération des données (similaires à celles du dashboard)
    bibliothecaire = Bibliothecaire.objects.get(bibliothecaire_id=request.session['utilisateur_id'])
    total_livres = Livre.objects.count()
    total_emprunts = Emprunt.objects.filter(date_retour__isnull=True).count()
    total_retard = Emprunt.objects.filter(est_en_retard=True).count()
    taux_rotation = int((total_emprunts / total_livres) * 100) if total_livres > 0 else 0
    derniers_emprunts = Emprunt.objects.select_related('livre', 'lecteur').order_by('-date_emprunt')[:10]
    
    # Création du PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_booknova_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    # Création du document PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=72)
    
    # Contenu du document
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    # Utiliser des noms personnalisés pour éviter les conflits avec les styles existants
    styles.add(ParagraphStyle(name='BookNovaTitle', 
                              fontName='Helvetica-Bold', 
                              fontSize=24, 
                              alignment=TA_CENTER,
                              spaceAfter=20))
    styles.add(ParagraphStyle(name='BookNovaSubtitle', 
                              fontName='Helvetica-Bold', 
                              fontSize=18, 
                              alignment=TA_LEFT,
                              spaceAfter=12,
                              textColor=colors.chocolate))
    styles.add(ParagraphStyle(name='BookNovaNormalBold', 
                              fontName='Helvetica-Bold', 
                              fontSize=12))
    styles.add(ParagraphStyle(name='BookNovaHeader', 
                              fontName='Helvetica-Bold', 
                              fontSize=14,
                              textColor=colors.darkblue))
    styles.add(ParagraphStyle(name='BookNovaFooter', 
                              fontName='Helvetica-Oblique', 
                              fontSize=8,
                              alignment=TA_CENTER,
                              textColor=colors.darkgrey))
    
    # Titre et entête
    title = Paragraph("<font color=\"#8B5E3C\">BOOKNOVA</font>", styles['BookNovaTitle'])
    story.append(title)
    
    subtitle = Paragraph(f"Rapport de la Bibliothèque - {datetime.datetime.now().strftime('%d/%m/%Y')}", styles['BookNovaSubtitle'])
    story.append(subtitle)
    
    story.append(Paragraph(f"Généré par : {bibliothecaire.prenom} {bibliothecaire.nom}", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Résumé des statistiques
    story.append(Paragraph("Résumé des statistiques", styles['BookNovaHeader']))
    story.append(Spacer(1, 0.2*inch))
    
    # Tableau des statistiques
    stats_data = [
        ["Métrique", "Valeur"],
        ["Nombre total de livres", f"{total_livres}"],
        ["Emprunts en cours", f"{total_emprunts}"],
        ["Emprunts en retard", f"{total_retard}"],
        ["Taux de rotation", f"{taux_rotation}%"],
    ]
    
    # Création du tableau avec style
    col_widths = [doc.width/2.0, doc.width/2.0]
    stats_table = Table(stats_data, colWidths=col_widths)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.chocolate),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Liste des derniers emprunts
    story.append(Paragraph("Derniers emprunts", styles['BookNovaHeader']))
    story.append(Spacer(1, 0.2*inch))
    
    # En-têtes du tableau des emprunts
    emprunts_data = [
        ["ID", "Livre", "Lecteur", "Date d'emprunt", "Date de retour"]
    ]
    
    # Données des emprunts
    for emprunt in derniers_emprunts:
        # Calculer ou utiliser une date appropriée pour la date de retour prévue
        # Utiliser date_retour si disponible, sinon indiquer "En cours"
        if emprunt.date_retour:
            date_retour = emprunt.date_retour.strftime("%d/%m/%Y")
        else:
            # Si la date de retour n'est pas définie, l'emprunt est toujours en cours
            date_retour = "En cours"
            
        emprunts_data.append([
            str(emprunt.emprunt_id),
            emprunt.livre.titre_livre,
            f"{emprunt.lecteur.prenom} {emprunt.lecteur.nom}",
            emprunt.date_emprunt.strftime("%d/%m/%Y"),
            date_retour
        ])
    
    # Création du tableau avec style
    col_widths = [doc.width*0.1, doc.width*0.25, doc.width*0.25, doc.width*0.2, doc.width*0.2]
    emprunts_table = Table(emprunts_data, colWidths=col_widths, repeatRows=1)
    emprunts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.chocolate),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(emprunts_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Pied de page
    current_date = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    footer = Paragraph(f"Document confidentiel - BookNova - Généré le {current_date}", styles['BookNovaFooter'])
    story.append(footer)
    
    # Construire le document
    doc.build(story)
    
    # Récupérer le contenu du buffer et le renvoyer dans la réponse
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response