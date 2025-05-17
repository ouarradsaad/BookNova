from django.urls import path
from . import views

urlpatterns = [
    path('a-propos/', views.a_propos_view, name='a_propos'),
    # Page de connexion/inscription
    path('', views.connexion_view, name='connexion'),
    path('connexion/', views.connexion_view, name='connexion'),
    path('S_inscrire/', views.S_inscrire, name='s_inscrire'),
    path('Inscription/', views.inscription_view, name='inscription'),
    path('deconnexion/', views.deconnexion_view, name='deconnexion'),
    
    # Pages principales
    path('accueil/', views.accueil_view, name='accueil'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('ajouter-livre/', views.ajouter_livre_view, name='ajouter_livre'),
    path('modifier-livre/<int:livre_id>/', views.modifier_livre_view, name='modifier_livre'),
    path('supprimer-livre/<int:livre_id>/', views.supprimer_livre_view, name='supprimer_livre'),
    path('confirmer-suppression-livre/<int:livre_id>/', views.confirmer_suppression_livre, name='confirmer_suppression_livre'),
    path('ajouter-lecteur/', views.ajouter_lecteur_view, name='ajouter_lecteur'),
    path('ajouter-emprunt/', views.ajouter_emprunt_view, name='ajouter_emprunt'),
    path('catalogue/', views.catalogue_view, name='catalogue'),
    path('livres-admin/', views.liste_livres_admin_view, name='livres_admin'),
    path('emprunts-en-cours/', views.liste_emprunts_en_cours_view, name='emprunts_en_cours'),
    path('emprunts-en-retard/', views.emprunts_en_retard_view, name='emprunts_en_retard'),
    path('reserver-livre/<int:livre_id>/', views.reserver_livre, name='reserver_livre'),
    path('paiement/<int:livre_id>/', views.paiement_view, name='paiement'),
    path('emprunter-livre/<int:livre_id>/', views.emprunter_livre, name='emprunter_livre'),
    path('retourner-livre/<int:emprunt_id>/', views.retourner_livre, name='retourner_livre'),
    path('mes-emprunts/', views.mes_emprunts_view, name='mes_emprunts'),
    path('ajouter-bibliothecaire/', views.ajouter_bibliothecaire_view, name='ajouter_bibliothecaire'),
    path('contact/', views.contact, name='contact'),
    path('conditions/', views.conditions_view, name='conditions'),
    path('telecharger-reçu/<int:emprunt_id>/', views.telecharger_reçu, name='telecharger_reçu'),
    path('mes-reservations/', views.mes_reservations, name='mes_reservations'),
    path('mes-avis/', views.mes_avis, name='mes_avis'),
    path('ajouter-avis/', views.ajouter_avis, name='ajouter_avis'),
    path('modifier-avis/<int:avis_id>/', views.modifier_avis, name='modifier_avis'),
    path('supprimer-avis/<int:avis_id>/', views.supprimer_avis, name='supprimer_avis'),
    # Exportation PDF du dashboard
    path('exporter-dashboard-pdf/', views.exporter_dashboard_pdf, name='exporter_dashboard_pdf'),
    # Notifications d'amendes
    path('get-amendes-notifications/', views.get_amendes_notifications, name='get_amendes_notifications'),
    
    # Gestion des réservations (côté administrateur)
    path('gerer-reservations/', views.gerer_reservations, name='gerer_reservations'),
    path('confirmer-reservation/<int:reservation_id>/', views.confirmer_reservation, name='confirmer_reservation'),
    path('annuler-reservation/<int:reservation_id>/', views.annuler_reservation, name='annuler_reservation'),
]
