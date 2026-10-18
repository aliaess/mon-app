"""VAN Project Analyzer — analyse de la Valeur Actuelle Nette de projets.

Package principal de l'application. Les modules sont organisés ainsi :

- ``finance``       : moteur de calcul (VAN, TRI, IP, délai de récupération)
- ``donnees``       : persistance locale de l'historique + exemples de démonstration
- ``presentation``  : formatage des nombres, palette de couleurs, feuille de style
- ``graphiques``    : construction des graphiques Plotly
- ``pages_*``       : une page de l'application par module
"""

__all__ = ["finance", "donnees", "presentation", "graphiques"]
__version__ = "1.0.0"
