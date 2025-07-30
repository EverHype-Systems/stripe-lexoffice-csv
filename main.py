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
    Uses LexOffice-compatible German column headers for automatic field mapping
    :return: array
    """
    return [
        'Buchungsdatum',  # Booking Date (accounting_date)
        'Auftraggeber / Empfänger',  # Client/Payer / Recipient (customer)
        'Verwendungszweck', # Purpose of Use/Description (description)
        'Betrag',         # Amount (amount)
        'Soll Betrag (Ausgabe)', # Debit Amount/Expense (negative amounts)
        'Haben Betrag (Einnahme)', # Credit Amount/Income (positive amounts)
        'Wertstellungsdatum', # Value Date (value_date)
    ]


def getCustomerByPayment(payment_id: str):
    """
    This method tries to fetch the Customer name from various Stripe objects
    if it does not succeed, it returns the stripe name (happens e.g. when there is a chargeback from a customer)
    :param payment_id: => source id in import.csv
    :return:
    """
    try:
        # Handle None or empty payment_id
        if not payment_id:
            return STRIPE_NAME
            
        client = get_client()
        
        # Handle different types of Stripe objects
        if payment_id.startswith('ch_'):
            # It's a charge
            charge = client.Charge.retrieve(payment_id)
            # Try billing_details first
            if charge.get('billing_details', {}).get('name'):
                return charge['billing_details']['name']
            # Try customer object if available
            if charge.get('customer'):
                try:
                    customer = client.Customer.retrieve(charge['customer'])
                    return customer.get('name') or customer.get('email', STRIPE_NAME)
                except:
                    pass
            # Try payment intent if available
            if charge.get('payment_intent'):
                try:
                    pi = client.PaymentIntent.retrieve(charge['payment_intent'])
                    if pi.get('customer'):
                        customer = client.Customer.retrieve(pi['customer'])
                        return customer.get('name') or customer.get('email', STRIPE_NAME)
                except:
                    pass
            return STRIPE_NAME
            
        elif payment_id.startswith('pi_'):
            # It's a payment intent
            payment_intent = client.PaymentIntent.retrieve(payment_id)
            # Try to get customer from the payment intent
            if payment_intent.get('customer'):
                try:
                    customer = client.Customer.retrieve(payment_intent['customer'])
                    return customer.get('name') or customer.get('email', STRIPE_NAME)
                except:
                    pass
            # Try to get the latest charge from this payment intent
            if payment_intent.get('latest_charge'):
                try:
                    charge = client.Charge.retrieve(payment_intent['latest_charge'])
                    if charge.get('billing_details', {}).get('name'):
                        return charge['billing_details']['name']
                except:
                    pass
            return STRIPE_NAME
            
        elif payment_id.startswith('py_'):
            # Could be various payment-related objects, try different approaches
            try:
                # Try as PaymentMethod first
                pm = client.PaymentMethod.retrieve(payment_id)
                if pm.get('customer'):
                    customer = client.Customer.retrieve(pm['customer'])
                    return customer.get('name') or customer.get('email', STRIPE_NAME)
                return STRIPE_NAME
            except:
                # If PaymentMethod doesn't work, try other approaches
                return STRIPE_NAME
                
        elif payment_id.startswith('cs_'):
            # It's a checkout session
            session = client.checkout.Session.retrieve(payment_id)
            if session.get('customer'):
                try:
                    customer = client.Customer.retrieve(session['customer'])
                    return customer.get('name') or customer.get('email', STRIPE_NAME)
                except:
                    pass
            # Try to get customer details from the session itself
            customer_details = session.get('customer_details', {})
            if customer_details.get('name'):
                return customer_details['name']
            if customer_details.get('email'):
                return customer_details['email']
            return STRIPE_NAME
            
        elif payment_id.startswith('in_'):
            # It's an invoice
            invoice = client.Invoice.retrieve(payment_id)
            if invoice.get('customer'):
                try:
                    customer = client.Customer.retrieve(invoice['customer'])
                    return customer.get('name') or customer.get('email', STRIPE_NAME)
                except:
                    pass
            return STRIPE_NAME
            
        elif payment_id.startswith('sub_'):
            # It's a subscription
            subscription = client.Subscription.retrieve(payment_id)
            if subscription.get('customer'):
                try:
                    customer = client.Customer.retrieve(subscription['customer'])
                    return customer.get('name') or customer.get('email', STRIPE_NAME)
                except:
                    pass
            return STRIPE_NAME
            
        else:
            # For unknown types, try as charge first (legacy behavior)
            try:
                charge = client.Charge.retrieve(payment_id)
                if charge.get('billing_details', {}).get('name'):
                    return charge['billing_details']['name']
                if charge.get('customer'):
                    customer = client.Customer.retrieve(charge['customer'])
                    return customer.get('name') or customer.get('email', STRIPE_NAME)
                return STRIPE_NAME
            except:
                return STRIPE_NAME
                
    except InvalidRequestError:
        return STRIPE_NAME
    except Exception as e:
        print(f"Warning: Could not fetch customer for {payment_id}: {str(e)}")
        return STRIPE_NAME


def getPaymentMethodFromSource(source_id: str):
    """
    Fetches the payment method from the original Stripe object
    :param source_id: The source ID (charge, payment_intent, etc.)
    :return: Payment method string
    """
    try:
        client = get_client()
        
        if source_id.startswith('ch_'):
            # It's a charge
            charge = client.Charge.retrieve(source_id)
            payment_method = charge.get('payment_method_details', {})
            if payment_method.get('card'):
                brand = payment_method['card'].get('brand', 'Karte').capitalize()
                last4 = payment_method['card'].get('last4', 'XXXX')
                return f"{brand} ****{last4}"
            elif payment_method.get('sepa_debit'):
                last4 = payment_method['sepa_debit'].get('last4', 'XXXX')
                return f"SEPA Lastschrift ****{last4}"
            else:
                return payment_method.get('type', 'Unbekannt').replace('_', ' ').title()
        else:
            return "Online Payment"
    except Exception:
        return "Unbekannt"


def getProductInfoFromSource(source_id: str):
    """
    Fetches product information from the original Stripe object
    :param source_id: The source ID (charge, payment_intent, etc.)
    :return: Product name string or empty string
    """
    try:
        client = get_client()
        
        if source_id.startswith('ch_'):
            # It's a charge
            charge = client.Charge.retrieve(source_id)
            
            # Try to get product from metadata first
            metadata = charge.get('metadata', {})
            if metadata.get('product_name'):
                return metadata['product_name']
            if metadata.get('product'):
                return metadata['product']
            if metadata.get('item_name'):
                return metadata['item_name']
            
            # Try to get from payment intent
            payment_intent_id = charge.get('payment_intent')
            if payment_intent_id:
                try:
                    pi = client.PaymentIntent.retrieve(payment_intent_id)
                    pi_metadata = pi.get('metadata', {})
                    if pi_metadata.get('product_name'):
                        return pi_metadata['product_name']
                    if pi_metadata.get('product'):
                        return pi_metadata['product']
                    if pi_metadata.get('item_name'):
                        return pi_metadata['item_name']
                except:
                    pass
            
            # Try to get from invoice if available
            invoice_id = charge.get('invoice')
            if invoice_id:
                try:
                    invoice = client.Invoice.retrieve(invoice_id)
                    line_items = invoice.get('lines', {}).get('data', [])
                    if line_items:
                        # Get the first line item's description or price description
                        first_item = line_items[0]
                        if first_item.get('description'):
                            return first_item['description']
                        price = first_item.get('price', {})
                        if price.get('nickname'):
                            return price['nickname']
                        product_data = price.get('product', {})
                        if isinstance(product_data, dict) and product_data.get('name'):
                            return product_data['name']
                except:
                    pass
                    
        elif source_id.startswith('py_'):
            # Try as different object types - this might be from a checkout session
            try:
                # Try to find related checkout session through metadata patterns
                # This is a bit tricky since py_ objects can be various things
                pass
            except:
                pass
                
        return ""
    except Exception as e:
        print(f"Warning: Could not fetch product info for {source_id}: {str(e)}")
        return ""


def getDescriptionFromSource(source_id: str, transaction_type: str):
    """
    Fetches the real description from the original Stripe object
    :param source_id: The source ID (charge, payment_intent, etc.)
    :param transaction_type: The transaction type (payment, charge, etc.)
    :return: Description string or empty string
    """
    try:
        client = get_client()
        
        # Handle different source types
        if source_id.startswith('ch_'):
            # It's a charge
            charge = client.Charge.retrieve(source_id)
            description = charge.get('description', '') or charge.get('statement_descriptor', '') or ''
            if description:
                return description
            # If charge has no description, try to get it from payment intent
            payment_intent_id = charge.get('payment_intent')
            if payment_intent_id:
                pi = client.PaymentIntent.retrieve(payment_intent_id)
                return pi.get('description', '') or pi.get('statement_descriptor', '') or ''
            return ''
        elif source_id.startswith('py_'):
            # This seems to be a checkout session or setup intent, try different approaches
            try:
                # Try as PaymentMethod
                pm = client.PaymentMethod.retrieve(source_id)
                return pm.get('description', '') or ''
            except:
                try:
                    # Try as Setup Intent
                    si = client.SetupIntent.retrieve(source_id)
                    return si.get('description', '') or si.get('statement_descriptor', '') or ''
                except:
                    return ''
        elif source_id.startswith('pi_'):
            # It's a payment intent
            payment_intent = client.PaymentIntent.retrieve(source_id)
            return payment_intent.get('description', '') or payment_intent.get('statement_descriptor', '') or ''
        elif source_id.startswith('re_'):
            # It's a refund
            refund = client.Refund.retrieve(source_id)
            return refund.get('reason', '') or 'Refund'
        elif source_id.startswith('cs_'):
            # It's a checkout session
            session = client.checkout.Session.retrieve(source_id)
            return session.get('description', '') or session.get('client_reference_id', '') or ''
        else:
            # For unknown types, try to create a meaningful description from transaction type
            if transaction_type == 'payment':
                return 'Online Payment'
            elif transaction_type == 'charge':
                return 'Card Payment'
            elif transaction_type == 'refund':
                return 'Refund'
            elif transaction_type == 'payout':
                return 'Payout to Bank'
            else:
                return transaction_type.replace('_', ' ').title()
    except Exception as e:
        # If we can't retrieve the object, create a fallback description
        print(f"Warning: Could not fetch description for {source_id}: {str(e)}")
        if transaction_type == 'payment':
            return 'Online Payment'
        elif transaction_type == 'charge':
            return 'Card Payment'
        elif transaction_type == 'refund':
            return 'Refund'
        elif transaction_type == 'payout':
            return 'Payout to Bank'
        else:
            return transaction_type.replace('_', ' ').title()


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


def getRefundReason(source_id: str, transaction_type: str):
    """
    Gets the refund reason from Stripe
    :param source_id: The source ID
    :param transaction_type: Transaction type
    :return: Refund reason in German
    """
    try:
        client = get_client()
        
        if source_id.startswith('re_'):
            # It's a refund
            refund = client.Refund.retrieve(source_id)
            reason = refund.get('reason', '')
            if reason == 'duplicate':
                return 'Doppelte Zahlung'
            elif reason == 'fraudulent':
                return 'Verdacht auf Betrug'
            elif reason == 'requested_by_customer':
                return 'Kunde hat Rückerstattung angefordert'
            elif reason:
                return reason
            else:
                return 'Rückerstattung'
        elif transaction_type == 'payment_failure_refund':
            return 'Rückerstattung aufgrund fehlgeschlagener Zahlung'
        else:
            return 'Rückerstattung'
    except Exception:
        return 'Rückerstattung'


def createDefaultDescription(source_id: str, transaction_type: str, amount: float, customer_name: str, accounting_date: str, original_description: str = ""):
    """
    Creates a default description when none is available
    :param source_id: The source ID
    :param transaction_type: Transaction type
    :param amount: Transaction amount
    :param customer_name: Customer name
    :param accounting_date: Transaction date
    :param original_description: Original description from Stripe
    :return: Formatted description string
    """
    try:
        # Parse and format date from "YYYY-MM-DD HH:MM:SS" to "DD.MM.YYYY"
        from datetime import datetime
        date_obj = datetime.strptime(accounting_date.split(' ')[0], '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d.%m.%Y')
        
        # Format amount with German decimal separator (make amount positive for display)
        amount_abs = abs(amount)
        amount_str = f"{amount_abs:.2f}".replace('.', ',')
        
        # Handle different transaction types
        if transaction_type == 'refund':
            refund_reason = getRefundReason(source_id, transaction_type)
            description = f"Rückerstattung vom {formatted_date} über {amount_str}€, Kunde: {customer_name}, Grund: {refund_reason}"
        elif transaction_type == 'payment_failure_refund':
            description = f"Rückerstattung vom {formatted_date} über {amount_str}€, Kunde: {customer_name}, Grund: Fehlgeschlagene Zahlung"
        elif transaction_type == 'payout':
            description = f"Geldtransit vom {formatted_date} über {amount_str}€ - Auszahlung von gesammelten Transaktionen"
        elif transaction_type in ['stripe_fee', 'application_fee']:
            # Create description based on what the fee is for
            fee_reason = ""
            if "tax" in original_description.lower() or "automatic" in original_description.lower():
                fee_reason = " - Automated Tax Berechnung"
            elif "connect" in original_description.lower():
                fee_reason = " - Connect Gebühr"
            elif "processing" in original_description.lower():
                fee_reason = " - Zahlungsabwicklung"
            elif original_description and original_description.strip():
                fee_reason = f" - {original_description}"
            
            description = f"Kontoführungsgebühr vom {formatted_date} über {amount_str}€{fee_reason}"
        else:
            # Regular payment/charge
            payment_method = getPaymentMethodFromSource(source_id)
            description = f"Zahlung vom {formatted_date} über {amount_str}€ ({payment_method}), Kunde: {customer_name}"
            
            # Try to get product information for payments/charges
            product_name = getProductInfoFromSource(source_id)
            if product_name and product_name.strip():
                description += f", Kunde hat Produkt \"{product_name}\" gekauft"
        
        return description
    except Exception as e:
        # Fallback if anything goes wrong
        if transaction_type == 'refund':
            return f"Rückerstattung über {abs(amount):.2f}€, Kunde: {customer_name}"
        elif transaction_type == 'payment_failure_refund':
            return f"Rückerstattung über {abs(amount):.2f}€, Kunde: {customer_name}, Grund: Fehlgeschlagene Zahlung"
        elif transaction_type == 'payout':
            return f"Geldtransit über {abs(amount):.2f}€ - Auszahlung von gesammelten Transaktionen"
        elif transaction_type in ['stripe_fee', 'application_fee']:
            return f"Kontoführungsgebühr über {abs(amount):.2f}€"
        else:
            return f"Zahlung über {amount:.2f}€, Kunde: {customer_name}"


def generate_export_filename(start_date, end_date):
    """
    Generate export filename based on date range
    :param start_date: Start date (datetime object or None)
    :param end_date: End date (datetime object or None)
    :return: Filename string
    """
    if start_date and end_date:
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        return f'export_{start_str}_{end_str}.csv'
    else:
        # Fallback for CSV method or when dates are not specified
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        return f'export_{timestamp}.csv'


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
    
    # Generate export filename
    export_filename = generate_export_filename(start_date, end_date)
    
    print(f"Configuration:")
    print(f"  STRIPE_METHOD: {STRIPE_METHOD}")
    print(f"  SUM_FEES: {SUM_FEES}")
    print(f"  Export filename: {export_filename}")
    if start_date and end_date:
        print(f"  Time range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Get transaction data
    stripeCSV = get_transactions_data(start_date, end_date)
    everhypeCSV = []
    
    # Variables for fee aggregation - separate by type
    charge_fees = 0.0
    payment_fees = 0.0
    billing_usage_fees = 0.0
    charge_fee_descriptions = []
    payment_fee_descriptions = []
    billing_fee_descriptions = []
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
        # --> description from original source or balance transaction
        description = line[11]
        
        # Handle billing usage fees (stripe_fee) when SUM_FEES is enabled
        if transType == 'stripe_fee' and SUM_FEES:
            billing_usage_fees += abs(toMoney(amount))
            billing_fee_descriptions.append(f'Billing fee {id}')
            if fee_accounting_date is None:
                fee_accounting_date = accounting_date
                fee_value_date = value_date
            # Skip adding to everhypeCSV - will be added as summary
            continue
        
        # For refunds, payment_failure_refunds, payouts and stripe_fees, always use German descriptions
        if transType in ['refund', 'payment_failure_refund', 'payout', 'stripe_fee', 'application_fee']:
            description = createDefaultDescription(source, transType, toMoney(amount), customer, accounting_date, line[11])
        else:
            # If description is empty, try to get it from the original source
            if not description or description.strip() == '':
                description = getDescriptionFromSource(source, transType)
            
            # If still empty, create a default description
            if not description or description.strip() == '':
                description = createDefaultDescription(source, transType, toMoney(amount), customer, accounting_date, line[11])

        # Determine if this is income (positive) or expense (negative)
        amount_float = toMoney(amount)
        soll_betrag = ""  # Debit amount (expense)
        haben_betrag = ""  # Credit amount (income)
        
        if amount_float < 0:
            soll_betrag = abs(amount_float)  # Expense (negative amount becomes positive in Soll)
        else:
            haben_betrag = amount_float  # Income (positive amount stays positive in Haben)
        
        everhypeCSV.append([
            accounting_date,  # Buchungsdatum
            customer,         # Auftraggeber / Empfänger
            description,      # Verwendungszweck
            amount_float,     # Betrag (original amount)
            soll_betrag,      # Soll Betrag (Ausgabe)
            haben_betrag,     # Haben Betrag (Einnahme)
            value_date,       # Wertstellungsdatum
        ])

        # Processing fee handling (from fee column)
        if line[4] != '0,00':
            fee_amount = toMoney(line[4])
            
            if SUM_FEES:
                # Categorize fees by transaction type
                if transType == 'charge':
                    charge_fees += fee_amount
                    charge_fee_descriptions.append(f'Processing fee for charge {id}')
                elif transType == 'payment':
                    payment_fees += fee_amount
                    payment_fee_descriptions.append(f'Processing fee for payment {id}')
                else:
                    # Fallback for other types (refunds, etc.)
                    if transType == 'charge':
                        charge_fees += fee_amount
                        charge_fee_descriptions.append(f'Fee for {transType} {id}')
                    else:
                        payment_fees += fee_amount
                        payment_fee_descriptions.append(f'Fee for {transType} {id}')
                
                if fee_accounting_date is None:
                    fee_accounting_date = accounting_date
                    fee_value_date = value_date
            else:
                # Create individual fee line (original behavior)
                fee_description = f'Fees for payment {id} -- {description}'
                
                everhypeCSV.append([
                    accounting_date,  # Buchungsdatum
                    STRIPE_NAME,      # Auftraggeber / Empfänger
                    fee_description,  # Verwendungszweck
                    round(fee_amount * -1, 2),  # Betrag
                    abs(fee_amount),  # Soll Betrag (Ausgabe) - fees are always expenses
                    "",               # Haben Betrag (Einnahme)
                    value_date,       # Wertstellungsdatum
                ])

    # If SUM_FEES is enabled, add separate summarized lines for each fee type
    if SUM_FEES:
        if charge_fees > 0:
            everhypeCSV.append([
                fee_accounting_date,  # Buchungsdatum
                STRIPE_NAME,          # Auftraggeber / Empfänger
                'Stripe Processing Fees for Charges',  # Verwendungszweck
                round(charge_fees * -1, 2),  # Betrag
                charge_fees,          # Soll Betrag (Ausgabe) - fees are always expenses
                "",                   # Haben Betrag (Einnahme)
                fee_value_date,       # Wertstellungsdatum
            ])
        
        if payment_fees > 0:
            everhypeCSV.append([
                fee_accounting_date,  # Buchungsdatum
                STRIPE_NAME,          # Auftraggeber / Empfänger
                'Stripe Processing Fees for Payments',  # Verwendungszweck
                round(payment_fees * -1, 2),  # Betrag
                payment_fees,         # Soll Betrag (Ausgabe) - fees are always expenses
                "",                   # Haben Betrag (Einnahme)
                fee_value_date,       # Wertstellungsdatum
            ])
        
        if billing_usage_fees > 0:
            everhypeCSV.append([
                fee_accounting_date,  # Buchungsdatum
                STRIPE_NAME,          # Auftraggeber / Empfänger
                'Billing Usage Fee',  # Verwendungszweck
                round(billing_usage_fees * -1, 2),  # Betrag
                billing_usage_fees,   # Soll Betrag (Ausgabe) - fees are always expenses
                "",                   # Haben Betrag (Einnahme)
                fee_value_date,       # Wertstellungsdatum
            ])

    # Writing to export file
    with open(export_filename, 'w', newline='', encoding='utf-8') as exportFile:
        writer = csv.writer(exportFile, delimiter=';')

        writer.writerow(csv_header())
        writer.writerows(everhypeCSV)
    
    print(f"Export completed! {len(everhypeCSV)} lines written to {export_filename}.")


# Run the script
if __name__ == '__main__':
    main()
