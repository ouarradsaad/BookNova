# forms.py

from django import forms
from django.contrib.auth.models import User
from .models import Livre

class InscriptionForm(forms.Form):
    prenom = forms.CharField(max_length=100)
    nom = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())
    confirmPassword = forms.CharField(widget=forms.PasswordInput())
    type_utilisateur = forms.ChoiceField(choices=[('lecteur', 'Lecteur'), ('bibliothecaire', 'Bibliothécaire')])

class LivreForm(forms.ModelForm):
    class Meta:
        model = Livre
        fields = [
            'titre_livre', 
            'auteur_livre', 
            'categorie_livre', 
            'isbn', 
            'nombre_exemplaires', 
            'couverture',
            'prix',
            'description'
        ]
        
        widgets = {
            'titre_livre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre du livre'}),
            'auteur_livre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auteur du livre'}),
            'categorie_livre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Catégorie du livre'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ISBN (ex: 978-3-16-148410-0)'}),
            'nombre_exemplaires': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'value': '0.00'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Description du livre'}),
        }
        
        labels = {
            'titre_livre': 'Titre',
            'auteur_livre': 'Auteur',
            'categorie_livre': 'Catégorie',
            'isbn': 'ISBN',
            'nombre_exemplaires': 'Nombre d\'exemplaires',
            'couverture': 'Couverture du livre',
            'prix': 'Prix d\'emprunt',
            'description': 'Description'
        }
        
        help_texts = {
            'isbn': 'Format international d\'identification de livre (13 chiffres)',
            'prix': 'Prix de l\'emprunt du livre en euros',
            'nombre_exemplaires': 'Nombre d\'exemplaires disponibles',
        }
