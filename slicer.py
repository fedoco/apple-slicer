#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Apple Slicer
#
# This script parses App Store Connect financial reports and splits sales
# by Apple subsidiaries which are legally accountable for them.
# It may be used to help generating Reverse Charge invoices for accounting and
# in order to correctly issue Recapitulative Statements mandatory in the EU.
#
# Copyright (c) 2015 fedoco <fedoco@users.noreply.github.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys, os, re, csv, locale, argparse
import apple
from decimal import Decimal
from datetime import datetime

# CONFIGURATION

# ISO code of local currency into which foreign sales amounts should be converted
local_currency = 'EUR'

# desired locale used for formatting dates and prices
locale.setlocale(locale.LC_ALL, 'de_DE')

# name of CSV file in which currency exchange rates are listed - can be downloaded from App Store Connect's
# "Payments & Financial Reports" page and needs to match the financial reports' date range
currency_data_filename = 'financial_report.csv'

# -------------------------------------------------------------------------------------------------------------------------------------

def format_date(date_str):
    """Formats an US-style date string according to the default format of the current locale."""
    return datetime.strptime(date_str,"%m/%d/%Y").strftime('%x')

def format_currency(number, precise = False):
    """Format a number according to the currency format of the current locale but without the currency symbol.""" 
    if not precise:
        # round according to the current locale's currency format (fractional digits, thousands grouping and decimal mark)
        return locale.currency(number, False, True)
    else:
        # while still obeying to the current locale's currency format regarding thousands grouping and decimal mark,
        # always round to 4 decimal places
        return locale.format_string("%.4f", number, True, True)

def parse_currency_data(filename):
    """Parse exchange rate and taxation factor (relevant f. ex. for JPY revenue) for each currency listed in the given file."""

    line = 0
    result = {}

    # column indices differ if report has a "Balance" column
    column_index_amount_pre_tax = 3
    column_index_amount_after_tax = 7
    column_index_earnings = 9

    try:
        f = open(filename, 'r')
    except IOError:
        print('Exchange rates data file missing: "%s"' % filename)
        print('You can download this file from App Store Connect\'s "Payments & Financial Reports" page')
        sys.exit(1)

    for fields in csv.reader(f, delimiter = ','):
        line = line + 1

        # make sure it is a valid file by examining the column count of the first line
        if line == 1:
            if len(fields) == 10:
                print('Aborting: You seem to have downloaded a pending month\'s ' + currency_data_filename)
                print('Such reports contain estimated figures and should not be used for invoicing')
                sys.exit(1)

            if len(fields) != 13:
                print('Aborting: Invalid column count in ' + currency_data_filename)
                sys.exit(1)

        # if the report contains earnings that haven't surpassed the origin country's payout threshold, line 3 has a
        # "Balance" column which makes for shifted column indices
        if line == 3:
            if len(fields) == 13:
                column_index_amount_pre_tax += 1
                column_index_amount_after_tax += 1
                column_index_earnings += 1

            if len(fields) != 12 and len(fields) != 13:
                print('Aborting: Invalid column count in ' + currency_data_filename)
                sys.exit(1)

        # actual financial data starts at line 4
        if line < 4:
            continue

        # abort processing at the first blank line: separated by a line with empty fields, reports can contain earnings
        # which haven't surpassed the payout threshold and therefore need to be ignored
        if len(fields[0]) == 0:
            break

        # extract currency symbol from parentheses
        r = re.search('\(([A-Z]{3})\)$', fields[0])
        if not r:
            print('Aborting: Encountered line without a valid currency symbol in ' + currency_data_filename)
            sys.exit(1)
        currency = r.group(1)

        # USD can occur twice in the file: We must take special care to distinguish between USD (and their corresponding
        # exchange rate) for purchases made in "Americas" and in "Rest of World", as Apple calls it. Unfortunately, Apple
        # decided to localize the aforementioned strings so they need to be looked up in a translation table. Luckily,
        # localized report files currently seem to be generated only for French, German, Italian and Spanish locale settings.
        localizations_RoW = ["of World", "du monde", "der Welt", "del mondo", "del mundo"]
        if currency == 'USD':
            for localization in localizations_RoW:
                if localization.lower() in fields[0].lower():
                    currency = 'USD - RoW'
 
        amount_pre_tax = Decimal(fields[column_index_amount_pre_tax].replace(',', ''))
        amount_after_tax = Decimal(fields[column_index_amount_after_tax].replace(',', ''))
        earnings = Decimal(fields[column_index_earnings].replace(',', ''))

        # calculate the exchange rate explicitly instead of relying on the "Exchange Rate“ column
        # because its value is rounded to 6 decimal places and sometimes not precise enough
        exchange_rate = earnings / amount_after_tax 

        tax = amount_pre_tax - amount_after_tax
        tax_factor = Decimal(1.0) - abs(tax / amount_pre_tax)

        result[currency] = exchange_rate, tax_factor

    f.close()

    return result

