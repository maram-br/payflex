"""Génère le rapport de synthèse PDF du TP PayFlex."""

from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT = Path("output/pdf/rapport-synthese-payflex.pdf")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

NAVY = colors.HexColor("#102A43")
BLUE = colors.HexColor("#1677FF")
CYAN = colors.HexColor("#00A6A6")
GREEN = colors.HexColor("#1F9D55")
AMBER = colors.HexColor("#D97706")
RED = colors.HexColor("#C53030")
LIGHT = colors.HexColor("#F4F7FB")
MID = colors.HexColor("#D8E2EE")
TEXT = colors.HexColor("#243B53")
MUTED = colors.HexColor("#627D98")


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="CoverTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=29,
        leading=34,
        textColor=NAVY,
        alignment=TA_LEFT,
        spaceAfter=8 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="CoverSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=19,
        textColor=MUTED,
        spaceAfter=7 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="H1Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=NAVY,
        spaceBefore=2 * mm,
        spaceAfter=5 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="H2Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=BLUE,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="BodyCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.4,
        leading=13.2,
        textColor=TEXT,
        spaceAfter=2.5 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="SmallCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=MUTED,
    )
)
styles.add(
    ParagraphStyle(
        name="Callout",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=NAVY,
        leftIndent=5 * mm,
        rightIndent=5 * mm,
        borderColor=CYAN,
        borderWidth=1,
        borderPadding=4 * mm,
        backColor=colors.HexColor("#EAFBFA"),
        spaceBefore=3 * mm,
        spaceAfter=4 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="Placeholder",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=MUTED,
    )
)


def p(text, style="BodyCustom"):
    return Paragraph(text, styles[style])


def bullet(text):
    return Paragraph(f"• {text}", styles["BodyCustom"])


def header_footer(canvas, document):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(MID)
    canvas.line(18 * mm, height - 15 * mm, width - 18 * mm, height - 15 * mm)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(NAVY)
    canvas.drawString(18 * mm, height - 11 * mm, "PAYFLEX API")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(width - 18 * mm, height - 11 * mm, "Pipeline CI/CD intelligent")
    canvas.line(18 * mm, 13 * mm, width - 18 * mm, 13 * mm)
    canvas.drawString(18 * mm, 8.5 * mm, "Rapport de synthèse — 11 novembre 2026")
    canvas.drawRightString(width - 18 * mm, 8.5 * mm, f"Page {document.page}")
    canvas.restoreState()


