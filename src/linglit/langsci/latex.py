import re
import logging
import functools

from clldutils import lgr
from pylatexenc import latexwalker, latex2text, macrospec
from pyigt.igt import NON_OVERT_ELEMENT

__all__ = ['simple_to_text', 'to_text', 'strip_tex_comment', 'iter_abbreviations']

# Replace \<key> with <value> for the following macros:
SIMPLE_MACROS = {
    'ANA': 'ANA',
    'Tilde': '~',
    'tld': '~',
    'oneS': '1S',
    'twoS': '2S',
    'oneP': '1P',
    'twoP': '2P',
    'CL': 'CL',
    'ob': '[',
    'cb': ']',
    'op': '(',
    'cp': ')',
    'db': ' [',
    'R': 'r',
    'Nonpast': 'NONPAST',
    'redp': '~',
    'Stpl': '2|3PL',
    'Masc': 'MASC',
    'PSP': 'PSP',
    'Fsg': '1SG',
    'Fpl': '1PL',
    'ATT': 'ATT',
    'deff': 'DEFF',
    'Ssg': '2SG',
    'Stsg': '2|3SG',
    'Third': '3',
    'Tsg': '3SG',
    'IFV': 'IFV',
    'Second': '2',
    'HOR': 'HOR',
    'pp': 'PP',
    'Aand': '&',
    'IO': 'IO',
    'Io': 'IO',
    'LINK': 'LINK',
    'flobv': '→3',
    'fl': '→',
    'Venit': 'VENT',
    'Ndu': 'NDU',
    'PN': 'PN',
    'slash': '/',
    'DEP': 'DEP',
    'USSmaller': '<',
    'USGreater': '>',
    'defn': 'DEFN',
    'Char': 'CHAR',
    'DO': 'DO',
    'Rpst': 'RPST',
    'Ext': 'EXT',
    'EXT': 'EXT',
    'shin': 'ʃ',
    'shinB': 'ʃ',
    'alef': 'ʔ',
    'alefB': 'ʔ',
    'ayin': 'ʕ',
    'ayinB': 'ʕ',
    'het': 'ħ',
    'hetB': 'ħ',
    'PRON': 'PRON',
    'NOUN': 'NOUN',
    'CONJ': 'CONJ',
    'glossF': 'F',
    'glossNeg': 'NEG',
    'glsg': 'SG',
    'sq': '~',
    'INSTR': 'INSTR',
    'POT': 'POT',
    'PLU': 'PLU',
    'RETRO': 'RETRO',
    'CONTR': 'CONTR',
    'USOParen': '(',
    'USCParen': ')',
    'conn': 'CONN',
    'At': 'AT',
    'textepsilon': 'ɛ',
    'textopeno': 'ɔ',
    'textbeltl': 'ɬ',
    'textless': '<',
    'textgreater': '>',
    'textltailn': 'ɲ',
    'textquotedbl': '"',
    'textsci': 'ɪ',
    'IDPH': 'IDPH',
    'ID': 'ID',
    'Priv': 'PRIV',  # privative case
    'MOD': 'MOD',
    'Aor': 'AOR',
    'glossINF': 'INF',
    'Subj': 'SUBJ',
    'abi': 'ABI',
    'hest': 'HEST',
    'quant': 'QUANT',
    'RECIP': 'RECIP',
    'USEmptySet': '∅',
    'Obl': 'OBL',
    'Indic': 'INDIC',
    'Dei': 'DEI',
    'Expl': 'EXPL',
    'Sdu': 'SDU',
    'Mid': 'MID',
    'Npst': 'NPST',
    'Nom': 'NOM',
    'Nw': 'NW',
    'Act': 'ACT',
    'textgamma': 'ɣ',
    'textperiodcentered': '·',
    'cras': 'CRAS',
    'PRIOR': 'PRIOR',
    'SIM': 'SIM',
    'Lnk': 'LNK',
    'Av': 'AV',
    'Ppp': 'PPP',
    'Futimp': 'FUTIMP',
    'deter': 'DETER',
    'mut': 'MUT',
    'NC': 'NC',
    'textglotstop': 'ʔ',
    'textraiseglotstop': 'ʔ',
    'Intj': 'INTJ',
    'Prt': 'PRT',
    'NEUT': 'NEUT',
    'PF': 'PF',
    'z': '',
    'expl': 'EXPL',
    'Emph': 'EMPH',
    'Hab': 'HAB',
    'Gam': 'GAM',
    'Vc': 'VC',
    'Stnsg': '2|3NSG',
    'Stdu': '2|3DU',
    'Only': 'ONLY',
    'Imn': 'IMN',
    'Rs': 'RS',
    'Recog': 'RECOG',
    'Iam': 'IAM',
    'ds': 'ꜜ',
    'Prop': 'PROP',
    'Betaone': 'Β1',
    'Betatwo': 'Β2',
    'Appr': 'APPR',
    'AP': 'AP',
    'Bet': 'Β',
    'Pot': 'POT',
    'Imm': 'IMM',
    'Immpst': 'IPST',
    'Fnsg': '1NSG',
    'Dim': 'DIM',
    'Med': 'MED',
    'Stat': 'STAT',
    'Zero': NON_OVERT_ELEMENT,
    'Fdu': '1DU',
    'Lk': 'LK',
    'Alph': 'Α',
    'reln': 'RELN',
    'postp': 'POSTP',
    'dxm': 'DXM',
    'ideo': 'IDEO',
    'IDEO': 'IDEO',
    'ident': 'IDENT',
    'psg': 'PSG',
    'mod': 'MOD',
    'itr': 'ITR',
    'hab': 'HAB',
    'egr': 'EGR',
    'qual': 'QUAL',
    'la': 'lá',
    'baru': 'ʉ',
    'baruL': 'ʉ̀',
    'baruH': 'ʉ́',
    'ep': 'ε',
    'epL': 'ὲ',
    'epH': 'έ',
    'schwa': 'ə',
    'schwaH': 'ə́',
    'schwaL': 'ə̀',
    'mbuHL': 'mbʉ́ʉ̀',
    'mbuLH': 'mbʉ̀ʉ́',
    'mbuL': 'mb̀ʉ̀',
    'oo': 'ɔ',
    'ooH': 'ɔ́',
    'ooL': 'ɔ̀',
    'nda': 'ndà',
    'longrule': '_',
    'cmpr': 'CMPR',
    'thestrong': 'the',
    'theweak': 'the',
    'emphat': 'EMPH',
    'pstpunc': 'PSTPUNC',
    'relativ': 'REL',
    'cert': 'CERT',
    'att': 'ATT',
    'antip': 'ANTIP',
    'prep': 'PREP',
    'partic': 'PART',
    'antgen': 'ANTGEN',
    'am': 'AM',
    'asp': 'ASP',
    'ideoph': 'IDEOPH',
    'prosp': 'PROSP',
    'PROSP': 'PROSP',
    'pstrem': 'PSTREM',
    'fem': 'F',
    'mas': 'M',
    'faff': 'FAFF',
    'intens': 'INTENS',
    ':': 'ː',
    'fin': 'FIN',
    'conj': 'CONJ',
    'allo': 'ALLO',
    'ines': 'INES',
    'icml': 'ICML',
    'tns': 'TNS',
    'uop': 'UOP',
    'Hyp': 'HYP',
    'dsbj': 'DSBJ',
    'topic': 'TOP',
    'ctopic': "CTOPIC",
    'dir': 'DIR',
    'cs': 'CS',
    'question': 'Q',
    'glopa': 'OPA',
    'glme': 'TOP',
    'glte': 'NFIN',
    'glta': 'NFIN',
    'Cl': 'CL',
    'Rci': 'RCI',
    'Spl': '2PL',
    'Sm': 'SM',
    'Fv': 'FV',
    'Aug': 'AUG',
    'Dj': 'DJ',
    'Om': 'OM',
    "Adlzr": "ADLZR",  # adjectivaliser
    'glossQ': 'Q',
    'Depend': 'DEPEND',
    'Simp': 'SIMP',
    'Vn': 'VN',
    'Asp': 'ASP',
    'Invol': 'INVOL',
    'Volition': 'volition',
    'sVP': 'VP',
    'part': 'PARTICLE',
    'prag': 'PRAG',
    'pda': 'PDA',
    'Recip': 'REC',
    'persm': 'PM',
    'complx': 'COMPLX',
    'defsc': 'DEF',
    'transitiv': 'TR',
    'detr': 'DETR',
    'epen': 'EPEN',
    'agnm': 'AGNM',
    'ssbj': 'SSBJ',
    'rdp': 'RDP',
    'NR': 'NR',
    'con': 'CON',
    'Verb': 'VBLZ',
    'instr': 'INS',
    'firstperson': '1',
    'secondperson': '2',
    'thirdperson': '3',
    'an': 'AN',
    'rep': 'REP',
    'illa': 'ILLA',
    'topi': 'TOP',
    'lptcp': 'l_PTCP',
    'masc': 'M',
    'negation': 'NEG',
    'object': 'O',
    'impr': 'IMPR',
    'add': 'ADD',
    'andat': 'AND',  # andative
    'Andat': 'AND',  # andative
    'nsg': 'NSG',  # non-singular
    'Nsg': 'NSG',
    'Jj': 'J',
    'Lv': 'LV',
    'Lat': 'LAT',
    'Tns': 'TNS',
    'Etc': 'ETC',
    'Cmpr': 'CMPR',
    'AUTOCAUS': 'AUTOCAUS',
    'HAB': 'HAB',
    'Iii': 'III',
    'Cont': 'CONT',
    'Int': 'INT',
    'Prov': 'PROV',
    'Perm': 'PERM',
    'Cntr': 'CNTR',
    'Dv': 'DV',  # default vowel
    'TNS': 'TNS',
    'ASP': 'ASP',
    'glinf': 'INF',
    'glgen': 'GEN',
    'glprog': 'PROG',
    'Rem': 'REM',  # remote
    'Ti': 'TI',
    'Inv': 'INV',
    'Ss': 'SS',
    'Su': 'S',
    'Tpl': '3PL',
    'Desc': 'DESC',
    'Red': 'RED',
    'Iter': 'ITER',
    'Th': 'TH',
    'Vblz': 'VBLZ',
    'Detr': 'DETR',
    'Nth': 'NTH',
    'zero': NON_OVERT_ELEMENT,
    'sprl': 'SPRL',
    'wk': 'WK',
    'Ints': 'INTS',
    'Ds': 'DS',  # different subject
    'First': '1',
    'GH': 'ɣ',
    'vir': 'VIR',
    'nvir': 'N_VIR',
    'rls': 'RLS',
    'bg': 'BG',
    'stat': 'STAT',
    'dep': 'DEP',
    'punc': 'PUNC',
    'neu': 'N',
    'pstcont': 'PSTCONT',
    'polite': 'POL',
    'h': "'",
    'eer': 'ε',
    "textrtaild": "ɖ",
    "D": "ɖ",  # \textrtaild} %for retroflex d
    "F": "ʄ",  # \texthtbardotlessj}
    "oor": "ɔ",  # \textopeno}  % for ooor
    "Ng": "N",  # \textipa{N}}  %for NG
    "shw": "ə",  # \textschwa}  %for Shwa
    "gy": "ʤ",  # \textdyoghlig}  %for GY
    "ssh": "ʃ",  # \textesh} %ssh
    "tts": "ʧ",  # \textteshlig} %ts
    "zzh": "ʒ",  # \textyogh} %zzh
    "ny": "ɲ",  # \textltailn}
    "ph": "ɸ",  # \textphi}  %phi
    "lw": "`",  # \`} %LOW
    # "ds": "",  # \textdownstep} %DOWNSTEP
    "ns": "~",  # \~} %NAS
    "syl": "σ",  # $\sigma$} %SYLL
    "mo": "μ",  # $\mu$} %MORA
    "rnk": "≫",  # $\gg$} %>>
    "textcrh": "ħ",
    "rs": "\u030c",  # \v}
    'subj': "SUBJ",
    'PREP': 'PREP',
    'PAST': 'PAST',
    'glossM': 'M',
    'PRES': 'PRES',
    'NUM': 'NUM',
    'NOUNPROPER': 'NOUNPROPER',
    'ESS': 'ESS',
    'ESSIVE': 'ESSIVE',
    'ADESS': 'ADESS',
    'Redup': 'REDUP',
    'Anim': 'ANIM',
    'Temp': 'TEMP',
    'Snsg': '2NSG',
    'Pos': 'POS',  # positional verb stem
    'ᵓ': 'ᵓ',
    '°': '°',
    "ᵃ": "ᵃ",  # \textsf{{\hspace{.5pt}ᵃ}}}
    "ᵋ": "ᵋ",  # \textsf{{\hspace{.5pt}ᵋ}}}
    "ᵉ": "ᵉ",  # \textsf{{\hspace{.1pt}ᵉ}}}
    "ⁱ": "ⁱ",  # {\raisebox{-.65mm": "",  #{\textsuperscript{\sffamily\scriptsize i}}}}}
    "ᴵ": "ᴵ",  # \textsf{{\hspace{.5pt}ᴵ}}}
    "ᶤ": "ᶤ",  # \textsf{{\hspace{.5pt}ᶤ}}}
    "ᵒ": "ᵒ",  # \textsf{{\hspace{.5pt}ᵒ}}}
    "ᵘ": "ᵘ",  # \textsf{{\hspace{.5pt}ᵘ}}}
    "ᶶ": "ᶶ",  # \textsf{{\hspace{.5pt}ᶶ}}}
    "ꜜ": "ꜜ",  # \textsf{ꜜ\hspace*{-2pt}}}
    'supperl': 'SUPPERL',
    'supp': 'SUP',
    'definite': 'DEF',
    "PART": "PART",
    "PRV": "PRV",
    "STR": "STR",
    "INTENS": "INTENS",
    "HUMAN": "HUMAN",
    "NONHUMAN": "NONHUMAN",
    "ASSERT": "ASSERT",
    "IMPV": "IMPV",
    "IMPF": "IMPF",
    "INT": "INTR",
    "POSTP": "POSTP",
    'MAS': 'M',
    "Fosg": "4SG",  # {\gls{4}\gls{sg}}
    "Fopl": "4PL",  # {\gls{4}\gls{pl}}
    "Abl": "ABL",  # {\gls{abl}}
    "Abs": "ABS",  # {\gls{abs}}
    "Acc": "ACC",  # {\gls{acc}}
    "Ade": "ADE",  # {\gls{ade}}
    "Adj": "ADJ",  # {\gls{adj}}
    "Adv": "ADV",  # {\gls{adv}}
    "Agr": "AGR",  # {\gls{agr}}
    'ALL': 'ALL',
    "All": "ALL",  # {\gls{all}}
    "Anom": "ADNOM",  # {\gls{adnom}}
    "Ant": "ANT",  # {\gls{ant}}
    "Antip": "ANTIP",  # {\gls{antip}}
    "An": "AN",  # {\gls{an}}
    "Appl": "APPL",  # {\gls{appl}}
    "Apud": "APUD",  # {\gls{apud}}
    "Art": "ART",  # {\gls{art}}
    "Assoc": "ASSOC",  # {\gls{assoc}}
    "Aud": "AUD",  # {\gls{aud}}
    "Aux": "AUX",  # {\gls{aux}}
    "Bb": "B",  # {\gls{B}}
    "Ben": "BEN",  # {\gls{ben}}
    "BrP": "BRP",  # {\gls{BrP}}
    "Caus": "CAUS",  # {\gls{caus}}
    "Cci": "CCI",  # {\gls{cci}}
    "Cf": "CF",  # {\gls{cf}}
    "Cj": "CJ",  # {\gls{cj}}
    "Clf": "CLF",  # {\gls{clf}}
    "Cmpl": "CMPL",  # {\gls{cmpl}}
    "Cnj": "CNJ",  # {\gls{cnj}}
    "Comp": "COMP",  # {\gls{comp}}
    "Compl": "COMPL",  # {\gls{compl}}
    "Com": "COM",  # {\gls{com}}
    "Cond": "COND",  # {\gls{cond}}
    "Conn": "CONN",  # {\gls{conn}}
    "Cop": "COP",  # {\gls{cop}}
    "Cr": "CR",  # {\gls{cr}}
    "Cvb": "CVB",  # {\gls{cvb}}
    "Dat": "DAT",  # {\gls{dat}}
    "Decl": "DECL",  # {\gls{decl}}
    "Def": "DEF",  # {\gls{def}}
    "Dem": "DEM",  # {\gls{dem}}
    "Dep": "DEP",  # {\gls{dep}}
    "Det": "DET",  # {\gls{det}}
    "Dir": "DIR",  # {\gls{dir}}
    "Disp": "DISP",  # {\gls{disp}}
    "Distr": "DISTR",  # {\gls{distr}}
    "Dist": "DIST",  # {\gls{dist}}
    "Dom": "DOM",  # {\gls{dom}}
    "Do": "DO",  # {\gls{do}}
    "Dptcl": "DPTCL",  # {\gls{dptcl}}
    "Dr": "DR",  # {\gls{dr}}
    "Dur": "DUR",  # {\gls{dur}}
    "Du": "DU",  # {\gls{du}}
    "Ela": "ELA",  # {\gls{ela}}
    "Ep": "EP",  # {\gls{ep}}
    "Erg": "ERG",  # {\gls{erg}}
    "Es": "ES",  # {\gls{es}}
    "EuP": "EUP",  # {\gls{EuP}}
    "Evid": "EVID",  # {\gls{evid}}
    "Excl": "EXCL",  # {\gls{excl}}
    "Foc": "FOC",  # {\gls{foc}}
    "Fs": "FS",  # {\gls{fs}}
    "Fut": "FUT",  # {\gls{fut}}
    "Gen": "GEN",  # {\gls{gen}}
    "Genc": "GENC",  # {\gls{genc}}
    "Ger": "GER",  # {\gls{ger}}
    "Gg": "G_grade_(Muskogean)",  # {\gls{g}-grade (Muskogean)}
    "Ill": "ILL",  # {\gls{ill}}
    "Impass": "IMPASS",  # {\gls{impass}}
    "Imp": "IMP",  # {\gls{imp}}
    "Inch": "INCH",  # {\gls{inch}}
    'INCH': 'INCH',
    "Incl": "INCL",  # {\gls{incl}}
    "Incmpl": "INCMPL",  # {\gls{incmpl}}
    "Indef": "INDEF",  # {\gls{indef}}
    "Indir": "INDIR",  # {\gls{indir}}
    "Ind": "IND",  # {\gls{ind}}
    "Ine": "INE",  # {\gls{ine}}
    "Inf": "INF",  # {\gls{inf}}
    'inf': 'INF',
    "Infr": "INFR",  # {\gls{infr}}
    "Ins": "INS",  # {\gls{ins}}
    "Intr": "INTR",  # {\gls{intr}}
    "Ipfv": "IPFV",  # {\gls{ipfv}}
    "Ipf": "IPF",  # {\gls{ipf}}
    "Irr": "IRR",  # {\gls{irr}}
    "Ll": "L",  # {\gls{l}}
    "Loc": "LOC",  # {\gls{loc}}
    "M": "M",  # {\gls{m}}
    "Mnom": "MNOM",  # {\gls{mnom}}
    "Mr": "MR",  # {\gls{mr}}
    "Mut": "MUT",  # {\gls{mut}}
    "glossN": "N",  # {\gls{n}}
    "Nact": "NACT",  # {\gls{nact}}
    "Ncm": "NCM",  # {\gls{ncm}}
    "Neg": "NEG",  # {\gls{neg}}
    "Nfin": "NFIN",  # {\gls{nfin}}
    "Nmlz": "NMLZ",  # {\gls{nmlz}}
    "Num": "NUM",  # {\gls{num}}
    "Obj": "OBJ",  # {\gls{obj}}
    "Obv": "OBJV",  # {\gls{obv}}
    "Ov": "OV",  # {\gls{ov}}
    "Part": "PART",  # {\gls{part}}
    "Pass": "PASS",  # {\gls{pass}}
    "Pauc": "PAUC",  # {\gls{pauc}}
    "Pfv": "PFV",  # {\gls{pfv}}
    "Pg": "PG",  # {\gls{pg}}
    "Pip": "PIP",  # {\gls{pip}}
    "Pl": "PL",  # {\gls{pl}}
    "Pn": "PN",  # {\gls{pn}}
    "Poss": "POSS",  # {\gls{poss}}
    "Prdst": "PRDST",  # {\gls{prdst}}
    "Pred": "PRED",  # {\gls{pred}}
    "Prf": "PRF",  # {\gls{prf}}
    "Prep": "PREP",  # {\gls{prep}}
    "Prog": "PROG",  # {\gls{prog}}
    "Proh": "PROH",  # {\gls{proh}}
    "Pron": "PRON",  # {\gls{pron}}
    "Propn": "PROPN",  # {\gls{propn}}
    "Pros": "PROS",  # {\gls{pros}}
    "Prox": "PROX",  # {\gls{prox}}
    "Prs": "PRS",  # {\gls{prs}}
    "Prv": "PRV",  # {\gls{prv}}
    "Pst": "PST",  # {\gls{pst}}
    "Ptcl": "PTCL",  # {\gls{ptcl}}
    "Ptcp": "PTCP",  # {\gls{ptcp}}
    "ptcp": "PTCP",
    "Purp": "PURP",  # {\gls{purp}}
    "Pv": "PV",  # {\gls{pv}}
    "Quot": "QUOT",  # {\gls{quot}}
    "Real": "REAL",  # {\gls{real}}
    "Recp": "RECP",  # {\gls{recp}}
    "Refl": "REFL",  # {\gls{refl}}
    "Rel": "REL",  # {\gls{rel}}
    "Rep": "REP",  # {\gls{rep}}
    "Res": "RES",  # {\gls{res}}
    "Rg": "RG",  # {\gls{rg}}
    "Rm": "RM",  # {\gls{rm}}
    "Rpt": "RPT",  # {\gls{rpt}}
    "Sbjv": "SBJV",  # {\gls{sbjv}}
    "Sbj": "SBJ",  # {\gls{sbj}}
    "Secun": "SEC",  # {\gls{sec}}
    "Sg": "SG",  # {\gls{sg}}
    "Sim": "SIM",  # {\gls{sim}}
    "Sr": "SR",  # {\gls{sr}}
    "Subl": "SUBL",  # {\gls{subl}}
    "Supe": "SUPE",  # {\gls{supe}}
    "Supl": "SUPL",  # {\gls{supl}}
    "Ta": "TA",  # {\gls{ta}}
    "Term": "TERM",  # {\gls{term}}
    "Topic": "TOP",  # {\gls{top}}
    "Transl": "TRANS",  # {\gls{transl}}
    "Tr": "TR",  # {\gls{tr}}
    "Tto": "TT",  # {\gls{tt}}
    "Ut": "UT",  # {\gls{ut}}
    "Uu": "U",  # {\gls{u}}
    "Vm": "VM",  # {\gls{vm}}
    "Voc": "VOC",  # {\gls{voc}}
    "Vol": "VOL",  # {\gls{vol}}
    "Yn": "Y.N",  # {\gls{y.n}}
    "Aa": "A",  # {\gls{a}}
    "Pp": "P",  # {\gls{p}}
    "Rr": "R",  # {\gls{r}}
    "Tt": "T",  # {\gls{t}}
    "Ig": "I",  # {\gls{i}}
    "Ii": "II",  # {\gls{ii}}
    "Iv": "IV",  # {\gls{iv}}
    "SCC": "SC3",  # {\gls{SC3}}
    "SC": "SC2",  # {\gls{SC2}}
    'SUB': 'SUB',
    "nom": "NOM",  # {{\sc nom}}
    "gen": "GEN",  # {{\sc gen}}
    "dat": "DAT",  # {{\sc dat}}
    "acc": "ACC",  # {{\sc acc}}
    "abs": "ABS",  # {{\sc abs}}
    "erg": "ERG",  # {{\sc erg}}
    "voc": "VOC",  # {{\sc voc}}
    "poss": "POSS",  # {{\sc poss}}
    "pl": "PL",  # {{\sc pl}}
    "sg": "SG",  # {{\sc sg}}
    "thirdsg": "3SG",  # {3{\sc sg}}
    "ali": "ALI",  # {{\sc ali}}
    "appl": "APPL",  # {{\sc appl}}
    "augv": "AUGV",  # {{\sc augv}}
    "aux": "AUX",  # {{\sc aux}}
    "ben": "BEN",  # {{\sc ben}}
    "caus": "CAUS",  # {{\sc caus}}
    "clf": "CLF",  # {{\sc clf}}
    "coll": "COLL",  # {{\sc coll}}
    "com": "COM",  # {{\sc com}}
    "comp": "COMP",  # {{\sc comp}}
    "compl": "COMPL",  # {{\sc compl}}
    "cond": "COND",  # {{\sc cond}}
    "cop": "COP",  # {{\sc cop}}
    "cvb": "CVB",  # {{\sc cvb}}
    "decl": "DECL",  # {{\sc decl}}
    "dem": "DEM",  # {{\sc dem}}
    "dist": "DIST",  # {{\sc dist}}
    "distr": "DISTR",  # {{\sc distr}}
    "dscn": "DSCN",  # {{\sc dscn}}
    "cn": "CN",
    "du": "DU",  # {{\sc du}}
    "dubt": "DUBT",  # {{\sc dubt}}
    "dur": "DUR",  # {{\sc dur}}
    "dyn": "DYN",  # {{\sc dyn}}
    "ego": "EGO",  # {{\sc ego}}
    "excl": "EXCL",  # {{\sc excl}}
    "foc": "FOC",  # {{\sc foc}}
    "fut": "FUT",  # {{\sc fut}}
    "imp": "IMP",  # {{\sc imp}}
    "incep": "INCEP",  # {{\sc incep}}
    "ind": "IND",  # {{\sc ind}}
    "indf": "INDF",  # {{\sc indf}}
    "intr": "INTR",  # {{\sc intr}}
    "ipfv": "IPFV",  # {{\sc ipfv}}
    "irr": "IRR",  # {{\sc irr}}
    "lin": "LIN",  # {{\sc lin}}
    "loc": "LOC",  # {{\sc loc}}
    "modal": "MODAL",  # {{\sc modal}}
    "Non": "N",  # {{\sc n}}
    "nmlz": "NMLZ",  # {{\sc nmlz}}
    "nts": "NTS",  # {{\sc nts}}
    "obj": "OBJ",  # {{\sc obj}}
    "obl": "OBL",  # {{\sc obl}}
    "opt": "OPT",  # {{\sc opt}}
    "pass": "PASS",  # {{\sc pass}}
    "propnoun": "PN",  # {{\sc pn}}
    "pronoun": "PRO",  # {{\sc pro}}
    "pred": "PRED",  # {{\sc pred}}
    "prf": "PRF",  # {{\sc prf}}
    "prog": "PROG",  # {{\sc prog}}
    "prs": "PRS",  # {{\sc prs}}
    "prtv": "PRTV",  # {{\sc prtv}}
    "proh": "PROH",  # {{\sc proh}}
    "propr": "PROPR",  # {{\sc propr}}
    "prox": "PROX",  # {{\sc prox}}
    "pst": "PST",  # {{\sc pst}}
    "purp": "PURP",  # {{\sc purp}}
    "pfv": "PFV",  # {{\sc pfv}}
    "pvs": "PVS",  # {{\sc pvs}}
    "reas": "REAS",  # {{\sc reas}}
    "refl": "REFL",  # {{\sc refl}}
    "result": "RES",  # {{\sc res}}
    "sbj": "SBJ",  # {{\sc sbj}}
    "semb": "SEMB",  # {{\sc semb}}
    "simult": "SIM",  # {{\sc sim}}
    "them": "THEM",  # {{\sc them}}
    "tmp": "TMP",  # {{\sc tmp}}
    "ventiv": "VEN",  # {{\sc ven}}
    "ELAT": "ELAT",
    "E": "E",  # epenthetic morpheme
    "ATTRs": "ATTR",  # {{\Sc{attr}}}%shortcut for ATTR in small caps
    "PREDs": "PRED",  # {{\Sc{pred}}}%shortcut for PRED in small caps
    "SGs": "SG",  # {{\Sc{sg}}}%shortcut for SG in small caps
    "DUs": "DU",  # {{\Sc{du}}}%shortcut for DU in small caps
    "PLs": "PL",  # {{\Sc{pl}}}%shortcut for PL in small caps
    "NOMs": "NOM",  # {{\Sc{nom}}}%shortcut for NOM in small caps
    "ACCs": "ACC",  # {{\Sc{acc}}}%shortcut for ACC in small caps
    "GENs": "GEN",  # {{\Sc{gen}}}%shortcut for GEN in small caps
    "ILLs": "ILL",  # {{\Sc{ill}}}%shortcut for ILL in small caps
    "INESSs": "INESS",  # {{\Sc{iness}}}%shortcut for INESS in small caps
    "ELATs": "ELAT",  # {{\Sc{elat}}}%shortcut for ELAT in small caps
    "COMs": "COM",  # {{\Sc{com}}}%shortcut for COM in small caps
    "ABESSs": "ABESS",  # {{\Sc{abess}}}%shortcut for ABESS in small caps
    "ESSs": "ESS",  # {{\Sc{ess}}}%shortcut for ESS in small caps
    "PROXs": "PROX",  # {{\Sc{prox}}}%shortcut for PROX in small caps
    "DISTs": "DIST",  # {{\Sc{dist}}}%shortcut for DIST in small caps
    "RMTs": "RMT",  # {{\Sc{rmt}}}%shortcut for RMT in small caps
    "REFLs": "REFL",  # {{\Sc{refl}}}%shortcut for REFL in small caps
    "PRSs": "PRS",  # {{\Sc{prs}}}%shortcut for PRS in small caps
    "PSTs": "PST",  # {{\Sc{pst}}}%shortcut for PST in small caps
    "IMPs": "IMP",  # {{\Sc{imp}}}%shortcut for IMP in small caps
    "POTs": "POT",  # {{\Sc{pot}}}%shortcut for POT in small caps
    "PROGs": "PROG",  # {{\Sc{prog}}}%shortcut for PROG in small caps
    "PRFs": "PRF",  # {{\Sc{prf}}}%shortcut for PRF in small caps
    "INFs": "INF",  # {{\Sc{inf}}}%shortcut for INF in small caps
    "NEGs": "NEG",  # {{\Sc{neg}}}%shortcut for NEG in small caps
    "CONNEGs": "CONNEG",  # {{\Sc{conneg}}}%shortcut for CONNEG in small caps
    "BS": "<backslash>",
    'PRG': 'PRG',
    "pafr": "š",
    "paaf": "č",  # voiceless post-alveolar affricate
    "vuvfr": "ʁ",  # voiced uvular fricative
    "uvfr": "χ",  # voiceless uvular fricative
    "phfr": "ħ",  # voiceless pharyngeal fricative
    "eppl": "ʡ",  # epiglottal plosive
    "glpl": "ʔ",  # glottal stop
    "glst": "ʔ",  # alias for glottal stop
    "ej": "’",  # ejective
    "lab": "ʷ",  # labialized
    "pha": "ˤ",  # pharyngealized
    "lmk": "ː",
    "tet": "ṭ",
    "dao": "ố",
    "daa": "ấ",
    "dae": "ế",
    "daob": "ồ",
    "daab": "ầ",
    "daeb": "ề",
    'ts': "ts",
    'textdownstep': 'ꜜ',
    'Simil': 'SIMIL',  # similative
    'SSS': '3S',
    'ingr': 'INGR',
}

