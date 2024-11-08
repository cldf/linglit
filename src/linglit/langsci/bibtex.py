"""
Functionality to read LSP BibTeX files.
"""
import re
import typing
import logging
import pathlib
import subprocess
import unicodedata

from pybtex import database
from clldutils.source import Source
from clldutils.misc import slug
from clldutils.path import ensure_cmd

from .latex import simple_to_text
from . import cfg

__all__ = ['iter_bib', 'normalize_key']

# Invalid author lists (and fixes):
NAMES = {
    'Trommler, Friederike, Hammann, Marcus': 'Trommler, Friederike and Hammann, Marcus',
    'De Decker, Paul, Nycz, Jennifer': 'De Decker, Paul and Nycz, Jennifer',
    'SkL, Holm. B 74, 4\\textsuperscript{o} = Brøndum-Nielsen, Johs':
        'SkL, Holm. B and Brøndum-Nielsen, Johs',
    'De Marneffe, Marie-Catherine, Timothy Dozat, Natalia Silveira, Katri Haverinen, Filip Ginter, '
    'Joakim Nivre,':
        'De Marneffe, Marie-Catherine and Timothy Dozat and Natalia Silveira and Katri Haverinen '
        'and Filip Ginter and Joakim Nivre,',
    'Igoo Ribaa, Mark Post,Ilii Ribaa, Miilii Nodu, Kenjum Bagra, Bomcak Ribaa, Toomoo Ribaa, '
    'Notoo Aado, Dambom Keenaa':
        'Igoo Ribaa and Mark Post and Ilii Ribaa and Miilii Nodu and Kenjum Bagra and Bomcak Ribaa '
        'and Toomoo Ribaa and Notoo Aado and Dambom Keenaa',
    'Ringe, Donald A., Jr.,':
        'Ringe, Donald A. Jr.,',
    'Yahalom-Mack, Naama, Eliyahu-Behar, Adi':
        'Yahalom-Mack, Naama and Eliyahu-Behar, Adi',
    'Vajrabhaya, P., Kapatsinski, Vsevolod':
        'Vajrabhaya, P. and Kapatsinski, Vsevolod',
    'Kroch, Anthony, Santorini, Beatrice':
        'Kroch, Anthony and Santorini, Beatrice',
    'Féry, Caroline, Fanselow, Gisbert':
        'Féry, Caroline and Fanselow, Gisbert',
    'Dan Velleman, David Beaver, Emilie Destruel, Dylan Bumford, Edgar Onea, Liz Coppock':
        'Dan Velleman and David Beaver and Emilie Destruel and Dylan Bumford and Edgar Onea and '
        'Liz Coppock',
    'Riad, Tomas, & Gussonhoven, Carlos':
        'Riad, Tomas and Gussonhoven, Carlos',
    "B\\'{e}r\\'{e}nice Bellina, Elisabeth A Bacus, Thomas Oliver Pryce, Jan Wisseman Christie":
        "B\\'{e}r\\'{e}nice Bellina and Elisabeth A Bacus and Thomas Oliver Pryce and Jan "
        "Wisseman Christie",
    "D'Alessandro, Roberta \\& Fischer, Susann \\& Hrafnbjargarson, Gunnar Hrafn":
        "D'Alessandro, Roberta and Fischer, Susann and Hrafnbjargarson, Gunnar Hrafn",
    'Mitchell, Rosamond, Tracy-Ventura, Nicole':
        'Mitchell, Rosamond and Tracy-Ventura, Nicole',
    'Juan-Garau, Maria., Joana Salazar-Noguera,':
        'Juan-Garau, Maria and Joana Salazar-Noguera',
    'Andr{\\\'e} M{\\"u}ller, Annkathrin Wett, Viveka Velupillai, Julia Bischoffberger, '
    'Cecil H. Brown, Eric W. Holman, Sebastian Sauppe, Zarina Molochieva, Pamela Brown, '
    'Harald Hammarstr{\\"o}m, Oleg Belyaev, Johann-Mattis List, Dik Bakker, Dmitry Egorov, '
    'Matthias Urban, Robert Mailhammer, Agustina Carrizo, Matthew S. Dryer, Evgenia Korovina, '
    'David Beck, Helen Geyer, Patience Epps, Anthony Grant,':
        'Andr{\\\'e} M{\\"u}ller and Annkathrin Wett and Viveka Velupillai and Julia '
        'Bischoffberger and Cecil H. Brown and Eric W. Holman and Sebastian Sauppe and Zarina '
        'Molochieva and Pamela Brown and Harald Hammarstr{\\"o}m and Oleg Belyaev and '
        'Johann-Mattis List and Dik Bakker and Dmitry Egorov and Matthias Urban and Robert '
        'Mailhammer and Agustina Carrizo and Matthew S. Dryer and Evgenia Korovina and David Beck '
        'and Helen Geyer and Patience Epps and Anthony Grant',
}

