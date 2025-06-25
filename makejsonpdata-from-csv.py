#!/usr/bin/env python
# coding: utf-8
# -*- coding: utf-8 -*-

# dataフォルダ内の郵便番号データをJSONP形式にしてzipdataフォルダ内に保存します
# See: http://www.post.japanpost.jp/zipcode/dl/roman-zip.html
#     wget http://www.post.japanpost.jp/zipcode/dl/roman/ken_all_rome.zip
#     unzip ken_all_rome.zip
#     nkf -Sw KEN_ALL_ROME.CSV > KEN_ALL_ROME.UTF8.CSV
#     python ./makejsonpdata-from-csv.py KEN_ALL_ROME.UTF8.CSV

import sys
import csv
import re
reload(sys)
sys.setdefaultencoding("UTF-8")

prefmap_ja = [
    None,       '北海道',   '青森県',   '岩手県',   '宮城県',
    '秋田県',   '山形県',   '福島県',   '茨城県',   '栃木県',
    '群馬県',   '埼玉県',   '千葉県',   '東京都',   '神奈川県',
    '新潟県',   '富山県',   '石川県',   '福井県',   '山梨県',
    '長野県',   '岐阜県',   '静岡県',   '愛知県',   '三重県',
    '滋賀県',   '京都府',   '大阪府',   '兵庫県',   '奈良県',
    '和歌山県', '鳥取県',   '島根県',   '岡山県',   '広島県',
    '山口県',   '徳島県',   '香川県',   '愛媛県',   '高知県',
    '福岡県',   '佐賀県',   '長崎県',   '熊本県',   '大分県',
    '宮崎県',   '鹿児島県', '沖縄県'
]

prefmap_en = [
    None,        'Hokkaido',  'Aomori',    'Iwate',    'Miyagi',
    'Akita',     'Yamagata',  'Fukushima', 'Ibaraki',  'Tochigi',
    'Gumma',     'Saitama',   'Chiba',     'Tokyo',    'Kanagawa',
    'Niigata',   'Toyama',    'Ishikawa',  'Fukui',    'Yamanashi',
    'Nagano',    'Gifu',      'Shizuoka',  'Aichi',    'Mie',
    'Shiga',     'Kyoto',     'Osaka',     'Hyogo',    'Nara',
    'Wakayama',  'Tottori',   'Shimane',   'Okayama',  'Hiroshima',
    'Yamaguchi', 'Tokushima', 'Kagawa',    'Ehime',    'Kochi',
    'Fukuoka',   'Saga',      'Nagasaki',  'Kumamoto', 'Oita',
    'Miyazaki',  'Kagoshima', 'Okinawa'
]

def prefecture_ja_to_prefecture_id(prefecture_ja):
    """ Convert prefecture name in Japanese to PrefectureID
    >>> prefecture_ja_to_prefecture_id('北海道')
    1
    >>> prefecture_ja_to_prefecture_id('東京都')
    13
    >>> prefecture_ja_to_prefecture_id('沖縄県')
    47
    """
    return prefmap_ja.index(prefecture_ja)

def normalize_prefecture_en(prefecture_ro):
    """ Normalize english prefecture name
    >>> normalize_prefecture_en('HOKKAIDO')
    'Hokkaido'
    >>> normalize_prefecture_en('TOKYO TO')
    'Tokyo'
    >>> normalize_prefecture_en('SAITAMA KEN')
    'Saitama'
    >>> normalize_prefecture_en('KYOTO FU')
    'Kyoto'
    """
    words = prefecture_ro.split(' ')
    words = map(lambda word: word.capitalize(), words)
    return words[0]

def normalize_city_ja(city_ja):
    u""" Normalize japanese city name
    >>> print normalize_city_ja('球磨郡　五木村')
    球磨郡五木村
    >>> print normalize_city_ja('名古屋市　千種区')
    名古屋市千種区
    """
    return city_ja.replace('　', '')

