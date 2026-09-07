#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère les ressources téléchargeables de la page /templates/.

    python3 tools/generate-templates.py

Sortie : templates/files/*.xlsx et *.pdf

RÈGLE : on ne publie ici que des documents qui **ne reflètent aucun code**.
Un fichier qui recopie une structure de l'application (colonnes d'import,
schéma de données…) devient faux dès que l'application évolue, et le prospect
qui l'a téléchargé se retrouve avec un fichier cassé. Le modèle d'import des
élèves a été retiré pour cette raison : l'application le génère elle-même, à
jour et par établissement (StudentController → generateImportTemplate).
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                Spacer, KeepTogether)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "templates", "files")
os.makedirs(OUT, exist_ok=True)

SITE = "www.madrassanet.com"
PITCH = ("MadrassaNET — le logiciel des écoles coraniques, madrasas et associations "
         "scolaires. Élèves, présences, bulletins et paiements, en français comme en "
         "arabe, pour 1 € par élève et par an.")

INDIGO = "3949AB"
INDIGO_LIGHT = "E8EAF6"
GREY = "F5F5F7"

THIN = Side(style="thin", color="D0D0D8")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_header(ws, ncols, row=1):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(bold=True, color="FFFFFF", size=10)
        cell.fill = PatternFill("solid", fgColor=INDIGO)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[row].height = 32


def add_pitch_sheet(wb):
    ws = wb.create_sheet("À propos")
    ws.column_dimensions["A"].width = 100
    ws["A1"] = "MadrassaNET"
    ws["A1"].font = Font(bold=True, size=16, color=INDIGO)
    ws["A3"] = PITCH
    ws["A3"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[3].height = 50
    ws["A5"] = "Site : https://%s" % SITE
    ws["A6"] = "Tarifs publics : https://%s/tarifs/" % SITE
    ws["A7"] = "Demander une démonstration : https://%s/#contact" % SITE
    ws["A9"] = ("Ce modèle est libre d'usage et de partage. Si vous le trouvez utile, "
                "transmettez-le à une autre école — c'est comme cela qu'on nous découvre.")
    ws["A9"].alignment = Alignment(wrap_text=True, vertical="top")
    return ws


# ═════════════════════════════════════════════════════════════════════════════
# 1. Modèle de bulletin bilingue
# ═════════════════════════════════════════════════════════════════════════════
SUBJECTS = [
    ("Coran — mémorisation", "القرآن — الحفظ"),
    ("Coran — récitation", "القرآن — التلاوة"),
    ("Tajwid", "التجويد"),
    ("Arabe — lecture", "العربية — القراءة"),
    ("Arabe — écriture", "العربية — الكتابة"),
    ("Arabe — expression orale", "العربية — التعبير"),
    ("Sciences islamiques", "العلوم الإسلامية"),
    ("Comportement et assiduité", "السلوك والمواظبة"),
]


def build_report_card():
    wb = Workbook()
    ws = wb.active
    ws.title = "Bulletin"
    rtl = Alignment(horizontal="right", vertical="center", readingOrder=2)

    ws["A1"] = "BULLETIN TRIMESTRIEL"
    ws["A1"].font = Font(bold=True, size=15, color=INDIGO)
    ws["F1"] = "كشف الدرجات الفصلي"
    ws["F1"].font = Font(bold=True, size=15, color=INDIGO)
    ws["F1"].alignment = rtl

    meta = [("Établissement / المؤسسة", ""), ("Élève / التلميذ", ""),
            ("Classe / القسم", ""), ("Trimestre / الفصل", ""),
            ("Année scolaire / السنة الدراسية", "")]
    r = 3
    for label, val in meta:
        ws["A%d" % r] = label
        ws["A%d" % r].font = Font(bold=True, size=10)
        ws["C%d" % r] = val
        ws["C%d" % r].fill = PatternFill("solid", fgColor=GREY)
        ws["C%d" % r].border = BORDER
        r += 1

    r += 1
    header = ["Matière", "المادة", "Note / 20", "Coef.", "Appréciation", "ملاحظات"]
    for i, h in enumerate(header, start=1):
        ws.cell(row=r, column=i, value=h)
    style_header(ws, len(header), row=r)
    first_data = r + 1
    r += 1
    for fr, ar in SUBJECTS:
        ws.cell(row=r, column=1, value=fr).font = Font(size=10)
        c = ws.cell(row=r, column=2, value=ar)
        c.font = Font(size=11)
        c.alignment = rtl
        ws.cell(row=r, column=4, value=1)
        ws.cell(row=r, column=6).alignment = rtl
        for i in range(1, 7):
            ws.cell(row=r, column=i).border = BORDER
        ws.row_dimensions[r].height = 22
        r += 1
    last_data = r - 1

    ws.cell(row=r, column=1, value="Moyenne générale / المعدل العام").font = Font(
        bold=True, size=10)
    avg = ws.cell(row=r, column=3)
    avg.value = "=IF(SUM(D%d:D%d)=0,\"\",SUMPRODUCT(C%d:C%d,D%d:D%d)/SUM(D%d:D%d))" % (
        first_data, last_data, first_data, last_data,
        first_data, last_data, first_data, last_data)
    avg.font = Font(bold=True, size=11, color=INDIGO)
    avg.number_format = "0.00"
    for i in range(1, 7):
        ws.cell(row=r, column=i).fill = PatternFill("solid", fgColor=INDIGO_LIGHT)
        ws.cell(row=r, column=i).border = BORDER

    r += 2
    ws.cell(row=r, column=1, value="Appréciation générale / الملاحظة العامة").font = Font(
        bold=True, size=10)
    r += 1
    ws.merge_cells(start_row=r, start_column=1, end_row=r + 2, end_column=6)
    ws.cell(row=r, column=1).border = BORDER
    r += 4
    ws.cell(row=r, column=1, value="Signature de l'enseignant").font = Font(size=9)
    ws.cell(row=r, column=5, value="Signature de la direction").font = Font(size=9)

    for col, w in zip("ABCDEF", [30, 26, 11, 8, 34, 30]):
        ws.column_dimensions[col].width = w
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    doc = wb.create_sheet("Mode d'emploi")
    doc.column_dimensions["A"].width = 100
    doc["A1"] = "Bulletin bilingue — mode d'emploi"
    doc["A1"].font = Font(bold=True, size=14, color=INDIGO)
    notes = [
        "Saisissez les notes dans la colonne « Note / 20 ». La moyenne générale se calcule "
        "automatiquement, pondérée par les coefficients.",
        "Le coefficient est à 1 par défaut : montez-le à 2 ou 3 pour les matières que votre "
        "école veut prioriser (souvent la mémorisation du Coran).",
        "Les intitulés arabes sont alignés à droite avec le sens de lecture RTL : ils "
        "s'impriment correctement sans réglage.",
        "Ajoutez ou supprimez des lignes de matières selon votre programme — la formule de "
        "moyenne suit automatiquement si vous insérez les lignes à l'intérieur du tableau.",
        "Pour imprimer : la feuille est déjà réglée en A4 portrait, ajustée à la largeur de "
        "la page.",
        "",
        "Dans MadrassaNET, ces bulletins sont générés en PDF pour toute une classe en une "
        "seule opération, avec les notes déjà saisies par les enseignants — ce fichier "
        "Excel est là pour les écoles qui n'ont pas encore franchi le pas.",
    ]
    r = 3
    for n in notes:
        doc["A%d" % r] = n
        doc["A%d" % r].alignment = Alignment(wrap_text=True, vertical="top")
        if n:
            doc.row_dimensions[r].height = 32
        r += 1

    add_pitch_sheet(wb)
    path = os.path.join(OUT, "modele-bulletin-bilingue.xlsx")
    wb.save(path)
    return path


# ═════════════════════════════════════════════════════════════════════════════
# 2. Feuille de présence trimestrielle (PDF, A4 paysage)
# ═════════════════════════════════════════════════════════════════════════════
BRAND_LINE = ("MadrassaNET — logiciel de gestion pour écoles coraniques, madrasas "
              "et associations scolaires · dès 1€/élève/an")


def _footer(canvas, doc):
    """Pied de page commun : une ligne de marque discrète, à gauche ; l'URL à droite."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#8A8A94"))
    canvas.drawString(15 * mm, 8 * mm, BRAND_LINE)
    canvas.drawRightString(doc.pagesize[0] - 15 * mm, 8 * mm, SITE)
    canvas.restoreState()


def _footer_attendance(canvas, doc):
    """Pied de page de la feuille d'appel : la légende des codes est dessinée ici
    (et non dans le flux) afin que le tableau tienne 20 élèves sur une seule page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#333333"))
    canvas.drawString(15 * mm, 17 * mm,
                      "Codes à inscrire :  P présent   ·   A absent   ·   R retard   ·   "
                      "E absence excusée   ·   —  pas de cours cette semaine")
    canvas.drawRightString(doc.pagesize[0] - 15 * mm, 17 * mm,
                           "Total absences du trimestre : ________     "
                           "Signature : ____________________")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#8A8A94"))
    canvas.drawString(15 * mm, 8 * mm, BRAND_LINE)
    canvas.drawRightString(doc.pagesize[0] - 15 * mm, 8 * mm, SITE)
    canvas.restoreState()


def build_attendance_sheet():
    path = os.path.join(OUT, "feuille-presence-trimestre.pdf")
    doc = SimpleDocTemplate(path, pagesize=landscape(A4),
                            leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=12 * mm, bottomMargin=22 * mm,
                            title="Feuille de présence trimestrielle",
                            author="MadrassaNET", subject="Feuille d'appel imprimable")
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=14, spaceAfter=2,
                        spaceBefore=0, textColor=colors.HexColor("#3949AB"))
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8,
                           textColor=colors.HexColor("#666666"))

    story = [Paragraph("Feuille de présence — trimestre", h1),
             Paragraph("École : ______________________________&nbsp;&nbsp;&nbsp; "
                       "Classe : ____________________&nbsp;&nbsp;&nbsp; "
                       "Enseignant : ____________________&nbsp;&nbsp;&nbsp; "
                       "Trimestre : ______&nbsp;&nbsp;&nbsp; "
                       "Année : __________", small),
             Spacer(1, 4 * mm)]

    nweeks = 12
    header = ["N°", "Nom et prénom de l'élève"] + ["S%d" % i for i in range(1, nweeks + 1)]
    rows = [header]
    nrows = 20
    for i in range(1, nrows + 1):
        rows.append([str(i), ""] + [""] * nweeks)

    col_widths = [10 * mm, 52 * mm] + [16 * mm] * nweeks
    table = Table(rows, colWidths=col_widths,
                  rowHeights=[8 * mm] + [7.1 * mm] * nrows, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3949AB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("LEFTPADDING", (1, 1), (1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0B0BC")),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7FA")]),
    ]))
    story.append(table)
    doc.build(story, onFirstPage=_footer_attendance, onLaterPages=_footer_attendance)
    return path


# ═════════════════════════════════════════════════════════════════════════════
# 3. Checklist de rentrée (PDF, A4 portrait)
# ═════════════════════════════════════════════════════════════════════════════
CHECKLIST = [
    ("MAI — arrêter l'année en cours", [
        "Arrêter les effectifs réels par classe et par niveau",
        "Repérer les classes surchargées et celles qui ne se rempliront pas",
        "Décider des ouvertures et fermetures de classes pour l'an prochain",
        "Recenser les enseignants qui reconduisent, et ceux qu'il faudra remplacer",
        "Fixer les tarifs de l'année suivante et les faire valider en réunion",
        "Fixer les dates : ouverture des réinscriptions, des inscriptions, rentrée",
    ]),
    ("JUIN — réinscrire les familles déjà présentes", [
        "Ouvrir les réinscriptions AUX SEULES familles déjà présentes (elles sont prioritaires)",
        "Envoyer l'information à toutes les familles, avec la date limite",
        "Encaisser les premiers règlements et enregistrer les échéanciers",
        "Suivre le taux de réinscription classe par classe, chaque semaine",
        "Remettre les bulletins du 3e trimestre",
    ]),
    ("JUILLET — relancer, puis ouvrir aux nouveaux", [
        "Relancer individuellement les familles non réinscrites (téléphone, pas email)",
        "Clôturer les réinscriptions et figer les places restantes",
        "Ouvrir les inscriptions aux nouvelles familles, avec liste d'attente",
        "Vérifier les documents manquants (justificatif de domicile, autorisations)",
    ]),
    ("AOÛT — préparer, pour ne pas improviser", [
        "Affecter chaque élève à une classe et à un créneau",
        "Constituer les groupes de niveau à l'intérieur des classes",
        "Confirmer à chaque enseignant ses classes, ses horaires et sa salle",
        "Préparer les listes d'appel, les registres et les supports",
        "Vérifier l'assurance de l'association et les autorisations de sortie",
        "Envoyer aux familles : date de rentrée, horaires, matériel, règlement intérieur",
    ]),
    ("SEPTEMBRE — accueillir, pas administrer", [
        "Afficher les listes de classes et le plan des salles le jour de la rentrée",
        "Accueillir les nouvelles familles séparément (10 minutes suffisent)",
        "Faire le premier appel dès la première séance, et le tenir chaque semaine",
        "Traiter les demandes de changement de classe dans la première quinzaine",
        "Relancer les impayés du premier versement",
    ]),
    ("OCTOBRE — verrouiller l'année", [
        "Arrêter définitivement les effectifs et clore les inscriptions",
        "Vérifier que chaque élève a une famille et un responsable joignable",
        "Faire le point financier : encaissé, échelonné, impayé",
        "Tenir la première réunion de rentrée avec les enseignants",
    ]),
]


def build_checklist():
    path = os.path.join(OUT, "checklist-rentree-ecole-associative.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title="Checklist de rentrée d'une école associative",
                            author="MadrassaNET",
                            subject="Rétroplanning de rentrée, mai à octobre")
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=17, spaceAfter=3,
                        textColor=colors.HexColor("#3949AB"))
    lead = ParagraphStyle("lead", parent=styles["Normal"], fontSize=9.5, leading=13,
                          textColor=colors.HexColor("#555555"), spaceAfter=6)
    month = ParagraphStyle("month", parent=styles["Heading2"], fontSize=11.5,
                           textColor=colors.HexColor("#1F2340"), spaceBefore=8,
                           spaceAfter=3)
    item = ParagraphStyle("item", parent=styles["Normal"], fontSize=9.5, leading=12,
                          leftIndent=0)

    story = [
        Paragraph("Checklist de rentrée d'une école associative", h1),
        Paragraph(
            "Le rétroplanning de mai à octobre, dans l'ordre où les choses doivent être "
            "faites. L'erreur la plus fréquente est d'ouvrir les inscriptions aux nouvelles "
            "familles avant d'avoir bouclé les réinscriptions : on se retrouve à arbitrer "
            "entre une famille fidèle et une nouvelle, en septembre, au comptoir. "
            "Imprimez, cochez, transmettez.", lead),
    ]
    # Les cases sont dessinées comme de vraies bordures de tableau : le glyphe
    # Unicode ☐ n'existe pas dans Helvetica et s'imprimerait en carré noir.
    box_style = TableStyle([
        ("GRID", (0, 0), (0, -1), 0.7, colors.HexColor("#5B62A8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 0),
        ("LEFTPADDING", (1, 0), (1, -1), 5),
        ("RIGHTPADDING", (1, 0), (1, -1), 0),
    ])
    for title, items in CHECKLIST:
        rows = [["", Paragraph(it, item)] for it in items]
        t = Table(rows, colWidths=[3.4 * mm, 170 * mm],
                  rowHeights=[4.6 * mm] * len(rows), style=box_style)
        # Une case ne doit pas dépasser la hauteur de sa ligne de texte.
        story.append(KeepTogether([Paragraph(title, month), t]))

    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        "<b>Combien de temps cela prend-il vraiment ?</b> Pour une école de 150 élèves "
        "tenue sur cahier ou tableur, ce rétroplanning représente environ 60 heures de "
        "bénévolat entre mai et octobre, dont la moitié en ressaisie. C'est exactement "
        "cette moitié que MadrassaNET supprime : réinscriptions en ligne, tarifs déduits "
        "de la classe et de la fratrie, reçus envoyés automatiquement, listes d'appel "
        "générées. " + SITE, lead))
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return path


if __name__ == "__main__":
    for fn in (build_report_card, build_attendance_sheet, build_checklist):
        p = fn()
        print("  ✓ %-46s %6.1f Ko" % (os.path.basename(p),
                                      os.path.getsize(p) / 1024))
    print("\nSortie : %s" % OUT)
