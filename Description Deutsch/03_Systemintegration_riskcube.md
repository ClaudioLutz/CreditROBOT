## RiskCUBE

English [connections-for-webshops](https://www.creditreform.ch/en/solutions/system-integration/connections-for-webshops)
Deutsch [webshop-anbindung](https://www.creditreform.ch/loesungen/systemintegration/webshop-anbindung)

**RiskCUBE** ist eine Lösung von Creditreform, welche die Zahlart „Kauf auf Rechnung" in Onlineshops nur bonitätsgeprüften Kundinnen und Kunden mit kalkulierbarem Risiko anbietet. Durch ein intelligentes Regelwerk werden Risiken und Betrugsversuche erkannt und minimiert. Shop-Betreiber können so die Zahlart „Rechnung" sicher integrieren, was erfahrungsgemäss zu einer höheren Konversionsrate und einem gesteigerten Umsatz führt.

> *«Mit diesem Modul können wir jetzt im Webshop auch gegen Rechnung verkaufen. Seither hat sich unser Umsatz um 30% gesteigert.» – Markus Roger Jenny, Geschäftsführer, deinKonzept GmbH, Uznach*

### Bedürfnis

- „Rechnung" ist in der Schweiz die beliebteste Zahlungsart im Online-Handel.
- Wird diese Zahlart nicht angeboten, besteht ein erhöhtes Risiko von Kaufabbrüchen.
- Ohne Bonitätsprüfung entstehen jedoch potenziell hohe Zahlungsausfallrisiken.
- RiskCUBE soll sicherstellen, dass nur Kundinnen und Kunden mit ausreichender Bonität den Rechnungskauf nutzen können.

### Hintergrund

- Durch den hohen Beliebtheitsgrad des Rechnungskaufs sind Betrug und Zahlungsausfälle ein Problem.
- RiskCUBE stellt anhand einer Bonitätsprüfung und weiterer Faktoren fest, ob die Rechnungsoption angeboten werden kann.

### Leistungsumfang

1. **Bonitätsprüfung vor dem Anzeigen der Zahlungsoptionen**
   - Nach Eingabe der Adressangaben im Bestellprozess werden die Daten an RiskCUBE übergeben.
   - RiskCUBE ermittelt Bonität und Verhalten des Bestellers.
   - Je nach Ergebnis werden Zahlarten eingeschränkt oder zugelassen.

2. **Individuelle Einstellungsmöglichkeiten**
   - Rechnungsoption nur bei ausreichender Bonität.
   - Auf Wunsch: keine Rechnungsoption bei auffälligem Verhalten, ungültiger Anschrift oder Überschreitung von Kreditlimiten.
   - Möglichkeit, die Zahlart „Rechnung" bei mittelmässiger Bonität (Gelb) oder unbekannter Person (kein Treffer) weiterhin freizugeben.

3. **Risikosteuerung**
   - Freigabe- oder Sperrregeln für bestimmte Zeitfenster (z.B. Nachtsperre zwischen 01:00 und 04:30 Uhr).
   - Definierbare Mindest-Bestellwerte, maximale Kreditlimiten und Matchtoleranzen.

### Betrugserkennung

- **Auffälliges Verhalten im Shop**: Bei Betrugsindikatoren (z.B. mehrere Bestellungen in kurzer Zeit, abweichende Lieferadresse, etc.) kann die Zahlungsart „Rechnung" deaktiviert werden.
- **Postalisch ungültige Anschriften**: Keine Rechnungsoption, wenn Adresse nicht existiert oder bereits als betrugsverdächtig gemeldet wurde.
- **Zeitbasierte Einschränkungen**: Nachtsperre (kein Kauf auf Rechnung zwischen 01:00 und 04:30 Uhr).
- **Bekannte Betrugsadressen**: Werden von Creditreform gesperrt und gemeldet.
- **Ergänzende IP-Fraud-Analyse**: Empfehlung zur Nutzung zusätzlicher Fraud-AddOns.

### Steuerungsmöglichkeiten (Auszug)

- **Matchtoleranz**: Einstellbar, um z.B. leichte Schreibfehler in Adressen zuzulassen.
- **Mindest-Bestellwert pro Transaktion**: Kauf auf Rechnung nur ab einem gewissen Einkaufswert.
- **Individuelle Kreditlimiten**:
  - B2B/B2C, pro Tag und/oder innerhalb eines definierten Zeitraums (z.B. 30 Tage).
  - Unterschiedliche Limiten je nach Bonitätsampel (Grün/Gelb/Rot) oder spezieller Kundentyp (öffentliche Verwaltung, etc.).
- **Maximale Kreditlimite bei Systemausfall**: Fallback-Regel, wenn RiskCUBE oder die Schnittstelle nicht verfügbar ist.
- **Abweichende Rechnungs- und Lieferadresse**: Je nach Wunsch erlauben oder sperren.
- **Zahlungsstörungen**: Automatischer Ausschluss vom Rechnungskauf bei Zahlungsstörungen in der Vergangenheit.

### Vorgehen (allgemein)

1. **Informationen an Creditreform übermitteln**
   - Shop-Software und Version
   - Erwartete Anzahl Shop-Bestellungen pro Jahr
   - Geplanter Termin für die Installation (Plug-in oder Schnittstelle)

2. **Prüfung durch Creditreform**
   - Gemeinsame Klärung mit dem jeweiligen Entwicklungspartner, ob für Ihre Shop-Version ein Plug-in existiert oder eine Individualanbindung notwendig ist.
   - Erstellung eines Angebots für die Bonitätsprüfungen.

3. **Vertragsabschluss und Installation**
   - Nach Abschluss des Vertrags koordiniert ein Creditreform-Projektleiter die Installation bzw. Anbindung.
   - Sie erhalten Zugangsdaten, technische Unterlagen und weitere Details zur Konfiguration Ihrer Risikosteuerung.

### Verfügbare Shop-PlugIns & Systeme

#### Allgemeine Übersicht

- **Magento** (ab Version 2.2)
- **PrestaShop** (Version 8.1.x)
- **Gambio** (ab Version 3.14)
- **WooCommerce** (WordPress ab Version 5.3, PHP ab Version 7.4)
- **Shopware** (ab Version 6 mit RiskCUBE, ab Version 5.1.0 ohne RiskCUBE)
- **PepperShop** (ab Version 9 mit RiskCUBE, bis Version 8 ohne RiskCUBE)
- **AbaShop** (ab Version 2016 ohne RiskCUBE, mit separater Bonitätsprüfung)

Eine aktuelle Übersicht aller Plug-ins:
[plugin.creditreform.ch](http://plugin.creditreform.ch)

#### Magento & Shopware

- **Unterstützte Länder**: Schweiz, Liechtenstein (für Firmen)
- **Preise**
  - Nutzung und Einrichtung der RiskCUBE-Lizenz: CHF 960 pro Jahr
  - Einrichtungskosten (einmalig): € 399 (inkl. 2 Stunden Support)
  - Modulkosten: € 39 pro Monat (jährliche Vorauszahlung)
  - Bonitätsprüfung: Individuelles Angebot durch Creditreform (Pauschalen günstiger bei zusätzlichem Inkasso oder Lieferung von Zahlungserfahrungen)

- **Plug-in-Partner**
  - *LEONEX Internet GmbH*
    Technologiepark 6, DE-33100 Paderborn
    +49 5251 4142 500
    [www.leonex.de](https://www.leonex.de)
    info@leonex.de

#### PrestaShop & WooCommerce

- **Unterstützte Länder**: Schweiz, Liechtenstein
- **Preise**
  - Nutzung und Einrichten der RiskCUBE-Lizenz inkl. Shop-Plug-in: CHF 960 pro Jahr
  - Bonitätsprüfung: Individuelles Angebot (Pauschalen möglich, günstiger bei zusätzlichem Inkasso oder Lieferung von Zahlungserfahrungen)

- **Download**
  - **WooCommerce**: [WordPress-Plug-in](https://wordpress.org/plugins/riskcube-von-creditreform-schweiz)
  - **PrestaShop**: [addons.prestashop.com](https://addons.prestashop.com/de/search.php?search_query=riskcube&compatibility=8.1.7&)

- **Plug-in-Partner**
  - *Masterhomepage GmbH*
    Thiersteinerallee 17, 4053 Basel
    +41 61 681 54 50
    [masterhomepage.ch](https://www.masterhomepage.ch)
    info@masterhomepage.ch

#### PepperShop

- **Unterstützte Länder**: Schweiz, Liechtenstein (für Firmen)
- **Preise**
  - RiskCUBE-Lizenz mit Plug-in: CHF 960 p.a.
  - RiskCUBE-Lizenz *ohne* Plug-in: CHF 660 p.a.
  - Shop-Plug-in-Nutzungsgebühr: CHF 9.60 pro Monat (Mindestlaufzeit 12 Monate)
  - Bonitätsprüfung: Individuelles Angebot (Pauschalen günstiger bei zusätzlichem Inkasso oder Lieferung von Zahlungserfahrungen)

- **Plug-in-Partner**
  - *Glarotech GmbH*
    Toggenburgerstr. 156, 9500 Wil
    [www.peppershop.com](https://www.peppershop.com)

#### Gambio

- **Unterstützte Länder**: Schweiz, Liechtenstein (für Firmen)
- **Preise**
  - Nutzung und Einrichten der RiskCUBE-Lizenz inkl. Shop-Plug-in: CHF 960 p.a.
  - Shop-Plug-in:
    - Lizenz pro URL (einmalig): € 150 (Wartung/Upgrade nach Aufwand)
    - Lizenz pro URL *inkl. Wartung/Upgrade*: € 29 pro Monat (Mindestlaufzeit 12 Monate)
    - Installationsunterstützung (einmalig, empfohlen): € 340
  - Bonitätsprüfung: Individuelles Angebot (Pauschalen günstiger bei zusätzlichem Inkasso oder Zahlungserfahrungen)

- **Plug-in-Partner**
  - *WinHelp GmbH*
    Bienwaldstrasse 41, DE-76287 Rheinstetten
    +49 721 8198 7100
    [www.winhelp.eu](https://www.winhelp.eu)
    info@winhelp.eu

#### AbaShop mit integrierter Bonitätsprüfung

- **Unterstützte Länder**: Schweiz, Liechtenstein (für Firmen)
- **Preise**
  - Betrieb des Moduls: CHF 20.00 pro Monat
  - Bonitätsprüfung: Separate Offerte durch Creditreform
  - Kosten für die AbaShop-Option „Bonitätsprüfung": Werden durch den jeweiligen Abacus-Vertriebspartner in Rechnung gestellt

> *«Mit der Zusatzoption zu AbaShop wird die Bonitätsprüfung automatisiert im Shop integriert. Das spart Zeit und gibt Sicherheit.»
– Bruno Rhomberg, Mitglied der Geschäftsleitung, Creditreform Egeli Gruppe*

- **Risikoeinstellung mit Ampelsteuerung**
  - Je nach Score der Bonitätsprüfung wird eine Ampel (Grün/Gelb/Rot) geliefert.
  - Einstellungen für unterschiedliche Risikobereitschaft (tief, mittel, hoch).
  - Optional: Prüfung nur für Firmen oder nur für Neukunden.

- **Einstellmöglichkeiten Zahlarten** (Beispiele aus AbaShop):
  - Bonitätsprüfung vor, während oder nach der Zahlungsauswahl.
  - Zeitintervall für Aktualisierung der Bonitätsabfrage.
  - Rechnungsoption bei Bonität Gelb (Ja/Nein), ohne Treffer (Ja/Nein) oder bei Verbindungsfehler (Ja/Nein).
  - Einschränkung auf Warenkörbe von CHF X bis CHF Y.
  - Mindestbestellbeträge für die Anzeige der Rechnungsoption.

**Voraussetzungen**
- Abacus ab Version 2016
- Mitgliedschaft bei Creditreform
- Ggf. Inkassoabwicklung über Creditreform (empfohlen)

### RiskCUBE API & Individualanbindung

- **REST-Schnittstelle**
  - Moderne, skalierbare REST-API für individuelle Lösungen.
  - Dokumentation und Zugangsdaten werden nach Unterzeichnung einer Vertraulichkeitsvereinbarung bereitgestellt.

- **Ohne RiskCUBE**
  - Auch ohne die RiskCUBE-Funktionen können Sie für Ihren Shop (abgewandelte) Bonitätsprüfungen integrieren.
  - Benötigt separate Schnittstellendokumentation und ggf. eigene Entwicklung.

### Preise (Zusammenfassung)

1. **RiskCUBE-Lizenz**
   - **Mit Shop-Plug-in**: CHF 960 p.a. (sofern nicht anders ausgewiesen)
   - **Ohne Shop-Plug-in**: CHF 660 p.a.
   - Abweichende Preisangaben je nach System (siehe jeweilige Details oben).

2. **Shop-Plug-in-Kosten**
   - Teils monatliche, teils einmalige Lizenz- oder Installationskosten je nach System und Partner.

3. **Bonitätsprüfung**
   - Individuelle Angebote mit Pauschalen (vergünstigt bei zusätzlichem Inkasso oder Lieferung von Zahlungserfahrungen).

4. **Weitere Kosten**
   - Installation, Wartung, Upgrade oder Support gemäß Angaben der jeweiligen Plug-in-Partner.

*Alle Preise verstehen sich exklusive Mehrwertsteuer (MwSt.).*

### Kontakt Creditreform AG

- **Adresse**
  Teufener Strasse 36
  CH-9000 St. Gallen
- **Telefon**
  +41 71 221 11 99
- **E-Mail**
  support@creditreform.ch

Für detaillierte Auskünfte zu Plug-ins, Preisen, Bonitätsprüfungen und Inkasso kontaktieren Sie bitte Ihren Kundenbetreuer oder besuchen Sie
[plugin.creditreform.ch](http://plugin.creditreform.ch).
