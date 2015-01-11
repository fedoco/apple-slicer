# -*- coding: utf-8 -*-

# Apple Slicer
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

# List of countries handled by Apple USA and each of Apple's (currently four) foreign subsidiaries.
# Information is taken from Schedule 2, Exhibit A of Apple's "iOS / Mac OS X Paid Applications" contract as effecive of January, 2015.

australia = {
'AU': 'Australia',
'NZ': 'New Zealand'
}

canada = {
'CA': 'Canada' 
}

europe = {
'AL': 'Albania',
'DZ': 'Algeria',
'AO': 'Angola',
'AM': 'Armenia',
'AT': 'Austria',
'AZ': 'Azerbaijan',
'BH': 'Bahrain',
'BY': 'Belarus',
'BE': 'Belgium',
'BJ': 'Benin',
'BT': 'Bhutan',
'BW': 'Botswana',
'BN': 'Brunei',
'BG': 'Bulgaria',
'BF': 'Burkina-Faso',
'KH': 'Cambodia',
'CV': 'Cape Verde',
'TD': 'Chad',
'CN': 'China',
'CD': 'Republic of Congo',
'HR': 'Croatia',
'CY': 'Cyprus',
'CZ': 'Czech Republic',
'DK': 'Denmark',
'EG': 'Egypt',
'EE': 'Estonia',
'FJ': 'Fiji',
'FI': 'Finland',
'FR': 'France',
'GM': 'Gambia',
'DE': 'Germany',
'GH': 'Ghana',
'GR': 'Greece',
'GW': 'Guinea-Bissau',
'HK': 'Hong Kong',
'HU': 'Hungary',
'IS': 'Iceland',
'IN': 'India',
'ID': 'Indonesia',
'IE': 'Ireland',
'IL': 'Israel',
'IT': 'Italy',
'JO': 'Jordan',
'KZ': 'Kazakhstan',
'KE': 'Kenya',
'KR': 'Korea',
'KW': 'Kuwait',
'KG': 'Kyrgyzstan',
'LA': 'Laos',
'LV': 'Latvia',
'LB': 'Lebanon',
'LR': 'Liberia',
'LT': 'Lithuania',
'LU': 'Luxembourg',
'MO': 'Macao',
'MK': 'Macedonia',
'MG': 'Madagascar',
'MW': 'Malawi',
'MY': 'Malaysia',
'ML': 'Mali',
'MT': 'Republic of Malta',
'MR': 'Mauritania',
'MU': 'Mauritius',
'FM': 'Federal States of Micronesia',
'MD': 'Moldova',
'MN': 'Mongolia',
'MZ': 'Mozambique',
'NA': 'Namibia',
'NP': 'Nepal',
'NL': 'Netherlands',
'NE': 'Niger',
'NG': 'Nigeria',
'NO': 'Norway',
'OM': 'Oman',
'PK': 'Pakistan',
'PW': 'Palau',
'PG': 'Papua New Guinea',
'PH': 'Philippines',
'PL': 'Poland',
'PT': 'Portugal',
'QA': 'Qatar',
'RO': 'Romania',
'RU': 'Russia',
'ST': 'Sao Tome e Principe',
'SA': 'Saudi Arabia',
'SN': 'Senegal',
'SC': 'Seychelles',
'SL': 'Sierra Leone',
'SG': 'Singapore',
'SK': 'Slovakia',
'SI': 'Slovenia',
'SB': 'Solomon Islands',
'ZA': 'South Africa',
'ES': 'Spain',
'LK': 'Sri Lanka',
'SZ': 'Swaziland',
'SE': 'Sweden',
'CH': 'Switzerland',
'TW': 'Taiwan',
'TJ': 'Tajikistan',
'TZ': 'Tanzania',
'TH': 'Thailand',
'TN': 'Tunisia',
'TR': 'Turkey',
'TM': 'Turkmenistan',
'AE': 'United Arab Emirates',
'UG': 'Uganda',
'UA': 'Ukraine',
'GB': 'United Kingdom',
'UZ': 'Uzbekistan',
'VN': 'Vietnam',
'YE': 'Yemen',
'ZW': 'Zimbabwe'
}

japan = {
'JP': 'Japan'
}

us = {
'AR': 'Argentinia',
'AI': 'Anguilla',
'AG': 'Antigua & Barbuda',
'BS': 'Bahamas',
'BB': 'Barbados',
'BZ': 'Belize',
'BM': 'Bermuda',
'BO': 'Bolivia',
'BR': 'Brazil',
'VG': 'British Virgin Islands',
'KY': 'Cayman Islands',
'CL': 'Chile',
'CO': 'Colombia',
'CR': 'Costa Rica',
'DM': 'Dominica',
'DO': 'Dominican Republic',
'EC': 'Ecuador',
'SV': 'El Salvador',
'GD': 'Grenada',
'GY': 'Guyana',
'GT': 'Guatemala',
'HN': 'Honduras',
'JM': 'Jamaica',
'MX': 'Mexico',
'MS': 'Montserrat',
'NI': 'Nicaragua',
'PA': 'Panama',
'PY': 'Paraguay',
'PE': 'Peru',
'KN': 'St. Kitts & Nevis',
'LC': 'St. Lucia',
'VC': 'St. Vincent & The Grenadines',
'SR': 'Suriname',
'TT': 'Trinidad & Tobago',
'TC': 'Turks & Caicos',
'UY': 'Uruguay',
'VE': 'Venezuela',
'US': 'United States'
}

corporations = [australia, canada, europe, japan, us]

def corporation(cc):
    """Get Apple subsidiary handling sales of the given country"""
    if cc in australia: return 'AU'
    if cc in canada: return 'CA'
    if cc in europe: return 'EU'
    if cc in japan: return 'JP'
    if cc in us: return 'US'
    raise LookupError('Unknown country code "%s"' % cc)

def countryname(cc):
    """Get name of country with given country code"""
    for corporation in corporations:
        if cc in corporation:
            return corporation[cc]
    raise LookupError('Unknown country code "%s"' % cc)

def address(corporation):
    """Get billing address of Apple subsidiary with given handle"""
    if corporation == 'AU':
        return """Apple Pty Limited
Level 13, Capital Centre
255 Pitt Street
Sydney South NSW 2000
Australia"""
    elif corporation == 'CA':
        return """Apple Canada, Inc.
7495 Birchmount Road
Markham, ON L3R 5G2
Canada"""
    elif corporation == 'EU':
        return """iTunes S.à.r.l.
31-33 rue Sainte Zithe
2763 Luxembourg
Luxembourg
VAT ID: LU20165772"""
    elif corporation == 'JP':
        return """iTunes K.K.
〒 163-1480
3-20-2 Nishi-Shinjuku, Shinjuku-ku, Tokyo
Japan"""
    elif corporation == 'US':
        return """Apple Inc.
1 Infinite Loop
Cupertino, CA 95014
U.S.A."""
    raise LookupError('Unknown Apple corporation "%s"' % corporation)
