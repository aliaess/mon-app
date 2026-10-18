# VAN Project Analyzer

Application web pédagogique d'analyse d'investissement, écrite en **Python / Streamlit**.
Elle calcule, explique et compare la **valeur actuelle nette (VAN)** de projets
d'investissement, pour les étudiants en finance et en gestion.

L'interface est entièrement en français. Aucun compte, aucun serveur externe,
aucune donnée ne quitte votre machine.

---

## 1. Installation

Prérequis : Python 3.9 ou plus récent.

```bash
cd "/Users/user/Desktop/mon app"

# Environnement virtuel (déjà présent dans ce dépôt)
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Dépendances : `streamlit`, `plotly`, `pandas`, `numpy`.

## 2. Lancement

```bash
cd "/Users/user/Desktop/mon app"
.venv/bin/python -m streamlit run app.py
```

Le navigateur s'ouvre sur <http://localhost:8501>. Pour arrêter l'application :
`Ctrl + C` dans le terminal.

## 3. Fonctionnalités

| Page | Contenu |
| --- | --- |
| **🏠 Accueil** | Présentation de la VAN, du vocabulaire et de la démarche, raccourcis vers les autres pages, accès à l'exemple de démonstration. |
| **🧮 Calculateur VAN** | Hypothèses du projet (nom, investissement initial I₀, taux d'actualisation, durée), saisie des flux année par année dans un tableau éditable, puis résultats complets : VAN, TRI, indice de rentabilité, délai de récupération, interprétation automatique, graphique et tableau détaillé des calculs. Export CSV des flux. |
| **⚖️ Comparaison des projets** | Sélection de deux projets ou plus (enregistrés ou exemples), option pour les réévaluer **au même taux d'actualisation** afin que la comparaison porte sur le seul échelonnement des flux, tableau comparatif, graphique des cumuls et recommandation argumentée. |
| **🗂️ Historique** | Liste de tous les calculs enregistrés, détail, rechargement dans le calculateur, suppression, export et import d'un fichier JSON. |
| **📘 Guide pédagogique** | Définition de la VAN, formule et légende de chaque variable, méthode pas à pas, exemple numérique entièrement déroulé (calcul du coefficient d'actualisation, des flux actualisés, du cumul), pièges fréquents et conflit VAN / TRI. |

### Formule utilisée

```
VAN = −I₀ + Σ [ CFt / (1 + r)^t ]   pour t = 1 … n
```

avec `I₀` l'investissement initial, `CFt` le flux de trésorerie de l'année `t`,
`r` le taux d'actualisation et `n` la durée du projet.

### Règles de calcul et de validation

- Tous les montants sont saisis hors taxes, en euros (devise modifiable dans la barre latérale).
- Le taux d'actualisation doit être strictement supérieur à −100 % ; les taux négatifs sont acceptés.
- La durée est un entier compris entre 1 et 50 ans.
- Les flux peuvent être négatifs (années de réinvestissement, démantèlement) ou nuls.
- L'investissement initial est saisi en positif ; il est automatiquement compté en décaissement dans la formule.
- Chaque erreur de saisie produit un message explicite en français, et **aucun résultat n'est affiché tant que les données ne sont pas valides**.
- Le TRI n'est affiché que s'il existe : en l'absence de changement de signe des flux, la mention « Non calculable » apparaît.

## 4. Exemple de démonstration

Le bouton **« Charger l'exemple de démonstration »** remplit le calculateur avec un
projet fictif, clairement identifié comme tel :

| Paramètre | Valeur |
| --- | --- |
| Projet | Projet A — Extension d'atelier |
| Investissement initial | 1 000 € |
| Taux d'actualisation | 10 % |
| Durée | 3 ans |
| Flux | 500 € / 500 € / 500 € |

Résultat attendu : **VAN = +243,43 €**, TRI = 23,38 %, indice de rentabilité = 1,24,
délai de récupération ≈ 2,35 ans. Ce résultat sert de vérification : il est repris
à l'identique dans le guide pédagogique.

Les exemples utilisés sur la page de comparaison (Projets A, B et C) montrent en
plus un cas de conflit entre VAN et TRI : le projet B a la VAN la plus élevée mais
un TRI plus faible que le projet A.

## 5. Où sont enregistrées les données ?

Streamlit s'exécute côté serveur : le navigateur ne peut pas stocker durablement
l'historique. Celui-ci est donc conservé dans un fichier JSON local, indiqué dans
la barre latérale :

```
/Users/user/Desktop/mon app/.van_data/historique.json
```

Ce fichier survit à la fermeture du navigateur et à l'arrêt de l'application.
La page **Historique** permet aussi d'**exporter** cet historique dans un fichier
JSON et de le **réimporter** (sauvegarde, transfert vers une autre machine).

## 6. Structure du projet

```
app.py                         point d'entrée : configuration, navigation, barre latérale
requirements.txt               dépendances Python
.streamlit/config.toml         thème (bleu foncé / blanc / vert) et options du serveur
van_analyzer/
    finance.py                 moteur de calcul pur (VAN, TRI, IP, délai, interprétation)
    donnees.py                 persistance JSON et jeux de données de démonstration
    etat.py                    état de session, navigation, versionnage des tableaux
    presentation.py            formatage français des nombres, feuille de style, composants HTML
    graphiques.py              graphiques Plotly (flux, cumuls, comparaison, profil de VAN)
    pages_accueil.py           page d'accueil
    pages_calculateur.py       calculateur de VAN
    pages_comparaison.py       comparaison de projets
    pages_historique.py        historique des calculs
    pages_guide.py             guide pédagogique
tests/
    test_finance.py            tests unitaires du moteur de calcul (41 tests)
    test_app.py                tests d'intégration des pages (22 tests)
```

## 7. Tests

```bash
cd "/Users/user/Desktop/mon app"
.venv/bin/python -m unittest discover -s tests -t .
```

Les tests couvrent la formule de la VAN, le TRI, l'indice de rentabilité, le délai
de récupération, les cas limites (durée nulle, flux négatifs, taux extrêmes), la
validation des saisies, ainsi que le rendu et les interactions des cinq pages
(63 tests au total).

## 8. Déploiement sur Streamlit Cloud

Le dépôt contient tout ce qu'il faut : `app.py` (point d'entrée) et
`requirements.txt` (dépendances). Le dossier `.venv` est exclu par `.gitignore` :
Streamlit installe lui-même les bibliothèques.

1. Pousser le code sur GitHub (branche `main`).
2. Aller sur <https://share.streamlit.io> et choisir **New app**.
3. Sélectionner le dépôt, la branche `main`, puis indiquer **`app.py`** comme
   *Main file path*.
4. Cliquer sur **Deploy**.

> **À savoir pour l'historique en ligne.** Sur Streamlit Cloud, le disque est
> temporaire : le fichier `.van_data/historique.json` est recréé à chaque
> redémarrage ou redéploiement de l'application. Les calculs enregistrés
> fonctionnent normalement pendant une session de travail, mais pour les
> conserver durablement, utilisez le bouton **Exporter** de la page Historique
> (fichier JSON) et réimportez-le à la prochaine connexion. En local, le fichier
> est permanent.

## 9. Notes

- Les calculs sont effectués à la volée : toute modification d'une hypothèse
  actualise immédiatement les résultats.
- Les graphiques sont produits avec Plotly et respectent les conventions
  françaises d'écriture des nombres (virgule décimale, espace pour les milliers).
- Aucune fonctionnalité ne dépend d'Internet.
