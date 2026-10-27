"""Opt-in Chromium smoke checks against a real .preview build (Playwright 1.56.0)."""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".local/playwright-browsers"))
from playwright.sync_api import sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    artifact = ROOT / ".preview"
    evidence = ROOT / "reports/notes-browser"
    evidence.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(artifact)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    book = "/books/quantum-python-notes/"
    chapters = sorted((artifact / book.lstrip("/") / "chapters").glob("*.html"))
    report = {"ok": False, "browser": "", "pages": [], "interactions": [], "failed_requests": [], "console_errors": []}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            report["browser"] = browser.version
            for width in (390, 768, 1440):
                context = browser.new_context(viewport={"width": width, "height": 900},
                                              permissions=["clipboard-read", "clipboard-write"])
                page = context.new_page()
                page.set_default_timeout(15000)
                page.on("requestfailed", lambda request: report["failed_requests"].append({"url": request.url, "failure": request.failure}))
                page.on("pageerror", lambda error: report["console_errors"].append(str(error)))
                for path in [artifact / book.lstrip("/") / "index.html", *chapters]:
                    relative = path.relative_to(artifact).as_posix()
                    response = page.goto(origin + "/" + relative, wait_until="networkidle")
                    page.wait_for_function("!document.querySelector('.math') || !!document.querySelector('mjx-container')")
                    page.evaluate("async () => { if (window.MathJax?.startup?.promise) await MathJax.startup.promise; await document.fonts.ready; }")
                    metrics = page.evaluate("""() => ({
                      viewport: innerWidth, pageWidth: document.documentElement.scrollWidth,
                      math: document.querySelectorAll('.math').length,
                      renderedMath: document.querySelectorAll('mjx-container').length,
                      mathErrors: [...document.querySelectorAll('mjx-merror, [data-mjx-error]')].map(e => e.textContent),
                      code: document.querySelectorAll('pre.sourceCode').length,
                      next: document.querySelector('.nav-page-next a')?.getAttribute('href'),
                      previous: document.querySelector('.nav-page-previous a')?.getAttribute('href'),
                      heading: document.querySelector('h1')?.textContent,
                      overflow: [...document.querySelectorAll('pre, mjx-container[display]')].filter(e => e.scrollWidth > e.clientWidth + 2).map(e => {
                        let node = e, scrollable = false;
                        while (node && node !== document.body) {
                          if (['auto', 'scroll'].includes(getComputedStyle(node).overflowX)) {
                            const previous = node.scrollLeft;
                            node.scrollLeft = 20;
                            scrollable = node.scrollLeft > 0;
                            node.scrollLeft = previous;
                            if (scrollable) break;
                          }
                          node = node.parentElement;
                        }
                        return {tag:e.tagName, style:getComputedStyle(e).overflowX, width:e.clientWidth, content:e.scrollWidth, scrollable};
                      })
                    })""")
                    metrics.update(path=relative, width=width, status=response.status)
                    report["pages"].append(metrics)
                    if path.stem in {"index", "13-mean-field", "16-properties"}:
                        page.screenshot(path=str(evidence / f"{width}-{path.stem}.png"), full_page=False)
                    if response.status != 200 or metrics["pageWidth"] > width + 2 or metrics["mathErrors"]:
                        raise AssertionError(f"Page check failed: {metrics}")
                    if metrics["math"] != metrics["renderedMath"]:
                        raise AssertionError(f"Unrendered math: {relative}")
                    if any(not item["scrollable"] for item in metrics["overflow"]):
                        raise AssertionError(f"Clipped code/math: {relative}")
                page.goto(origin + book + "chapters/13-mean-field.html", wait_until="networkidle")
                # Search through the visible control, not a programmatic API call.
                search = page.locator("input.aa-Input:visible")
                if not search.count():
                    page.locator("button.quarto-search-button:visible").click()
                    search = page.locator("input.aa-Input:visible")
                search.fill("费米")
                results = page.locator(".aa-Panel a.search-result-link")
                results.first.wait_for(state="visible")
                hrefs = results.evaluate_all("els => els.map(e => e.href)")
                assert hrefs and all(book in href for href in hrefs), hrefs
                results.first.click()
                page.wait_for_url("**/books/quantum-python-notes/**")
                page.keyboard.press("Escape")
                # Theme control is in the collapsible sidebar on narrow screens.
                toggle = page.locator("a.quarto-color-scheme-toggle:visible")
                if not toggle.count():
                    page.locator("button.quarto-btn-toggle:visible").click()
                    toggle = page.locator("a.quarto-color-scheme-toggle:visible")
                before = page.locator("body").get_attribute("class")
                toggle.click()
                page.wait_for_function("before => document.body.className !== before", arg=before)
                after = page.locator("body").get_attribute("class")
                page.wait_for_load_state("networkidle")
                page.evaluate("document.fonts.ready")
                if width < 992:
                    collapse = page.locator("button.quarto-btn-toggle:visible")
                    if collapse.get_attribute("aria-expanded") == "true":
                        collapse.click()
                page.goto(origin + book + "chapters/13-mean-field.html", wait_until="networkidle")
                page.locator("button.code-copy-button").first.click()
                copied = page.evaluate("navigator.clipboard.readText()")
                assert "import numpy" in copied
                page.locator(".nav-page-next a").click()
                page.wait_for_url("**/14-fci.html")
                page.wait_for_load_state("networkidle")
                page.evaluate("document.fonts.ready")
                page.locator(".nav-page-previous a").click()
                page.wait_for_url("**/13-mean-field.html")
                page.wait_for_load_state("networkidle")
                page.evaluate("document.fonts.ready")
                report["interactions"].append({"width": width, "search_results": len(hrefs), "theme_before": before,
                                               "theme_after": after, "copy": True, "next_previous": True})
                context.close()
            browser.close()
        report["ok"] = len(report["pages"]) == 51 and len(report["interactions"]) == 3 and not report["console_errors"] and not report["failed_requests"]
    except Exception as error:
        report["error"] = str(error)
    finally:
        server.shutdown()
        server.server_close()
        (ROOT / "reports/notes-browser.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("ok", "browser", "interactions", "failed_requests", "console_errors")}, ensure_ascii=False))
    print("Pages checked:", len(report["pages"]), "error:", report.get("error"))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