logging.getLogger('pylatexenc.latexwalker').setLevel(logging.WARNING)

#
# Define macros for the *parser*
#
macros = [
    macrospec.MacroSpec("footnotetext", "{"),
    macrospec.MacroSpec("footnote", "{"),
    macrospec.MacroSpec("japhdoi", "{"),
    macrospec.MacroSpec("textup", "{"),
    macrospec.MacroSpec("textupsc", "{"),
    macrospec.MacroSpec("glossfeat", "{"),
    macrospec.MacroSpec("langinfo", "{{{"),
    macrospec.MacroSpec("tss", "{"),
    macrospec.MacroSpec("ili", "{"),
    macrospec.MacroSpec("ilt", "{"),
    macrospec.MacroSpec("il", "{"),
    macrospec.MacroSpec("is", "{"),
    macrospec.MacroSpec("ist", "{"),
    macrospec.MacroSpec("ia", "{"),
    macrospec.MacroSpec("ix", "{"),
    macrospec.MacroSpec("ux", "{"),
    macrospec.MacroSpec("ref", "{"),
    macrospec.MacroSpec("llap", "{"),
    macrospec.MacroSpec("textsc", "{"),
    macrospec.MacroSpec("Sc", "{"),
    macrospec.MacroSpec("tsc", "{"),
    macrospec.MacroSpec("gsc", "{"),
    macrospec.MacroSpec("ig", "{"),
    macrospec.MacroSpec("linieb", "{{"),
    macrospec.MacroSpec("ulp", "{{"),
    macrospec.MacroSpec("ulg", "{{"),
    macrospec.MacroSpec("japhug", "{{"),
    macrospec.MacroSpec("gloss", "{"),
    macrospec.MacroSpec("REF", "{"),
    macrospec.MacroSpec("mc", "{"),
    macrospec.MacroSpec("particle", "{"),
    macrospec.MacroSpec("jambox", "[{"),
    macrospec.MacroSpec("mbox", "{"),
    macrospec.MacroSpec("blockcquote", "{{"),
    macrospec.MacroSpec("scite", "{{"),
    macrospec.MacroSpec("fatcit", "{{"),
    macrospec.MacroSpec("fatcitNP", "{{"),
    macrospec.MacroSpec("nocite", "{"),
    macrospec.MacroSpec("possessivecite", "[[{"),
    macrospec.MacroSpec("pgcitet", "[[{"),
    macrospec.MacroSpec("posscite", "[[{"),
    macrospec.MacroSpec("posscitet", "[[{"),
    macrospec.MacroSpec("posscitealt", "[[{"),
    macrospec.MacroSpec("namecite", "[[{"),
    macrospec.MacroSpec("Textcite", "[[{"),
    macrospec.MacroSpec("textcite", "[[{"),
    macrospec.MacroSpec("textcites", "[[{"),
    macrospec.MacroSpec("parencite", "[{"),
    macrospec.MacroSpec("textcquote", "[{"),
    macrospec.MacroSpec("href", "{{"),
    macrospec.MacroSpec("dline", "{{{"),
    macrospec.MacroSpec("autocite", "[[{"),
    macrospec.MacroSpec("autocites", "[[{"),
    macrospec.MacroSpec("cite", "[[{"),
    # FIXME: 17 Corpus and CorpusE
]
for k in SIMPLE_MACROS:
    macros.append(macrospec.MacroSpec(k, ""))
