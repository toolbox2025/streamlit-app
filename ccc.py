# -- Vollständige SupervisionsDeck-App mit Interventionsnamen, Impulsen und Anliegenbeschreibungen --

import streamlit as st
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import base64


# -----------------------------
# 0. Passwort
# -----------------------------

def login():
    st.title("Login")
    password = st.text_input("Passwort", type="password")
    if password == "#ACIM2025#":  # ← Hier dein eigenes Passwort reinschreiben
        return True
    else:
        st.warning("Bitte Passwort eingeben.")
        return False

if login():
    st.title("Meine geheime App")
    st.write("Nur für mich sichtbar.")

# -----------------------------
# 1. METADATEN UND STRUKTUREN
# -----------------------------

# Interventionen: Code -> (Titel, Impuls)
intervention_meta = {
    "A": ("Anliegen klären", "…weil mir das Thema heute wichtig ist."),
    "B": ("Rollenklärung", "…um meine Rolle im Team besser zu verstehen."),
    "C": ("Erwartungen klären", "…weil sich vieles daran entscheidet."),
    "D": ("Selbstbild reflektieren", "…weil mein Blick auf mich eine Rolle spielt."),
    "E": ("Ressourcen entdecken", "…damit ich mich auf meine Stärken besinne."),
    "F": ("Erfolge sichern", "…um zu wissen, was funktioniert."),
    "G": ("Unterstützung einbeziehen", "…damit ich nicht alles allein tragen muss."),
    "H": ("Inneres Gleichgewicht", "…damit ich bei mir bleiben kann."),
    "I": ("Optionen erkennen", "…um mehr Handlungsspielraum zu sehen."),
    "J": ("Hindernisse überwinden", "…damit ich weiterkomme."),
    "K": ("Umsetzung fördern", "…weil es jetzt konkret wird."),
    "L": ("Selbstfürsorge stärken", "…um gesund zu bleiben."),
    "2": ("Abschluss", "…damit ich mit einem klaren Gefühl gehe.")
}



# Anliegen: Name -> Interventionscodes
anliegen_interventionen = {
    "A1: Unklare Kommunikation": ["D", "C", "J", "E"],
    "A2: Rollenunklarheit": ["B", "J", "I", "E"],
    "A3: Unerfüllte Erwartungen": ["C", "D", "F", "E"],
    "A4: Selbstbild und Identität": ["D", "C", "H", "E"],
    "A5: Verdeckte Ressourcen": ["E", "B", "I", "F"],
    "A6: Erfolg und Rückschläge": ["F", "D", "J", "E"],
    "A7: Fehlende Unterstützung": ["G", "B", "J", "E"],
    "A8: Inneres Ungleichgewicht": ["H", "C", "J", "E"],
    "A9: Eingeschränkte Handlungsoptionen": ["I", "D", "J", "E"],
    "A10: Konkrete Hindernisse": ["J", "B", "F", "E"],
    "A11: Umsetzung stockt": ["K", "D", "I", "E"],
    "A12: Vernachlässigte Selbstfürsorge": ["L", "H", "D", "E"],
    "A13: Klärung & Abschluss": ["2", "F", "G", "E"]
}



# Anliegenbeschreibungen
anliegen_beschreibung = {
    "A1: Unklare Kommunikation": "Im Team läuft vieles nebeneinander her, Absprachen sind unklar oder werden nicht eingehalten.",
    "A2: Rollenunklarheit": "Meine Rolle oder Verantwortung im Team ist unklar oder wird unterschiedlich interpretiert.",
    "A3: Unerfüllte Erwartungen": "Ich habe Erwartungen an mich oder andere, die regelmäßig enttäuscht werden.",
    "A4: Selbstbild und Identität": "Ich erlebe Widersprüche zwischen meinem Selbstbild und meinem beruflichen Handeln.",
    "A5: Verdeckte Ressourcen": "Ich spüre, dass ich über Kompetenzen verfüge, die ich aktuell kaum nutze.",
    "A6: Erfolg und Rückschläge": "Ein Rückschlag oder Misserfolg beschäftigt mich – ich möchte ihn besser verstehen.",
    "A7: Fehlende Unterstützung": "Ich fühle mich in einer aktuellen Situation alleingelassen oder überfordert.",
    "A8: Inneres Ungleichgewicht": "Ich merke, dass ich mich innerlich nicht mehr stabil oder ausgeglichen fühle.",
    "A9: Eingeschränkte Handlungsoptionen": "Ich sehe aktuell keine guten Lösungen oder Handlungsmöglichkeiten.",
    "A10: Konkrete Hindernisse": "Es gibt etwas sehr Konkretes, das mich in meiner Arbeit ausbremst.",
    "A11: Umsetzung stockt": "Ich möchte etwas umsetzen – doch es geht nicht richtig voran.",
    "A12: Vernachlässigte Selbstfürsorge": "Ich spüre, dass ich mich selbst zu wenig im Blick habe.",
    "A13: Klärung & Abschluss": "Ich möchte offene Themen klären und mit einem guten Gefühl abschließen."
}



# Jokerfragen zur optionalen Vertiefung
jokerfragen = [
    "Was noch?",
    "Was wäre, wenn es trotzdem klappt?",
    "Was stattdessen?",
    "Was sagt dein Bauchgefühl?"
]

# -----------------------------
# 2. EXPORTFUNKTIONEN
# -----------------------------

# Markdown-Export (Textformat, zwischenspeicherbar)
@st.cache_data
def create_markdown_export():
    md = ["# SupervisionsReflexion\n"]
    md.append(f"**Name:** {st.session_state.get('supervisand_name', '')}")
    md.append(f"**Rolle:** {st.session_state.get('supervisand_rolle', '')}")
    md.append(f"**Datum:** {st.session_state.get('supervisions_datum', '')}\n")
    for k, v in st.session_state.items():
        if k.startswith(("antwort_", "abschluss_", "antwort_anliegen_", "joker_", "reflexion_")):
            md.append(f"**{k.replace('_', ' ').capitalize()}:**\n{v}\n")
    return "\n".join(md)

# Base64-Downloadlink generieren
def generate_download_link(text, filename):
    b64 = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">📄 Antworten als Textdatei herunterladen</a>'
    return href

# -----------------------------
# 3. INTERVENTIONSFRAGEN
# -----------------------------

# Erweiterung der bestehenden Streamlit-App um die vollständigen Fragen für 13 Anliegen
# Struktur: interventionen = {Code: [(Fragetext, [Beispielantworten])]} – mit Auswahl und Freitext

