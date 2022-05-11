from csvw.dsv import reader

from linglit import util

CFG_PATH = util.CFG_PATH / 'langsci'
BIBTOOL_RSC = CFG_PATH / 'bibtool.rsc'
LNAME_MAP = {
    'Logoori': 'logo1258',
    'Līkpākpáln': 'konk1269',
    'Totoró Namtrik': 'toto1306',
    'Jóola Fóoñi': 'jola1263',
    'Mojeño Trinitario': 'trin1274',
    'Bùlì': 'buli1254',
    'Sereer-Siin': 'sere1260',  # 45
    'Fròʔò': 'tagw1240',  # 45
    'Siwi Berber': 'siwi1239',  # 41
    'Hoocąk': 'hoch1243',  # 40
    'Veraa': 'vera1241',  # 39
    'Early Vedic': '',  # 36
    'Greek, Attic': 'atti1240',  # 34
    'Late Modern Swedish': '',  # 30
    'Sembiran Balinese': '',  # 24
    'Beirut/Damascus': '',  # 24
    'Tsotsil': 'tzot1259',  # 23
    'Kakataibo': 'cash1251',  # 23
    'Bantu': '',  # 22
    'North Sámi': '',  # 22
    'Nganasan  (Avam)': 'avam1236',  # 21
    'Lycopolitan Coptic': 'lyco1237',  # 20
    'inglês': 'stan1293',  # 18
    'Greek, Classical|(': 'anci1242',  # 18
    'Greek, Homeric': 'anci1242',  # 17
    'Greek, Homeric|(': 'anci1242',  # 17
    'Greek, Cypriot': 'cypr1249',  # 17
    "K'abeena": 'alab1254',  # 16
    'francês': 'stan1290',  # 16
    'Luragooli': 'logo1258',  # 15
    'Rhonga': 'rong1268',  # 15
    'Sino-Japanese': '',  # 14
    'Hellenic': '',  # 14
    'Slavonic': 'chur1257',  # 13
    'Greek, Doric': 'dori1248',  # 13
    'Yixing Chinese': '',  # 13
    'Standard German': 'stan1295',  # 13
    'Allemand': 'stan1295',  # 12
    'Ioway, Otoe-Missouria': 'iowa1245',  # 12
    'Tanti Dargwa': '',  # 12
    'Singapore Malay': 'mala1479',  # 42
    'Early Modern Japanese': 'nucl1643',  # 23
    'Gulf Pidgin Arabic': 'pidg1248',  # 4
    'Nêlêmwa': 'kuma1276',  # 4
    'Övdalian': 'elfd1234',  # 15
    'Present-day Swedish': 'stan1279',  # 14
    'Älvdalen (Os)': 'elfd1234',  # 11
    'Sollerön (Os)': 'soll1234',  # 6
    'Orsa (Os)': 'orsa1234',  # 6
    'Nama-Damara': 'dama1270',  # 5
    'Nǀuuki': 'nuuu1241',  # 5
    r'\LangTurk': 'nucl1301',  # 5
    r'\LangTok': 'tokp1240',  # 4
    r'\LangVed': 'sans1269',  # 4
    r'\LangJap': 'nucl1643',  # 4
    r'\LangQue': 'quec1387',  #
    r'\LangMang': 'mang1381',  # 3
    r'\LangMand': 'mand1415',  # 3
    'Standard Greek': 'mode1248',  # 3
    'Överkalix (Kx)': 'arch1246',  # 3
    'Donno Sɔ': 'donn1239',  # 3
    'Ḥassāniyya': 'hass1238',  # 3
}


def iter_texfile_titles():
    yield from reader(CFG_PATH / 'texfile_titles.tsv', delimiter='\t', dicts=True)
