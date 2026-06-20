"""Tests for the integration's constants module."""

from __future__ import annotations

import json
import os
import re

from waveshare_eth2x.const import DOMAIN, MANUFACTURER


def test_domain_is_non_empty_string() -> None:
    assert isinstance(DOMAIN, str)
    assert DOMAIN
    # HA domains may not start with the reserved "ha_" prefix.
    assert not DOMAIN.startswith("ha_"), (
        f"HA domain {DOMAIN!r} must not start with 'ha_' (HA convention)."
    )


def test_manufacturer_is_non_empty_string() -> None:
    assert isinstance(MANUFACTURER, str)
    assert MANUFACTURER


def test_manifest_domain_matches_const_domain() -> None:
    """The manifest domain must equal const.DOMAIN. A mismatch causes
    'Invalid handler specified' on every config-flow call."""
    manifest_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "waveshare_eth2x",
        "manifest.json",
    )
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    assert manifest["domain"] == DOMAIN, (
        f"manifest.domain ({manifest['domain']!r}) must equal "
        f"const.DOMAIN ({DOMAIN!r})."
    )


def test_manifest_folder_matches_domain() -> None:
    """The custom_components folder name must match the domain, otherwise
    HACS fails with 'No manifest.json file found ...'."""
    manifest_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "waveshare_eth2x",
        "manifest.json",
    )
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    folder = os.path.basename(os.path.dirname(manifest_path))
    assert folder == manifest["domain"], (
        f"Folder name {folder!r} must match manifest.domain "
        f"{manifest['domain']!r} (HACS requires the folder to live at "
        f"custom_components/<domain>/)."
    )


def test_manifest_has_config_flow_flag() -> None:
    manifest_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "waveshare_eth2x",
        "manifest.json",
    )
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    assert manifest.get("config_flow") is True, (
        "manifest.config_flow must be true so the integration is configurable "
        "via the UI."
    )


def test_manifest_version_is_semver() -> None:
    manifest_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "waveshare_eth2x",
        "manifest.json",
    )
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    version = manifest.get("version", "")
    assert re.match(r"^\d+\.\d+\.\d+", version), (
        f"manifest.version {version!r} must follow semver (X.Y.Z)."
    )