interventionen = {
    "A": [
        ("Was beschäftigt Sie gerade?", [
            "Konflikte mit Kollegen/Vorgesetzten, die meine tägliche Arbeit belasten.",
            "Überforderung durch zu viele parallel laufende Aufgaben und Deadlines.",
            "Unsicherheit in meiner beruflichen Rolle und Verantwortung.",
            "Schwierigkeiten, mich abzugrenzen und Nein zu sagen.",
            "Eine anstehende wichtige Entscheidung, die ich treffen muss."
        ]),
        ("Was macht das aktuell so drängend?", [
            "Ich muss täglich mit den betreffenden Personen zusammenarbeiten.",
            "Mehrere wichtige Termine stehen gleichzeitig an.",
            "Ich soll demnächst ein wichtiges Projekt leiten.",
            "Ich merke, dass meine Energiereserven zur Neige gehen.",
            "Ich muss bis Ende der Woche eine Antwort geben."
        ]),
        ("Was wünschen Sie sich heute konkret?", [
            "Klarheit, wie ich mit der Situation umgehen soll.",
            "Einen konkreten Plan für die nächsten Schritte.",
            "Eine neue Perspektive auf mein Problem.",
            "Strategien zum besseren Umgang mit Stress.",
            "Mehr Selbstvertrauen in meiner Position."
        ]),
        ("Was würde Ihnen dabei helfen?", [
            "Die verschiedenen Handlungsoptionen durchzuspielen.",
            "Prioritäten zu setzen und konkrete Teilschritte zu definieren.",
            "Das Problem aus verschiedenen Blickwinkeln zu betrachten.",
            "Konkrete Techniken zum Stressmanagement zu erlernen.",
            "Meine Stärken besser zu erkennen und zu nutzen."
        ]),
        ("Was wäre, wenn es genauso weitergeht?", [
            "Ich würde irgendwann ausbrennen.",
            "Die Situation würde eskalieren und das Arbeitsklima verschlechtern.",
            "Ich bliebe unzufrieden und könnte mein Potenzial nicht entfalten.",
            "Die Qualität meiner Arbeit würde leiden.",
            "Ich würde diese Chance verpassen und es später bereuen."
        ]),
        ("Was würde das für Sie bedeuten?", [
            "Dass ich meinen Job nicht mehr gut machen könnte.",
            "Dass ich jeden Tag mit Bauchschmerzen zur Arbeit gehen würde.",
            "Dass ich mich beruflich nicht weiterentwickeln kann.",
            "Dass ich meine eigenen Standards nicht mehr erfüllen kann.",
            "Dass ich mich lange mit 'Was wäre wenn'-Fragen quälen würde."
        ]),
        ("Was lief zuletzt gut?", [
            "Ein Teammeeting war besonders produktiv.",
            "Ein schwieriges Kundengespräch verlief erfolgreich.",
            "Ich habe ein Projekt termingerecht abgeschlossen.",
            "Ich konnte einmal klar 'Nein' sagen, als ich überlastet war.",
            "Meine Präsentation kam sehr gut an."
        ]),
        ("Woran haben Sie das gemerkt?", [
            "An den konkreten Beschlüssen und dem Engagement aller Beteiligten.",
            "An der positiven Rückmeldung und der gefundenen Lösung.",
            "An meiner eigenen Zufriedenheit und dem positiven Feedback.",
            "An meinem Gefühl der Erleichterung danach.",
            "An den interessierten Nachfragen und dem anerkennenden Feedback."
        ])
    ],
    "B": [
        ("Wo war Ihre Rolle zuletzt unklar?", [
            "In unserem neuen Projekt waren die Zuständigkeiten nicht klar definiert.",
            "Bei der Übergabe an meine neue Position gab es überlappende Verantwortlichkeiten.",
            "In der Zusammenarbeit mit externen Partnern war unklar, wer welche Entscheidungen treffen darf.",
            "Bei der Einarbeitung einer neuen Kollegin war die Grenze meiner Anleitung nicht definiert.",
            "In einer Krisensituation war unklar, wer die Führung übernimmt."
        ]),
        ("Wer war daran beteiligt?", [
            "Der Projektleiter und Kollegen aus anderen Abteilungen.",
            "Mein Vorgänger und mein Vorgesetzter.",
            "Die Ansprechpartner des Partners und unser Management.",
            "Die neue Kollegin und meine Vorgesetzte.",
            "Mehrere Kollegen auf derselben Hierarchieebene."
        ]),
        ("Wie würden Sie Ihre Wunschrolle beschreiben?", [
            "Mit klaren Verantwortungsbereichen ohne ständige Einmischung.",
            "Mit mehr strategischen und weniger operativen Aufgaben.",
            "Als anerkannter Experte, der bei Entscheidungen einbezogen wird.",
            "Mit einer ausgewogenen Balance zwischen Führungsaufgaben und Facharbeit.",
            "In einer koordinierenden Funktion ohne direkte Personalverantwortung."
        ]),
        ("Was würde sich dadurch verändern?", [
            "Ich könnte selbständiger und effizienter arbeiten.",
            "Ich könnte meine Stärken in der Konzeptarbeit besser einsetzen.",
            "Ich würde mehr Wertschätzung erfahren und motivierter sein.",
            "Ich hätte mehr Abwechslung und breitere Entwicklungsmöglichkeiten.",
            "Ich könnte mein Kommunikationstalent einsetzen, ohne den Druck der Personalführung."
        ]),
        ("Was befürchten Sie, wenn Ihre Rolle so bleibt wie sie ist?", [
            "Dass ich weiterhin für Fehler verantwortlich gemacht werde, die nicht in meinem Einflussbereich liegen.",
            "Dass ich in meiner Entwicklung stagniere.",
            "Dass ich zwischen widersprüchlichen Anforderungen zerrieben werde.",
            "Dass meine Fähigkeiten nicht gesehen und genutzt werden.",
            "Dass die Unklarheit zu weiteren Konflikten im Team führt."
        ]),
        ("Was würde das auslösen?", [
            "Frustration und Demotivation.",
            "Langeweile und das Gefühl, beruflich festzustecken.",
            "Dauerhaften Stress und Erschöpfung.",
            "Ein Gefühl der Unterforderung und Wertlosigkeit.",
            "Ein angespanntes Arbeitsklima und Vermeidungsverhalten."
        ]),
        ("Wann war Ihre Rolle schon einmal stimmig?", [
            "Bei meinem letzten Projekt mit klar definierten Verantwortungsbereichen.",
            "In meiner vorherigen Position, wo ich meine Fachexpertise optimal einbringen konnte.",
            "Während der Vertretung einer Kollegin konnte ich meine Fähigkeiten voll einsetzen.",
            "Als mir die Leitung eines kleinen Teams übertragen wurde.",
            "Bei der Einführung eines neuen Systems war ich der zentrale Ansprechpartner."
        ]),
        ("Was hat das ermöglicht?", [
            "Eine gute Vorbereitung und klare Kommunikation vom Projektleiter.",
            "Ein Chef, der meine Stärken erkannt und gefördert hat.",
            "Das Vertrauen, das man mir entgegengebracht hat.",
            "Meine Initiative und der Mut meines Vorgesetzten, mir etwas zuzutrauen.",
            "Meine Vorbereitung und die klare Kommunikation meiner Rolle an alle Beteiligten."
        ])
    ],
  
    "C": [
        ("Welche Erwartung enttäuscht Sie immer wieder?", [
            "Die Erwartung, dass meine Arbeit angemessen gewürdigt wird.",
            "Die Erwartung, dass Absprachen eingehalten werden.",
            "Die Erwartung, dass Kollegen eigenverantwortlich arbeiten.",
            "Die Erwartung, dass ich alle zufriedenstellen kann.",
            "Die Erwartung, dass Entscheidungen auf sachlicher Basis getroffen werden."
        ]),
        ("Was macht sie so belastend?", [
            "Das Gefühl, dass meine Anstrengungen nicht gesehen werden.",
            "Dass ich mich darauf verlasse und dann meine Planung anpassen muss.",
            "Dass ich oft hinterher arbeiten und kontrollieren muss.",
            "Dass es unmöglich zu erfüllen ist und ich mich ständig unzulänglich fühle.",
            "Dass ich mich gut vorbereite und dann erlebe, dass andere Faktoren wichtiger sind."
        ]),
        ("Welche Erwartungen möchten Sie an sich stellen?", [
            "Professionell und qualitativ hochwertig arbeiten, ohne perfektionistisch zu sein.",
            "Klar kommunizieren und Grenzen setzen, wenn nötig.",
            "Meine Fachkompetenz kontinuierlich erweitern.",
            "Verlässlich sein und Zusagen einhalten.",
            "Meine Arbeitszeit effektiv nutzen, ohne mich zu überfordern."
        ]),
        ("Welche fühlen sich stimmig an?", [
            "Die realistische und gesunde Balance zwischen Qualität und Machbarkeit.",
            "Die authentische Kommunikation meiner Bedürfnisse und Grenzen.",
            "Die Weiterentwicklung meiner Fähigkeiten aus Neugier und eigenem Anspruch.",
            "Die Verlässlichkeit, die meinen Werten entspricht und Vertrauen schafft.",
            "Die Verbindung von Leistung und Selbstfürsorge."
        ]),
        ("Was passiert, wenn Sie diesen Erwartungen nicht gerecht werden?", [
            "Ich würde mich selbst stark kritisieren und mein Selbstwertgefühl würde leiden.",
            "Die Qualität meiner Arbeit könnte sinken.",
            "Ich könnte wichtige Fristen verpassen.",
            "Ich würde innerlich unzufrieden und unruhig werden.",
            "Es könnten Konflikte entstehen, wenn ich Erwartungen nicht kläre."
        ]),
        ("Wer würde das merken?", [
            "Ich selbst als Erste, aber wahrscheinlich auch meine engsten Kollegen.",
            "Meine Vorgesetzten und Kunden.",
            "Das ganze Team, da es den Projektablauf stören würde.",
            "Zunächst ich selbst, langfristig aber auch mein privates Umfeld.",
            "Die betroffenen Kollegen oder Kunden, mit denen Missverständnisse entstehen."
        ]),
        ("Welche Erwartungen wurden schon einmal erfüllt?", [
            "Meine Erwartung, ein herausforderndes Projekt erfolgreich abzuschließen.",
            "Meine Erwartung, in meinem Team respektiert zu werden.",
            "Meine Erwartung, eine ausgewogene Work-Life-Balance zu erreichen.",
            "Meine Erwartung, beruflich aufzusteigen.",
            "Meine Erwartung, eine konstruktive Feedback-Kultur zu etablieren."
        ]),
        ("Was war dafür entscheidend?", [
            "Meine gute Vorbereitung und die klare Kommunikation mit allen Beteiligten.",
            "Dass ich konsequent authentisch blieb und meine Expertise eingebracht habe.",
            "Dass ich klare Grenzen gesetzt und kommuniziert habe.",
            "Dass ich kontinuierlich an meinen Fähigkeiten gearbeitet und Initiative gezeigt habe.",
            "Dass ich selbst mit gutem Beispiel vorangegangen bin und Offenheit vorgelebt habe."
        ])
    ],
    "D": [
        ("Wann waren Sie mit sich unzufrieden?", [
            "Als ich in einer Besprechung nicht klar Position bezogen habe.",
            "Als ich ein Projekt nicht termingerecht abschließen konnte.",
            "Als ich einen Konflikt vermieden habe, statt ihn anzusprechen.",
            "Als ich eine Aufgabe übernommen habe, obwohl ich bereits überlastet war.",
            "Als ich in einer fachlichen Diskussion nicht überzeugen konnte."
        ]),
        ("Was hat diese Sicht geprägt?", [
            "Mein Ideal von Mut und Authentizität.",
            "Mein hoher Anspruch an Zuverlässigkeit.",
            "Frühere Erfahrungen, wo Vermeidung zu größeren Problemen führte.",
            "Mein Selbstbild als hilfsbereiter Mensch.",
            "Mein Selbstverständnis als Experte."
        ]),
        ("Wie möchten Sie als Fachkraft wahrgenommen werden?", [
            "Als kompetent und lösungsorientiert.",
            "Als vertrauenswürdig und verlässlich.",
            "Als innovativ und kreativ.",
            "Als teamorientiert und kooperativ.",
            "Als selbstbewusst und durchsetzungsstark."
        ]),
        ("Was verkörpert das für Sie?", [
            "Professionalität und Effizienz in meiner Arbeit.",
            "Integrität und Beständigkeit.",
            "Fortschritt und die Fähigkeit, über den Tellerrand zu schauen.",
            "Die Überzeugung, dass wir gemeinsam mehr erreichen können.",
            "Klarheit und die Fähigkeit, für meine Überzeugungen einzustehen."
        ]),
        ("Was wäre Ihre größte Sorge in Bezug auf Ihr Selbstbild?", [
            "Als inkompetent wahrgenommen zu werden.",
            "Als egoistisch oder rücksichtslos zu gelten.",
            "Als schwach oder verletzlich gesehen zu werden.",
            "Als Mitläufer ohne eigene Meinung zu gelten.",
            "Als unzuverlässig angesehen zu werden."
        ]),
        ("Wovor schützt es Sie?", [
            "Vor Versagensängsten und Selbstzweifeln.",
            "Vor sozialer Ablehnung.",
            "Vor dem Gefühl der Hilflosigkeit.",
            "Vor dem Gefühl der Bedeutungslosigkeit.",
            "Vor dem Gefühl, andere zu enttäuschen."
        ]),
        ("Wann haben Sie sich stimmig erlebt?", [
            "Als ich ein schwieriges Feedbackgespräch geführt habe.",
            "Als ich in einer Teamsituation meine Meinung vertreten habe.",
            "Als ich ein komplexes Problem gelöst habe.",
            "Als ich einem Kollegen in einer schwierigen Situation geholfen habe.",
            "Als ich eine Entscheidung getroffen habe, die meinen Werten entspricht."
        ]),
        ("Was war Ihre Haltung dabei?", [
            "Offen, wertschätzend und gleichzeitig klar.",
            "Selbstbewusst, aber auch kompromissbereit.",
            "Konzentriert, methodisch und lösungsorientiert.",
            "Empathisch und unterstützend.",
            "Authentisch und prinzipientreu."
        ])
    ],
    "E": [
        ("Welche Ressource nutzen Sie zu wenig?", [
            "Mein berufliches Netzwerk.",
            "Meine Fähigkeit zur klaren Kommunikation.",
            "Meine kreativen Fähigkeiten.",
            "Meine Delegationsfähigkeit.",
            "Meine Reflexionsfähigkeit."
        ]),
        ("Was hindert Sie daran?", [
            "Die Sorge, andere zu belästigen oder als inkompetent zu erscheinen.",
            "Die Angst vor Konflikten oder negativen Reaktionen.",
            "Der Zeitdruck und die Routine des Alltags.",
            "Der Gedanke, dass es schneller geht, wenn ich es selbst mache.",
            "Der ständige Aktionismus und die fehlende Zeit für Pausen."
        ]),
        ("Welche Stärke möchten Sie künftig gezielter einsetzen?", [
            "Meine analytischen Fähigkeiten.",
            "Meine Kommunikationsstärke.",
            "Meine Organisationsfähigkeit.",
            "Meine Empathie.",
            "Meine Kreativität."
        ]),
        ("In welchem Bereich zuerst?", [
            "Bei der strategischen Projektplanung.",
            "In schwierigen Kundengesprächen und Verhandlungen.",
            "Bei der Strukturierung meines eigenen Arbeitsalltags.",
            "In meiner Rolle als Teamleiter bei Mitarbeitergesprächen.",
            "Bei der Entwicklung neuer Lösungsansätze für wiederkehrende Probleme."
        ]),
        ("Was wäre, wenn diese Ressource ausfällt?", [
            "Wenn meine Belastbarkeit nachlässt, würde ich schneller an meine Grenzen kommen.",
            "Wenn mein fachliches Wissen nicht mehr ausreicht, würde ich unsicherer werden.",
            "Wenn meine Kommunikationsfähigkeit eingeschränkt wäre, würden mehr Missverständnisse entstehen.",
            "Wenn mein Netzwerk wegfallen würde, wäre ich isolierter in meiner Arbeit.",
            "Wenn meine Kreativität blockiert wäre, würde ich in Routinen verharren."
        ]),
        ("Wie würden Sie damit umgehen?", [
            "Ich würde versuchen, mehr Pausen einzuplanen und Prioritäten noch klarer zu setzen.",
            "Ich würde gezielt Weiterbildungen suchen und Experten um Rat fragen.",
            "Ich würde mehr schriftlich arbeiten und um Feedback bitten.",
            "Ich würde aktiv neue Kontakte aufbauen und andere Informationsquellen erschließen.",
            "Ich würde methodischer vorgehen und bewährte Lösungswege nutzen."
        ]),
        ("Welche Fähigkeit hat Ihnen zuletzt geholfen?", [
            "Meine Fähigkeit, in Stresssituationen ruhig zu bleiben.",
            "Meine Strukturierungsfähigkeit.",
            "Meine Kommunikationsstärke.",
            "Meine Hartnäckigkeit.",
            "Meine Reflexionsfähigkeit."
        ]),
        ("Wie kam sie zum Einsatz?", [
            "Als ein wichtiger Kunde kurzfristig sein Konzept änderte und wir schnell reagieren mussten.",
            "Als wir ein komplexes Projekt in überschaubare Arbeitspakete aufteilen mussten.",
            "Als ich zwischen zwei Abteilungen mit unterschiedlichen Interessen vermitteln musste.",
            "Als ein technisches Problem auftrat, das nicht auf Anhieb lösbar schien.",
            "Als ich nach einem Konflikt das Gespräch analysierte und daraus lernte."
        ])
    ],
    "F": [
        ("Was ist damals nicht gelungen?", [
            "Die Implementierung des neuen Systems lief nicht wie geplant.",
            "Wir haben einen wichtigen Kunden verloren.",
            "Die Teambildung ist gescheitert.",
            "Das Projekt hat die Deadline nicht eingehalten.",
            "Die Präsentation hat nicht überzeugt."
        ]),
        ("Woran lag es aus Ihrer Sicht?", [
            "An unzureichender Vorbereitung und mangelnder Einbindung aller Beteiligten.",
            "Daran, dass wir die wirklichen Bedürfnisse nicht ausreichend erfasst haben.",
            "An unklaren Rollen und unterschiedlichen Erwartungen, die nicht thematisiert wurden.",
            "An zu optimistischer Planung und fehlenden Puffern für unvorhergesehene Ereignisse.",
            "Daran, dass ich mich zu sehr auf Fakten konzentriert und die emotionale Ebene vernachlässigt habe."
        ]),
        ("Was müsste passieren, damit Sie wieder Erfolg erleben?", [
            "Ich müsste mehr Verantwortung für strategische Entscheidungen bekommen.",
            "Ich müsste meine Ideen erfolgreicher umsetzen können.",
            "Ich müsste mehr Zeit für qualitativ hochwertige Arbeit haben.",
            "Ich müsste mehr Rückhalt im Team erfahren.",
            "Ich müsste selbstbewusster auftreten können."
        ]),
        ("Wer würde das erkennen?", [
            "Mein Vorgesetzter und meine Kollegen würden merken, dass ich motivierter und engagierter bin.",
            "Die Kunden und mein Team würden die besseren Ergebnisse sehen.",
            "Meine Fachkollegen würden den Unterschied in der Qualität meiner Arbeit erkennen.",
            "Die Teammitglieder würden die positivere Atmosphäre spüren.",
            "Meine Gesprächspartner würden meine gesteigerte Überzeugungskraft wahrnehmen."
        ]),
        ("Was wäre, wenn es trotz aller Anstrengung nicht gelingt?", [
            "Ich müsste akzeptieren, dass manche Dinge außerhalb meiner Kontrolle liegen.",
            "Ich müsste einen alternativen Weg finden oder das Ziel anpassen.",
            "Ich müsste mir eingestehen, dass vielleicht die Rahmenbedingungen nicht stimmen.",
            "Ich müsste mir mehr Unterstützung holen.",
            "Ich müsste meine Strategie grundlegend überdenken."
        ]),
        ("Was würde das für Sie bedeuten?", [
            "Dass ich lernen muss, meine Erwartungen anzupassen und resilienter zu werden.",
            "Dass ich flexibler werden und verschiedene Optionen offen halten muss.",
            "Dass ich über einen Positions- oder Jobwechsel nachdenken sollte.",
            "Dass ich mein Netzwerk aktivieren und eingestehen muss, nicht alles alleine schaffen zu können.",
            "Dass ich offen für Lernprozesse bleiben und mich weiterentwickeln muss."
        ]),
        ("Wann haben Sie eine ähnliche Situation gemeistert?", [
            "Bei einem früheren Projekt mit ähnlichen Herausforderungen.",
            "In meiner vorherigen Position hatte ich einen vergleichbaren Konflikt.",
            "Beim Aufbau eines neuen Teams gab es ähnliche Anlaufschwierigkeiten.",
            "Bei der Einführung einer neuen Software hatten wir ähnliche Widerstände.",
            "Bei einem wichtigen Kundenprojekt standen wir unter ähnlichem Zeitdruck."
        ]),
        ("Was war Ihr Beitrag dazu?", [
            "Frühzeitig alle Stakeholder einzubinden und transparent zu kommunizieren.",
            "Aktiv das Gespräch zu suchen und eine gemeinsame Lösung zu erarbeiten.",
            "Klare Strukturen zu schaffen und regelmäßigen Austausch zu fördern.",
            "Geduldige Schulungen anzubieten und die Vorteile konkret aufzuzeigen.",
            "Prioritäten zu setzen und das Team zu motivieren."
        ])
    ],
    "G": [
        ("Wann hat Unterstützung gefehlt?", [
            "Bei der Übernahme neuer Aufgaben fehlte eine strukturierte Einarbeitung.",
            "In einer Konfliktsituation mit einem Kollegen fehlte die Unterstützung meines Vorgesetzten.",
            "Bei einem komplexen Projekt fehlte fachliche Beratung.",
            "Bei hoher Arbeitsbelastung fehlte Entlastung durch das Team.",
            "Bei einer wichtigen Entscheidung fehlten klare Vorgaben."
        ]),
        ("Was hat das erschwert?", [
            "Dass ich viel Zeit mit Trial-and-Error verbringen musste.",
            "Dass der Konflikt lange schwelte und die Zusammenarbeit belastete.",
            "Dass ich unsicher war und mehr Zeit für Recherche aufwenden musste.",
            "Dass ich an meine Grenzen kam und die Qualität meiner Arbeit litt.",
            "Dass ich lange zögerte und Angst hatte, etwas falsch zu machen."
        ]),
        ("Wer oder was könnte Sie jetzt unterstützen?", [
            "Ein Mentor mit Erfahrung auf diesem Gebiet.",
            "Mehr Austausch im Team.",
            "Eine Weiterbildung zu diesem Thema.",
            "Ein klareres Mandat von meinem Vorgesetzten.",
            "Technische Tools zur besseren Organisation."
        ]),
        ("Wie würden Sie das anstoßen?", [
            "Gezielt nach einer Person suchen und sie direkt um Rat fragen.",
            "Regelmäßige Kurzmeetings für Feedback und Ideen vorschlagen.",
            "Konkrete Angebote recherchieren und mit meinem Vorgesetzten besprechen.",
            "Ein Gespräch vereinbaren, um meine Rolle und Befugnisse zu klären.",
            "Mich informieren und einen Vorschlag zur Einführung machen."
        ]),
        ("Was, wenn keine Unterstützung kommt?", [
            "Ich würde selbständig Prioritäten setzen und kommunizieren, was realistisch machbar ist.",
            "Ich würde versuchen, die Situation aus eigener Kraft zu meistern.",
            "Ich würde die Anforderungen neu verhandeln.",
            "Ich würde mich auf meine Kernaufgaben konzentrieren.",
            "Ich würde mein informelles Netzwerk aktivieren."
        ]),
        ("Was wäre Ihr Plan B?", [
            "Klare Grenzen zu ziehen und Nein zu sagen, wenn nötig.",
            "Mir externe Unterstützung zu suchen, z.B. durch Coaching oder Beratung.",
            "Alternative Lösungswege vorzuschlagen, die mit den vorhandenen Ressourcen umsetzbar sind.",
            "Nicht-essentielle Aufgaben zurückzustellen und dies transparent zu kommunizieren.",
            "Durch Austausch mit Kollegen aus anderen Bereichen neue Impulse zu bekommen."
        ]),
        ("Wer war Ihnen schon einmal eine Hilfe?", [
            "Mein früherer Teamleiter.",
            "Eine erfahrene Kollegin.",
            "Mein Mentor aus dem Netzwerkprogramm.",
            "Ein externer Coach.",
            "Mein Partner/meine Partnerin."
        ]),
        ("Was hat diese Person getan?", [
            "Mir regelmäßig konstruktives Feedback gegeben und mir zugleich vertraut.",
            "Ihr Wissen geteilt und mir bei komplexen Fragen zur Seite gestanden.",
            "Mir seine Erfahrungen mitgeteilt und mich ermutigt, neue Wege zu gehen.",
            "Mir durch gezielte Fragen geholfen, selbst Lösungen zu finden.",
            "Mir zugehört, mich emotional unterstützt und mir einen anderen Blickwinkel gegeben."
        ])
    ],
    "H": [
        ("Wann war Ihre innere Balance gestört?", [
            "Als mehrere Projekte gleichzeitig in die heiße Phase kamen.",
            "Nach einem Konflikt mit meinem Vorgesetzten.",
            "Während einer längeren Phase der Überlastung.",
            "Als ich zwischen beruflichen und familiären Anforderungen zerrissen war.",
            "Als ich meine Werte in der Arbeit nicht leben konnte."
        ]),
        ("Was hat das ausgelöst?", [
            "Die unzureichende Planung und fehlende Kommunikation zwischen den Abteilungen.",
            "Sein kritisches Feedback, das ich als ungerecht empfand.",
            "Meine Schwierigkeit, Nein zu sagen und Aufgaben zu delegieren.",
            "Ein familiärer Notfall bei gleichzeitig hohem Termindruck.",
            "Eine Unternehmensentscheidung, die ich ethisch bedenklich fand."
        ]),
        ("Was bringt Sie wieder in Ihre Mitte?", [
            "Sport und Bewegung.",
            "Gespräche mit vertrauten Menschen.",
            "Meditation und Achtsamkeitsübungen.",
            "Zeit in der Natur.",
            "Kreative Tätigkeiten."
        ]),
        ("Wie könnten Sie das öfter nutzen?", [
            "Indem ich feste Zeiten dafür einplane und sie wie wichtige Termine behandle.",
            "Indem ich regelmäßige Treffen oder Telefonate vereinbare.",
            "Indem ich kurze Übungen in meinen Arbeitsalltag integriere.",
            "Indem ich Meetings als Spaziergänge gestalte oder meine Mittagspause draußen verbringe.",
            "Indem ich mir bewusst Zeit dafür reserviere, auch wenn es nur kurze Momente sind."
        ]),
        ("Was würde passieren, wenn Sie aus dem Gleichgewicht geraten?", [
            "Ich würde unkonzentriert und fehleranfällig werden.",
            "Ich würde gereizt reagieren und Konflikte provozieren.",
            "Ich würde wichtige Aufgaben aufschieben und in Passivität verfallen.",
            "Meine Gesundheit würde leiden, mit Schlafproblemen und körperlichen Symptomen.",
            "Ich würde mich zurückziehen und isolieren."
        ]),
        ("Wie könnten Sie sich schützen?", [
            "Indem ich frühe Warnsignale ernstnehme und sofort gegensteuere.",
            "Indem ich in angespannten Momenten eine Pause einlege, bevor ich reagiere.",
            "Indem ich meine Aufgaben in kleine, überschaubare Schritte aufteile.",
            "Indem ich regelmäßige Gesundheits-Checks einplane und auf meinen Körper höre.",
            "Indem ich auch in stressigen Phasen den Kontakt zu unterstützenden Menschen pflege."
        ]),
        ("Wann waren Sie zuletzt innerlich stabil?", [
            "Während meines letzten Urlaubs.",
            "Nach Abschluss eines erfolgreichen Projekts.",
            "Als ich einen klaren Fahrplan für ein komplexes Vorhaben hatte.",
            "Als ich regelmäßig Sport gemacht habe.",
            "Als ich mich in einem unterstützenden Team gut aufgehoben fühlte."
        ]),
        ("Was hat dazu beigetragen?", [
            "Die räumliche Distanz zum Arbeitsalltag und die Zeit für mich selbst.",
            "Das Gefühl der Selbstwirksamkeit und die Anerkennung meiner Leistung.",
            "Die Struktur und Klarheit, die mir Sicherheit gab.",
            "Die körperliche Aktivität und die Zeit für mich.",
            "Das Gefühl von Zugehörigkeit und gegenseitiger Wertschätzung."
        ])
    ],
    "I": [
        ("Welche Optionen haben sich als Sackgasse erwiesen?", [
            "Der Versuch, es allen recht zu machen.",
            "Probleme auszusitzen und zu hoffen, dass sie sich von selbst lösen.",
            "Der Versuch, alles allein zu stemmen.",
            "Die Konzentration nur auf kurzfristige Erfolge.",
            "Der Versuch, durch noch mehr Arbeit alle Probleme zu lösen."
        ]),
        ("Warum?", [
            "Weil es unmöglich ist und zu Selbstaufgabe führt.",
            "Weil Probleme meist größer werden und dann schwerer zu bewältigen sind.",
            "Weil meine Ressourcen begrenzt sind und ich an meine Grenzen stoße.",
            "Weil langfristige Probleme dadurch oft verschärft werden.",
            "Weil die Quantität der Arbeit nicht automatisch zu besserer Qualität oder Lösungen führt."
        ]),
        ("Welche Möglichkeit reizt Sie heute besonders?", [
            "Ein interdisziplinäres Projekt zu leiten.",
            "Neue Kommunikationsstrukturen im Team zu etablieren.",
            "Meine Expertise durch eine Weiterbildung zu vertiefen.",
            "Mehr Verantwortung in strategischen Entscheidungen zu übernehmen.",
            "Flexibler zu arbeiten und mehr Homeoffice zu nutzen."
        ]),
        ("Was wäre Ihr erster Schritt?", [
            "Mit meinem Vorgesetzten darüber zu sprechen und mein Interesse zu signalisieren.",
            "Die aktuellen Schwachstellen zu analysieren und Verbesserungsvorschläge zu erarbeiten.",
            "Passende Angebote zu recherchieren und meinen Lernbedarf konkret zu definieren.",
            "Mich in relevante Diskussionen einzubringen und fundierte Vorschläge zu machen.",
            "Ein Konzept zu erstellen, wie ich meine Aufgaben ortsunabhängig gut erfüllen kann."
        ]),
        ("Was hindert Sie, diesen Weg zu gehen?", [
            "Die Unsicherheit, ob ich den Anforderungen gewachsen bin.",
            "Die Befürchtung, dass andere meine Initiative als Kritik auffassen könnten.",
            "Der Zeitmangel, neben dem Tagesgeschäft noch etwas Neues anzugehen.",
            "Das fehlende Mandat von oben.",
            "Die Sorge vor finanziellen Einbußen oder zusätzlichen Kosten."
        ]),
        ("Was wäre das Risiko?", [
            "Zu scheitern und damit mein Ansehen zu beschädigen.",
            "Widerstände zu erzeugen und die Zusammenarbeit zu belasten.",
            "Dass ich mich übernehme und beides nicht gut mache.",
            "Dass mein Engagement ins Leere läuft oder als Überschreitung meiner Kompetenzen gesehen wird.",
            "Dass sich die Investition nicht auszahlt."
        ]),
        ("Welche Lösungsidee hat früher funktioniert?", [
            "Ein Pilotprojekt zu starten, bevor wir es im großen Maßstab umsetzen.",
            "Externe Expertise hinzuzuziehen.",
            "Durch offene Kommunikation Transparenz zu schaffen.",
            "Einen strukturierten Prozess einzuführen.",
            "Das Problem zu priorisieren und andere Aufgaben zurückzustellen."
        ]),
        ("In welcher Situation?", [
            "Als wir ein neues Verfahren einführen wollten und unsicher waren, wie es angenommen wird.",
            "Als wir mit unserem internen Wissen nicht weiterkamen und frische Impulse brauchten.",
            "Als Gerüchte und Unsicherheit die Stimmung belasteten.",
            "Als die Abläufe chaotisch waren und zu Fehlern führten.",
            "Als wir unter Zeitdruck standen und fokussiert arbeiten mussten."
        ])
    ],
    "J": [
        ("Was steht Ihnen aktuell im Weg?", [
            "Die unklare Entscheidungsstruktur im Unternehmen.",
            "Mein eigener Perfektionismus.",
            "Der Informationsmangel.",
            "Der fehlende Teamgeist in der Abteilung.",
            "Die mangelnde technische Ausstattung."
        ]),
        ("Wie zeigt sich das?", [
            "Projekte stocken oft, weil niemand die Verantwortung übernimmt.",
            "Ich wende zu viel Zeit für Details auf und gerate dadurch unter Zeitdruck.",
            "Ich muss ständig nachfragen und Entscheidungen auf unzureichender Grundlage treffen.",
            "Es gibt wenig Unterstützung und viel Einzelkämpfertum.",
            "Durch langsame Prozesse und häufige Systemausfälle."
        ]),
        ("Was wäre ein machbarer Umgang mit dem Hindernis?", [
            "Selbst mehr Initiative ergreifen und Entscheidungen vorbereiten.",
            "Bewusst Prioritäten setzen und 'gut genug' akzeptieren.",
            "Proaktiv Informationen einholen und Netzwerke aufbauen.",
            "Teambuilding-Aktivitäten anstoßen und selbst kooperatives Verhalten vorleben.",
            "Alternative Arbeitsmethoden entwickeln, die weniger technikabhängig sind."
        ]),
        ("Welche Unterstützung wäre hilfreich?", [
            "Die Unterstützung meines Vorgesetzten, der mir den Rücken stärkt.",
            "Ein Feedback-System, das mir bestätigt, wann etwas ausreichend bearbeitet ist.",
            "Ein verbessertes Informationsmanagement im Unternehmen.",
            "Die Unterstützung der Führungsebene für solche Initiativen.",
            "Ein Budget für notwendige technische Erneuerungen."
        ]),
        ("Was passiert, wenn das Hindernis bestehen bleibt?", [
            "Wir werden weiterhin ineffizient arbeiten.",
            "Ich werde weiterhin unter Stress und Zeitdruck leiden.",
            "Konflikte im Team werden zunehmen.",
            "Wir können die Qualitätsstandards nicht halten.",
            "Innovationen werden ausgebremst."
        ]),
        ("Welche Folgen hätte das?", [
            "Wir fallen im Wettbewerb zurück und verlieren Marktanteile.",
            "Meine Gesundheit und Motivation leiden dauerhaft.",
            "Eine schlechtere Arbeitsatmosphäre und eventuell höhere Fluktuation.",
            "Unzufriedenheit bei Kunden und möglicherweise Reputationsschäden.",
            "Stagnation und fehlende Weiterentwicklung des Unternehmens."
        ]),
        ("Welches Hindernis haben Sie bereits bewältigt?", [
            "Das Hindernis der fehlenden Anerkennung.",
            "Das Hindernis der unzureichenden Kommunikation.",
            "Das Hindernis der Wissensdefizite.",
            "Das Hindernis der Prokrastination.",
            "Das Hindernis eines schwierigen Teammitglieds."
        ]),
        ("Wie?", [
            "Indem ich aktiv Feedback eingefordert und meine Erfolge sichtbarer gemacht habe.",
            "Durch regelmäßige Team-Meetings und die Förderung einer offenen Feedback-Kultur.",
            "Durch gezielte Weiterbildung und den Aufbau eines Experten-Netzwerks.",
            "Mit der Pomodoro-Technik und klaren Tageszielen.",
            "Durch offene Gespräche und klare Vereinbarungen."
        ])
    ],
    "K": [
        ("Wo sind Sie in der Umsetzung gescheitert?", [
            "Bei der Einführung eines neuen Dokumentationssystems.",
            "Bei meinem Zeitmanagement-Vorhaben.",
            "Bei einer Prozessoptimierung.",
            "Bei meinem Delegationsvorhaben.",
            "Bei der Umsetzung einer Kommunikationsstrategie."
        ]),
        ("Was war der Knackpunkt?", [
            "Dass ich nicht alle Nutzer rechtzeitig eingebunden und geschult habe.",
            "Dass ich zu viele Änderungen auf einmal versucht habe.",
            "Der Widerstand einiger Schlüsselpersonen, die den Wert der Änderung nicht erkannt haben.",
            "Meine Schwierigkeit, wirklich loszulassen und zu vertrauen.",
            "Dass ich die unterschiedlichen Bedürfnisse der Zielgruppen nicht ausreichend berücksichtigt habe."
        ]),
        ("Was möchten Sie als Nächstes umsetzen?", [
            "Eine strukturiertere Meetingkultur.",
            "Ein Feedbacksystem in meinem Team.",
            "Eine bessere Work-Life-Balance.",
            "Ein neues Projektmanagement-Tool.",
            "Einen coachenden Führungsstil."
        ]),
        ("Was wäre ein realistischer erster Schritt?", [
            "Eine Agenda-Vorlage entwickeln und für das nächste Meeting nutzen.",
            "Im nächsten Teammeeting das Thema ansprechen und Ideen sammeln.",
            "Feste Zeiten für den Feierabend definieren und einhalten.",
            "Eine kleine Pilotgruppe bilden und das Tool für ein überschaubares Projekt testen.",
            "Mir Feedback von meinen Mitarbeitern einholen."
        ]),
        ("Was könnte die Umsetzung gefährden?", [
            "Zeitmangel.",
            "Widerstand im Team.",
            "Mangelnde Unterstützung von oben.",
            "Überforderung durch zu ambitionierte Ziele.",
            "Technische Probleme."
        ]),
        ("Wie könnten Sie vorbeugen?", [
            "Indem ich feste Zeitfenster für die Umsetzung blockiere und diese wie wichtige Termine behandle.",
            "Indem ich frühzeitig alle einbeziehe, den Nutzen klar kommuniziere und Bedenken ernst nehme.",
            "Indem ich meinen Vorgesetzten von Anfang an einbinde und den Mehrwert herausstelle.",
            "Indem ich realistische Teilziele definiere und Erfolge sichtbar mache.",
            "Indem ich vorab Tests durchführe und einen Plan B für den Notfall habe."
        ]),
        ("Wann haben Sie etwas erfolgreich umgesetzt?", [
            "Die Einführung eines neuen Berichtswesens.",
            "Ein schwieriges Konfliktgespräch.",
            "Die Führung eines Teams in einer Veränderungsphase.",
            "Ein komplexes Kundenprojekt.",
            "Neue Abläufe in meinem Arbeitsalltag."
        ]),
        ("Was hat das möglich gemacht?", [
            "Meine gründliche Vorbereitung und die frühzeitige Einbindung aller Beteiligten.",
            "Meine Vorbereitung, klare Kommunikation und die Bereitschaft, die andere Perspektive zu verstehen.",
            "Meine transparente Kommunikation und das Schaffen von frühen Erfolgserlebnissen.",
            "Meine strukturierte Herangehensweise und die gute Teamarbeit.",
            "Meine Konsequenz und die spürbaren positiven Effekte."
        ])
    ],
    "L": [
    ("Wann haben Sie sich selbst vernachlässigt?", [
        "Als ich wochenlang Überstunden gemacht habe.",
        "Als ich trotz Krankheit zur Arbeit gegangen bin.",
        "Als ich ständig für alle erreichbar war, auch im Urlaub.",
        "Als ich Konflikte nicht angesprochen habe, um Harmonie zu wahren.",
        "Als ich meine Hobbys und sozialen Kontakte eingeschränkt habe."
    ]),
    ("Was hat Sie davon abgehalten?", [
        "Der Gedanke, dass das Projekt sonst scheitern könnte und ich das Team im Stich lassen würde.",
        "Die Vorstellung, dass wichtige Entscheidungen anstanden und niemand mich vertreten konnte.",
        "Die Sorge, etwas Wichtiges zu verpassen oder nicht als engagiert zu gelten.",
        "Die Angst vor negativen Reaktionen und Ablehnung.",
        "Der Gedanke, dass die Arbeit momentan Vorrang haben muss."
    ]),
    ("Was brauchen Sie für gute Selbstfürsorge?", [
        "Regelmäßige Pausen im Arbeitsalltag und bewusste Erholung.",
        "Klare Grenzen zwischen Arbeit und Privatleben.",
        "Zeit für Bewegung und Sport.",
        "Regelmäßige Reflexionszeiten.",
        "Bewusste Momente der Selbstwertschätzung."
    ]),
    ("Was davon ist heute umsetzbar?", [
        "Eine echte Mittagspause machen und einen Spaziergang einplanen.",
        "Eine feste Feierabendzeit festlegen und keine E-Mails mehr danach checken.",
        "Einen Termin für eine Sporteinheit in den Kalender eintragen und als nicht verschiebbar markieren.",
        "15 Minuten am Ende des Tages für ein kurzes Journal reservieren.",
        "Mir am Ende des Tages drei Dinge notieren, die gut gelaufen sind."
    ]),
    ("Was wäre, wenn Sie keine Zeit für sich finden?", [
        "Ich würde erschöpfter und gereizter werden.",
        "Ich würde mich zunehmend unwohl und gestresst fühlen.",
        "Ich würde weniger kreativ und lösungsorientiert arbeiten können.",
        "Ich würde mich von Kollegen und Familie distanzieren.",
        "Ich würde meine eigenen Bedürfnisse nicht mehr wahrnehmen."
    ]),
    ("Was würde langfristig passieren?", [
        "Das könnte zu Burnout-Symptomen, gesundheitlichen Problemen und einem Leistungsabfall führen.",
        "Meine Arbeitszufriedenheit und Motivation würden stark beeinträchtigt werden.",
        "Das würde zu Routinedenken und beruflicher Stagnation führen.",
        "Es könnte zu sozialer Isolation und Einsamkeit führen.",
        "Ich könnte meine Identität und meine Werte aus den Augen verlieren."
    ]),
    ("Was hat Ihnen in stressigen Phasen geholfen?", [
        "Morgens früher aufzustehen und zu meditieren.",
        "Regelmäßige Gespräche mit vertrauten Menschen.",
        "Kurze Pausen und Raumwechsel während der Arbeit.",
        "Am Wochenende komplett abzuschalten und die Natur zu genießen.",
        "Jeden Tag eine Sache zu tun, die mir Freude bereitet."
    ]),
    ("Was haben Sie bewusst dafür getan?", [
        "Den Wecker gestellt und die Meditation fest in meinen Tagesablauf integriert.",
        "Feste Telefontermine vereinbart, die ich auch in stressigen Zeiten eingehalten habe.",
        "Einen Timer gestellt und mir erlaubt, alle 90 Minuten kurz auszusteigen.",
        "Das Handy zu Hause gelassen und bewusst Ausflüge geplant.",
        "Eine Liste mit kleinen Freuden erstellt und täglich etwas davon umgesetzt."
    ])
],
"2": [
    ("Was ist noch offen geblieben?", [
        "Wie ich mit dem Widerstand bestimmter Kollegen umgehen soll.",
        "Die Frage nach meinen langfristigen Karrierezielen.",
        "Der Umgang mit wiederkehrenden Konflikten im Team.",
        "Wie ich meine Arbeitsbelastung nachhaltig reduzieren kann.",
        "Wie ich meine Komfortzone verlassen kann."
    ]),
    ("Was möchten Sie weiter bedenken?", [
        "Welche Bedenken der Kollegen berechtigt sein könnten und wie ich darauf eingehen kann.",
        "Welche Richtung wirklich zu mir passt und was mich erfüllt.",
        "Welche Muster hinter den Konflikten stecken und wie wir sie durchbrechen können.",
        "Welche Aufgaben ich abgeben oder anders organisieren könnte.",
        "Welche konkreten Schritte mich herausfordern, aber nicht überfordern würden."
    ]),
    ("Was nehmen Sie sich konkret vor?", [
        "Klarer zu kommunizieren, wenn ich überlastet bin.",
        "Mehr Struktur in meine Arbeit zu bringen.",
        "Aktiver Feedback einzuholen.",
        "Meine Präsentationsfähigkeiten zu verbessern.",
        "Mehr auf meine Energiebilanz zu achten."
    ]),
    ("Was ist Ihr nächster kleiner Schritt?", [
        "In der nächsten Teamsitzung offen ansprechen, welche Unterstützung ich brauche.",
        "Morgen früh 30 Minuten investieren, um meine Woche zu planen.",
        "Drei Kollegen um ein kurzes Gespräch bitten, um ihre Sicht auf ein aktuelles Projekt zu erfahren.",
        "Einen Kurs recherchieren und mich anmelden.",
        "Jeden Tag nach der Arbeit eine kurze Sporteinheit einplanen."
    ]),
    ("Was könnte es schwer machen, dranzubleiben?", [
        "Der Alltagsstress und die vielen dringenden Anfragen.",
        "Meine Tendenz, in alte Gewohnheiten zurückzufallen.",
        "Der fehlende sichtbare Erfolg am Anfang.",
        "Widerstand aus dem Umfeld.",
        "Selbstzweifel und innere Kritik."
    ]),
    ("Was würde dann helfen?", [
        "Feste Zeiten für die Umsetzung meiner Vorhaben zu blockieren und diese zu respektieren.",
        "Einen Buddy zu haben, der mich regelmäßig an meine Vorhaben erinnert.",
        "Mir kleine Zwischenziele zu setzen und diese zu feiern.",
        "Im Vorfeld Unterstützer zu identifizieren und einzubinden.",
        "Mir regelmäßig meine Fortschritte bewusst zu machen und wohlwollend mit mir zu sein."
    ]),
    ("Was war heute stärkend für Sie?", [
        "Die Erkenntnis, dass ich mehr Ressourcen habe, als mir bewusst war.",
        "Die Zeit, über meine Situation nachzudenken.",
        "Die Klarheit über meine nächsten Schritte.",
        "Die Wertschätzung meiner bisherigen Erfolge.",
        "Das Gefühl, nicht allein mit meinen Herausforderungen zu sein."
    ]),
    ("Was nehmen Sie mit?", [
        "Dass ich auf meine Erfahrungen und Stärken vertrauen kann.",
        "Dass Reflexion ein wichtiger Teil der Lösung ist.",
        "Dass konkrete Handlungsschritte mir Sicherheit geben.",
        "Dass ich auch in schwierigen Situationen schon vieles gemeistert habe.",
        "Dass Austausch und Unterstützung wichtige Ressourcen sind."
    ])
]
}
# Seite einrichten
st.set_page_config(page_title="Supervision – Anliegen klären", layout="wide")
st.title("Supervision: Anliegen klären")

