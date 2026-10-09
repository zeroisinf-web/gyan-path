"""Assemble the deployable site:  web/ + data/  ->  site/   (what GitHub Pages serves)

Usage:  python build_site.py
- copies the app and the latest data
- stamps sw.js with a hash of the app files, so phones pick up a new app version automatically
- draws the PNG app icons (192/512) if they are missing
"""
import hashlib, os, shutil

import paths

WEB = os.path.join(paths.ROOT, "web")
SITE = os.path.join(paths.ROOT, "site")


def icons():
    from PIL import Image, ImageDraw
    for n in (192, 512):
        out = os.path.join(WEB, "icons", f"icon-{n}.png")
        if os.path.exists(out):
            continue
        s = n / 512
        img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, n - 1, n - 1], radius=int(112 * s), fill="#1d4f91")
        d.polygon([(120 * s, 150 * s), (256 * s, 168 * s), (256 * s, 388 * s), (120 * s, 370 * s)], fill="#ffffff")
        d.polygon([(392 * s, 150 * s), (256 * s, 168 * s), (256 * s, 388 * s), (392 * s, 370 * s)], fill="#cfe0fb")
        d.line([(256 * s, 168 * s), (256 * s, 388 * s)], fill="#1d4f91", width=max(2, int(10 * s)))
        img.save(out)


def main():
    icons()
    if os.path.exists(SITE):
        shutil.rmtree(SITE)
    shutil.copytree(WEB, SITE)
    shutil.copytree(paths.DATA, os.path.join(SITE, "data"), ignore=shutil.ignore_patterns("*.tmp"))
    h = hashlib.sha1()
    for root, _, files in sorted(os.walk(WEB)):
        for f in sorted(files):
            h.update(open(os.path.join(root, f), "rb").read())
    sw = os.path.join(SITE, "sw.js")
    code = open(sw, encoding="utf-8").read().replace("__BUILD__", h.hexdigest()[:10])
    open(sw, "w", encoding="utf-8").write(code)
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    total = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(SITE) for f in fs)
    print(f"site built: {SITE}  ({total / 1048576:.1f} MB)")


if __name__ == "__main__":
    main()
