import re

from rdflib.term import Literal


class StatementComparator:
    def __init__(self, hashstr=None):
        self.hashstr = hashstr

    def compare(self, q1, q2):
        c = self.compare_context(q1, q2)
        if not c == 0:
            return c
        c = self.compare_subject(q1, q2)
        if not c == 0:
            return c
        c = self.compare_predicate(q1, q2)
        if not c == 0:
            return c
        return self.compare_object(q1, q2)

    def compare_context(self, q1, q2):
        r1 = q1[0]
        r2 = q2[0]
        if (r1 is None) and (r2 is None):
            return 0
        if (r1 is None) and (r2 is not None):
            return -1
        if (r1 is not None) and (r2 is None):
            return 1
        return self.compare_uri(r1, r2)

    def compare_subject(self, q1, q2):
        return self.compare_uri(q1[1], q2[1])

    def compare_predicate(self, q1, q2):
        return self.compare_uri(q1[2], q2[2])

    def compare_object(self, q1, q2):
        r1 = q1[3]
        r2 = q2[3]
        if isinstance(r1, Literal) and not isinstance(r2, Literal):
            return 1
        if not isinstance(r1, Literal) and isinstance(r2, Literal):
            return -1
        if isinstance(r1, Literal):
            return self.compare_literal(r1, r2)
        else:
            return self.compare_uri(r1, r2)

    def compare_literal(self, l1, l2):
        x1 = l1.encode("utf-8")
        x2 = l2.encode("utf-8")
        if x1 < x2:
            return -1
        if x1 > x2:
            return 1
        x1 = l1.datatype
        if l1.language is not None:
            x1 = None
        if l1.language is None and x1 is None:
            x1 = "http://www.w3.org/2001/XMLSchema#string"
        x2 = l2.datatype
        if l2.language is not None:
            x2 = None
        if l2.language is None and x2 is None:
            x2 = "http://www.w3.org/2001/XMLSchema#string"
        if (x1 is None) and (x2 is not None):
            return -1
        if (x1 is not None) and (x2 is None):
            return 1
        if (x1 is not None) and (x1 < x2):
            return -1
        if (x1 is not None) and (x1 > x2):
            return 1
        x1 = l1.language
        x2 = l2.language
        if (x1 is None) and (x2 is not None):
            return -1
        if (x1 is not None) and (x2 is None):
            return 1
        if (x1 is not None) and (x1 < x2):
            return -1
        if (x1 is not None) and (x1 > x2):
            return 1
        return 0

    def compare_uri(self, r1, r2):
        s1 = r1.encode("utf-8")
        s2 = r2.encode("utf-8")
        p1 = s1
        p2 = s2
        if self.hashstr is not None:
            try:
                p1 = re.sub(self.hashstr, " ", s1)
            except Exception:
                p1 = re.sub(self.hashstr, " ", r1)
            try:
                p2 = re.sub(self.hashstr, " ", s2)
            except Exception:
                p2 = re.sub(self.hashstr, " ", r2)
        if p1 < p2:
            return -1
        if p1 == p2:
            return 0
        return 1