# Auswahl des Anliegens
kürzel = st.selectbox("Wähle ein Anliegen", list(interventionen.keys()))

st.markdown("### Deine Antworten")

# Fragen und Eingabefelder
for i, (frage, beispiele) in enumerate(interventionen[kürzel]):
    st.markdown(f"**{frage}**")
    st.text_area("Antwort", key=f"antwort_{kürzel}_{i}")
    with st.expander("Beispielantworten anzeigen"):
        for b in beispiele:
            st.markdown(f"- {b}")
      
# -----------------------------
# 4. STREAMLIT-APP-LOGIK
# -----------------------------

# Seitenleiste – Nutzer*in identifizieren
st.sidebar.header("👤 Supervisanden-Informationen")
st.sidebar.text_input("Name oder Initialen", key="supervisand_name")
st.sidebar.text_input("Funktion / Rolle", key="supervisand_rolle")
st.sidebar.date_input("Datum der Supervision", key="supervisions_datum", value=datetime.date.today())

# Phasensteuerung
if "phase" not in st.session_state:
    st.session_state.phase = "anliegen_erkunden"

# PHASE 1: Einstieg mit Intervention A
if st.session_state.phase == "anliegen_erkunden":
    st.title("🎴 SupervisionsDeck")
    st.header("🔍 Intervention A – Anliegen klären")
    st.markdown(f"_🌀 {intervention_meta['A'][1]}_")
    for i, frage in enumerate(interventionen["A"]):
        st.text_area(frage, key=f"antwort_anliegen_{i}")
    if st.button("➡️ Weiter zur Anliegenauswahl"):
        st.session_state.phase = "anliegenwahl"

