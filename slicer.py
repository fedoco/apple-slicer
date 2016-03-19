#!/usr/bin/python
# -*- coding: utf-8 -*-

# Apple Slicer
#
# This script parses iTunes Connect financial reports and splits sales
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

import sys, os, re, csv, locale
import apple
from decimal import Decimal
from datetime import datetime

# CONFIGURATION

# ISO code of local currency into which foreign sales amounts should be converted
local_currency = 'EUR'

# desired locale used for formatting dates and prices
locale.setlocale(locale.LC_ALL, 'de_DE')

# name of CSV file in which currency exchange rates are listed - can be downloaded from iTunes Connect's
# "Payments & Financial Reports" page and needs to match the financial reports' date range
currency_data_filename = 'financial_report.csv'

# -------------------------------------------------------------------------------------------------------------------------------------

def format_date(date_str):
    """Formats an US-style date string according to the default format of the current locale."""
    return datetime.strptime(date_str,"%m/%d/%Y").strftime('%x')

def format_currency(number):
    """Format a number according to the currency format of the current locale but without the currency symbol.""" 
    return locale.currency(number, False, True)

def parse_currency_data(filename):
    """Parse exchange rate and taxation factor (relevant f. ex. for JPY revenue) for each currency listed in the given file."""

    d = {}

    try:
        f = open(filename, 'r')
    except IOError:
      print 'Exchange rates data file missing: "%s"' % filename
      print 'You can download this file from iTunes Connect\'s "Payments & Financial Reports" page'
      sys.exit(1)

    line = 0
    for fields in csv.reader(f, delimiter = ','):
        line = line + 1

        # make sure it is a valid file by examining the column count of the header in line 3
        if line == 3:
            if len(fields) == 11:
                print 'Aborting: You seem to have downloaded a pending month\'s ' + currency_data_filename
                print 'Such reports contain estimated figures and should not be used for invoicing'
                sys.exit(1)

            if len(fields) != 12:
                print 'Aborting: Invalid column count in ' + currency_data_filename
                sys.exit(1)

        # skip all lines that don't contain financial data
        if line < 4 or len(fields) != 12:
            continue

        # extract currency symbol from parentheses
        r = re.search('\(([A-Z]{3})\)$', fields[0])
        if not r:
            print 'Aborting: Encountered line without a valid currency symbol in ' + currency_data_filename
            sys.exit(1)
        currency = r.group(1)
 
        exchange_rate = float(fields[8].replace(',', ''))
        amount_pre_tax = float(fields[3].replace(',', ''))
        amount_after_tax = float(fields[7].replace(',', ''))
        tax = amount_pre_tax - amount_after_tax
        tax_factor = 1.0 - abs(tax / amount_pre_tax)

        d[currency] = exchange_rate, tax_factor

    f.close()

    return d

def parse_financial_reports(workingdir):
    """Parse the sales listed in all iTunes Connect financial reports in the given directory and group them by country and product."""

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
                date_range = format_date(line[0]) + ' - ' + format_date(line[1])

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
            # in the sales reports but the corresponding exchange rate is labelled "USD - RoW" - a pragmatic way of identifying
            # those "RoW" countries is to inspect the filename of the sales report
            if "_WW." in filename and currency == "USD":
              currencies[countrycode] = "USD - RoW"

        f.close()

    # break if we didn't read any meaningful data
    if not countries:
      print 'No valid iTunes Connect financial reports (*.txt) found in ' + workingdir
      sys.exit(1)

    return countries, currencies, date_range 

def print_sales_by_corporation(sales, currencies):
    """Print sales grouped by Apple subsidiaries, by countries in which the sales have been made and by products sold."""

    corporations = {}

    for country in sales:
        corporations.setdefault(apple.corporation(country), {})[country] = sales[country]

    for corporation in corporations:
        corporation_sum = Decimal(0)
        print '\n\n' + apple.address(corporation)

        for countrycode in corporations[corporation]:
            country_currency = currencies[countrycode]
            products_sold = corporations[corporation][countrycode]

            print '\nSales in {0} ({1})'.format(apple.countryname(countrycode), countrycode)
            print '\tQuantity\tProduct\tAmount\tExchange Rate\tAmount in ' + local_currency

            for product in products_sold:
                exchange_rate = Decimal('1.00000')
                quantity, amount = products_sold[product]
                amount_in_local_currency = amount

                if not country_currency == local_currency:
                    exchange_rate, tax_factor = currency_data[country_currency]
                    amount_in_local_currency = amount * Decimal(exchange_rate) * Decimal(tax_factor)

                    # subtract local tax(es) if applicable in country (f. ex. in JPY)
                    amount -= amount - amount * Decimal(tax_factor)

                print '\t{0}\t{1}\t{2} {3}\t{4}\t{5} {6}'.format(quantity, product, country_currency, format_currency(amount),
                exchange_rate, format_currency(amount_in_local_currency), local_currency.replace('EUR', '€'))

                corporation_sum += amount_in_local_currency

        print '\n{0} Total:\t{1} {2}'.format(corporation, format_currency(corporation_sum), local_currency.replace('EUR', '€'))

# -------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Apple Slicer'
        print 'Usage: ' + sys.argv[0] + ' <directory>'
        print 'Directory must contain iTunes Connect financial reports (*.txt) and a file named "' + currency_data_filename + '"'
        print 'which contains matching currency data downloaded from iTunes Connect\'s "Payments & Financial Reports" page'
        sys.exit(1)

    workingdir = sys.argv[1]

    currency_data = parse_currency_data(workingdir + '/' + currency_data_filename)

    sales, currencies, date_range = parse_financial_reports(workingdir)

    print 'Sales date: ' + date_range,

    print_sales_by_corporation(sales, currencies)

    sys.exit(0)
