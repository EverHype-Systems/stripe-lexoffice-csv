import csv
import stripe
from stripe.error import InvalidRequestError


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


# Run the script
if __name__ == '__main__':
    stripeCSV = read_csv()
    everhypeCSV = []

    for line in stripeCSV:
        id = line[0]
        transType = line[1]
        source = line[2]
        amount = line[3]

        customer = getCustomerByPayment(source)
        # --> created (utc)
        accounting_date = line[9]
        # --> available_on (utc)
        value_date = line[10]
        # --> description
        description = line[11]

        if description == '' and toMoney(amount) > 0:
            description = 'Erlöse'

        everhypeCSV.append([
            accounting_date,
            customer,
            description,
            toMoney(amount)
        ])

        # If there are fees, we are generating a new line
        if line[4] != '0,00':
            everhypeCSV.append([
                accounting_date,
                STRIPE_NAME,
                f'Gebühren für Zahlung {id} -- {description}',
                toMoney(line[4]) * -1
            ])

    # writing to export.csv
    with open('export.csv', 'w', newline='', encoding='utf-8') as exportFile:
        writer = csv.writer(exportFile, delimiter=',')

        writer.writerow(csv_header())
        writer.writerows(everhypeCSV)
