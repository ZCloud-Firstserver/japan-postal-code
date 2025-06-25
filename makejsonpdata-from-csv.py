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
    >>> print normalize_area_ja(u'川上町（３６４９、３６６１、３６６', u'')
    川上町
    """
    if area_ja == '以下に掲載がない場合': return ''
    if re.search(u'の次に.*がくる', area_ja): return u''
    # loadAddressesでこのロジックが直接処理されるため、ここでのreturnは残りのケース用です。
    if re.search(u'^[^\uff08]*\uff09$', area_ja): return main_area_ja
    if re.search(u'^[^\uff08]*\u3001[^\uff08]*\uff09$', area_ja): return main_area_ja
    if main_area_ja and u'（' not in area_ja and u'、' in area_ja: return main_area_ja

    words = area_ja # area_ja の内容でwordsを初期化

    # 階数表記の処理を先に実行（例: （１０階） -> １０階）
    words = re.sub(u'（([０-９]+階)）', u'\\1', words)

    # 開き括弧以降の補足情報を確実に削除
    # re.sub(r'（.*$', '', words) の代わりにstring.splitを使用
    if u'（' in words:
        words = words.split(u'（', 1)[0] # 最初の開き括弧で分割し、その前の部分のみを取得

    # 開き括弧がない単独の閉じ括弧を削除するロジック (例: '番地）' -> '番地')
    if u'（' not in words and u'）' in words:
        words = words.replace(u'）', u'')
    
    words = words.replace(u'　', u'') # 全角スペースを削除

    return words

def normalize_area_en(area_ro):
    """ Normalize english area name
    >>> normalize_area_en('KITA2-JONISHI(1-19-CHOME)')
    'Kita2-jonishi'
    >>> normalize_area_en('KAKUNODATEMACHI SONODA')
    'Kakunodatemachi Sonoda'
    """
    words = re.sub(r'\((\d+)-KAI\)', r' \1F', area_ro)
    # 末尾の閉じ括弧を削除する処理を追加（もし開き括弧がない場合も考慮）
    words = re.sub(r'\)$', '', words) # 文字列の末尾にある閉じ括弧を削除
    words = re.sub(r'\(.*$', '', words) # 開き括弧から末尾までを削除 (元のロジック)
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

    # CSVファイルをUTF-8で開く際に、universal newlines modeを使用
    # Python 2の場合、'r'モードでencodingを指定し、bytesではなくUnicodeとして読み込むのが推奨
    with open(file_name, 'r') as f: # 'rb'から'r'に変更
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            # csv.readerが返す要素は、Python 2ではバイト文字列ですが、
            # open(..., 'r', encoding='utf-8')のようにすればUnicode文字列になります。
            # ただし、現状のPython 2環境で`open`関数に`encoding`引数がない可能性も考慮し、
            # `row`の要素を直接デコードします。
            
            # 各要素をUTF-8からUnicode文字列にデコード (Python 2の一般的な対応)
            row = [s.decode('utf-8') for s in row] 
            
            postalcode, prefecture_ja, city_ja_raw, area_ja_raw, prefecture_ro, city_ro, area_ro = row
            street_ja, street_ro, street_en = '', '', '' # これらのフィールドはCSVに存在しないため、空で初期化

            postalcode3   = postalcode[0:3]
            prefecture_id = prefecture_ja_to_prefecture_id(prefecture_ja)
            prefecture_en = normalize_prefecture_en(prefecture_ro)
            city_ja = normalize_city_ja(city_ja_raw) # 正規化された市区町村名
            city_en = normalize_city_en(city_ro)

            # 「X番地）」のようなパターンをチェックし、直接area_jaとarea_enを設定する
            # 正規表現の代わりに、より確実な文字列メソッドを使用
            # ここでは、CSVから読み込んだ生の `area_ja_raw` を再度チェックします
            # そして、この条件にマッチしかつcity_jaに正規化された場合に、そのエントリを追加しないようにする
            should_exclude_entry = False
            if area_ja_raw.endswith(u'）') and u'（' not in area_ja_raw:
                # このパターンに合致した場合、これを「無視」したいエントリと見なす
                # ただし、他の情報（例えば「川上町」）を優先するため、このエントリは追加しない
                should_exclude_entry = True
                
                # 念のため、ここでarea_jaとarea_enをcity_ja/enに設定するロジックも残しておきます。
                # もしこのエントリをフィルタリングしない他のケースがある場合のため。
                area_ja = city_ja 
                area_en = city_en 
            else:
                # 通常のnormalize_area_ja/enのロジックを適用
                temp_main_area_ja = ''
                temp_main_area_en = ''
                if postalcode3 in addresses and postalcode in addresses[postalcode3]:
                    temp_main_area_ja = addresses[postalcode3][postalcode][0][3]
                    temp_main_area_en = addresses[postalcode3][postalcode][0][6]

                area_ja = normalize_area_ja(area_ja_raw, temp_main_area_ja)

                if area_ja == temp_main_area_ja:
                    area_en = temp_main_area_en
                else:
                    area_en = normalize_area_en(area_ro)

            # エントリを除外すべき場合は、ここでスキップ
            if should_exclude_entry:
                continue # 次の行の処理へ

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
            # addressリストの0番目の要素（郵便番号）でソート
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