for abbr in lgr.ABBRS:
    if abbr:
        if abbr not in SIMPLE_MACROS:
            macros.append(macrospec.MacroSpec(abbr, ""))
        if abbr.lower() not in SIMPLE_MACROS:
            macros.append(macrospec.MacroSpec(abbr.lower(), ""))
        if len(abbr) > 1:
            if abbr.capitalize() not in SIMPLE_MACROS:
                macros.append(macrospec.MacroSpec(abbr.capitalize(), ""))

lw_context_db = latexwalker.get_default_latex_context_db()
lw_context_db.add_context_category('gll', prepend=True, macros=macros[:])

simple_parser_context_db = latexwalker.get_default_latex_context_db()
simple_parser_context_db.add_context_category(
    'simple',
    prepend=True,
    macros=[macrospec.MacroSpec("href", "{{")])


#
# Implement macros for the *conversion to text*
#

def uppercase_arg(n, l2tobj):
    if n.nodeargd:
        return l2tobj.nodelist_to_text([n.nodeargd.argnlist[0]]).upper()
    return ''


def dot_uppercase_arg(n, l2tobj):
    return '.' + l2tobj.nodelist_to_text([n.nodeargd.argnlist[0]]).upper()


def footnote(n, l2tobj):
    return "§fn§{}§/fn§".format(l2tobj.nodelist_to_text([n.nodeargd.argnlist[0]]))


