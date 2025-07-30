# Stripe to LexOffice CSV Converter

Ein flexibles Python-Tool zur Konvertierung von Stripe-Transaktionsdaten in ein LexOffice-kompatibles CSV-Format. Das Tool unterstützt sowohl CSV-Import als auch direkten API-Zugriff auf Stripe Balance-Transaktionen.

## ✨ Features

- **Dual-Mode Support**: CSV-Import oder direkte Stripe API-Abfrage
- **Flexible Datumsbereichs-Abfragen**: CLI-Parameter für Start- und Enddatum
- **Automatische deutsche Beschreibungen**: Intelligente Generierung deutschsprachiger Transaktionsbeschreibungen
- **Intelligente Transaktionserkennung**: Automatische Erkennung von Zahlungsmethoden, Produkten und Transaktionstypen
- **Gebühren-Aggregation**: Option zum Zusammenfassen aller Gebühren in einer Zeile
- **Umgebungsvariablen-Support**: Sichere Konfiguration über `.env`-Datei
- **Automatisches Kunden-Mapping**: Holt Kundennamen direkt von Stripe
- **Produkterkennung**: Automatische Extraktion von Produktinformationen aus Stripe-Metadaten
- **Zahlungsmethoden-Details**: Erkennung von Kartentypen, SEPA, etc. mit maskierten Kartennummern
- **Intelligentes Fehlerhandling**: Hilfreiche Fehlermeldungen und Lösungsvorschläge
- **Virtual Environment Support**: Isolierte Python-Umgebung

## 📋 Voraussetzungen

- Python 3.7+
- Stripe Account mit API-Zugriff
- LexOffice Account (für den Import der generierten CSV)

## 🚀 Installation

### 1. Repository klonen

```bash
git clone https://github.com/EverHype-Systems/stripe-lexoffice-csv.git
cd stripe-lexoffice-csv
```

### 2. Virtual Environment erstellen und aktivieren

```bash
python3 -m venv venv
source venv/bin/activate  # Auf Windows: venv\Scripts\activate
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 4. Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
```

Bearbeiten Sie die `.env`-Datei:

```env
# Stripe API Konfiguration
STRIPE_KEY=sk_live_...  # Oder sk_test_... für Testumgebung

# Unternehmensinformationen
STRIPE_NAME=Ihr Unternehmensname

# Gebühren-Konfiguration
# false = Einzelne Gebührenzeilen (Standard)
# true = Alle Gebühren in einer Zeile zusammenfassen
SUM_FEES=false

# Datenquellen-Methode
# CSV = Liest aus import.csv (Standard)
# API = Holt Daten direkt von Stripe API
STRIPE_METHOD=CSV
```

## 📖 Verwendung

### Methode 1: CSV-Import (Standard)

