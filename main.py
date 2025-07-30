import csv
import stripe
from stripe.error import InvalidRequestError
import os
from dotenv import load_dotenv
import argparse
from datetime import datetime
import time

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
STRIPE_KEY = os.getenv('STRIPE_KEY', '')
STRIPE_NAME = os.getenv('STRIPE_NAME', 'Stripe Technology Europe, Limited')
SUM_FEES = os.getenv('SUM_FEES', 'false').lower() == 'true'
STRIPE_METHOD = os.getenv('STRIPE_METHOD', 'CSV').upper()


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
        'id',
        'type',
        'source',
        'amount',
        'customer',
        'accounting_date',
        'value_date',
        'description',
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
    # Check if CSV file exists
    if not os.path.exists('import.csv'):
        raise FileNotFoundError(
            "The file 'import.csv' was not found!\n"
            "Possible solutions:\n"
            "1. Create an 'import.csv' file with your Stripe data\n"
            "2. Or switch to API method: Set STRIPE_METHOD=API in the .env file"
        )
    
    csvlines = []
    with open('import.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)

        # Appending rows to csvlines
        for row in reader:
            csvlines.append(row)

    # We remove the header
    csvlines.pop(0)

    return csvlines


def fetch_balance_transactions(start_date, end_date):
    """
    Fetches balance transactions directly from the Stripe API
    :param start_date: Start date (datetime)
    :param end_date: End date (datetime)
    :return: CSV-like array with transaction data
    """
    client = get_client()
    transactions = []
    
    # Convert dates to Unix timestamps
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    
    print(f"Fetching balance transactions from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    
    # Fetch all balance transactions in the timeframe
    balance_transactions = client.BalanceTransaction.list(
        created={
            'gte': start_timestamp,
            'lte': end_timestamp
        },
        limit=100
    )
    
    for transaction in balance_transactions.auto_paging_iter():
        # Convert balance transaction to CSV format
        # Adapt Stripe Balance Transaction format
        csv_row = [
            transaction.id,  # id (0)
            transaction.type,  # type (1)
            transaction.source,  # source (2)
            format_stripe_amount(transaction.amount),  # amount (3)
            format_stripe_amount(transaction.fee),  # fee (4)
            '',  # currency (5) - not used
            '',  # net (6) - not used  
            '',  # reporting_category (7) - not used
            '',  # customer_facing_amount (8) - not used
            datetime.fromtimestamp(transaction.created).strftime('%Y-%m-%d %H:%M:%S'),  # created/accounting_date (9)
            datetime.fromtimestamp(transaction.available_on).strftime('%Y-%m-%d %H:%M:%S'),  # available_on/value_date (10)
            transaction.description or ''  # description (11)
        ]
        transactions.append(csv_row)
    
    print(f"Found {len(transactions)} transactions.")
    return transactions


def format_stripe_amount(amount_in_cents):
    """
    Converts Stripe amounts (in cents) to German format
    :param amount_in_cents: Amount in cents
    :return: German format string (e.g. "10,50")
    """
    if amount_in_cents == 0:
        return "0,00"
    
    amount_in_euros = amount_in_cents / 100
    return f"{amount_in_euros:.2f}".replace('.', ',')


def parse_date(date_string):
    """
    Parses date string to datetime object
    :param date_string: Date in format YYYY-MM-DD
    :return: datetime object
    """
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Invalid date format: {date_string}. Use YYYY-MM-DD (e.g. 2024-01-01)")


def get_transactions_data(start_date=None, end_date=None):
    """
    Gets transaction data either from CSV or API based on STRIPE_METHOD
    :param start_date: Start date for API retrieval
    :param end_date: End date for API retrieval
    :return: Transaction data in CSV format
    """
    if STRIPE_METHOD == 'CSV':
        print("Using CSV method...")
        return read_csv()
    elif STRIPE_METHOD == 'API':
        if not start_date or not end_date:
            raise ValueError("Start and end date are required for API method!")
        print("Using API method...")
        return fetch_balance_transactions(start_date, end_date)
    else:
        raise ValueError(f"Invalid STRIPE_METHOD: {STRIPE_METHOD}. Use 'CSV' or 'API'")


def toMoney(am: str):
    """
    Convert the amount part to float and to an easy format, so lexoffice does not get in trouble
    :param am:
    :return:
    """
    return float(
        am.replace('.', '').replace(',', '.')
    )


def main():
    """
    Main function with CLI argument parsing
    """
    parser = argparse.ArgumentParser(description='Stripe to LexOffice CSV Converter')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD) for API retrieval')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD) for API retrieval')
    
    args = parser.parse_args()
    
    start_date = None
    end_date = None
    
    # Parse date parameters if present
    if args.start_date:
        start_date = parse_date(args.start_date)
    if args.end_date:
        end_date = parse_date(args.end_date)
    
    # Validation for API method
    if STRIPE_METHOD == 'API' and (not start_date or not end_date):
        print("Error: Start and end date are required for API method!")
        print("Usage: python main.py --start-date 2024-01-01 --end-date 2024-01-31")
        return
    
    print(f"Configuration:")
    print(f"  STRIPE_METHOD: {STRIPE_METHOD}")
    print(f"  SUM_FEES: {SUM_FEES}")
    if start_date and end_date:
        print(f"  Time range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Get transaction data
    stripeCSV = get_transactions_data(start_date, end_date)
    everhypeCSV = []
    
    # Variables for fee aggregation
    total_fees = 0.0
    fee_descriptions = []
    fee_accounting_date = None
    fee_value_date = None

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

        everhypeCSV.append([
            id,
            transType,
            source,
            toMoney(amount),
            customer,
            accounting_date,
            value_date,
            description
        ])

        # Fee processing
        if line[4] != '0,00':
            fee_amount = toMoney(line[4])
            
            if SUM_FEES:
                # Collect all fees for a summarized line
                total_fees += fee_amount
                fee_descriptions.append(f'Fees for payment {id}')
                if fee_accounting_date is None:
                    fee_accounting_date = accounting_date
                    fee_value_date = value_date
            else:
                # Create individual fee line (original behavior)
                everhypeCSV.append([
                    id + '_fee',
                    'Kontoführungsgebühr',
                    source + '_fee',
                    fee_amount * -1,
                    STRIPE_NAME,
                    accounting_date,
                    value_date,
                    f'Fees for payment {id} -- {description}'
                ])

    # If SUM_FEES is enabled and there are fees, add a summarized line
    if SUM_FEES and total_fees > 0:
        everhypeCSV.append([
            'fees_total',
            'Kontoführungsgebühr',
            'fees_total',
            total_fees * -1,
            STRIPE_NAME,
            fee_accounting_date,
            fee_value_date,
            f'Aggregated fees -- {"; ".join(fee_descriptions)}'
        ])

    # Writing to export.csv
    with open('export.csv', 'w', newline='', encoding='utf-8') as exportFile:
        writer = csv.writer(exportFile, delimiter=';')

        writer.writerow(csv_header())
        writer.writerows(everhypeCSV)
    
    print(f"Export completed! {len(everhypeCSV)} lines written to export.csv.")


# Run the script
if __name__ == '__main__':
    main()
