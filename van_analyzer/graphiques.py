"""Construction des graphiques Plotly de l'application."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import finance, presentation as pres

POLICE = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'


def _mise_en_page(fig: go.Figure, hauteur: int = 430, titre: str = "") -> go.Figure:
    """Applique la charte graphique commune à tous les graphiques.

    ``separators=", "`` demande à Plotly d'utiliser la virgule comme séparateur
    décimal et l'espace comme séparateur de milliers : les axes et les infobulles
    respectent ainsi les conventions françaises.
    """
    disposition = dict(
        template="plotly_white",
        height=hauteur,
        separators=", ",
        # Sans titre, on laisse tout de même de l'air au-dessus du graphique :
        # la légende y est ancrée (y = 1,02).
        margin=dict(l=8, r=8, t=48 if titre else 40, b=8),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=12),
        ),
        font=dict(family=POLICE, size=12, color="#334155"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hoverlabel=dict(bgcolor="white", font_size=12, bordercolor=pres.GRIS_BORDURE),
        bargap=0.28,
        bargroupgap=0.08,
    )
    # On n'ajoute un titre que s'il y en a un : passer ``title=None`` fait
    # apparaître la chaîne « undefined » dans le graphique.
    if titre:
        disposition["title"] = dict(
            text=titre, font=dict(size=15, color=pres.BLEU_FONCE)
        )

    fig.update_layout(**disposition)
    fig.update_xaxes(showgrid=False, linecolor=pres.GRIS_BORDURE, zeroline=False)
    fig.update_yaxes(
        gridcolor="#EDF1F6", zerolinecolor="#B9C4D4", linecolor=pres.GRIS_BORDURE
    )
    return fig


# --------------------------------------------------------------------------
# Graphique principal du calculateur
# --------------------------------------------------------------------------


def graphique_flux(resultat: finance.Resultat, symbole: Optional[str] = None) -> go.Figure:
    """Flux de trésorerie saisis / actualisés et cumul actualisé."""
    symbole = symbole or pres.devise()
    lignes = resultat.lignes
    etiquettes = [f"Année {l.annee}" if l.annee else "Année 0<br>(invest.)" for l in lignes]
    annees = [l.annee for l in lignes]
    flux = [l.flux for l in lignes]
    actualises = [l.flux_actualise for l in lignes]
    cumuls = [l.cumul_actualise for l in lignes]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=etiquettes,
            y=flux,
            name="Flux de trésorerie",
            marker_color=pres.BLEU,
            marker_line_width=0,
            customdata=[[pres.formater_montant_signe(v, symbole=symbole)] for v in flux],
            hovertemplate="<b>%{x}</b><br>Flux saisi : %{customdata[0]}<extra></extra>",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=etiquettes,
            y=actualises,
            name="Flux actualisé",
            marker_color=pres.BLEU_CLAIR,
            marker_line_width=0,
            customdata=[
                [pres.formater_montant_signe(v, symbole=symbole)] for v in actualises
            ],
            hovertemplate="<b>%{x}</b><br>Flux actualisé : %{customdata[0]}<extra></extra>",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=etiquettes,
            y=cumuls,
            name="Cumul actualisé",
            mode="lines+markers",
            line=dict(color=pres.VERT if resultat.est_positive else pres.ORANGE, width=3),
            marker=dict(size=8, color="white", line=dict(width=2)),
            customdata=[[pres.formater_montant_signe(v, symbole=symbole)] for v in cumuls],
            hovertemplate="<b>%{x}</b><br>Cumul actualisé : %{customdata[0]}<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_yaxes(
        title_text=f"Flux par année ({symbole})", secondary_y=False, tickformat=",.0f"
    )
    fig.update_yaxes(
        title_text=f"Cumul actualisé ({symbole})", secondary_y=True, showgrid=False, tickformat=",.0f"
    )
    fig.add_hline(y=0, line=dict(color="#B9C4D4", width=1), secondary_y=False)

    _mise_en_page(fig, hauteur=440)
    fig.update_layout(hovermode="x unified")
    return fig


# --------------------------------------------------------------------------
# Profil de la VAN selon le taux d'actualisation
# --------------------------------------------------------------------------


def graphique_profil(resultat: finance.Resultat, taux_max: float = 0.6) -> go.Figure:
    """Courbe de la VAN en fonction du taux d'actualisation (profil de VAN)."""
    symbole = pres.devise()
    taux, valeurs = finance.profil_van(
        resultat.projet.investissement_initial, resultat.projet.flux, taux_max=taux_max
    )
    pourcentages = [t * 100.0 for t in taux]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=pourcentages,
            y=valeurs,
            name="VAN",
            mode="lines",
            line=dict(color=pres.BLEU, width=3),
            fill="tozeroy",
            fillcolor="rgba(27,79,138,0.08)",
            customdata=[
                [pres.formater_montant(v, symbole=symbole)] for v in valeurs
            ],
            hovertemplate="Taux : %{x:.1f} %<br>VAN : %{customdata[0]}<extra></extra>",
        )
    )

    taux_actuel = resultat.projet.taux_actualisation * 100.0
    fig.add_vline(
        x=taux_actuel,
        line=dict(color=pres.ORANGE, width=2, dash="dash"),
        annotation_text=f"Taux retenu : {pres.formater_nombre(taux_actuel)} %",
        annotation_position="top right",
        annotation_font=dict(color=pres.ORANGE, size=11),
    )
    fig.add_hline(y=0, line=dict(color="#B9C4D4", width=1))

    if resultat.tri is not None and 0.0 <= resultat.tri <= taux_max:
        fig.add_trace(
            go.Scatter(
                x=[resultat.tri * 100.0],
                y=[0.0],
                name=f"TRI : {pres.formater_pourcentage(resultat.tri)}",
                mode="markers",
                marker=dict(size=13, color=pres.VERT, symbol="diamond"),
                hovertemplate="TRI : %{x:.2f} %<extra></extra>",
            )
        )

    fig.update_xaxes(title_text="Taux d'actualisation (%)")
    fig.update_yaxes(title_text=f"VAN ({symbole})")
    return _mise_en_page(fig, hauteur=380)


