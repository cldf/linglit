"""
We aggregate the relevant source files of langsci books in a repository.

This repository is created and synched with the upstream repositories by using the GitHub
REST API via [gh](https://cli.github.com/).
"""
import json
import base64
import pathlib
import subprocess

import attr
from clldutils.jsonlib import update_ordered, load
from clldutils.path import ensure_cmd

from linglit import base
from .catalog import Catalog, GITHUB_ORG
from .publication import Publication
from . import cfg

CATALOG_NAME = "catalog.tsv"
FILELIST_NAME = "files.json"
MISSING_TEX_SOURCES = [
    155, 192, 195, 255, 287, 297, 311, 325, 373, 380,
    410,
    284,  # For the time being ...
    292,
    438,
]
MISSING_REPOS = [410, 389, 392, 393, 438]
TEX_BRANCH = {187: 'master'}


@attr.s
class File:
    path = attr.ib(converter=pathlib.Path)  # "chapters/01.tex",
    sha = attr.ib()   # "9b724bc0398020c9c9b14926319a38d219f56786",
    mode = attr.ib()
    type = attr.ib()
    size = attr.ib()  # 23220,
    url = attr.ib()

    @property
    def content(self):
        data = gh_api(None, url=self.url)
        file_content = data['content']
        file_content_encoding = data.get('encoding')
        if file_content_encoding == 'base64':
            file_content = base64.b64decode(file_content)
        return file_content

    def same_content(self, p, shallow=True):
        if shallow:
            return p.stat().st_size == self.size
        return self.content == p.read_bytes()

    def fullpath(self, d):
        p = pathlib.Path(d).joinpath(self.path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def save(self, d):
        self.fullpath(d).write_bytes(self.content)


def gh_api(item, path=None, url=None):
    if url is None:
        url = "https://api.github.com/repos/{}/{}{}".format(
            GITHUB_ORG, getattr(item, 'ID', item), path or '')
    print('requesting {}'.format(url))
    return json.loads(subprocess.check_output([ensure_cmd('gh'), "api", url]))


def branch_and_tree(item, olddata):
    default_branch = olddata[0] if olddata else gh_api(item)['default_branch']
    if int(getattr(item, 'ID', item)) in TEX_BRANCH:  # pragma: no cover
        default_branch = TEX_BRANCH[item.int_id]
    return default_branch, gh_api(item, '/git/trees/{}?recursive=1'.format(default_branch))


class Repository(base.Repository):
    id = 'langsci'
    lname_map = cfg.LNAME_MAP

    def __getitem__(self, item):
        return Publication(self.catalog[item], self.dir / item, self)

    def iter_publications(self):
        for item in self.catalog:
            # if item.int_id != 22:
            #     continue
            if item.int_id in MISSING_REPOS:
                continue
            if item.int_id not in MISSING_TEX_SOURCES:
                yield Publication(item, self.dir / item.ID, self)

    def create(self, verbose=False):  # pragma: no cover
        """
        Create a repository from scratch (may need to be restarted a couple of times if
        GH rate limit problems are encountered):
        """
        self.fetch_catalog()
        self.fetch_filelist(refresh=True)
        self.fetch_files()

    @property
    def catalog(self):
        return Catalog.from_local(self.dir / CATALOG_NAME)

    def fetch_catalog(self):
        catalog = Catalog.from_remote()
        catalog.write(self.dir / CATALOG_NAME)

    def fetch_filelist(self, ids=None, refresh=False):
        ids = {int(i) for i in ids or []}
        with update_ordered(self.dir / FILELIST_NAME) as d:
            for item in self.catalog:
                if item.int_id in MISSING_REPOS or (not refresh and (item.ID in d)):
                    continue
                if not ids or (item.int_id in ids):
                    d[item.ID] = branch_and_tree(item, d.get(item.ID))

    def fetch_files(self, filelist=None):
        exclude = [
            'seriesinfo',
            'langsci/locale',
            'langsci-hyphenation',
            '.texpadtmp',
            'bibstyles.deprecated',
            'figures/',
            'graphics/',
            'biblatex-sp-unified',
            'draftinfo.tex',
            'generated/',
            'bibstyles/',
            'Figures/',
            'styles/tcb',
            '__MACOSX',
            'pdf/',
        ]
        for itemid, (_, filelist) in load(filelist or self.dir / FILELIST_NAME).items():
            sd = self.dir / itemid
            if not sd.exists():
                sd.mkdir()
            for file in filelist['tree']:
                if file['type'] not in ['tree', 'commit']:
                    file = File(**file)
                    if (file.path.suffix in ['.bib', '.tex'] or file.path.name == 'Makefile') \
                            and not any(e in str(file.path) for e in exclude):
                        fp = file.fullpath(sd)
                        if not fp.exists() or (not file.same_content(fp)):
                            file.save(sd)