def japhdoi(n, l2tobj):
    return '<a href="https://doi.org/10.24397/pangloss-{}"></fn>'.format(
        l2tobj.nodelist_to_text([n.nodeargd.argnlist[0]]))


def lastarg(n, l2tobj):
    return l2tobj.nodelist_to_text([n.nodeargd.argnlist[-1]])


def firstarg(n, l2tobj):
    if n.nodeargd:
        return l2tobj.nodelist_to_text([n.nodeargd.argnlist[0]])
    return ''


def secondarg(n, l2tobj):
    return l2tobj.nodelist_to_text([n.nodeargd.argnlist[1]])


def repl(abbr, *args):
    return abbr


def japhug(n, l2tobj):
    return "{} [{}]".format(
        l2tobj.nodelist_to_text([n.nodeargd.argnlist[0]]),
        l2tobj.nodelist_to_text([n.nodeargd.argnlist[1]]),
    )


def href(n, l2tobj):
    return "[{}]({})".format(
        l2tobj.nodelist_to_text([n.nodeargd.argnlist[1]]),
        l2tobj.nodelist_to_text([n.nodeargd.argnlist[0]]),
    )


def scite(n, l2tobj):
    return '<cit page="">{}</cit>'.format(l2tobj.nodelist_to_text([n.nodeargd.argnlist[1]]))