# PHASE 2: Anliegenwahl
elif st.session_state.phase == "anliegenwahl":
    st.header("🧭 Anliegen wählen")
    st.markdown("_Klicke auf eine Karte, um dein Anliegen auszuwählen._")
    cols = st.columns(2)
    for i, key in enumerate(anliegen_beschreibung):
        col = cols[i % 2]
        with col:
            if st.button(f"🗂️ {key}\n\n{anliegen_beschreibung[key]}", key=f"anliegen_{key}"):
                st.session_state.auswahl = key
                st.session_state.phase = "interventionen"
    if st.button("⬅️ Zurück zu Intervention A"):
        st.session_state.phase = "anliegen_erkunden"

# PHASE 3: Ausgewählte Interventionen durchgehen
elif st.session_state.phase == "interventionen":
    st.header(f"🎯 Interventionen für: {st.session_state.auswahl}")
    codes = anliegen_interventionen.get(st.session_state.auswahl, [])
    for code in codes:
        if code in intervention_meta:
            name, impuls = intervention_meta[code]
            st.subheader(f"🧩 Intervention {code} – {name}")
            st.markdown(f"_🌀 {impuls}_")
            for i, frage in enumerate(interventionen.get(code, [])):
                st.text_area(frage, key=f"antwort_{code}_{i}")
                if st.checkbox(f"💬 Jokerfrage zu Frage {i+1} aktivieren", key=f"jokerfrage_{code}_{i}_check"):
                    st.selectbox("Jokerfrage wählen:", jokerfragen, key=f"jokerfrage_{code}_{i}_text")
                    st.text_area("Antwort auf die Jokerfrage:", key=f"jokerantwort_{code}_{i}")
    if st.button("➡️ Weiter zum Abschluss"):
        st.session_state.phase = "abschluss"
    if st.button("⬅️ Zurück zur Anliegenwahl"):
        st.session_state.phase = "anliegenwahl"