def architecture_diagram():
    drawing = Drawing(172 * mm, 64 * mm)
    box_w, box_h = 48 * mm, 14 * mm
    positions = [
        (0, 46, "1. Confidentialité", "Gitleaks + build", BLUE),
        (62, 46, "2. Tests unitaires", "PyTest + couverture", CYAN),
        (124, 46, "3. Qualité", "SonarQube", BLUE),
        (124, 16, "4. Intégration", "Docker + Newman", CYAN),
        (62, 16, "5. Performance", "k6 + Quality Gate", BLUE),
        (0, 16, "6. Déploiement", "GHCR / main", GREEN),
    ]
    for x_mm, y_mm, title, subtitle, color in positions:
        x, y = x_mm * mm, y_mm * mm
        drawing.add(Rect(x, y, box_w, box_h, rx=3 * mm, ry=3 * mm, fillColor=color, strokeColor=color))
        drawing.add(String(x + 4 * mm, y + 8.3 * mm, title, fontName="Helvetica-Bold", fontSize=8.2, fillColor=colors.white))
        drawing.add(String(x + 4 * mm, y + 3.5 * mm, subtitle, fontName="Helvetica", fontSize=7, fillColor=colors.white))
    line_color = colors.HexColor("#829AB1")
    drawing.add(Line(48 * mm, 53 * mm, 62 * mm, 53 * mm, strokeColor=line_color, strokeWidth=1.5))
    drawing.add(Line(110 * mm, 53 * mm, 124 * mm, 53 * mm, strokeColor=line_color, strokeWidth=1.5))
    drawing.add(Line(148 * mm, 46 * mm, 148 * mm, 30 * mm, strokeColor=line_color, strokeWidth=1.5))
    drawing.add(Line(124 * mm, 23 * mm, 110 * mm, 23 * mm, strokeColor=line_color, strokeWidth=1.5))
    drawing.add(Line(62 * mm, 23 * mm, 48 * mm, 23 * mm, strokeColor=line_color, strokeWidth=1.5))
    drawing.add(String(51 * mm, 55.5 * mm, "OK", fontName="Helvetica-Bold", fontSize=6.5, fillColor=GREEN))
    drawing.add(String(113 * mm, 55.5 * mm, "OK", fontName="Helvetica-Bold", fontSize=6.5, fillColor=GREEN))
    drawing.add(String(150 * mm, 36 * mm, "OK", fontName="Helvetica-Bold", fontSize=6.5, fillColor=GREEN))
    drawing.add(String(113 * mm, 25.5 * mm, "OK", fontName="Helvetica-Bold", fontSize=6.5, fillColor=GREEN))
    drawing.add(String(51 * mm, 25.5 * mm, "OK", fontName="Helvetica-Bold", fontSize=6.5, fillColor=GREEN))
    drawing.add(String(1 * mm, 4 * mm, "Toute erreur critique produit un rapport d'incident et empêche les étapes suivantes.", fontName="Helvetica-Oblique", fontSize=8, fillColor=RED))
    return drawing


def threshold_table():
    data = [
        [p("Indicateur", "SmallCustom"), p("Conforme", "SmallCustom"), p("Warning", "SmallCustom"), p("Critique", "SmallCustom")],
        ["Couverture", ">= 80 %", "70 à < 80 %", "< 70 %"],
        ["Latence p95", "<= 200 ms", "> 200 à <= 500 ms", "> 500 ms"],
        ["Taux d'erreur", "< 1 %", ">= 1 à <= 2 %", "> 2 %"],
        ["Bugs / vulnérabilités", "0", "Code smells", "> 0"],
        ["Confidentialité", "100 %", "—", "< 100 %"],
    ]
    table = Table(data, colWidths=[43 * mm, 37 * mm, 47 * mm, 42 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("TEXTCOLOR", (0, 1), (-1, -1), TEXT),
                ("BACKGROUND", (1, 1), (1, -1), colors.HexColor("#EAF7EF")),
                ("BACKGROUND", (2, 1), (2, -1), colors.HexColor("#FFF5E5")),
                ("BACKGROUND", (3, 1), (3, -1), colors.HexColor("#FDECEC")),
                ("GRID", (0, 0), (-1, -1), 0.5, MID),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2 * mm),
            ]
        )
    )
    return table


class ScreenshotPlaceholder(Flowable):
    def __init__(self, title, expected, height=42 * mm):
        super().__init__()
        self.title = title
        self.expected = expected
        self.width = 169 * mm
        self.height = height

    def draw(self):
        canvas = self.canv
        canvas.setStrokeColor(MID)
        canvas.setDash(5, 4)
        canvas.roundRect(0, 0, self.width, self.height, 3 * mm, stroke=1, fill=0)
        canvas.setDash()
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawCentredString(self.width / 2, self.height - 12 * mm, self.title)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 8.5)
        canvas.drawCentredString(self.width / 2, self.height - 20 * mm, self.expected)
        canvas.setFillColor(colors.HexColor("#F4F7FB"))
        canvas.roundRect(18 * mm, 7 * mm, self.width - 36 * mm, 9 * mm, 2 * mm, stroke=0, fill=1)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica-Oblique", 7.5)
        canvas.drawCentredString(self.width / 2, 10.2 * mm, "Insérer ici la capture GitHub Actions après l'exécution du workflow corrigé")


story = []

