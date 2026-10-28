# -*- coding: utf-8 -*-
"""Build a numbered MDPI bibliography in order of first citation."""
import os
import re
import glob
from refs import REFS

BASE = os.path.dirname(os.path.abspath(__file__))
files = sorted(glob.glob(os.path.join(BASE, "sections", "*.tex"))) + \
        sorted(glob.glob(os.path.join(BASE, "tables", "*.tex")))
text = "\n".join(open(f, encoding="utf-8").read() for f in files)

keys = []
for m in re.finditer(r"\\cite\{([^}]*)\}", text):
    for k in m.group(1).split(","):
        k = k.strip()
        if k and k not in keys:
            keys.append(k)

missing = [k for k in keys if k not in REFS]
uncited = [k for k in REFS if k not in keys]
print("cited", len(keys), "missing", missing, "uncited", uncited)


def wrap_urls(t):
    def repl(m):
        u = m.group(0)
        tail = ""
        while u and u[-1] in ".,;":
            tail = u[-1] + tail
            u = u[:-1]
        return "\\url{" + u + "}" + tail
    return re.sub(r"https://[^\s]+", repl, t)


body = ["\\begin{thebibliography}{99}", ""]
for k in keys:
    body.append("\\bibitem{" + k + "}")
    body.append(wrap_urls(REFS[k]))
    body.append("")
body.append("\\end{thebibliography}")
open(os.path.join(BASE, "sections", "references.tex"), "w", encoding="utf-8").write("\n".join(body))
print("wrote references.tex")
