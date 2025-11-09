# Grocery Shopping List Manager

Ich möchte für mich die analoge Shopping Liste in das 21 Jahrhunder bringen und diese in einer digitale selbst gehostete Variante erstellen.

## Aufgaben

- Zugriff auf die Webseite
  - Alle Funktionen und Ansichten sollen nur nach einer erfolgreichen Anmeldung möglich sein
  - Geteilte Shopping List (mithilfe eines Direktlinks) sollen für jedermann sichtbar sein; Auch nicht angemeldete Benutzer
  - Angemeldete Benutzer dürfen Änderungen an den geteilten Listen vornehmen, d.h. Einträge anpassen oder löschen
- Die erstellten Shopping Lists sollen nur für den Ersteller sichtbar sein. Alle anderen Benutzer sehen die Listen der anderen Benutzer nicht.
- Die Shopping List soll mit einer zufällig generierten GUID in einer Datenbank gespeichert werden.
- Eine Shopping List soll die folgende Einträge behalten (von links nach rechts):
  - Box zum Abhaken
  - Anzahl
  - Artikelbezeichnung
- Sobald ein Artikel abgehakt wurde (weil es z.B. im Wagen liegt) soll der Artikeltext und die Artikelanzahl durchgestrichen werden.
- Die Eingabefelder für neue Artikel sollen sich über der Liste befinden
  - Die neuen Elemente sollen wenn möglich ohne Seitenrefresh dynamisch ausgeführt werden.
- Zwei Benutzerrollen:
  - Administratoren
  - Benutzer
- Es gibt einen Standard Admin Benutzer admin / admin123
- Die Administratoren können folgendes:
  - Benutzerverwaltung (neue Benutzer / Benutzer löschen / Benutzer bearbeiten)
    - Wenn Benutzer gelöscht werden, sollen auch alle dazugehörigen Listen gelöscht werden
  - Alle erstellten Listen, aller Benutzer sehen. Benutzerlisten löschen

## Design

- Light und Dark Theme
  - Dark Theme: dunkelblau grundfarbe
  - Light Theme: orange, pasteltöne
- Webseite für Desktop und Mobile Endgeräte erstellen

## Backend Technologie

- Flask
  - weitere Module sofern notwendig (bereits eingetragen behalten)
- Rest API für späteren Zugriff über eine separate App
  - JWT Token für Anmeldung