# Couverture
story.extend(
    [
        Spacer(1, 23 * mm),
        p("TP AVANCÉ", "SmallCustom"),
        p("Pipeline CI/CD intelligent &<br/>analyse de qualité / risque applicatif", "CoverTitle"),
        p("PayFlex API — FastAPI, Docker, PyTest, Newman, k6, SonarQube et Gitleaks", "CoverSub"),
        Spacer(1, 7 * mm),
        Table(
            [
                [p("OBJECTIF", "SmallCustom"), p("GARANTIE PRINCIPALE", "SmallCustom")],
                [p("Automatiser la validation et le déploiement d'une API financière."), p("Aucune erreur critique, baisse de performance ou fuite ne peut atteindre la production.")],
            ],
            colWidths=[82 * mm, 82 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BACKGROUND", (0, 1), (-1, 1), LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.7, MID),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, MID),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
                ]
            ),
        ),
        Spacer(1, 22 * mm),
        p("Rapport de synthèse technique", "H2Custom"),
        p("Version préparée le 11 novembre 2026. Le document décrit le pipeline implémenté et la procédure de preuve des trois scénarios demandés."),
        PageBreak(),
    ]
)

# Architecture
story.extend(
    [
        p("1. Architecture générale", "H1Custom"),
        p("Le workflow est une chaîne séquentielle. Chaque job dépend du précédent avec <b>needs</b>. Un échec critique arrête donc la progression avant le déploiement."),
        Spacer(1, 3 * mm),
        architecture_diagram(),
        Spacer(1, 4 * mm),
        p("Principe de l'artefact unique", "H2Custom"),
        p("L'image Docker est construite une seule fois dans le premier job, puis exportée comme artefact. Newman, k6 et le déploiement chargent exactement cette image identifiée par le SHA du commit. Le code testé est ainsi identique au code publié."),
        p("Déclencheurs", "H2Custom"),
        bullet("<b>push</b> : exécute toute la CI ; un push sur main peut publier l'image."),
        bullet("<b>pull_request</b> : valide le changement sans déployer."),
        bullet("<b>workflow_dispatch</b> : permet d'exécuter les trois scénarios de démonstration."),
        p("Fail-fast", "H2Custom"),
        p("Un code de sortie non nul marque le job en échec. GitHub Actions ignore alors tous ses descendants. Les étapes marquées <b>if: always()</b> conservent néanmoins les logs, métriques et rapports d'incident."),
        PageBreak(),
    ]
)

# Stages 1-3
story.extend(
    [
        p("2. Confidentialité, tests et qualité", "H1Custom"),
        p("Étape 1 — Gitleaks et construction", "H2Custom"),
        p("Gitleaks analyse l'historique Git, les sources/configurations suivies et le contenu applicatif de l'image Docker. Les règles standards sont complétées par des expressions de détection pour les cartes bancaires et les IBAN."),
        p("Le seuil maximal toléré étant zéro, la formule fournie dans l'énoncé est remplacée par une convention binaire : <b>0 fuite = 100 %</b> ; <b>au moins 1 fuite = 0 %</b>. Un rapport absent ou illisible vaut également 0 %, afin d'éviter qu'une panne du scanner soit interprétée comme un succès."),
        p("Étape 2 — PyTest et couverture", "H2Custom"),
        p("Les tests unitaires couvrent le health check, la création, la validation métier, les champs obligatoires et la consultation d'un paiement. PyTest produit coverage.xml, junit.xml et pytest.log. Le Quality Gate classe ensuite la couverture selon le tableau des seuils."),
        p("Étape 3 — SonarQube Community", "H2Custom"),
        p("Une instance éphémère est démarrée dans le runner. Son Quality Gate bloque une couverture inférieure à 70 %, tout bug ou toute vulnérabilité. Les code smells et la zone de couverture 70–80 % restent non critiques et génèrent un warning."),
        Spacer(1, 4 * mm),
        threshold_table(),
        Spacer(1, 5 * mm),
        p("Règle de décision", "Callout"),
        p("VERT : continuer.  ORANGE : continuer avec alerte.  ROUGE : rapport d'incident, code de sortie 1 et aucun déploiement."),
        PageBreak(),
    ]
)