# --------------------------------------------------------------------------
# Graphiques de comparaison
# --------------------------------------------------------------------------


def graphique_comparaison_van(resultats: Sequence[finance.Resultat]) -> go.Figure:
    """Comparaison des VAN des projets sélectionnés."""
    symbole = pres.devise()
    noms = [r.projet.nom for r in resultats]
    valeurs = [r.van for r in resultats]
    couleurs = [pres.couleur_van(v) for v in valeurs]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=noms,
            y=valeurs,
            marker_color=couleurs,
            marker_line_width=0,
            text=[pres.formater_montant_signe(v, symbole=symbole) for v in valeurs],
            textposition="outside",
            textfont=dict(size=12, color=pres.BLEU_FONCE),
            cliponaxis=False,
            customdata=[
                [
                    pres.formater_montant(v, symbole=symbole),
                    pres.formater_pourcentage(r.projet.taux_actualisation),
                ]
                for r, v in zip(resultats, valeurs)
            ],
            hovertemplate=(
                "<b>%{x}</b><br>VAN : %{customdata[0]}"
                "<br>Taux retenu : %{customdata[1]}<extra></extra>"
            ),
        )
    )
    fig.add_hline(y=0, line=dict(color="#7C8DA6", width=1))
    fig.update_yaxes(title_text=f"VAN ({symbole})")
    fig.update_xaxes(title_text="")
    _mise_en_page(fig, hauteur=420)
    fig.update_layout(showlegend=False)
    return fig


