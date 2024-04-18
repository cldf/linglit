import pathlib
import collections

from tqdm import tqdm

from . import langsci
from . import glossa
from . import cldf
from .base import Repository, Glottolog

assert langsci and glossa and cldf
PROVIDERS = {r.id: r for r in Repository.__subclasses__() if r.id}


def iter_publications(d='.', glottolog='glottolog', with_examples=False, exclude=None, **dirs):
    d = pathlib.Path(d)
    glottolog = Glottolog(glottolog)
    for rid, cls in sorted(PROVIDERS.items(), key=lambda i: i[0]):
        if exclude and rid in exclude:
            continue  # pragma: no cover
        sd = dirs.get(rid, d / rid)
        if sd.exists():
            repos = cls(sd)
            glottolog.register_names(repos.lname_map)
            for pub in cls(sd).iter_publications():
                if with_examples:
                    for ex in pub.examples:
                        ex.Language_ID = glottolog(ex.Language_Name)
                        ex.Meta_Language_ID = glottolog(ex.Meta_Language_ID)
                        if not ex.Language_ID:
                            if ex.Comment in glottolog.by_name:  # pragma: no cover
                                ex.Language_ID = glottolog.by_name[ex.Comment].id
                                ex.Comment = None
                yield pub


def iter_examples(d='.', glottolog='glottolog', **dirs):  # pragma: no cover
    d = pathlib.Path(d)
    c = collections.Counter()
    glottolog = Glottolog(glottolog)
    for rid, cls in PROVIDERS.items():
        # if rid != 'glossa':
        if rid != 'langsci':
            continue
        sd = dirs.get(rid, d / rid)
        bibtex = sd / 'bibtex'
        if sd.exists():
            if not bibtex.exists():
                bibtex.mkdir()
            repos = cls(sd)
            glottolog.register_names(repos.lname_map)

            for pub in tqdm(cls(sd).iter_publications(), desc=rid):
                # if pub.record.int_id not in [6371]:
                # if rid == 'langsci' and pub.record.int_id < 289:
                #    continue

                # print(pub.id, len(pub.references), len(pub.cited))
                t = []
                for src in pub.cited_references:
                    #
                    # FIXME: add lgcode for refs related to identified examples!
                    #
                    t.append(src.bibtex())

                bibtex.joinpath(
                    '{}.bib'.format(pub.record.ID)).write_text('\n\n'.join(t), encoding='utf8')

                continue
                pid = '{}-{}'.format(rid, pub.record.ID)
                for i, ex in enumerate(pub.iter_examples()):
                    if ex.Language_ID is None:
                        ex.Language_ID = glottolog(ex.Language_Name)
                    print(ex.ID, ex.Language_ID)
                    c.update([pid])
    # for k, v in c.most_common(50):
    #    print(k, v)

    return

    d = pathlib.Path(d)
    # lsp = langsci.Repository(d / 'langsci')
    lsp = glossa.Repository(d / 'glossa')
    for pub in lsp.iter_publications():
        # if pub.record.int_id not in [94]:
        #    continue

        i = -1
        for i, ex in enumerate(pub.iter_examples()):
            print(ex.as_igt().pprint())
            break
        print('{}: {}'.format(pub.record.ID, i + 1))
        continue