# Stages 4-6
story.extend(
    [
        p("3. Intégration, performance et déploiement", "H1Custom"),
        p("Étape 4 — Docker + Newman", "H2Custom"),
        p("Le job charge l'image validée et démarre un conteneur éphémère. Un health check confirme la disponibilité de l'API, puis Newman vérifie les contrats HTTP et le flux création/lecture. Les cas d'erreur 400 et 404 sont aussi contrôlés. Un crash ou une assertion Newman échouée est critique."),
        p("Étape 5 — k6", "H2Custom"),
        p("k6 applique 20 utilisateurs virtuels pendant 30 secondes. Il mesure le p95, les erreurs HTTP et les checks. Le taux d'erreur effectif est la valeur la plus défavorable entre erreurs HTTP et checks en échec. Les seuils critiques sont présents dans k6 et réévalués par quality_gate.py pour produire une classification claire."),
        p("Étape 6 — publication contrôlée", "H2Custom"),
        p("Le job de déploiement ne s'exécute que sur un push réussi vers main. Il charge l'image déjà testée, la marque avec le SHA du commit puis la publie dans GitHub Container Registry. Une branche, une Pull Request ou un lancement manuel ne peut pas publier."),
        p("Analyse des logs", "H2Custom"),
        p("Après PyTest, Newman et k6, les sorties et les logs applicatifs sont scannés par Gitleaks. Une fuite dans un log est soumise au même seuil de confidentialité de 100 % que le code et l'artefact."),
        p("Rapports produits", "H2Custom"),
        Table(
            [
                ["Job", "Rapports principaux"],
                ["Confidentialité", "gitleaks-*.json, quality-report-secrets.json"],
                ["Unitaires", "coverage.xml, junit.xml, pytest.log"],
                ["SonarQube", "sonar-measures.json, quality-report-sonar.json"],
                ["Intégration", "newman-report.json, logs applicatifs"],
                ["Performance", "k6-summary.json, k6.log, logs applicatifs"],
                ["Erreur critique", "incident-*.md + résumé GitHub Actions"],
            ],
            colWidths=[42 * mm, 127 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.2),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                    ("GRID", (0, 0), (-1, -1), 0.5, MID),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.3 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.3 * mm),
                ]
            ),
        ),
        PageBreak(),
    ]
)

# Error classification
story.extend(
    [
        p("4. Classification automatique des erreurs", "H1Custom"),
        p("Le script quality_gate.py lit les rapports techniques, normalise les métriques et produit un rapport JSON contenant stage, status, metrics, warnings et critical_errors."),
        p("Erreur non critique", "H2Custom"),
        bullet("Couverture comprise entre 70 % et 80 %."),
        bullet("Latence p95 comprise entre 200 ms et 500 ms."),
        bullet("Taux d'erreur compris entre 1 % et 2 %."),
        bullet("Code smells sans bug ni vulnérabilité."),
        p("Le pipeline continue, mais une annotation warning et un résumé sont générés."),
        p("Erreur critique", "H2Custom"),
        bullet("Test unitaire, Newman ou démarrage de l'API en échec."),
        bullet("Couverture inférieure à 70 %, bug ou vulnérabilité SonarQube."),
        bullet("p95 supérieur à 500 ms ou taux d'erreur supérieur à 2 %."),
        bullet("Fuite dans les sources, l'historique, l'artefact ou les logs."),
        bullet("Rapport obligatoire absent ou invalide."),
        p("Le script écrit incident-*.md, publie des erreurs GitHub et termine avec le code 1. La dépendance needs bloque alors immédiatement la suite."),
        p("Scénarios de preuve intégrés", "H2Custom"),
        Table(
            [
                ["Entrée", "Effet", "Résultat attendu"],
                ["success", "Aucune injection", "Pipeline vert"],
                ["performance_failure", "Latence de test à 600 ms", "Échec au job k6"],
                ["secret_leak", "PAN de test créé à l'exécution", "Échec au premier job"],
            ],
            colWidths=[43 * mm, 62 * mm, 64 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.2),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                    ("GRID", (0, 0), (-1, -1), 0.5, MID),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ]
            ),
        ),
        Spacer(1, 6 * mm),
        p("Les données de démonstration sont synthétiques et ne contiennent aucun secret réel.", "Callout"),
        PageBreak(),
    ]
)