def fatcit(n, l2tobj):
    return '<cit page="{}">{}</cit>'.format(
        l2tobj.nodelist_to_text([n.nodeargd.argnlist[1]]),
        l2tobj.nodelist_to_text([n.nodeargd.argnlist[0]]))


def _get_optional_arg(node, default, l2tobj):
    """Helper that returns the `node` converted to text, or `default`
    if the node is `None` (e.g. an optional argument that was not
    specified)"""
    if node is None:
        return default
    return l2tobj.nodelist_to_text([node])


def cite(n, l2tobj):
    """Get the text replacement for the macro \\cite...[page]{bibkey}"""
    if not n.nodeargd:
        # n.nodeargd can be empty if e.g. \putinquotes was a single
        # token passed as an argument to a macro,
        # e.g. \newcommand\putinquotes...
        return ''
    page = ''
    if len(n.nodeargd.argnlist) > 1:
        page = _get_optional_arg(n.nodeargd.argnlist[0], '', l2tobj)
    key = l2tobj.nodelist_to_text([n.nodeargd.argnlist[-1]]).strip().replace('   ', '&')
    if key:
        return '<cit page="{}">{}</cit>'.format(page.replace('"', ''), key)
    return ''


def langinfo(n, l2tobj):
    if not n.nodeargd:
        return ''
    res = ''
    for i, arg in enumerate(n.nodeargd.argnlist):
        t = l2tobj.nodelist_to_text([arg]).strip()
        if t:
            if i != 2:
                res += ' ' + t
            else:
                res += '<cit page="">{}</cit>'.format(t)
    return res


