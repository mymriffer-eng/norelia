from whitenoise.storage import CompressedManifestStaticFilesStorage


class NonStrictManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Do not raise 500 errors when a referenced static file is missing from the manifest."""

    manifest_strict = False