GENRE_MAP = {
    "report": "techreport",
    "thesis": "phdthesis",
    "webpage": "online",
    "mphillthesis": "mastersthesis",
    "unpublished": "misc",
    "unpbulished": "misc",
    "mvbook": "book",
    "url": "online",
    "unpub": "misc",
    "data": "misc",
    "other": "misc",
    "customa": "misc",
    "mathesis": "mastersthesis",
    "hmisc": "misc",
}

FIELD_MAP = {
    "journaltitle": "journal",
    "ids": "ids",
    "urldate": "",
    "isbn": "isbn",
    "subtitle": "subtitle",
    "edition": "edition",
    "type": "type",
    "institution": "institution",
    "shorttitle": "",
    "month": "",
    "howpublished": "howpublished",
    "issn": "issn",
    "abstract": "",
    "booksubtitle": "booksubtitle",
    "issue": "issue",
    "organization": "organization",
    "venue": "venue",
    "langid": "",
    "annote": "",
    "annotation": "",
    "language": "",
    "numpages": "pages",
    "stableurl": "url",
    "addendum": "",
    "shortauthor": "",
    "chapter": "chapter",
    "file": "",
    "shortjournal": "journal",
    "optaddress": "",
    "call-number": "",
    "sortyear": "",
    "lgcode": "lgcode",
    "options": "",
    "namea": "",
    "maintitle": "",
    "acmid": "",
    "pubstate": "",
    "opturl": "url",
    "translator": "",
    "eprint": "eprint",
    "related": "",
    "alnumcodes": "",
    "languoidbase_ids": "",
    "numberofpages": "pages",
    "day": "",
    "bib": "",
    "eventtitle": "eventtitle",
    "optmonth": "",
    "collaborator": "",
    "optchapter": "",
    "titleaddon": "",
    "sortkey": "",
    "serie": "series",
    "optnote": "",
    "editors": "editor",
    "relatedstring": "",
    "lastchecked": "",
    "issuetitle": "",
    "optannote": "",
    "bdsk-url-2": "",
    "autheditor": "editor",
    "biburl": "",
    "opturldate": "",
    "bdsk-file-2": "",
    "read": "",
    "key": "key",
    "bibsource": "",
    "optkey": "",
    "pagetotal": "pages",
    "lccn": "lccn",
    "origdate": "",
    "sortauthor": "",
    "optnumber": "",
    "place": "address",
    "issue_date": "",
    "hyphenation": "",
    "urlaccessdate": "",
    "adress": "address",
    "archiveprefix": "",
    "version": "version",
    "eid": "",
    "optlocation": "",
    "eprinttype": "",
    "page": "pages",
    "lid": "",
    "chaper": "chapter",
    "author-translation": "",
    "rating": "",
    "creationdate": "",
    "opttype": "",
    "bdsk-file-3": "",
    "eventdate": "",
    "price": "",
    "booktitleaddon": "",
    "collection": "",
    "mendeley-groups": "",
    "urlmonth": "",
    "urlday": "",
    "vol": "volume",
    "optseries": "series",
    "inlg": "inlg",
    "macro_area": "",
    "pmid": "",
    "interhash": "",
    "intrahash": "",
    "oldhhfn": "",
    "src": "",
    "pdf": "",
    "editora": "editor",
    "editoratype": "",
    "sorttitle": "",
    "hhtype": "hhtype",
    "city": "address",
    "added-at": "",
    "optaddendum": "",
    "ozbib_id": "",
    "volumes": "",
    "hal_id": "",
    "hal_version": "",
    "bookauthor": "",
    "xjournal": "",
    "xpublisher": "",
    "xeditor": "",
    "opteditor": "",
    "ee": "",
    "ozbibreftype": "",
    "pubkey": "",
    "originalyear": "",
    "optpublisher": "",
    "journalsubtitle": "",
    "citeulike-article-id": "",
    "posted-at": "",
    "shorthand": "",
    "numer": "number",
    "addres": "address",
    "optxref": "",
    "optvolume": "",
    "groups": "",
    "fn": "",
    "annotate": "",
    "aiatsis_callnumber": "",
    "oclcid": "",
    "url_checked": "",
    "homepage": "",
    "uselessnote": "",
    "more-editors": "",
    "publishers": "publisher",
    "citedin": "",
    "optcrossref": "",
    "optedition": "",
    "primaryclass": "",
    "rights": "rights",
    "yaddress": "",
    "booktitel": "booktitle",
    "typ": "",
    "iso_code": "lgcode",
    "olac_field": "olac_field",
    "wals_code": "wals_code",
    "oclc": "oclc",
    "editorx": "",
    "xisbn": "",
    "aiatsis_code": "aiatsis_code",
    "aiatsis_reference_language": "",
    "accessdate": "",
    "institutions": "institution",
    "issue_year": "",
    "book": "",
    "research_area": "",
    "urlpage": "",
    "optpages": "",
    "quality": "",
    "author-transl": "",
    "origlanguage": "",
    "bootitle": "booktitle",
    "bdsk-file-4": "",
    "vols": "",
    "optbooktitle": "",
    "altauthor": "",
    "optorganization": "",
    "email": "",
    "issuesubtitle": "",
    "optvolumes": "",
    "cfn": "",
    "class_loc": "",
    "document_type": "",
    "mpi_eva_library_shelf": "",
    "optauthor": "",
    "notes": "",
    "ozbibnote": "",
    "asjp_name": "",
    "indexauthor": "",
    "urlx": "",
    "reprint": "",
    "optsubtitle": "",
    "opttitle": "",
    "mainsubtitle": "",
    "issueeditor": "",
    "anote": "",
    "articleno": "",
    "optschool": "",
    "research_sub_area": "",
    "urldsate": "",
    "urlzip": "",
    "origyear": "",
    "postscript": "",
    "editorbtype": "",
    "nourl": "",
    "optshorthand": "",
    "execute": "",
    "urladte": "",
    "eventvenue": "",
    "optrelated": "",
    "optrelatedtype": "",
    "seriestitle": "",
    "optassress": "",
    "db": "",
    "tags": "",
    "affiliation": "",
    "ean": "",
    "status": "",
    "eidtor": "editor",
    "publihers": "publisher",
    "risfield_0_bt": "",
    "paper": "",
    "class": "",
    "double_booktitle": "",
    "numnber": "number",
    "numbers": "number",
    "publihser": "publisher",
    "mpifn": "",
    "subject_headings": "",
    "announced": "",
    "paperbackoptisbn": "",
    "pgaes": "pages",
    "added": "",
    "refdb_id": "",
    "booktitle1": "",
    "addresss": "address",
    "annotex": "",
    "issnx": "",
    "publisherx": "",
    "venuedate": "",
    "editior": "editor",
    "priority": "",
    "part": "part",
    "dddress": "address",
    "opttitleaddon": "",
    "local-noopurl": "",
    "annnote": "",
    "publishing": "",
    "utf_author": "",
    "country": "",
    "subject": "",
    "publication": "",
    "institute": "school",
    "sannote": "",
    "tppubtype": "",
    "scshool": "school",
    "preis": "",
    "opthowpublished": "",
    "lastcheck": "",
    "bdsk-file-5": "",
    "bdsk-file-6": "",
    "bdsk-file-7": "",
    "journa": "journal",
    "source": "",
    "unmatched-authority": "",
    "dewey-call-number": "",
    "library-id": "",
    "size": "",
    "etc": "",
    "adderss": "address",
    "addrss": "address",
    "origtitle": "",
    "origlocation": "",
    "local-url": "",
    "misc": "",
    "longnote": "",
    "uuid": "",
    "introduction": "",
    "entrysubtype": "",
    "optissn": "",
    "verkauf": "",
    "optyear": "",
    "adsnote": "",
    "adsurl": "",
    "titel": "title",
    "optlanguage": "",
    "publsher": "publisher",
    "refid": "",
    "websitetitle": "",
    "booktile": "booktitle",
    "arxivid": "",
    "description": "",
    "ris_reference_number": "",
    "citeulike-linkout-0": "",
    "eventdatet": "",
    "bdsk-url-3": "",
    "bdsk-url-4": "",
    "sssauthor": "",
    "sssbooktitle": "",
    "optstableurl": "",
    "itemartakarmat": "",
    "yomi": "",
    "substitle": "subtitle",
    "bdsk-url": "",
    "types": "",
    "noter": "",
    "orig_": "",
    "title_english": "",
    "alteditor": "",
    "bookstitle": "booktitle",
    "unidentified": "",
    "sorname": "",
    "scool": "school",
    "bootktitle": "booktitle",
    "note_original": "",
    "abbrv": "",
    "confdate": "",
    "xdoi": "",
    "xurl": "",
    "editorb": "",
    "label": "",
    "vollume": "volume",
    "trad": "",
    "library": "",
    "elocation-id": "",
    "pooktitle": "booktitle",
    "attachments": "",
    "shorteditor": "",
    "xxxauthor": "",
    "pubisher": "publisher",
    "translation": "",
    "fnnote": "",
    "autor": "author",
    'modified': '',
    'authauthor': "author",
    'bdsk-url-1': "",
    'optisbn': "",
    'cited': "",
    'comment': "",
    'bilal': "",
    'achilleos': "",
    'xmonth': "",
    'xaddress': "",
    'last_changed': "",
    'urlyear': "",
    'copyright': "",
}


