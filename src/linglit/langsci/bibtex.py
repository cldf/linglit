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
from clldutils.path import ensure_cmd

from .latex import simple_to_text
from . import cfg

__all__ = ['iter_bib', 'normalize_key']

# Invalid author lists (and fixes):
NAMES = {
    'SkL, Holm. B 74, 4\\textsuperscript{o} = Brøndum-Nielsen, Johs':
        'SkL, Holm. B and Brøndum-Nielsen, Johs',
    'De Marneffe, Marie-Catherine, Timothy Dozat, Natalia Silveira, Katri Haverinen, Filip Ginter, Joakim Nivre,':
        'De Marneffe, Marie-Catherine and Timothy Dozat and Natalia Silveira and Katri Haverinen and Filip Ginter and Joakim Nivre,',
    'Igoo Ribaa, Mark Post,Ilii Ribaa, Miilii Nodu, Kenjum Bagra, Bomcak Ribaa, Toomoo Ribaa, Notoo Aado, Dambom Keenaa':
        'Igoo Ribaa and Mark Post and Ilii Ribaa and Miilii Nodu and Kenjum Bagra and Bomcak Ribaa and Toomoo Ribaa and Notoo Aado and Dambom Keenaa',
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
        'Dan Velleman and David Beaver and Emilie Destruel and Dylan Bumford and Edgar Onea and Liz Coppock',
    'Riad, Tomas, & Gussonhoven, Carlos':
        'Riad, Tomas and Gussonhoven, Carlos',
    "B\\'{e}r\\'{e}nice Bellina, Elisabeth A Bacus, Thomas Oliver Pryce, Jan Wisseman Christie":
        "B\\'{e}r\\'{e}nice Bellina and Elisabeth A Bacus and Thomas Oliver Pryce and Jan Wisseman Christie",
    "D'Alessandro, Roberta \\& Fischer, Susann \\& Hrafnbjargarson, Gunnar Hrafn":
        "D'Alessandro, Roberta and Fischer, Susann and Hrafnbjargarson, Gunnar Hrafn",
    'Mitchell, Rosamond, Tracy-Ventura, Nicole':
        'Mitchell, Rosamond and Tracy-Ventura, Nicole',
    'Juan-Garau, Maria., Joana Salazar-Noguera,':
        'Juan-Garau, Maria and Joana Salazar-Noguera',
    'Andr{\\\'e} M{\\"u}ller, Annkathrin Wett, Viveka Velupillai, Julia Bischoffberger, Cecil H. Brown, Eric W. Holman, Sebastian Sauppe, Zarina Molochieva, Pamela Brown, Harald Hammarstr{\\"o}m, Oleg Belyaev, Johann-Mattis List, Dik Bakker, Dmitry Egorov, Matthias Urban, Robert Mailhammer, Agustina Carrizo, Matthew S. Dryer, Evgenia Korovina, David Beck, Helen Geyer, Patience Epps, Anthony Grant,':
        'Andr{\\\'e} M{\\"u}ller and Annkathrin Wett and Viveka Velupillai and Julia Bischoffberger and Cecil H. Brown and Eric W. Holman and Sebastian Sauppe and Zarina Molochieva and Pamela Brown and Harald Hammarstr{\\"o}m and Oleg Belyaev and Johann-Mattis List and Dik Bakker and Dmitry Egorov and Matthias Urban and Robert Mailhammer and Agustina Carrizo and Matthew S. Dryer and Evgenia Korovina and David Beck and Helen Geyer and Patience Epps and Anthony Grant',
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
    src = LangsciSource.from_entry('x', e)
    src.id = normalize_key(key)
    src.genre = GENRE_MAP.get(src.genre.lower(), src.genre.lower())
    for k in list(src):
        src[k.lower() if k.lower() != 'date' else 'year'] = simple_to_text(src.pop(k))
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
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if len(lines) == 1 and len(lines[0]) < 200 and p.parent.joinpath(lines[0]).exists():
            # Special handling for 237, where the path to 223's bib is given in the bibfile!
            text = p.parent.joinpath(lines[0]).read_text(encoding='utf8')

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
            ('{\{AA}}', '{\AA}'),
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
    for line in stderr.decode('utf8').splitlines():
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
            continue
        if chunk.startswith('unpublished{rien'):  # empty stub.
            continue
        for k, v in NAMES.items():  # Fix invalid author lists.
            chunk = chunk.replace(k, v)
        # Field values without enclosing braces:
        chunk = re.sub(
            '^\s*([a-zA-Z]+)\s*=([^{]+),$',
            lambda m: '%s = {%s},' % (m.groups()[0], m.groups()[1]),
            chunk,
            flags=re.MULTILINE)
        if i:
            try:
                for k, e in database.parse_string('@' + chunk, 'bibtex').entries.items():
                    yield to_source(k, e)
            except:
                raise ValueError('{}::@{}'.format(ps, chunk))