def normalize_city_en(city_ro):
    """ Normalize english city name
    >>> normalize_city_en('KUMA GUN ITSUKI MURA')
    'Itsuki-mura, Kuma-gun'
    >>> normalize_city_en('OSAKA SHI CHUO KU')
    'Chuo-ku, Osaka-shi'
    >>> normalize_city_en('NAGOYA SHI CHIKUSA KU')
    'Chikusa-ku, Nagoya-shi'
    >>> normalize_city_en('SEMBOKU SHI')
    'Semboku-shi'
    >>> normalize_city_en('AOMORI SHI')
    'Aomori-shi'
    >>> normalize_city_en('DATE GUN KORI MACHI')
    'Kori-machi, Date-gun'
    >>> normalize_city_en('OSAKI SHI')
    'Osaki-shi'
    >>> normalize_city_en('ISHIKARI GUN TOBETSU CHO')
    'Tobetsu-cho, Ishikari-gun'
    >>> normalize_city_en('SAIHAKU GUN HIEZU SON')
    'Hiezu-son, Saihaku-gun'
    """

    words = city_ro.split(' ')
    words = map(lambda word: word.capitalize(), words)
    sections = []
    section_words = []
    for word in words:
        if word in ['Shi', 'Ku', 'Gun', 'Cho', 'Machi', 'Son', 'Mura']:
            section_words.append(''.join(['-', word.lower()]))
            sections.append(''.join(section_words))
            section_words = []
        else:
            section_words.append(word)

    if 0 < len(section_words):
        sections.append(' '.join(section_words))

    sections.reverse()
    city_en = ', '.join(sections)
    return city_en

def normalize_area_ja(area_ja, main_area_ja):
    u""" Normalize japanese area name
    >>> normalize_area_ja('以下に掲載がない場合', '')
    ''
    >>> print normalize_area_ja('北二条西（１〜１９丁目）', '')
    北二条西
    >>> print normalize_area_ja('角館町　薗田', '')
    角館町薗田
    """
    if area_ja == '以下に掲載がない場合': return ''
    if re.search(r'の次に.*がくる', area_ja): return ''
    if re.search(r'^[^（]*）$', area_ja): return main_area_ja
    if re.search(r'^[^（]*、[^（]*）$', area_ja): return main_area_ja
    if main_area_ja and '（' not in area_ja and '、' in area_ja: return main_area_ja
    words = re.sub(r'（([０-９]+階)）', r'\1', area_ja)
    words = re.sub(r'（.*$', '', words)
    words = words.replace('　', '')

    return words

def normalize_area_en(area_ro):
    """ Normalize english area name
    >>> normalize_area_en('KITA2-JONISHI(1-19-CHOME)')
    'Kita2-jonishi'
    >>> normalize_area_en('KAKUNODATEMACHI SONODA')
    'Kakunodatemachi Sonoda'
    """
    words = re.sub(r'\((\d+)-KAI\)', r' \1F', area_ro)
    words = re.sub(r'\(.*$', '', words)
    words = words.split(' ')
    words = map(lambda word: word.capitalize(), words)
    return ' '.join(words).strip()

def address_in_english(address):
    postalcode, prefecture_id, city_ja, area_ja, street_ja, city_en, area_en, street_en = address
    address_en = [city_en, prefmap_en[prefecture_id]]
    if 0 < len(street_en): address_en.insert(0, street_en)
    if 0 < len(area_en):   address_en.insert(0, area_en)
    name = ', '.join(address_en) + ', Japan ' + postalcode[0:3] + '-' + postalcode[3:7]
    return name

def address_in_japanese(address):
    postalcode, prefecture_id, city_ja, area_ja, street_ja, city_en, area_en, street_en = address
    name = postalcode[0:3] + '-' + postalcode[3:7] + ' ' + prefmap_ja[prefecture_id] + city_ja + area_ja + street_ja
    return name