macros = [
    latex2text.MacroTextSpec('section',
     lambda n, l2tobj: u'\n\n{}\n'.format(l2tobj.node_arg_to_text(n, 2))),
    latex2text.MacroTextSpec("footnote", simplify_repl=footnote),
    latex2text.MacroTextSpec("footnotetext", simplify_repl=footnote),
    latex2text.MacroTextSpec("japhdoi", simplify_repl=japhdoi),
    latex2text.MacroTextSpec("japhug", simplify_repl=japhug),
    latex2text.MacroTextSpec("textup", simplify_repl=firstarg),
    latex2text.MacroTextSpec("textupsc", simplify_repl=uppercase_arg),
    latex2text.MacroTextSpec("glossfeat", simplify_repl=uppercase_arg),
    latex2text.MacroTextSpec("linieb", simplify_repl=secondarg),
    latex2text.MacroTextSpec("langinfo", simplify_repl=langinfo),
    latex2text.MacroTextSpec("ulp", simplify_repl=firstarg),
    latex2text.MacroTextSpec("ulg", simplify_repl=firstarg),
    latex2text.MacroTextSpec("ref", simplify_repl=firstarg),
    latex2text.MacroTextSpec("textsc", simplify_repl=uppercase_arg),
    latex2text.MacroTextSpec("Sc", simplify_repl=uppercase_arg),
    latex2text.MacroTextSpec("tsc", simplify_repl=uppercase_arg),
    latex2text.MacroTextSpec("tss", simplify_repl=dot_uppercase_arg),
    latex2text.MacroTextSpec("gsc", simplify_repl=uppercase_arg),
    latex2text.MacroTextSpec("ig", simplify_repl=uppercase_arg),
    latex2text.MacroTextSpec("mc", simplify_repl=uppercase_arg),
    latex2text.MacroTextSpec("gloss", simplify_repl=uppercase_arg),
    latex2text.MacroTextSpec("llap", simplify_repl=lambda *args: ''),
    latex2text.MacroTextSpec("ilt", simplify_repl=lambda *args: ''),
    latex2text.MacroTextSpec("il", simplify_repl=lambda *args: ''),
    latex2text.MacroTextSpec("is", simplify_repl=lambda *args: ''),
    latex2text.MacroTextSpec("ist", simplify_repl=lambda *args: ''),
    latex2text.MacroTextSpec("ia", simplify_repl=lambda *args: ''),
    latex2text.MacroTextSpec("ix", simplify_repl=lambda *args: ''),
    latex2text.MacroTextSpec("ux", simplify_repl=lambda *args: ''),
    latex2text.MacroTextSpec("dline", simplify_repl=lambda *args: ''),
    # latex2text.MacroTextSpec("ili", simplify_repl=lambda *args: ''),
    latex2text.MacroTextSpec("ili", simplify_repl=firstarg),
    latex2text.MacroTextSpec("REF", simplify_repl=lambda *args: ''),
    latex2text.MacroTextSpec("particle", simplify_repl='PARTICLE'),
    # For example parsing, we want to disregard jambox content
    # latex2text.MacroTextSpec("jambox", simplify_repl=''),
    # But for citation parsing, we need it.
    latex2text.MacroTextSpec("jambox", simplify_repl=lastarg),
    latex2text.MacroTextSpec("mbox", simplify_repl=firstarg),
    latex2text.MacroTextSpec("blockcquote", simplify_repl=fatcit),
    latex2text.MacroTextSpec("scite", simplify_repl=scite),
    latex2text.MacroTextSpec("fatcit", simplify_repl=fatcit),
    latex2text.MacroTextSpec("fatcitNP", simplify_repl=fatcit),
    latex2text.MacroTextSpec("textcquote", simplify_repl=cite),
    latex2text.MacroTextSpec("pgcitet", simplify_repl=cite),
    latex2text.MacroTextSpec("posscite", simplify_repl=cite),
    latex2text.MacroTextSpec("posscitet", simplify_repl=cite),
    latex2text.MacroTextSpec("posscitealt", simplify_repl=cite),
    latex2text.MacroTextSpec("namecite", simplify_repl=cite),
    latex2text.MacroTextSpec("Textcite", simplify_repl=cite),
    latex2text.MacroTextSpec("textcite", simplify_repl=cite),
    latex2text.MacroTextSpec("textcites", simplify_repl=cite),
    latex2text.MacroTextSpec("nocite", simplify_repl=cite),
    latex2text.MacroTextSpec("parencite", simplify_repl=cite),
    latex2text.MacroTextSpec("href", simplify_repl=href),
    latex2text.MacroTextSpec("possessivecite", simplify_repl=cite),
    latex2text.MacroTextSpec("autocite", simplify_repl=cite),
    latex2text.MacroTextSpec("autocites", simplify_repl=cite),
    latex2text.MacroTextSpec("cite", simplify_repl=cite),
]
for k, v in SIMPLE_MACROS.items():
    macros.append(latex2text.MacroTextSpec(k, simplify_repl=functools.partial(repl, v)),)