# Screenshots
story.extend(
    [
        p("5. Captures d'écran des exécutions", "H1Custom"),
        p("Les emplacements ci-dessous doivent recevoir les captures réelles après publication du workflow corrigé. Dans GitHub Actions, lancer success, performance_failure puis secret_leak depuis Run workflow."),
        ScreenshotPlaceholder("Capture 1 — Pipeline réussi", "Tous les jobs de validation verts ; déploiement ignoré lors du lancement manuel."),
        Spacer(1, 5 * mm),
        ScreenshotPlaceholder("Capture 2 — Échec de performance", "Job performance rouge ; p95 > 500 ms ; job deploy absent ou skipped."),
        Spacer(1, 5 * mm),
        ScreenshotPlaceholder("Capture 3 — Fuite confidentielle", "Job confidentialité rouge ; taux 0 % ; jobs suivants skipped."),
        Spacer(1, 5 * mm),
        p("Note : les captures ne peuvent être produites qu'après un push et une exécution distante. Elles ne sont pas simulées dans ce rapport afin de préserver la valeur probante du livrable.", "SmallCustom"),
        PageBreak(),
    ]
)

# Checklist
story.extend(
    [
        p("6. Vérification du livrable", "H1Custom"),
        Table(
            [
                ["Exigence", "Implémentation", "État"],
                ["Tests unitaires + couverture", "PyTest, coverage.xml, seuils 70/80", "OK"],
                ["Tests d'intégration", "Docker éphémère + Newman", "OK"],
                ["Tests de performance", "k6, p95 et taux d'erreur", "OK"],
                ["Qualité statique", "SonarQube Community + Quality Gate", "OK"],
                ["Confidentialité", "Gitleaks sources, artefact, logs, PII", "OK"],
                ["Fail-fast", "needs + codes de sortie critiques", "OK"],
                ["Rapports d'incident", "JSON, Markdown, artefacts always()", "OK"],
                ["Déploiement conditionnel", "Image validée vers GHCR sur main", "OK"],
                ["Captures GitHub Actions", "Trois exécutions workflow_dispatch", "À insérer"],
            ],
            colWidths=[55 * mm, 86 * mm, 28 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.2),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                    ("TEXTCOLOR", (2, 1), (2, -2), GREEN),
                    ("TEXTCOLOR", (2, -1), (2, -1), AMBER),
                    ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, MID),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ]
            ),
        ),
        Spacer(1, 8 * mm),
        p("Conclusion", "H2Custom"),
        p("Le pipeline PayFlex couvre la chaîne demandée de bout en bout : construction immuable, tests multi-niveaux, analyse qualité, confidentialité à tolérance zéro, classification automatique et publication uniquement après validation complète. Les avertissements restent visibles sans interrompre le flux ; toute anomalie critique interdit le déploiement."),
    ]
)


document = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=20 * mm,
    leftMargin=20 * mm,
    topMargin=22 * mm,
    bottomMargin=19 * mm,
    title="PayFlex — Rapport de synthèse CI/CD",
    author="Projet PayFlex",
    subject="Pipeline CI/CD intelligent et analyse de qualité / risque applicatif",
)
document.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
print(OUTPUT)