def graphique_comparaison_profils(
    resultats: Sequence[finance.Resultat], taux_max: float = 0.6
) -> go.Figure:
    """Profils de VAN superposés, pour situer le taux de croisement."""
    symbole = pres.devise()
    palette = [pres.BLEU, pres.VERT, pres.ORANGE, "#7C3AED", "#0891B2", "#BE185D"]

    fig = go.Figure()
    for index, resultat in enumerate(resultats):
        taux, valeurs = finance.profil_van(
            resultat.projet.investissement_initial,
            resultat.projet.flux,
            taux_max=taux_max,
        )
        couleur = palette[index % len(palette)]
        fig.add_trace(
            go.Scatter(
                x=[t * 100.0 for t in taux],
                y=valeurs,
                name=resultat.projet.nom,
                mode="lines",
                line=dict(color=couleur, width=3),
                customdata=[
                    [pres.formater_montant(v, symbole=symbole)] for v in valeurs
                ],
                hovertemplate=(
                    "<b>" + resultat.projet.nom + "</b><br>Taux : %{x:.1f} %"
                    "<br>VAN : %{customdata[0]}<extra></extra>"
                ),
            )
        )
        if resultat.tri is not None and 0.0 <= resultat.tri <= taux_max:
            fig.add_trace(
                go.Scatter(
                    x=[resultat.tri * 100.0],
                    y=[0.0],
                    mode="markers",
                    marker=dict(size=11, color=couleur, symbol="diamond"),
                    showlegend=False,
                    hovertemplate=(
                        "<b>" + resultat.projet.nom + "</b><br>TRI : %{x:.2f} %"
                        "<extra></extra>"
                    ),
                )
            )

    if resultats:
        fig.add_vline(
            x=resultats[0].projet.taux_actualisation * 100.0,
            line=dict(color="#94A3B8", width=1, dash="dash"),
        )
    fig.add_hline(y=0, line=dict(color="#7C8DA6", width=1))
    fig.update_xaxes(title_text="Taux d'actualisation (%)")
    fig.update_yaxes(title_text=f"VAN ({symbole})")
    return _mise_en_page(fig, hauteur=420)


# --------------------------------------------------------------------------
# Graphique du guide pédagogique
# --------------------------------------------------------------------------


def graphique_actualisation(
    flux: Sequence[float], flux_actualises: Sequence[float], symbole: Optional[str] = None
) -> go.Figure:
    """Illustration de l'effet de l'actualisation sur chaque flux."""
    symbole = symbole or pres.devise()
    etiquettes = [f"Année {index}" for index in range(1, len(flux) + 1)]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=etiquettes,
            y=list(flux),
            name="Flux brut",
            marker_color=pres.BLEU,
            marker_line_width=0,
            customdata=[[pres.formater_montant(v, symbole=symbole)] for v in flux],
            hovertemplate="%{x}<br>Flux brut : %{customdata[0]}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=etiquettes,
            y=list(flux_actualises),
            name="Flux actualisé",
            marker_color=pres.BLEU_CLAIR,
            marker_line_width=0,
            customdata=[
                [pres.formater_montant(v, symbole=symbole)] for v in flux_actualises
            ],
            hovertemplate="%{x}<br>Flux actualisé : %{customdata[0]}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line=dict(color="#B9C4D4", width=1))
    fig.update_yaxes(title_text=f"Montant ({symbole})")
    _mise_en_page(fig, hauteur=340)
    return fig


def graphique_historique_van(entrees: Sequence[Dict[str, object]]) -> go.Figure:
    """Répartition des VAN enregistrées dans l'historique."""
    symbole = pres.devise()
    noms = [str(e.get("nom", "Projet")) for e in entrees]
    valeurs = [float(e.get("van_enregistree", 0.0)) for e in entrees]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=valeurs,
            y=noms,
            orientation="h",
            marker_color=[pres.couleur_van(v) for v in valeurs],
            marker_line_width=0,
            customdata=[[pres.formater_montant(v, symbole=symbole)] for v in valeurs],
            hovertemplate="<b>%{y}</b><br>VAN : %{customdata[0]}<extra></extra>",
        )
    )
    fig.add_vline(x=0, line=dict(color="#7C8DA6", width=1))
    fig.update_xaxes(title_text=f"VAN ({symbole})")
    fig.update_yaxes(autorange="reversed")
    _mise_en_page(fig, hauteur=max(280, 60 + 34 * len(entrees)))
    fig.update_layout(showlegend=False)
    return fig