for abbr in lgr.ABBRS:
    if abbr:
        macros.extend([
            latex2text.MacroTextSpec(abbr, simplify_repl=functools.partial(repl, abbr)),
            latex2text.MacroTextSpec(abbr.lower(), simplify_repl=functools.partial(repl, abbr)),
        ])
        if len(abbr) > 1:
            macros.append(
                latex2text.MacroTextSpec(
                    abbr.capitalize(), simplify_repl=functools.partial(repl, abbr)))

l2t_context_db = latex2text.get_default_latex_context_db()
l2t_context_db.add_context_category('gll', prepend=True, macros=macros[:])

simple_converter_context_db = latex2text.get_default_latex_context_db()
simple_converter_context_db.add_context_category(
    'simple',
    prepend=True,
    macros=[latex2text.MacroTextSpec("href", simplify_repl=firstarg)])


def custom_latex_to_text(input_latex, parser=lw_context_db, converter=l2t_context_db):
    # the latex parser instance with custom latex_context
    lw_obj = latexwalker.LatexWalker(input_latex, latex_context=parser)
    # parse to node list
    nodelist, pos, length = lw_obj.get_latex_nodes()
    # initialize the converter to text with custom latex_context
    l2t_obj = latex2text.LatexNodes2Text(latex_context=converter)
    # convert to text
    try:
        return l2t_obj.nodelist_to_text(nodelist)
    except (IndexError, ValueError):
        return input_latex


