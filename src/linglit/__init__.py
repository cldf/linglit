import collections
import pathlib

from pyglottolog import Glottolog as API

from . import langsci
from . import glossa
from .base import Repository


PROVIDERS = {r.id: r for r in Repository.__subclasses__() if r.id}

class Glottolog:
    def __init__(self, glottolog):
        if not isinstance(glottolog, API):
            glottolog = API(glottolog)
        self.by_glottocode = {}
        self.by_isocode = {}
        self._by_name = {}
        self.by_custom_name = {}

        for lg in glottolog.languoids():
            self.by_glottocode[lg.id] = lg
            if lg.iso:
                self.by_isocode[lg.iso] = lg
            self._by_name[lg.name] = lg
            for _, names in lg.names.items():
                for name in names:
                    name = name.split('[')[0].strip()
                    if name not in self._by_name:
                        self._by_name[name] = lg

        self.by_name = {k: v for k, v in self._by_name.items()}
        self.api = glottolog

    def register_names(self, names):
        self.by_name = {k: v for k, v in self._by_name.items()}
        for k, v in names.items():
            if v:
                self.by_name[k] = self.by_glottocode[v]

    def __call__(self, name):
        if name:
            if name in self.by_glottocode:
                return self.by_glottocode[name].id
            if name in self.by_isocode:
                return self.by_isocode[name].id
            gl = self.by_name.get(name)
            if gl:
                return gl.id


def iter_examples(d='.', glottolog='glottolog', **dirs):
    d = pathlib.Path(d)
    c = collections.Counter()
    glottolog = Glottolog(glottolog)
    for rid, cls in PROVIDERS.items():
        #if rid != 'glossa':
        #    continue
        sd = dirs.get(rid, d / rid)
        if sd.exists():
            repos = cls(sd)
            repos.register_language_names(glottolog)

            for pub in cls(sd).iter_publications():
                if not pub.record.current:
                    print(pub.as_source())

                continue
                if pub.record.int_id not in [6371]:
                    continue
                pid = '{}-{}'.format(rid, pub.record.ID)
                for i, ex in enumerate(pub.iter_examples()):
                    if ex.Language_ID is None:
                        ex.Language_ID = glottolog(ex.Language_Name)
                    print(ex.ID, ex.Language_ID)
                    c.update([pid])
    #for k, v in c.most_common(50):
    #    print(k, v)

    return

    d = pathlib.Path(d)
    #lsp = langsci.Repository(d / 'langsci')
    lsp = glossa.Repository(d / 'glossa')
    for pub in lsp.iter_publications():
        #if pub.record.int_id not in [94]:
        #    continue

        i = -1
        for i, ex in enumerate(pub.iter_examples()):
            print(ex.as_igt().pprint())
            break
        print('{}: {}'.format(pub.record.ID, i + 1))
        continue
