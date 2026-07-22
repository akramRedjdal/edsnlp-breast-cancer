"""
Vendored, near-verbatim port of the project's original ``TNM_extraction.py``
(itself adapted from the Regenstrief Institute TNM stager). The regex/parsing
LOGIC IS UNCHANGED from the original — this file exists so the
``breast_cancer.tnm`` pipe has a self-contained, dependency-free TNM parser to
wrap, without depending on the original monolithic project's file layout.

Only the CLI-only scaffolding of the original (argument parsing, ``--help``
text, ``__main__`` entry point) was dropped as dead code in a library
context — none of the regex or field-extraction logic was touched.

OVERVIEW:
The code in this module loads sentences containing TNM staging codes and
returns a JSON result describing the prefixes, suffixes, and values for
each portion of the code.

OUTPUT:
The set of JSON fields present in the output for each code includes:
        text             text of the complete code
        start            offset of first char in the matching text
        end              offset of final char in the matching text + 1
        t_prefix         see comments for 'str_prefix_symbols' below
        t_code           X, is, 0, 1, 2, 3, 4
        t_certainty      see comments for 'str_certainty' below
        t_suffixes       a, b, c, d
        t_multiplicity   tumor multiplicity value
        n_prefix         see comments for 'str_prefix_symbols' below
        n_code           X, 0, 1, 2, 3
        n_certainty      see comments for 'str_certainty' below
        n_suffixes       a, b, c, d, mi, sn, i+, i-, mol+, mol-
        n_regional_nodes_examined   integer value
        n_regional_nodes_involved   integer value
        m_prefix         see comments for 'str_prefix_symbols' below
        m_code           X, 0, 1
        m_certainty      see comments for 'str_certainty' below
        m_suffixes       a, b, c, d, i+, mol+, cy+, PUL, OSS, HEP, BRA,
                         LYM, OTH, MAR, PLE, PER, ADR, SKI
        l_code           X, 0, 1
        g_code           X, 1, 2, 3, 4
        v_code           X, 0, 1, 2
        pn_code          X, 0, 1
        serum_code       X, 0, 1, 2, 3
        r_codes          X, 0, 1, 2
        r_suffixes       is, cy+
        r_locations      string
        stage_prefix     y, yp
        stage_number     0, 1, 2, 3, 4
        stage_letter     a, b, c, d

All JSON fields will be present in the output for each code. If a field
should be ignored it will have the value EMPTY_FIELD.

Information on the TNM system was compiled from these sources:
1. Natural Language Processing in Determining Cancer Stage,
   Final Report, Regenstrief Institute, citation TBD
2. TNM Classification of Malignant Tumors, Eighth Edition,
   ed. Brierly et. al., Wiley-Blackwell, 2017
3. TNM Supplement: A Commentary on Uniform Use, Fourth Edition,
   ed. Wittekind et. al., Wiley-Blackwell, 2012
4. https://emedicine.medscape.com/article/2007800-overview
"""

import re
import json
from collections import namedtuple

EMPTY_FIELD = None
TNM_FIELDS = ['text', 'start', 'end',
              't_prefix', 't_code', 't_certainty', 't_suffixes', 't_mult',
              'n_prefix', 'n_code', 'n_certainty', 'n_suffixes',
              'n_regional_nodes_examined', 'n_regional_nodes_involved',
              'm_prefix', 'm_code', 'm_certainty', 'm_suffixes',
              'l_code', 'g_code', 'v_code', 'pn_code', 'serum_code',
              'r_codes', 'r_suffixes', 'r_locations',
              'stage_prefix', 'stage_number', 'stage_letter']
TnmCode = namedtuple('TnmCode', TNM_FIELDS)

# Common prefixes for T, N, M codes:
#
#     c     clinical classification
#     p     pathological classification
#    yc     clinical classification peformed during multimodal therapy
#    yp     pathological classification performed during multimodal therapy
#     r     recurrent tumor
#    rp     recurrence after a disease free interval, designated at autopsy
#           (see TNM Supplement)
#     a     classification determined at autopsy
str_prefix_symbols  = r'(c|p|yc|yp|r|rp|a)?'

# Certainty factor (present in 4th through 7th editions of TNM, not in the 8th)
str_certainty = r'(C[1-5])?'

