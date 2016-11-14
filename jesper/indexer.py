import glob
import math
import begin
import re
import nltk
import lxml
import pickle
import os.path
from pprint import pprint
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
from lxml.html.clean import Cleaner
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from collections import Counter

not_word_chars = re.compile(r'\s+|[^\w]|\s+[^\w]*|[^A-Za-z]')
stemmer = SnowballStemmer('english')
cleaner = Cleaner(scripts=True, javascript=True, comments=True, style=True, embedded=True, forms=True, annoying_tags=True)
num_docs = 0

class Document(object):
    def __init__(self, path, tokens, counter):
        self.path = path
        self.tokens = tokens
        self.counter = counter

    @property
    def doc_length(self):
        return math.sqrt(sum([math.pow((1. + math.log(cnt, 10)), 2) for cnt in self.counter.values()]))


class Token(object):
    def __init__(self, text):
        self.text = text
        self.posting_list = dict()

    def df(self):
        return len(self.posting_list)

    def idf(self, num_docs):
        df = self.df()
        return (math.log10(num_docs / self.df())) if df > 0 else 0

    def tf(self, path = None, query_doc = None):
        if query_doc:
            return query_doc.counter[self.text]
        elif path in self.posting_list.keys():
            return self.posting_list[path][1]
        else:
            return 0

    def tf_star(self, path = None, query_doc = None):
        tf = self.tf(path = path, query_doc = query_doc)
        return (1 + math.log10(tf)) if tf > 0 else 0

    def w(self, path = None, query_doc = None, num_docs = 0):
        return self.tf_star(path = path, query_doc = query_doc) * self.idf(num_docs)

    def norm_w(self, doc = None, query_doc = None, num_docs = 0):
        w = self.w(path = doc.path if doc else None, query_doc = query_doc, num_docs = num_docs)
        d_len = query_doc.doc_length if query_doc else doc.doc_length
        return w / d_len

def clean_text(string):
    return re.sub(not_word_chars, " ", string).lower()


def extract_text(html):
    text = lxml.html.fromstring(cleaner.clean_html(html)).text_content()
    return clean_text(text)


def tokenize_string(string):
    tokens = nltk.word_tokenize(string)
    tokens = [stemmer.stem(token) for token in tokens if token not in stopwords.words('english')]
    return tokens


def search(query, terms):
    query = clean_text(query)
    query_tokens = tokenize_string(query)
    query_doc = Document('query', query_tokens, Counter(query_tokens))
    findings = list()
    for word in query_tokens:
        print(word)
        if word in terms.keys():
            found = set([doc for doc, _ in terms[word].posting_list.values()])
            print('Found:', len(found), 'for', word)
        else:
            found = set()
            print('Nothing found for', word)
        findings.append(found)
    if findings:
        results = set.intersection(*findings)
        scored = list()
        q_norm_w = dict()
        for t in terms.values():
            if t.text in query_tokens:
                q_norm_w[t.text] = t.norm_w(query_doc = query_doc, num_docs = num_docs)
        for doc in results:
            score = sum([q_norm_w[t.text] * t.norm_w(doc = doc, num_docs = num_docs) for t in terms.values() if t.text in query_tokens])
            scored.append((score, doc.path))
        scored_view = sorted(scored, reverse=True)
        for s, p in scored_view:
            print(s, p)


def index_document(path):
    try:
        content = ''
        with open(path, "r") as f:
            content = bytes(f.read(), 'utf-8')
            content = content.decode('unicode_escape')
        clean_text = extract_text(content)
        tokens = tokenize_string(clean_text)
        return Document(path, tokens, Counter(tokens))
    except:
        return None


@begin.start
def main(dir: 'Directory tree of hosts' = './Back', max: 'Max pages to index' = -1, terms: 'Pickeled terms dict' = dict()):
    "Index stuff"
    global num_docs
    terms_path = None
    files = set()
    if not isinstance(terms, dict):
        terms_path = terms
        if os.path.exists(terms_path):
            print('Loading terms from', terms_path)
            terms, files = pickle.load(open(terms_path, "rb"))
        else:
            terms = dict()
    max = int(max)
    if max:
        print('Indexing...')
        tmp_files = glob.glob(dir + '/**/content', recursive=True)
        if max > 0:
            tmp_files = tmp_files[:int(max)]
        print('Files to index', num_docs)
        with ProcessPoolExecutor(max_workers=8) as executor:
            futures = { executor.submit(index_document, path) for path in tmp_files }
            for i, done in enumerate(as_completed(futures)):
                res = done.result()
                pprint(res)
                if not res:
                    continue
                for token_text, cnt in res.counter.items():
                    if not token_text in terms.keys():
                        token = Token(token_text)
                        terms[token_text] = token
                    terms[token_text].posting_list[res.path] = (res, cnt)
                print('{} / {} {}'.format(i, len(files), res.path))
        files.update(set(tmp_files))
    if terms_path:
        print('Hope you like pickles!')
        pickle.dump((terms, files), open(terms_path, "wb"))

    num_docs = len(files)
    print('Done indexing! [', len(terms), 'unique tokens]')
    while True:
        query = input('Enter search query: ')
        if len(query):
            search(query, terms)
        else:
            break