def normalize_key(k):
    return unicodedata.normalize('NFC', k.replace('–', '--').lower())


class LangsciSource(Source):
    """
    Some bibfiles provide fields "IDs" or "ids" which list alternative keys by which a record can
    be cited in the tex files.
    """
    @property
    def alt_keys(self):
        return set([normalize_key(s.strip()) for s in self.get('ids', '').split(',') if s.strip()])


def to_source(key, e):
    def remove_unbalanced_braces(s):
        for o, c in ['()', '{}']:
            if s.count(o) != s.count(c):
                s = s.replace(o, '').replace(c, '')
        return s

    src = LangsciSource.from_entry('x', e) if not isinstance(e, LangsciSource) else e
    src.id = normalize_key(key)
    src.genre = GENRE_MAP.get(src.genre.lower(), src.genre.lower())
    if src.genre == 'phdthesis' and (
            slug(src.get('type', '')) == 'mathesis' or 'M.A.' in src.get('type', '')):
        src.genre = 'mastersthesis'
        del src['type']
    for k in list(src):
        src[k.lower() if k.lower() != 'date' else 'year'] = remove_unbalanced_braces(
            simple_to_text(src.pop(k)))
        if k in ['author', 'editor']:
            src[k] = src[k].replace('[', '').replace(']', '')

    for field, value in list(src.items()):
        if field in FIELD_MAP:
            target = FIELD_MAP[field]
            if target:
                if target not in src:
                    src[target] = value
                if target != field:  # A field is renamed.
                    del src[field]
            else:
                del src[field]

    return src


