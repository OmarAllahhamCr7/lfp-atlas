#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inline styles + data + app into LFP_Atlas_standalone.html — one file, no server, no CDN."""
import os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(ROOT)
r = lambda p: open(os.path.join(OUT, p), encoding="utf-8").read()

html = r("index.html")
html = html.replace('<link rel="stylesheet" href="styles.css">', "<style>\n" + r("styles.css") + "\n</style>")
html = html.replace('<script src="data.js"></script>', "<script>\n" + r("data.js") + "\n</script>")
html = html.replace('<script src="app.js"></script>', "<script>\n" + r("app.js") + "\n</script>")
assert "styles.css" not in html and 'src="data.js"' not in html and 'src="app.js"' not in html
out = os.path.join(OUT, "LFP_Atlas_standalone.html")
open(out, "w", encoding="utf-8").write(html)
print("wrote", out, "|", os.path.getsize(out), "bytes")
