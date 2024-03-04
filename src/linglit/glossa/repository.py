import re
import urllib.request

from bs4 import BeautifulSoup as bs

from linglit import base
from .publication import Publication
from . import cfg

BASE_URL = "https://www.glossa-journal.org"
URL_PATTERN = re.compile('article/id/(?P<id>[0-9]+)')
CATALOG_URL = BASE_URL + "/articles/"


class Repository(base.Repository):
    id = 'glossa'
    lname_map = cfg.LNAME_MAP

    def create(self, verbose=False):
        get_all(self.dir, verbose=verbose, pages=30)

    def __getitem__(self, item):
        p = self.dir / '{}.xml'.format(item)
        if not p.exists():
            raise KeyError(item)
        lspecs = cfg.language_specs()
        return Publication(lspecs.get(int(item)), p, repos=self)

    def iter_publications(self):
        lspecs = cfg.language_specs()
        for p in sorted(self.dir.glob('*.xml'), key=lambda p_: int(p_.stem)):
            yield Publication(lspecs.get(int(p.stem)), p, repos=self)


def download(url, verbose=False):
    if verbose:
        print('retrieving {}'.format(url))
    return urllib.request.urlopen(url).read().decode('utf8')


def get_xml(url, d, verbose=False):
    if url:
        m = URL_PATTERN.search(url)
        if m:
            p = d / '{}.xml'.format(m.group('id'))
            if not p.exists():
                page = bs(download(url, verbose=verbose), 'lxml')
                xml_url = page.find('a', href=True, string='Download XML')
                if xml_url:
                    xml_url = xml_url['href']
                    if not xml_url.startswith('http'):
                        xml_url = BASE_URL + xml_url
                    p.write_text(download(xml_url), encoding='utf8')
                else:  # pragma: no cover
                    return
            return p.read_text(encoding='utf8')


def get_all(d, verbose=False, pages=None):
    url = CATALOG_URL
    pagenum = 0
    while url:
        pagenum += 1
        if pages and pagenum >= pages:
            break  # pragma: no cover
        page = bs(download(url, verbose=verbose), 'lxml')
        for p in page.find_all('div', class_='card-panel'):
            for a in p.find_all('a'):
                url = a['href']
                if not url.startswith('http'):
                    url = BASE_URL + url
                get_xml(url, d, verbose=verbose)
                # download HTML, look for "Download XML" link:
                # <a href="/article/5809/galley/21790/download/">Download XML</a>
                # https://www.glossa-journal.org/article/5821/galley/21844/download/
                break

        pagination = page.find('ul', class_='pagination')
        active = None
        for p in pagination.find_all('li'):
            if active:  # pragma: no cover
                try:
                    url = CATALOG_URL + p.find('a')['href']
                    break
                except KeyError:
                    continue
            if 'active' in p['class']:
                active = True
        else:
            break