def iter_bib(ps: typing.List[pathlib.Path], verbose=False) -> typing.Generator[Source, None, None]:
    """
    :param ps: `list` of paths to bibtex files making up one bibliography.
    """
    log = logging.getLogger(__name__)
    bibtex = []
    for p in ps:
        # preprocess the bibtex, fixing the stuff that bibtool can't fix:
        text = p.read_text(encoding='utf8')
        lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
        if len(lines) == 1 and len(lines[0]) < 200 and p.parent.joinpath(lines[0]).exists():
            # Special handling for 237, where the path to 223's bib is given in the bibfile!
            text = p.parent.joinpath(lines[0]).read_text(encoding='utf8')  # pragma: no cover

        text = text.replace('\xa0', ' ')

        for pattern, repl in [
            # Invalid field names:
            (r'^\s*\_orig\s*=', '  orig ='),
            (r'^\s*\@(Note|Abstract|Comments?)\s*=', '  xnote ='),
            (r'^\s*\_\_(M|m)(arkedentry|ARKEDENTRY)\s*=', '  markedentry ='),
            (r'^\s*\_\_publisher\s*=', '  publisher ='),
            (r'^\s*\-\-Address\s*=', '  xxaddress ='),
            (r'^\s*\-\-Author\s*=', '  xxauthor ='),
            # Commented lines:
            (r'^\s*%.*$', ''),
            # Trailing comments:
            (r',%([0-9a-z]*|Undefined\?|(N|n)ame is not available)$', ','),
            # Invalid keys:
            (r'@([a-z]+)\{\{(English|French|vedic)\}',
             lambda m: '@%s{%s_' % (m.groups()[0], m.groups()[1])),
            # crossref to id instead of key:
            (r'crossref\s*=\s*{dryhaspWALS}', 'crossref = {wals}'),
            (r'crossref\s*=\s*{coling98}', 'crossref = {Branco98a}'),
        ]:
            text = re.sub(pattern, repl, text, flags=re.MULTILINE)

        # Single instances of weirdness:
        for k, v in [
            (r'{{\{', '{{{'),
            (r'{L\{', '{L{\\'),
            ('}%,', '},'),
            (r'{\{AA}}', r'{\AA}'),
            ('RepúblicadelParaguay2001,', 'RepublicadelParaguay2001,'),
            (r'@book{Kury\l{}owicz1973', '@book{kurylowicz1973'),
            ('@Article{,', '@Article{undefined,'),
            ('@book:1997\n{foley,', '@book{foley:1997,'),
        ]:
            text = text.replace(k, v)
        bibtex.append(text)

    # Now run bibtool:
    cmd = subprocess.Popen(
        [ensure_cmd('bibtool'), '-r', str(cfg.BIBTOOL_RSC)],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    stdout, stderr = cmd.communicate(input='\n'.join(bibtex).encode('utf8'))
    for line in stderr.decode('utf8').splitlines():  # pragma: no cover
        if line.strip():
            if any(s in line for s in
                   ['Duplicate field', 'non-space characters ignored', "Missing ',' assumed"]):
                continue
            if verbose:
                log.warning('bibtool:::' + line)

    # Now feed the bibtex to pybtex one record at a time to skip duplicate keys:
    for i, chunk in enumerate(re.split(r'^@', stdout.decode('utf8'), flags=re.MULTILINE)):
        # Again some preprocessing:
        if re.match('[A-Za-z]+{,', chunk):  # record without key.
            continue  # pragma: no cover
        if chunk.startswith('unpublished{rien'):  # empty stub.
            continue  # pragma: no cover
        for k, v in NAMES.items():  # Fix invalid author lists.
            chunk = chunk.replace(k, v)
        # Field values without enclosing braces:
        chunk = re.sub(
            r'^\s*([a-zA-Z]+)\s*=([^{]+),$',
            lambda m: '%s = {%s},' % (m.groups()[0], m.groups()[1]),
            chunk,
            flags=re.MULTILINE)
        if i:
            try:
                for k, e in database.parse_string('@' + chunk, 'bibtex').entries.items():
                    yield to_source(k, e)
            except:  # pragma: no cover # noqa: E722
                raise ValueError('{}::@{}'.format(ps, chunk))  # pragma: no cover
