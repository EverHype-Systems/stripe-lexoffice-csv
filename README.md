# Stripe to LexOffice CSV Converter

Ein flexibles Python-Tool zur Konvertierung von Stripe-Transaktionsdaten in ein LexOffice-kompatibles CSV-Format. Das Tool unterstützt sowohl CSV-Import als auch direkten API-Zugriff auf Stripe Balance-Transaktionen.

## ✨ Features

- **Dual-Mode Support**: CSV-Import oder direkte Stripe API-Abfrage
- **Flexible Datumsbereichs-Abfragen**: CLI-Parameter für Start- und Enddatum
- **Gebühren-Aggregation**: Option zum Zusammenfassen aller Gebühren in einer Zeile
- **Umgebungsvariablen-Support**: Sichere Konfiguration über `.env`-Datei
- **Automatisches Kunden-Mapping**: Holt Kundennamen direkt von Stripe
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

**SUM_FEES=false (Standard):**

```csv
id;type;source;amount;customer;accounting_date;value_date;description
txn_123;charge;ch_456;100.00;Max Mustermann;2024-01-15 10:30:00;2024-01-17 00:00:00;Produktkauf
txn_123_fee;Kontoführungsgebühr;ch_456_fee;-2.90;Stripe Technology Europe, Limited;2024-01-15 10:30:00;2024-01-17 00:00:00;Gebühren für Zahlung txn_123
```

**SUM_FEES=true:**

```csv
id;type;source;amount;customer;accounting_date;value_date;description
txn_123;charge;ch_456;100.00;Max Mustermann;2024-01-15 10:30:00;2024-01-17 00:00:00;Produktkauf
fees_total;Kontoführungsgebühr;fees_total;-15.50;Stripe Technology Europe, Limited;2024-01-15 10:30:00;2024-01-17 00:00:00;Zusammengefasste Gebühren -- Gebühren für Zahlung txn_123; Gebühren für Zahlung txn_124
```

## 🔧 CLI-Parameter

| Parameter      | Beschreibung                           | Beispiel                  |
| -------------- | -------------------------------------- | ------------------------- |
| `--start-date` | Start-Datum für API-Abruf (YYYY-MM-DD) | `--start-date 2024-01-01` |
| `--end-date`   | End-Datum für API-Abruf (YYYY-MM-DD)   | `--end-date 2024-01-31`   |

**Hinweis:** Diese Parameter sind nur bei `STRIPE_METHOD=API` erforderlich.

## 📁 Ausgabe

Das Skript generiert eine `export.csv`-Datei mit folgenden Spalten:

| Spalte            | Beschreibung                                  |
| ----------------- | --------------------------------------------- |
| `id`              | Eindeutige Transaktions-ID                    |
| `type`            | Transaktionstyp (charge, refund, etc.)        |
| `source`          | Quell-ID der Transaktion                      |
| `amount`          | Transaktionsbetrag in Euro                    |
| `customer`        | Kundenname (automatisch von Stripe abgerufen) |
| `accounting_date` | Buchungsdatum                                 |
| `value_date`      | Valutadatum                                   |
| `description`     | Transaktionsbeschreibung                      |

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

## 🔄 Updates

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