def parse_financial_reports(workingdir):
    """Parse the sales listed in all App Store Connect financial reports in the given directory and group them by country and product."""

    countries = {}
    currencies = {}
    date_range = None

    for filename in os.listdir(workingdir):
        # skip files that are not financial reports
        if filename == currency_data_filename or not re.match(r'.*_[A-Z][A-Z]\.txt$', filename):
            continue

        f = open(workingdir + '/' + filename, 'r')
        for line in csv.reader(f, delimiter = '\t'):
            # skip lines that don't start with a date
            if not '/' in line[0]:
                continue

            # consider first occurrence the authoritative date range and assume it is the same for all reports
            if not date_range:
                date_range = format_date(line[0]) + ' – ' + format_date(line[1])

            # all fields of interest of the current line
            quantity = int(line[5])
            amount = Decimal(line[7])
            currency = line[8]
            product = line[12]
            countrycode = line[17]

            # add current line's product quantity and amount to dictionary
            products = countries.get(countrycode, dict())
            quantity_and_amount = products.get(product, (0, Decimal(0)))
            products[product] = tuple(map(lambda x, y: x + y, quantity_and_amount, (quantity, amount)))
            countries[countrycode] = products

            # remember currency of current line's country
            currencies[countrycode] = currency

            # special case affecting countries Apple put in the "Rest of World" group: currency for those is listed as "USD"
            # in the sales reports but the corresponding exchange rate is keyed "USD - RoW" - a pragmatic way of identifying
            # those "RoW" countries is to inspect the filename of the sales report
            if "_WW." in filename and currency == "USD":
              currencies[countrycode] = "USD - RoW"

        f.close()

    # break if we didn't read any meaningful data
    if not countries:
      print('No valid App Store Connect financial reports (*.txt) found in ' + workingdir)
      sys.exit(1)

    return countries, currencies, date_range 

def print_sales_by_corporation(sales, currencies, no_subtotals, only_subtotals):
    """Print sales grouped by Apple subsidiaries, by countries in which the sales have been made and by products sold."""

    corporations = {}

    for country in sales:
        corporations.setdefault(apple.corporation(country), {})[country] = sales[country]

    for corporation in corporations:
        corporation_sum = Decimal(0)
        print('\n\n' + apple.address(corporation))

        for countrycode in corporations[corporation]:
            country_sum = Decimal(0)
            country_currency = currencies[countrycode]
            products_sold = corporations[corporation][countrycode]

            print('\nSales in {0} ({1})'.format(apple.countryname(countrycode), countrycode))
            print('\tQuantity\tProduct\tAmount\tExchange Rate\tAmount in ' + local_currency)

            exchange_rate = tax_factor = Decimal('1.00000')
            if not country_currency == local_currency:
                exchange_rate, tax_factor = currency_data[country_currency]
            exchange_rate_formatted = locale.format_string("%.5f", exchange_rate)

            for product in products_sold:
                quantity, amount = products_sold[product]

                # subtract local tax(es) if applicable in country (f. ex. in JPY)
                amount -= amount - amount * tax_factor

                country_sum += amount

                # because of rounding errors, the per product amount can only serve as an informative estimate and is thus displayed with 4 fractional
                # digits in order to convey that probably some rounding took place
                amount_in_local_currency = amount * exchange_rate

                if not only_subtotals: print('\t{0}\t{1}\t{2} {3}\t{4}\t{5} {6}'.format(quantity, product, country_currency[:3], format_currency(amount),
                exchange_rate_formatted, format_currency(amount_in_local_currency, True), local_currency.replace('EUR', '€')))
                else: print('\t{0}\t{1}\t{2} {3}'.format(quantity, product, country_currency[:3], format_currency(amount)))

            # although of course rounding happens here, too, it won't show because Apple converts currencies in the same per country manner
            country_sum_in_local_currency = country_sum * exchange_rate

            if not no_subtotals: print('\n\t\tSubtotal {0}:\t{1} {2}\t{3}\t{4} {5}'.format(countrycode, country_currency[:3],
            format_currency(country_sum), exchange_rate_formatted, format_currency(country_sum_in_local_currency), local_currency.replace('EUR', '€')))

            corporation_sum += country_sum_in_local_currency

        print('\n{0} Total:\t{1} {2}'.format(corporation, format_currency(corporation_sum), local_currency.replace('EUR', '€')))

# -------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Tool for splitting App Store Connect financial reports by Apple legal entities')

    subtotals_group = parser.add_mutually_exclusive_group(required=False)
    subtotals_group.add_argument('--no-subtotals', action='store_true', help='omit printing of subtotal for each country')
    subtotals_group.add_argument('--only-subtotals', action='store_true', help='only print subtotal for each country (i.e. skip per product Euro conversion)')
    parser.add_argument('directory', help='path to directory that contains App Store Connect financial reports (*.txt) and a file named ' + 
    '"financial_report.csv" which contains matching currency data downloaded from App Store Connect\'s "Payments & Financial Reports" page')

    args = parser.parse_args()

    currency_data = parse_currency_data(args.directory + '/' + currency_data_filename)

    sales, currencies, date_range = parse_financial_reports(args.directory)

    print('Sales date: ' + date_range, end = '')

    print_sales_by_corporation(sales, currencies, args.no_subtotals, args.only_subtotals)

    sys.exit(0)