# T - extent of primary tumor
T_SUFFIX_STRINGS = ['a', 'b', 'c', 'd']  # exclude multiplicity
# NOTE (breast_cancer package fix): added bare 'mi' (micrometastasis, was
# only in str_n_suffixes despite also being valid T-suffix notation, e.g.
# "pT1mi") and a generic parenthesized descriptor "(...)" (e.g. "Tis(DCIS)")
# so these no longer break the T->N connector right after them.
str_t_suffixes = r'(a|b|c|d|mi|\+|\(m\)|\(\d+\)|\([A-Za-z]+\))*'
str_t = r'(?P<t_prefix>' + str_prefix_symbols + r')' +\
        r'T(?P<t_code>([0-4]|is|X))'                 +\
        r'(?P<t_certainty>' + str_certainty + r')'   +\
        r'(?P<t_suffixes>' + str_t_suffixes + r'\s*'+ r')'
regex_t = re.compile(str_t, re.IGNORECASE)

# use this to find multiplicity value
regex_t_mult = re.compile(r'(m|\d+)', re.IGNORECASE)

# N - regional lymph nodes
N_SUFFIX_STRINGS = ['a', 'b', 'c', 'd', 'mi', 'sn', 'i+', 'i-',
                    'mol+', 'mol-']

str_n_suffixes = r'(a|b|c|d|mi|\,|sn|i[-,+]|mol[-,+]|\(mi\)|\(sn\)|\(i[-,+]\)|' +\
                 r'\(mol[-,+]\)|\(\d+\s*/\s*\d+\))*'
str_n = r'(?P<n_prefix>' + str_prefix_symbols + r')' +\
        r'N(?P<n_code>([0-3]|X|\+|\-))'                    +\
        r'(?P<n_certainty>' + str_certainty + r')'   +\
        r'(?P<n_suffixes>' + str_n_suffixes + r'\s*' + r')'
regex_n = re.compile(str_n, re.IGNORECASE)

# check for regional lymph node metastases
regex_regional_metastases = re.compile(r'\((?P<regionals_involved>\d+)' +\
                                       r'\s*/\s*(?P<regionals_examined>\d+)\)',
                                       re.IGNORECASE)

# M - distant metastasis
M_SUFFIX_STRINGS = ['a', 'b', 'c', 'd', 'i+', 'mol+', 'cy+',
                    'pul', 'oss', 'hep', 'bra', 'lym', 'oth',
                    'mar', 'ple', 'per', 'adr', 'ski']
str_m_suffixes = r'(a|b|c|d|i\+|mol\+|cy\+|\(i\+\)|\(mol\+\)|\(cy\+\)|' +\
                 r'PUL|OSS|HEP|BRA|LYM|OTH|MAR|PLE|PER|ADR|SKI)*'
str_m = r'(?P<m_prefix>' + str_prefix_symbols + r')'        +\
        r'M(?P<m_code>(0|1|X))'                             +\
        r'(?P<m_certainty>' + str_certainty + r')'          +\
        r'(?P<m_suffixes>' + r'\s*' + str_m_suffixes + r'\s*' + r')'
regex_m = re.compile(str_m, re.IGNORECASE)

# R - residual metastases
R_SUFFIX_STRINGS = ['is', 'cy+']
str_r_suffixes = r'(is|cy\+|\(is\)|\(cy\+\))?'
str_r_loc      = r'(\((?P<r_loc>[a-z]+)\)[,;\s]*)*'
str_r = r'R(?P<r_code>(0|1|2|X))'                  +\
        r'(?P<r_suffixes>' + str_r_suffixes + r')' +\
        r'\s*' + str_r_loc
regex_r = re.compile(str_r, re.IGNORECASE)

# G - histopathological grading
str_g = r'G(?P<g_code>(1-2|3-4|X|1|2|3|4))'
regex_g = re.compile(str_g, re.IGNORECASE)

# L - lymphatic invasion
str_l = r'L(?P<l_code>(X|0|1))'
regex_l = re.compile(str_l, re.IGNORECASE)

# V - venous invasion
str_v = r'V(?P<v_code>(X|0|1|2))'
regex_v = re.compile(str_v, re.IGNORECASE)

# Perineural invasion
str_pn = r'Pn(?P<pn_code>(X|0|1))'
regex_pn = re.compile(str_pn, re.IGNORECASE)

# Serum tumor markers
str_serum = r'S(?P<serum_code>(X|0|1|2|3))'
regex_serum = re.compile(str_serum, re.IGNORECASE)