def simple_to_text(latex):
    return custom_latex_to_text(
        latex, parser=simple_parser_context_db, converter=simple_converter_context_db)


def strip_tex_comment(s):
    lines = re.split(r'\\\\', s)
    if len(lines) == 2 and lines[1].startswith('%'):
        s = lines[0] + r'\\'
    return re.split(r"(?<!\\)%", s)[0].replace(r"\%", "%")


def iter_abbreviations(tex):
    for line in tex.split('\n'):
        if not line.strip().startswith("%"):
            cells = line.split("&")
            if len(cells) == 2:
                yield to_text(cells[0].strip())[0], to_text(cells[1].strip())[0]


def to_text(latex):
    # preprocessing:
    latex = latex.replace(r'{\sc ', r'\textsc{')
    latex = latex.replace(r'{\scshape ', r'\textsc{')

    # custom latex-to-text conversion:
    text, comment, refs = custom_latex_to_text(latex), [], []

    # postprocessing:
    text = text.replace('<backslash>', '\\')
    text = text.strip()
    # extract footnotes:
    fn_pattern = re.compile(r'§fn§([^§]+)§/fn§')
    for m in fn_pattern.finditer(text):
        comment.append(m.groups()[0])
    if comment:
        text = fn_pattern.sub('', text).strip()

    # extract citations:
    pattern = re.compile(r'<cit page="([^"]*)">([^<]+)</cit>')
    for m in pattern.finditer(text):
        if m.groups()[1] != '[':
            for sid in m.groups()[1].split(','):
                if sid.strip():
                    refs.append((sid.strip(), m.groups()[0]))
    if refs:
        text = pattern.sub('', text).strip()

    for cc in comment:
        for m in pattern.finditer(cc):
            if m.groups()[1] != '[':
                for sid in m.groups()[1].split(','):
                    if sid.strip():
                        refs.append((sid.strip(), m.groups()[0]))
    comment = [pattern.sub(lambda m: m.groups()[1], cc).strip() for cc in comment]

    #
    # FIXME: handle *\textit commands
    #
    leading_amp = re.compile(r'^\s*&+\s*')
    #
    # FIXME: unicodedata.normalize.nfc!
    #
    return (
        text,
        '\n'.join(comment),
        [(leading_amp.sub('', k.replace('–', '--').lower()), v) for k, v in refs])
