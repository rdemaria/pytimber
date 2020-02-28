from pytimber.pagestore import *
from numpy import *


def mktest(idx, rec, comp=None):
    idx = array(idx)
    rec = array(rec)
    p = Page.from_data(idx, rec, ".", 0, comp=comp)
    try:
        nidx = p.get_idx_all()
        nrec = p.get_rec_all()
        assert all(nrec == rec)
        assert all(nidx == idx)
    finally:
        p.delete()


def makedata(nrec, lrec, lrecr):
    idx = arange(nrec * 1.0)
    val = [random.rand(lrec + int(random.rand() * lrecr)) for i in idx]
    return idx, val


def test_page():
    mktest([1], [""])
    mktest([1], ["a"])
    mktest([1], [["a", "b"]])
    mktest([1], [["a", "b", "ab"]])
    mktest([1, 2], ["a", "b"])
    mktest([1, 2], [["a"], ["b"]])
    mktest([1, 2], [["a", "b"], ["c", "d"]])
    mktest([1, 2], [["a", "b"], ["c", "d", "e"]])
    mktest([1, 2], [["a", "bc"], ["cd", "d", "eddd"]])

    mktest([1], [u""])
    mktest([1], [u"a"])
    mktest([1], [[u"a", u"b"]])
    mktest([1], [[u"a", u"b", u"ab"]])
    mktest([1, 2], [u"a", u"b"])
    mktest([1, 2], [[u"a"], [u"b"]])
    mktest([1, 2], [[u"a", u"b"], [u"c", u"d"]])
    mktest([1, 2], [[u"a", u"b"], [u"c", u"d", u"e"]])
    mktest([1, 2], [[u"a", u"bc"], [u"cd", u"d", u"eddd"]])

    mktest(arange(40), zeros((40, 4)))

    idx, rec = makedata(30, 80, 0)
    mktest(idx, rec)
    mktest(idx, rec, comp="gzip")