# Stage
str_stage = r'(\(?stage\s*(?P<stage_prefix>(yp?)?)' +\
            r'(?P<stage_num>([0-4]|iv|iii|ii|i))'   +\
            r'\s*(?P<stage_letter>(a|b|c|d)?)\)?)?'
regex_stage = re.compile(str_stage, re.IGNORECASE)

# dict to convert roman numerals to decimal strings
stage_dict = {'i': '1', 'ii': '2', 'iii': '3', 'iv': '4'}

# matcher for words, including hyphenated words, abbreviations, and punctuation
str_words = r'((\b[-a-zA-Z]+[.,;\s]*)+)?'

# punctuation that can appear in a code
str_punct = r'[,;]'

# The TNM code consists of T, N, and M codes with optional spacing inbetween,
# optional punctuation after, optional words, then zero or more optional
# R, G, L, V, Pn, or serum (S) codes with optional spacing inbetween.
str_tnm_opt = r'((' + str_r + '|' + str_g + r'|' + str_l + r'|' + str_v      +\
              r'|' + str_pn + r'|' + str_serum + r')[\s,;]?\s*)*' + str_stage

# NOTE (breast_cancer package fix): the original T->N connector
# (`\s*[\(]?m?[\)]?\s*`) only tolerated whitespace or a bare "(m)"
# multiplicity marker between the T and N blocks — real notation like
# "T2 multifocal N+" (a descriptive word in between) would not match at
# all. Widened to also skip up to 2 free words (that are not themselves the
# start of an N code) before requiring the N block.
str_t_to_n_connector = r'\s*(?:\(m\)\s*)?(?:(?!' + str_prefix_symbols + r'N)\w+\s+){0,2}'

# In EDS data, often the M is not present.
str_tnm_codeTNM = str_t + str_t_to_n_connector + str_n + str_m  +\
r'\s*' + r'(' + str_punct + r'\s*' + r')?'   +        r'(?P<tnm_opt>' + str_tnm_opt + r')'
regex_tnm_codeTNM = re.compile(str_tnm_codeTNM, re.IGNORECASE)
match_groupsTNM = ['t_prefix', 't_code', 't_certainty', 't_suffixes',
                'n_prefix', 'n_code', 'n_certainty', 'n_suffixes',
                'm_prefix', 'm_code', 'm_certainty', 'm_suffixes',
                'tnm_opt']

str_tnm_codeTN = str_t + str_t_to_n_connector + str_n + r'('+ str_punct + r'\s*' + r')?' + r'(?P<tnm_opt>' + str_tnm_opt + r')'
regex_tnm_codeTN = re.compile(str_tnm_codeTN, re.IGNORECASE)
match_groupsTN = ['t_prefix', 't_code', 't_certainty', 't_suffixes','n_prefix', 'n_code', 'n_certainty', 'n_suffixes','tnm_opt']

str_tnm_codeT = str_t + r'\s*[\(]?m?[\)]?\s*' + r'(' + str_punct + r'\s*' + r')?' + r'(?P<tnm_opt>' + str_tnm_opt + r')'
regex_tnm_codeT = re.compile(str_tnm_codeT, re.IGNORECASE)
match_groupsT = ['t_prefix', 't_code', 't_certainty', 't_suffixes','tnm_opt']

# valid punctuation chars for a TNM code
PUNCT_CHARS = [',', ';']

STR_NONE = 'None'


def get_certainty(text):
    """Return the certainty digit from a matching T, N, or M certainty factor."""
    certainty = None
    pos = text.find('C')
    if -1 != pos:
        certainty = text[pos + 1]
    return certainty


def get_suffixes(suffix_list, text):
    """Check text for all suffixes in the suffix list. Return a list of all
    suffixes found."""
    text_lc = text.lower()
    results = []
    for suffix in suffix_list:
        pos = text_lc.find(suffix)
        if -1 != pos:
            results.append(suffix)
    return results


def get_t_suffixes(group_name, text, code_dict):
    """Extract all T code suffixes and multiplicity values, if any."""
    suffixes = get_suffixes(T_SUFFIX_STRINGS, text)
    if len(suffixes) > 0:
        code_dict[group_name] = suffixes
    iterator = regex_t_mult.finditer(text)
    for match in iterator:
        code_dict['t_mult'] = match.group()