1. **CSV-Datei von Stripe herunterladen:**

   - Gehen Sie zu [Stripe Dashboard > Salden](https://dashboard.stripe.com/balance/overview)
   - Klicken Sie auf [Alle Aktivitäten](https://dashboard.stripe.com/balance)
   - Klicken Sie auf "Exportieren"
   - Stellen Sie Spalten auf "Spalten (17)"
   - Laden Sie den Export herunter und benennen Sie ihn zu `import.csv`

2. **Skript ausführen:**

```bash
python main.py
```

### Methode 2: Direkte API-Abfrage

1. **Konfiguration anpassen:**

```env
STRIPE_METHOD=API
```

2. **Skript mit Datumsbereich ausführen:**

```bash
# Transaktionen für einen Monat abrufen
python main.py --start-date 2024-01-01 --end-date 2024-01-31

# Transaktionen für eine Woche abrufen
python main.py --start-date 2024-01-15 --end-date 2024-01-21
```

## ⚙️ Konfigurationsoptionen

### STRIPE_METHOD

- **`CSV`**: Liest Transaktionen aus `import.csv`
- **`API`**: Holt Transaktionen direkt von der Stripe API

### SUM_FEES

- **`false`**: Erstellt für jede Transaktion eine separate Gebührenzeile
- **`true`**: Fasst alle Gebühren in einer einzigen Zeile zusammen

### Beispiel-Ausgaben

**SUM_FEES=false (Standard) - mit automatischen deutschen Beschreibungen:**

```csv
id;type;source;amount;customer;accounting_date;value_date;description
txn_123;charge;ch_456;105.91;Max Mustermann;2024-01-15 10:30:00;2024-01-17 00:00:00;Zahlung vom 15.01.2024 über 105,91€ (Mastercard ****4649), Kunde: Max Mustermann
txn_456;payment;py_789;105.91;Maria Schmidt;2024-01-15 11:00:00;2024-01-18 00:00:00;Zahlung vom 15.01.2024 über 105,91€ (Online Payment), Kunde: Maria Schmidt, Kunde hat Produkt "KI-Workshop Premium" gekauft
txn_789;refund;re_321;-105.91;Max Mustermann;2024-01-16 09:00:00;2024-01-18 00:00:00;Rückerstattung vom 16.01.2024 über 105,91€, Kunde: Max Mustermann, Grund: Kunde hat Rückerstattung angefordert
txn_101;payout;po_202;-500.00;Stripe Technology Europe, Limited;2024-01-17 02:00:00;2024-01-17 02:00:00;Geldtransit vom 17.01.2024 über 500,00€ - Auszahlung von gesammelten Transaktionen
txn_303;stripe_fee;;-1.06;Stripe Technology Europe, Limited;2024-01-15 10:30:00;2024-01-15 10:30:00;Kontoführungsgebühr vom 15.01.2024 über 1,06€ - Automated Tax Berechnung
```

**SUM_FEES=true:**

```csv
id;type;source;amount;customer;accounting_date;value_date;description
txn_123;charge;ch_456;105.91;Max Mustermann;2024-01-15 10:30:00;2024-01-17 00:00:00;Zahlung vom 15.01.2024 über 105,91€ (Mastercard ****4649), Kunde: Max Mustermann
fees_total;Kontoführungsgebühr;fees_total;-15.50;Stripe Technology Europe, Limited;2024-01-15 10:30:00;2024-01-17 00:00:00;Aggregated fees -- Fees for payment txn_123; Fees for payment txn_124
```

## 🔧 CLI-Parameter

| Parameter      | Beschreibung                           | Beispiel                  |
| -------------- | -------------------------------------- | ------------------------- |
| `--start-date` | Start-Datum für API-Abruf (YYYY-MM-DD) | `--start-date 2024-01-01` |
| `--end-date`   | End-Datum für API-Abruf (YYYY-MM-DD)   | `--end-date 2024-01-31`   |

**Hinweis:** Diese Parameter sind nur bei `STRIPE_METHOD=API` erforderlich.

## 📁 Ausgabe

Das Skript generiert eine `export.csv`-Datei mit folgenden Spalten:

| Spalte            | Beschreibung                                     |
| ----------------- | ------------------------------------------------ |
| `id`              | Eindeutige Transaktions-ID                       |
| `type`            | Transaktionstyp (charge, refund, payout, etc.)   |
| `source`          | Quell-ID der Transaktion                         |
| `amount`          | Transaktionsbetrag in Euro                       |
| `customer`        | Kundenname (automatisch von Stripe abgerufen)    |
| `accounting_date` | Buchungsdatum                                    |
| `value_date`      | Valutadatum                                      |
| `description`     | **Automatisch generierte deutsche Beschreibung** |

## 🇩🇪 Automatische deutsche Beschreibungen

Das Skript erstellt automatisch professionelle deutsche Beschreibungen für alle Transaktionstypen:

### Zahlungen (payment/charge)

- **Format**: `"Zahlung vom DD.MM.YYYY über XX,XX€ (Zahlungsmethode), Kunde: Kundenname"`
- **Beispiele**:
  - `"Zahlung vom 15.01.2024 über 105,91€ (Mastercard ****4649), Kunde: Max Mustermann"`
  - `"Zahlung vom 15.01.2024 über 105,91€ (Online Payment), Kunde: Maria Schmidt"`
  - `"Zahlung vom 15.01.2024 über 105,91€ (SEPA Lastschrift ****1234), Kunde: Firma GmbH"`

### Produkterkennung

Wenn Produktinformationen in Stripe-Metadaten gefunden werden:

- `"Zahlung vom 15.01.2024 über 105,91€ (Online Payment), Kunde: Maria Schmidt, Kunde hat Produkt "KI-Workshop Premium" gekauft"`

### Rückerstattungen (refund)

- **Format**: `"Rückerstattung vom DD.MM.YYYY über XX,XX€, Kunde: Kundenname, Grund: [Grund]"`
- **Beispiele**:
  - `"Rückerstattung vom 16.01.2024 über 105,91€, Kunde: Max Mustermann, Grund: Kunde hat Rückerstattung angefordert"`
  - `"Rückerstattung vom 16.01.2024 über 105,91€, Kunde: Maria Schmidt, Grund: Doppelte Zahlung"`

### Fehlgeschlagene Zahlungen (payment_failure_refund)

- **Format**: `"Rückerstattung vom DD.MM.YYYY über XX,XX€, Kunde: Kundenname, Grund: Fehlgeschlagene Zahlung"`

### Auszahlungen (payout)

- **Format**: `"Geldtransit vom DD.MM.YYYY über XX,XX€ - Auszahlung von gesammelten Transaktionen"`

### Stripe Gebühren (stripe_fee)

- **Format**: `"Kontoführungsgebühr vom DD.MM.YYYY über XX,XX€ - [Spezifikation]"`
- **Beispiele**:
  - `"Kontoführungsgebühr vom 15.01.2024 über 1,06€ - Automated Tax Berechnung"`
  - `"Kontoführungsgebühr vom 15.01.2024 über 2,90€ - Zahlungsabwicklung"`

## 💳 Zahlungsmethoden-Erkennung

Das Skript erkennt automatisch verschiedene Zahlungsmethoden:

| Stripe Typ  | Deutsche Bezeichnung        | Beispiel                                      |
| ----------- | --------------------------- | --------------------------------------------- |
| Kreditkarte | `Mastercard ****4649`       | Bei Charges mit Kartendaten                   |
| Kreditkarte | `Visa ****9826`             | Bei Charges mit Kartendaten                   |
| SEPA        | `SEPA Lastschrift ****1234` | Bei SEPA-Lastschriften                        |
| Andere      | `Online Payment`            | Bei Payment Intents oder unbekannten Methoden |

## 🛍️ Produkterkennung

Das Skript sucht automatisch nach Produktinformationen in folgenden Bereichen:

1. **Stripe Metadaten** (empfohlen):

   ```javascript
   const paymentIntent = await stripe.paymentIntents.create({
     amount: 10591,
     currency: "eur",
     metadata: {
       product_name: "KI-Workshop Premium",
       product: "Workshop Ticket",
       item_name: "Einzelberatung",
     },
   });
   ```

2. **Invoice Line Items**: Produktbeschreibungen aus Rechnungen
3. **Price Descriptions**: Produktnamen aus Stripe Preisen

## 🛠️ Erweiterte Verwendung

### Virtual Environment deaktivieren

```bash
deactivate
```

### Verschiedene Zeiträume abfragen

```bash
# Letzter Monat
python main.py --start-date 2024-01-01 --end-date 2024-01-31

# Letztes Quartal
python main.py --start-date 2024-01-01 --end-date 2024-03-31

# Bestimmte Woche
python main.py --start-date 2024-01-15 --end-date 2024-01-21
```

### Gebühren-Modi wechseln

```bash
# Einzelne Gebührenzeilen
echo "SUM_FEES=false" >> .env

# Zusammengefasste Gebühren
echo "SUM_FEES=true" >> .env
```

## 🔍 Troubleshooting

### Häufige Fehler

**1. "The file 'import.csv' was not found!"**

```
Lösungen:
- Erstellen Sie eine import.csv-Datei mit Ihren Stripe-Daten
- Oder wechseln Sie zur API-Methode: STRIPE_METHOD=API
```

**2. "Start and end date are required for API method!"**

```
Verwendung: python main.py --start-date 2024-01-01 --end-date 2024-01-31
```

**3. "Invalid date format"**

```
Verwenden Sie das Format YYYY-MM-DD (z.B. 2024-01-01)
```

### API-Limits

Die Stripe API hat Ratenlimits. Bei großen Datenmengen:

- Verwenden Sie kleinere Zeiträume
- Das Tool nutzt automatische Paginierung
- Große Exports können einige Minuten dauern

## 📦 Dependencies

Das Tool verwendet folgende Python-Pakete:

```
stripe>=5.0.0          # Stripe API Client
python-dotenv>=0.19.0  # Umgebungsvariablen-Support
```

Alle Dependencies werden automatisch über `pip install -r requirements.txt` installiert.

## 🔐 Sicherheit

- **API-Keys**: Speichern Sie niemals API-Keys im Code
- **`.env`-Datei**: Fügen Sie `.env` zu `.gitignore` hinzu
- **Test vs. Live**: Verwenden Sie Test-Keys für Entwicklung
- **Berechtigungen**: API-Key benötigt nur Lese-Berechtigung für Balance-Transaktionen

## 📊 LexOffice Import

Nach der Generierung der `export.csv`:

1. Melden Sie sich bei LexOffice an
2. Gehen Sie zu "Finanzen" > "Kassa & Bank"
3. Wählen Sie Ihr Bankkonto aus
4. Klicken Sie auf "Import"
5. Laden Sie die `export.csv` hoch
6. Überprüfen Sie die Zuordnung der Spalten
7. Führen Sie den Import durch

## 🤝 Support

Bei Fragen oder Problemen:

1. Überprüfen Sie die Troubleshooting-Sektion
2. Stellen Sie sicher, dass alle Dependencies installiert sind
3. Prüfen Sie Ihre `.env`-Konfiguration
4. Kontaktieren Sie support@everhype.de

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## 🎯 LexOffice-Integration

Die generierten deutschen Beschreibungen sind speziell für LexOffice optimiert:

### ✅ Vorteile für LexOffice:

- **Deutsche Sprache**: Alle Beschreibungen auf Deutsch
- **Einheitliches Format**: Konsistente Datums- und Währungsformatierung
- **Detaillierte Informationen**: Zahlungsmethode, Kunde und Produktdetails
- **Automatische Kategorisierung**: Klar unterscheidbare Transaktionstypen
- **Professionelle Darstellung**: Geschäftstaugliche Beschreibungen

### 📊 Import-Mapping für LexOffice:

| CSV-Spalte        | LexOffice-Feld   | Beispiel                                                                               |
| ----------------- | ---------------- | -------------------------------------------------------------------------------------- |
| `description`     | Verwendungszweck | "Zahlung vom 15.01.2024 über 105,91€ (Mastercard \*\*\*\*4649), Kunde: Max Mustermann" |
| `customer`        | Kontakt          | "Max Mustermann"                                                                       |
| `amount`          | Betrag           | 105.91                                                                                 |
| `accounting_date` | Buchungsdatum    | 2024-01-15                                                                             |
| `value_date`      | Valutadatum      | 2024-01-17                                                                             |

## 🔄 Updates

**Version 3.0 (Aktuell):**

- ✅ **Automatische deutsche Beschreibungen** für alle Transaktionstypen
- ✅ **Intelligente Zahlungsmethoden-Erkennung** (Mastercard, Visa, SEPA, etc.)
- ✅ **Produkterkennung** aus Stripe-Metadaten und Invoice-Daten
- ✅ **Spezifische deutsche Terminologie**:
  - `payout` → "Geldtransit - Auszahlung von gesammelten Transaktionen"
  - `stripe_fee` → "Kontoführungsgebühr" mit automatischer Spezifikation
  - `refund` → "Rückerstattung" mit Grund-Erkennung
- ✅ **Datum im deutschen Format** (DD.MM.YYYY)
- ✅ **Deutsche Währungsformatierung** (XX,XX€)
- ✅ **Automatische Beschreibungsgenerierung** bei leeren Feldern

**Version 2.0:**

- ✅ Dual-Mode Support (CSV/API)
- ✅ CLI-Parameter für Datumsbereich
- ✅ Gebühren-Aggregation
- ✅ .env-Datei Support
- ✅ Verbessertes Fehlerhandling
- ✅ Virtual Environment Support

**Version 1.0:**

- ✅ Basic CSV-Import
- ✅ Stripe-Kunden-Mapping
- ✅ LexOffice-Format-Export