def loadAddresses(file_name):
    addresses = {}

    with open(file_name, 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            postalcode, prefecture_ja, city_ja, area_ja, prefecture_ro, city_ro, area_ro = row
            street_ja, street_ro, street_en = '', '', ''
            original_city_ja = city_ja

            postalcode3   = postalcode[0:3]
            prefecture_id = prefecture_ja_to_prefecture_id(prefecture_ja)
            prefecture_en = normalize_prefecture_en(prefecture_ro)
            city_ja = normalize_city_ja(city_ja)
            city_en = normalize_city_en(city_ro)

            if postalcode3 in addresses and postalcode in addresses[postalcode3]:
                main_area_ja = addresses[postalcode3][postalcode][0][3] # 最初のarea_ja
                main_area_en = addresses[postalcode3][postalcode][0][6] # 最初のarea_en
            else:
                main_area_ja = ''
                main_area_en = ''

            area_ja = normalize_area_ja(area_ja, main_area_ja)

            if area_ja == main_area_ja:
                area_en = main_area_en
            else:
                area_en = normalize_area_en(area_ro)

            # 日本郵便株式会社提供データのローマ字表記は、以下の「ローマ字変換仕様」に基づき変換されている。
            # https://www.post.japanpost.jp/zipcode/dl/roman_shiyou.pdf
            #
            # 国土地理院の「地名等の英語表記規程」では、以下のとおりとなっており、
            # こちらのほうが一般的に通用しているローマ字表記と思われる。
            # > 表音のローマ字表記が「ou」「oo」「uu」となるときに、対応する元の漢字が一文字の場合には
            # > それぞれ「o」「o」「u」に短縮するが、二文字に分かれる場合には短縮しない。
            # > ただし、短縮する表記が通用している場合には、短縮してもよい。
            # https://www.gsi.go.jp/common/000138865.pdf
            #
            # そのため、暫定的に、例外ルールとして定義していくこととする。

            if postalcode in ['6800034', '7080061'] and area_ja == '元魚町' and area_en == 'Motoomachi':
                area_en = 'Motouomachi'

            if postalcode == '8171223' and area_ja == '豊玉町横浦' and area_en == 'Toyotamamachi Yokora':
                area_en = 'Toyotamamachi Yokoura'

            address = [postalcode, prefecture_id, city_ja, area_ja, street_ja, city_en, area_en, street_en]
            # print "%-90s          %-s" % (address_in_english(address), address_in_japanese(address))

            if postalcode3 not in addresses: addresses[postalcode3] = {}
            if postalcode  not in addresses[postalcode3]: addresses[postalcode3][postalcode] = []

            if address not in addresses[postalcode3][postalcode]:
                addresses[postalcode3][postalcode].append(address)

    return addresses

def writeAddressesIntoJsonpFiles(addresses, path_prefix, callback_name):
    postalcode3_list = addresses.keys()
    postalcode3_list.sort()

    for postalcode3 in postalcode3_list:
        postalcode_list = addresses[postalcode3].keys()
        postalcode_list.sort()

        record_sets = []
        for postalcode in postalcode_list:
            records = []
            for address in sorted(addresses[postalcode3][postalcode], key=lambda a: a[0]):
                record = '[{0[1]},"{0[2]}","{0[3]}","{0[4]}","{0[5]}","{0[6]}","{0[7]}"]'.format(address)
                records.append(record)
            record_sets.append('"%s":[%s]' % (postalcode, ','.join(records)))

        jsonp = callback_name + "({\n\t" + ",\n\t".join(record_sets) + "\n})\n"

        path = path_prefix + postalcode3 + '.js'
        f = open(path, "w")
        f.write(jsonp)
        f.close()

if __name__ == "__main__":

    if '--test' in sys.argv:

        import doctest
        doctest.testmod()

    else:

        path_prefix = 'zipdata/zip-'
        callback_name = 'zipdata'

        if 1 < len(sys.argv):
            file_name = sys.argv[1]
        else:
            file_name = 'KEN_ALL_ROME.UTF8.CSV'

        addresses = loadAddresses(file_name)

        writeAddressesIntoJsonpFiles(addresses, path_prefix, callback_name);
