import csv
import stripe
from stripe.error import InvalidRequestError
from collections import defaultdict
from datetime import datetime


# Define your stripe key here
with open('stripe.key', 'r') as key_file:
    STRIPE_KEY = key_file.read().strip()
STRIPE_NAME = 'Stripe Technology Europe, Limited'


def get_client():
    """
    This method sets the api key & return the client
    :return: stripe
    """
    stripe.api_key = STRIPE_KEY
    return stripe


def csv_header():
    """
    This method only returns the csv header for our export
    :return: array
    """
    return [
        'Buchungsdatum',
        'Auftraggeber/Empfänger',
        'Verwendungszweck',
        'Betrag'
    ]


def getCustomerByPayment(payment_id: str):
    """
    This method tries to fetch the Customer name from the payment
    if it does not succeed, it returns the stripe name (happens e.g. when there is a chargeback from a customer)
    :param payment_id: => source id in import.csv
    :return:
    """
    try:
        return get_client().Charge.retrieve(payment_id)['billing_details']['name']
    except InvalidRequestError:
        return STRIPE_NAME


def read_csv():
    """
    This method returns all csv lines in import.csv & drops the header.
    :return: CSV Lines in array from import.csv
    """
    csvlines = []
    with open('import.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)

        # Appending rows to csvlines
        for row in reader:
            csvlines.append(row)

    # We remove the header
    csvlines.pop(0)

    return csvlines


def toMoney(am: str):
    """
    Convert the amount part to float and to an easy format, so lexoffice does not get in trouble
    :param am:
    :return:
    """
    return float(
        am.replace('.', '').replace(',', '.')
    )


def get_month(date_str):
    """
    Extrahiert den Monat aus einem Datumsstring.
    """
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M').strftime('%Y-%m')


# Run the script
if __name__ == '__main__':
    stripeCSV = read_csv()
    everhypeCSV = []
    monatliche_gebuehren = defaultdict(float)

    for line in stripeCSV:
        try:
            id = line[0]
            transType = line[1]
            source = line[2]
            amount = line[3]
            fee = line[4]

            customer = getCustomerByPayment(source)
            # --> created (utc)
            accounting_date = line[9]
            # --> available_on (utc)
            value_date = line[10]
            # --> description
            description = line[11]

            if description == '' and toMoney(amount) > 0:
                description = 'Erlöse'
        except IndexError:
            print("Fehler: Die CSV-Datei hat nicht das erwartete Format.")
            print("Bitte stellen Sie sicher, dass die Datei alle erforderlichen Spalten enthält:")
            print("1. id")
            print("2. Type")
            print("3. Source")
            print("4. Amount")
            print("5. Fee")
            print("6. Destination Platform Fee")
            print("7. Destination Platform Fee Currency")
            print("8. Net")
            print("9. Currency")
            print("10. Created (UTC)")
            print("11. Available On (UTC)")
            print("12. Description")
            print("13. Customer Facing Amount")
            print("14. Customer Facing Currency")
            print("15. Transfer")
            print("16. Transfer Date (UTC)")
            print("17. Transfer Group")
            print("\nDie aktuelle Zeile enthält nur", len(line), "Spalten.")
            exit(1)

        # Sammle Gebühren für monatliche Zusammenfassung
        if fee != '0,00' or 'Automatic Taxes' in description or 'Post Payment Invoices' in description:
            monat = get_month(accounting_date)
            if fee != '0,00':
                gebuehr = toMoney(fee) * -1
            else:
                gebuehr = toMoney(amount)
            monatliche_gebuehren[monat] += gebuehr
        
        if description == 'Erlöse' or description == 'STRIPE PAYOUT':
            everhypeCSV.append([
                accounting_date,
                customer,
                description,
                toMoney(amount)
            ])


    # Füge die zusammengefassten Gebühren pro Monat hinzu
    for monat, summe in monatliche_gebuehren.items():
        buchungsdatum = f'{monat}-01'
        verwendungszweck = f'Stripe Gebühren für {datetime.strptime(monat, "%Y-%m").strftime("%B %Y")}'
        everhypeCSV.append([
            buchungsdatum,
            STRIPE_NAME,
            verwendungszweck,
            round(summe, 3)
        ])

    # writing to export.csv
    with open('export.csv', 'w', newline='', encoding='utf-8') as exportFile:
        writer = csv.writer(exportFile, delimiter=',')

        writer.writerow(csv_header())
        writer.writerows(everhypeCSV)

    # Erfolgsmeldung ausgeben
    print("\n✅ Export erfolgreich abgeschlossen!")
    print(f"📊 Exportierte Datensätze: {len(everhypeCSV)}")
    print(f"📁 Datei wurde gespeichert als: export.csv")
    
    # Statistiken über die exportierten Daten
    erloese = sum(1 for row in everhypeCSV if row[2] == 'Erlöse')
    auszahlungen = sum(1 for row in everhypeCSV if row[2] == 'STRIPE PAYOUT')
    gebuehren = sum(1 for row in everhypeCSV if 'Gebühren' in row[2])
    
    print("\n📈 Statistiken:")
    print(f"- Erlöse: {erloese}")
    print(f"- Auszahlungen: {auszahlungen}")
    print(f"- Gebührenbuchungen: {gebuehren}")
