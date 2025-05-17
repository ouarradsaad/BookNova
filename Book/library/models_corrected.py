from django.db import models # type: ignore
from django.contrib.auth.hashers import make_password # type: ignore

#--------------------------Classe Lecteur----------------------------------
class Lecteur(models.Model):
    lecteur_id = models.AutoField(primary_key=True)  # Clé primaire explicite
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nom} {self.prenom} (Lecteur)"
#----------------------------------------------------------------------------


#---------------------------Classe Bibliothecaire----------------------------
class Bibliothecaire(models.Model):
    bibliothecaire_id = models.AutoField(primary_key=True)  # Clé primaire explicite
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        # Hash the password only if it's not already hashed
        if not self.mot_de_passe.startswith('pbkdf2_sha256$'):
            self.mot_de_passe = make_password(self.mot_de_passe)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} {self.prenom} (Bibliothécaire)"
#----------------------------------------------------------------------------


#---------------------------------------------Classe Livre---------------------------------------------
class Livre(models.Model):
    livre_id = models.AutoField(primary_key=True)
    titre_livre = models.CharField(max_length=255)
    auteur_livre = models.CharField(max_length=255)
    categorie_livre = models.CharField(max_length=100, blank=True, null=True)
    isbn = models.CharField(max_length=13, unique=True)
    nombre_exemplaires = models.IntegerField(default=1)
    couverture = models.ImageField(upload_to='couvertures/', blank=True, null=True)
    prix = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, help_text="Prix de l'emprunt du livre")
    description = models.TextField(blank=True, null=True, help_text="Description du livre")

    # Relation avec la classe Bibliothecaire
    bibliothecaire = models.ForeignKey(Bibliothecaire, on_delete=models.CASCADE, related_name='livres')

    def __str__(self):
        return f"{self.titre_livre} par {self.auteur_livre}"
#-------------------------------------------------------------------------------------------------------



#---------------------------------------------Classe Reservation--------------------------------------------
from django.utils import timezone # type: ignore
class Reservation(models.Model):
    reservation_id = models.AutoField(primary_key=True)
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='reservations')
    lecteur = models.ForeignKey(Lecteur, on_delete=models.CASCADE, related_name='reservations')
    date_reservation = models.DateField(default=timezone.now)
    
    def __str__(self):
        return f"Reservation de {self.livre.titre_livre} par {self.lecteur.nom} {self.lecteur.prenom} le {self.date_reservation}"
class Emprunt(models.Model):
    emprunt_id = models.AutoField(primary_key=True)
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='emprunts')
    lecteur = models.ForeignKey(Lecteur, on_delete=models.CASCADE)
    date_emprunt = models.DateField()
    date_retour = models.DateField(null=True, blank=True)
    est_en_retard = models.BooleanField(default=False)

    def __str__(self):
        return f"Emprunt de {self.livre.titre_livre} par {self.lecteur.nom} {self.lecteur.prenom}"
#------------------------------------------------------------------------------------------------------


#----------------------------------------Classe EmpruntLecteur----------------------------------------
class EmpruntLecteur(models.Model):
    emprunt = models.ForeignKey(Emprunt, on_delete=models.CASCADE)
    lecteur = models.ForeignKey(Lecteur, on_delete=models.CASCADE)
    date_emprunt = models.DateField()
#------------------------------------------------------------------------------------------------------


#--------------------------------------------Classe Amende--------------------------------------------
class Amende(models.Model):
    amende_id = models.AutoField(primary_key=True)
    lecteur = models.ForeignKey(Lecteur, on_delete=models.CASCADE, null=True, blank=True)
    bibliothecaire = models.ForeignKey(Bibliothecaire, on_delete=models.CASCADE, null=True, blank=True)
    montant_amende = models.DecimalField(max_digits=6, decimal_places=2)
    amende_payee = models.BooleanField(default=False)

    def __str__(self):
        return f"Amende de {self.montant_amende} pour {self.lecteur.nom} {self.lecteur.prenom}" if self.lecteur else f"Amende de {self.montant_amende} pour {self.bibliothecaire.nom} {self.bibliothecaire.prenom}"

#----------------------------------------Classe Commentaire----------------------------------------
class Commentaire(models.Model):
    commentaire_id = models.AutoField(primary_key=True)
    livre = models.ForeignKey('Livre', on_delete=models.CASCADE, related_name='commentaires')
    lecteur = models.ForeignKey(Lecteur, on_delete=models.CASCADE, related_name='commentaires')
    note = models.IntegerField(default=5)
    commentaire = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire de {self.lecteur.nom} {self.lecteur.prenom} sur {self.livre.titre_livre}"
#------------------------------------------------------------------------------------------------------
