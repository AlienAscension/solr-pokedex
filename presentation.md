# Mini-Präsentation: Der Solr-Pokédex

**Zeit:** 5 Minuten

---

## 1. Was ist dieses Projekt? (1 Minute)

*   **Das Ziel:** Eine leistungsstarke Pokémon-Suchmaschine.
*   **Kerntechnologie:** Es verwendet **Apache Solr**, eine Open-Source-Unternehmenssuchplattform, für eine schnelle und flexible Suche.
*   **Benutzeroberfläche:** Eine einfache Web-App, die mit **Python (Flask)** erstellt wurde, stellt die Suchleiste und die Ergebnisanzeige bereit.
*   **Die Daten:** Alle Daten stammen von der öffentlichen **PokeAPI**.

**Kurz gesagt:** Es ist ein komplettes System, das Daten abruft, sie für die Suche indiziert und dem Benutzer eine Benutzeroberfläche zur Verfügung stellt.

---

## 2. Projektarchitektur (1 Minute)

Dieses Projekt besteht aus drei Hauptteilen, die zusammenarbeiten:

1.  **`fetcher_v2.py` (Die Daten-Pipeline):**
    *   Ein Python-Skript, das als Herzstück der Datenerfassung fungiert.
    *   Es verbindet sich mit der PokeAPI, um alle Pokémon-Informationen zu erhalten.
    *   Es bereinigt und bereitet die Daten auf.
    *   Es sendet die aufbereiteten Daten an Solr, um sie zu "indizieren".

2.  **`Solr` (Das Gehirn / Die Suchmaschine):**
    *   Läuft in einem Docker-Container.
    *   Speichert alle Pokémon-Daten auf eine Weise, die für die Suche hochoptimiert ist.
    *   Behandelt komplexe Abfragen, Facettierung (Filtern nach Kategorien) und Sortierung.

3.  **`web/web_app.py` (Das Gesicht / Die Benutzeroberfläche):**
    *   Eine einfache Flask-Webanwendung, die ebenfalls in einem Docker-Container läuft.
    *   Sie nimmt das, was der Benutzer in das Suchfeld eingibt.
    *   Sie sendet diese Abfrage an Solr.
    *   Sie erhält die Ergebnisse von Solr zurück und zeigt sie ansprechend auf der Webseite an.

**Ablauf:** `PokeAPI` -> `Fetcher-Skript` -> `Solr` -> `Web-App` -> **Benutzer**

---

## 3. Tiefer Einblick: `fetcher_v2.py` (2 Minuten)

Dieses Skript ist mehr als nur ein einfacher Datenabrufer. Es ist für die gesamte Daten-Pipeline verantwortlich und konfiguriert sogar die Datenbank.

### Was macht es?

1.  **Ruft Daten ab:** Es fordert Daten für die ersten 3 Generationen von Pokémon (Nummern 1-386) von der PokeAPI an.
    *   Es erhält grundlegende Statistiken, Typen und Fähigkeiten.
    *   Es erhält auch "Spezies-Daten" wie Flavor-Texte, Farbe und Lebensraum.

2.  **Bereinigt Daten:**
    *   API-Text kann unordentlich sein. Das Skript entfernt seltsame Zeichen (`
`, ``) und zusätzliche Leerzeichen, um ihn für die Indizierung sauber zu machen.
    *   Es kombiniert auf intelligente Weise alle verschiedenen Flavor-Text-Einträge für ein Pokémon zu einem großen Textblock, was die Volltextsuche wesentlich effektiver macht.

3.  **Automatisiert die Schema-Konfiguration (Das "V2"-Feature):**
    *   Dies ist das wichtigste neue Feature. Solr muss wissen, welche Art von Daten zu erwarten sind (z. B. `pokemon_id` ist eine Zahl, `name` ist Text). Dies wird als "Schema" bezeichnet.
    *   Anstatt eine manuelle Einrichtung zu erfordern, **konfiguriert das Skript das Solr-Schema automatisch** über die API von Solr.
    *   Es definiert alle notwendigen Felder und aktiviert entscheidend `docValues` für sie. `docValues` ist eine Funktion, die das Sortieren, Facettieren und andere Funktionen erheblich beschleunigt.
    *   Dieser Schritt macht die Bereitstellung wesentlich einfacher und weniger fehleranfällig.

4.  **Indiziert Daten:**
    *   Es löscht alle alten Pokémon-Daten aus Solr, um einen Neuanfang zu gewährleisten.
    *   Es sendet die sauberen, verarbeiteten Pokémon-Daten in Stapeln an Solr.
    *   Nach der Indizierung weist es Solr an, den Index für eine bessere Leistung zu "optimieren".

### Wichtige zu erwähnende Code-Ausschnitte:

*   `setup_solr_schema()`: Die Funktion, die die automatische Schema-Konfiguration übernimmt. Sie ist so konzipiert, dass sie mehrmals sicher ausgeführt werden kann.
*   `process_pokemon_data()`: Wo die Rohdaten von der API in ein strukturiertes Dokument für Solr umgewandelt werden.
*   `fetch_with_retry()`: Zeigt Respekt vor der PokeAPI, indem es Anfragen ratenbegrenzt und bei einem API-Fehler mit einem Backoff erneut versucht.

---

## 4. Wie man es ausführt (30 Sekunden)

Das Projekt ist vollständig containerisiert und einfach einzurichten.

1.  Stellen Sie sicher, dass Sie Docker (oder Podman) haben.
2.  Führen Sie das Setup-Skript aus:
    ```bash
    ./install.sh
    ```
3.  Dieses Skript erledigt alles:
    *   Startet die Solr- und Web-App-Container.
    *   Führt das Skript `fetcher_v2.py` aus, um die Datenbank zu füllen.
4.  Öffnen Sie Ihren Browser unter `http://localhost:5000` und beginnen Sie mit der Suche!

---