def get_n_suffixes(group_name, text, code_dict):
    """Extract all N code suffixes and multiplicity values, if any."""
    suffixes = get_suffixes(N_SUFFIX_STRINGS, text)
    if len(suffixes) > 0:
        code_dict[group_name] = suffixes
    match = regex_regional_metastases.search(text)
    if match:
        code_dict['n_regional_nodes_involved'] = match.group('regionals_involved')
        code_dict['n_regional_nodes_examined'] = match.group('regionals_examined')


def get_m_suffixes(group_name, text, code_dict):
    """Extract all M code suffixes, if any."""
    suffixes = get_suffixes(M_SUFFIX_STRINGS, text)
    if len(suffixes) > 0:
        code_dict[group_name] = suffixes


def extract_r(text, code_dict):
    """Extract all R code suffixes, if any."""
    r_codes = []
    r_suffixes = []
    r_locations = []

    iterator = regex_r.finditer(text)
    for match in iterator:
        r_codes.extend(match.group('r_code'))
        suffixes = get_suffixes(R_SUFFIX_STRINGS, match.group())
        if 0 == len(suffixes):
            suffixes = [STR_NONE]
        r_suffixes.extend(suffixes)
        loc = match.group('r_loc')
        if loc:
            r_locations.append(loc)
        else:
            r_locations.append(STR_NONE)

    if len(r_codes) > 0:
        code_dict['r_codes'] = r_codes
        code_dict['r_suffixes'] = r_suffixes
        code_dict['r_locations'] = r_locations


def get_code(code_name, code_dict, regex, text):
    match = regex.search(text)
    if match:
        code_dict[code_name] = match.group(code_name)


def get_stage(code_dict, text):
    match_stage = regex_stage.search(text)
    if match_stage:
        stage_prefix = match_stage.group('stage_prefix')
        stage_num = match_stage.group('stage_num')
        stage_letter = match_stage.group('stage_letter')

        if stage_prefix:
            code_dict['stage_prefix'] = stage_prefix
        if stage_num:
            key = stage_num.lower()
            code_dict['stage_number'] = stage_dict.get(key, stage_num)
        if stage_letter:
            code_dict['stage_letter'] = stage_letter.lower()


def run(sentence):
    """Search the sentence for all occurrences of a TNM code. Decode any
    that are found and serialize results to JSON."""
    results = []
    if list(regex_n.finditer(sentence)) == []:
        regex_tnm_code = regex_tnm_codeT
        match_groups = match_groupsT
    elif list(regex_m.finditer(sentence)) == []:
        regex_tnm_code = regex_tnm_codeTN
        match_groups = match_groupsTN
    else:
        regex_tnm_code = regex_tnm_codeTNM
        match_groups = match_groupsTNM

    iterator = regex_tnm_code.finditer(sentence)
    for match in iterator:
        code_dict = {}
        for field in TNM_FIELDS:
            code_dict[field] = EMPTY_FIELD

        match_text = match.group().strip()
        if len(match_text) > 0 and match_text[-1] in PUNCT_CHARS:
            match_text = match_text[:-1]

        code_dict['text'] = match_text
        code_dict['start'] = match.start()
        code_dict['end'] = match.start() + len(match_text)

        for group_name in match_groups:
            if match.group(group_name):
                group_text = match.group(group_name)
                if 'tnm_opt' == group_name:
                    get_code('l_code', code_dict, regex_l, group_text)
                    get_code('g_code', code_dict, regex_g, group_text)
                    get_code('v_code', code_dict, regex_v, group_text)
                    get_code('pn_code', code_dict, regex_pn, group_text)
                    get_code('serum_code', code_dict, regex_serum, group_text)
                    get_stage(code_dict, group_text)
                    extract_r(group_text, code_dict)
                elif 't_suffixes' == group_name:
                    get_t_suffixes(group_name, group_text, code_dict)
                elif 'n_suffixes' == group_name:
                    get_n_suffixes(group_name, group_text, code_dict)
                elif 'm_suffixes' == group_name:
                    get_m_suffixes(group_name, group_text, code_dict)
                elif -1 != group_name.find('certainty'):
                    code_dict[group_name] = get_certainty(group_text)
                else:
                    code_dict[group_name] = group_text

        results.append(code_dict)

    return json.dumps(results, indent=4)


def extractTNM(sentences):
    codes = []
    for sentence in sentences:
        json_string = run(sentence)
        json_data = json.loads(json_string)
        tnm_codes = [TnmCode(**c) for c in json_data]
        codes.append(tnm_codes)
    return codes
