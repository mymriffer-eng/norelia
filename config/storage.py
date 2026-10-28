from urllib.parse import quote, urljoin

from whitenoise.storage import CompressedManifestStaticFilesStorage


class NonStrictManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """
    Do not raise 500 errors when a referenced static file is missing.
    Missing files fall back to the plain (unhashed) URL and simply 404 in the browser.
    """

    manifest_strict = False

    def url(self, name, force=False):
        try:
            return super().url(name, force)
        except ValueError:
            return urljoin(self.base_url, quote(name))
