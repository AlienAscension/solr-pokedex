1. Einleitung
1.1. Motivation und Problemstellung
1.2. Projektziele und funktionale Anforderungen
1.3. Vorstellung der Suchmaschine "Solr Pokédex"
1.4. Verwendeter Technologie-Stack (Apache Solr, Flask, Python, Docker, pokeAPI)
1.5. Aufbau der Dokumentation

2. Datengrundlage und Datenakquise
2.1. Die Datenquelle: Pokémon-API (pokeAPI.co)
2.2. Analyse der Datenstruktur und relevanter Endpunkte
2.3. Datenakquise und Vorverarbeitung mit fetcher_v2.py
2.3.1. Automatisierter Datenabruf via Python-Skript
2.3.2. Datenbereinigung und Transformation für die Indexierung
2.3.3. Technische Besonderheiten: Implementierung eines Rate-Limits

3. Systemarchitektur und Konzeption
3.1. Überblick der containerisierten Gesamtarchitektur (Docker, Docker Compose)
3.2. Entwurf des Solr-Indexschemas (solr/configsets/)
3.2.1. Definition zentraler Feldtypen (z.B. für Textanalyse, Zahlen, exakte Strings)
3.2.2. Struktur des Index: Definierte Felder (z.B. pokemon_id, name, primary_type, generation, all_abilities, flavor_text, is_legendary)
3.2.3. Nutzung von copyField für eine übergreifende Keywordsuche

4. Implementierung der Kernkomponenten
4.1. Indexierungspipeline
4.1.1. Ansteuerung der Solr-API aus dem Fetcher-Skript
4.1.2. Logging des Indexierungsprozesses (pokemon_fetcher.log)
4.2. Entwicklung der Webanwendung mit Flask (web/web_app.py)
4.2.1. Backend-Logik: Anbindung an Solr und Verarbeitung von Suchanfragen
4.2.2. Frontend: Realisierung der Suchoberfläche mit HTML-Templates (templates/)
4.3. Implementierung der Suchfunktionalitäten
4.3.1. Standard-Keywordsuche (case-insensitive, über mehrere Felder)
4.3.2. Phrasen- und Wildcardsuche ("...", *)
4.3.3. Facettierte Suche (Filterung nach Generation, Primärtyp, Legendär-Status)
4.3.4. Feld-spezifische und kombinierte Suchen (inkl. Bereichsabfragen und Boolescher Logik)
4.3.5. Fehlerkorrektur: "Meinten Sie...?" (Spell-Checking / Did you mean)
4.3.6. Ermittlung ähnlicher Dokumente (More Like This)
4.4. Automatisierung des Setups (install.sh)

5. Evaluation und Optimierung
5.1. Funktionale Tests der implementierten Suchanfragetypen
5.2. Bewertung und Optimierung des Relevanzrankings (z.B. durch Boosting)
5.3. Diskussion der optionalen Features (Highlighting, Autocompletion)
5.4. Performanz-Betrachtungen

6. Fazit und Ausblick
6.1. Zusammenfassung der Projektergebnisse
6.2. Reflektion der Herausforderungen und Lösungsansätze
6.3. Mögliche Erweiterungen und zukünftige Optimierungen

Literatur- und Quellenverzeichnis

Anhang
A. Auszug aus dem Solr-Schema (managed-schema)
B. Relevante Code-Auszüge aus fetcher_v2.py und web_app.py
C. Screenshot der Benutzeroberfläche der "Solr Pokédex"
D. Eidesstattliche Erklärung