# PHASE 4: Abschlussintervention und Export
elif st.session_state.phase == "abschluss":
    st.header("🔚 Abschluss – Intervention 2")
    st.markdown(f"_🌀 {intervention_meta['2'][1]}_")
    for i, frage in enumerate(interventionen["2"]):
        st.text_area(frage, key=f"abschluss_{i}")

    # Jokerfrage zur Abschlussphase
    if st.checkbox("💬 Jokerfrage zur Abschlussintervention aktivieren"):
        st.selectbox("Jokerfrage wählen:", jokerfragen, key="jokerfrage_abschluss_text")
        st.text_area("Antwort auf die Jokerfrage:", key="jokerantwort_abschluss")

    # Markdown-Exportlink anzeigen
    markdown = create_markdown_export()
    st.markdown(generate_download_link(markdown, f"supervision_export_{datetime.date.today()}.md"), unsafe_allow_html=True)

    # PDF-Export (lokal, wenn PDFKit installiert)
    if st.button("📄 Antworten als PDF herunterladen"):
        import pdfkit
        from tempfile import NamedTemporaryFile
        html = """<html><body><h1>SupervisionsReflexion</h1>"""
        html += f"<p><strong>Name:</strong> {st.session_state.get('supervisand_name', '')}</p>"
        ...  # HTML export zusammenstellen (wie oben)
        with NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
            try:
                pdfkit.from_string(html, f.name, configuration=config)
                with open(f.name, "rb") as pdf_file:
                    b64_pdf = base64.b64encode(pdf_file.read()).decode("utf-8")
                    href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="supervision_reflexion.pdf">📄 PDF herunterladen</a>'
                    st.markdown(href, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Fehler beim Erstellen der PDF: {e}")

    # Optional: Export nach Google Sheets
    if st.button("📤 Antworten speichern in Google Sheets"):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
            client = gspread.authorize(creds)
            sheet = client.open("supervision_antworten").sheet1
            data = [[key, val] for key, val in st.session_state.items() if isinstance(val, str) and val.strip()]
            sheet.append_rows(data, value_input_option="USER_ENTERED")
            st.success("✅ Antworten wurden gespeichert!")
        except Exception as e:
            st.error(f"Fehler beim Speichern in Google Sheets: {e}")

    if st.button("⬅️ Zurück zu Interventionen"):
        st.session_state.phase = "interventionen"
