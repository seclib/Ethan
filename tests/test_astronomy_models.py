"""
Tests for the unified astronomy data models.
"""

import sys
import types

# Create a dummy httpx module for standalone model testing
dummy_httpx = types.ModuleType("httpx")
dummy_httpx.AsyncClient = object
dummy_httpx.Timeout = object
dummy_httpx.FollowRedirects = object
sys.modules["httpx"] = dummy_httpx

from core.models.astronomy import (
    CoordinateSystem,
    ObjectType,
    MagnitudeSystem,
    Waveband,
    ProvenanceStatus,
    AccessLevel,
    SkyCoord,
    SkyObject,
    EphemerisBody,
    LightCurve,
    LightCurvePoint,
    ImageCutout,
    Provenance,
    AstroCatalog,
    SkyObjectLike,
    SkyCoordLike,
    EphemerisBodyLike,
    ProvenanceLike,
)


def test_coordinate_system_enum():
    assert CoordinateSystem.EQUATORIAL_J2000.value == "icrs_j2000"
    assert CoordinateSystem.GALACTIC.value == "galactic"


def test_object_type_enum():
    assert ObjectType.STAR.value == "star"
    assert ObjectType.UNKNOWN.value == "unknown"
    assert ObjectType.SOLAR_SYSTEM_BODY.value == "solar_system_body"


def test_magnitude_system_enum():
    assert MagnitudeSystem.VEGETA.value == "vegeta"
    assert MagnitudeSystem.JOSO.value == "joso"


def test_waveband_enum():
    assert Waveband.OPTICAL.value == "optical"
    assert Waveband.X_RAY.value == "xray"
    assert Waveband.RADIO.value == "radio"


def test_provenance_status_enum():
    assert ProvenanceStatus.VERIFIED.value == "verified"
    assert ProvenanceStatus.PENDING.value == "pending"


def test_access_level_enum():
    assert AccessLevel.PUBLIC.value == "public"
    assert AccessLevel.CONFIDENTIAL.value == "confidential"


def test_skycoord_basic():
    coord = SkyCoord(ra=10.68458, dec=41.26917)
    ra, dec = coord.to_degrees()
    assert abs(ra - 10.68458) < 1e-6
    assert abs(dec - 41.26917) < 1e-6


def test_skycoord_with_epoch():
    coord = SkyCoord(ra=10.68458, dec=41.26917, epoch="J1950", system=CoordinateSystem.GALACTIC)
    assert coord.epoch == "J1950"
    assert coord.system == CoordinateSystem.GALACTIC


def test_skymobject_basic():
    obj = SkyObject(
        identifier="HD 209458",
        common_names=["Osiris"],
        type=ObjectType.STAR,
        coords=SkyCoord(ra=32.8485, dec=41.3207),
        magnitude=7.65,
        magnitude_system=MagnitudeSystem.VEGETA,
    )
    assert obj.identifier == "HD 209458"
    assert obj.common_names == ["Osiris"]
    assert obj.type == ObjectType.STAR
    assert obj.magnitude == 7.65
    assert obj.magnitude_system == MagnitudeSystem.VEGETA


def test_skymobject_to_dict():
    obj = SkyObject(
        identifier="HD 209458",
        common_names=["Osiris"],
        type=ObjectType.STAR,
        coords=SkyCoord(ra=32.8485, dec=41.3207),
    )
    d = obj.to_dict()
    assert d["identifier"] == "HD 209458"
    assert d["type"] == "star"
    assert len(d["catalog_links"]) == 0
    assert d["provenance"]["source"] == "unknown"


def test_ephemeris_body_basic():
    body = EphemerisBody(
        name="Jupiter",
        body_type="planet",
        identifier="501",
        coords=SkyCoord(ra=0, dec=0),
        distance_au=5.2,
        magnitude=-2.7,
        radius_km=69911,
        ephemeris_source="jpl_horizons",
    )
    assert body.name == "Jupiter"
    assert body.body_type == "planet"
    assert body.identifier == "501"
    assert body.distance_au == 5.2
    assert body.ephemeris_source == "jpl_horizons"


def test_ephemeris_body_basic():
    body = EphemerisBody(
        name="Mars",
        body_type="planet",
        identifier="3697",
        coords=SkyCoord(ra=0, dec=0),
        distance_au=1.52,
    )
    assert body.name == "Mars"
    assert body.body_type == "planet"
    assert body.identifier == "3697"
    assert body.distance_au == 1.52


def test_lightcurve_point():
    point = LightCurvePoint(
        time_btjd=2457000.5,
        flux=1.002,
        flux_error=0.001,
        magnitude=12.34,
        band=Waveband.V,
    )
    assert point.time_btjd == 2457000.5
    assert point.flux == 1.002
    assert point.magnitude == 12.34


def test_lightcurve_basic():
    lc = LightCurve(
        identifier="tess_2025000",
        target_name="TOI-1234",
        points=[
            LightCurvePoint(time_btjd=2457000.0, flux=1.0),
            LightCurvePoint(time_btjd=2457000.5, flux=0.995),
        ],
        band=Waveband.OPTICAL,
    )
    assert lc.identifier == "tess_2025000"
    assert lc.target_name == "TOI-1234"
    assert len(lc.points) == 2
    assert lc.band == Waveband.OPTICAL


def test_lightcurve_to_dict():
    lc = LightCurve(
        identifier="test_lc",
        target_name="TOI-1234",
        points=[],
        band=Waveband.OPTICAL,
    )
    d = lc.to_dict()
    assert d["identifier"] == "test_lc"
    assert d["target_name"] == "TOI-1234"
    assert "points" in d


def test_imagecutout_basic():
    img = ImageCutout(
        identifier="jw01234-00001",
        object_id="NGC 1234",
        source="jwst",
        waveband=Waveband.NIR,
        size_pixels=(1024, 1024),
        pixel_scale=0.06,
        timestamp=None,
    )
    assert img.identifier == "jw01234-00001"
    assert img.object_id == "NGC 1234"
    assert img.source == "jwst"
    assert img.waveband == Waveband.NIR


def test_imagecutout_to_dict():
    img = ImageCutout(
        identifier="test_img",
        object_id="Star A",
        source="test",
        waveband=Waveband.OPTICAL,
        size_pixels=(512, 512),
        pixel_scale=0.1,
    )
    d = img.to_dict()
    assert d["identifier"] == "test_img"
    assert d["source"] == "test"
    assert d["waveband"] == "optical"
    assert "provenance" not in d or d["provenance"] is None


def test_provenance_basic():
    prov = Provenance(
        source="simbad",
        access_date=None,  # uses default
        url="https://simbad.u-strasbg.fr/simbad/sim-id?Ident=HD+209458",
        fetcher="simbad_adapter",
        request_id="req_12345",
        status=ProvenanceStatus.VERIFIED,
    )
    d = prov.to_dict()
    assert d["source"] == "simbad"
    assert d["fetcher"] == "simbad_adapter"
    assert d["status"] == "verified"
    assert d["url"] == "https://simbad.u-strasbg.fr/simbad/sim-id?Ident=HD+209458"
    assert "api_key_ref" not in d or d["api_key_ref"] is None


def test_astrocatalog_basic():
    obj = SkyObject(
        identifier="Test",
        type=ObjectType.STAR,
        coords=SkyCoord(ra=0, dec=0),
    )
    cat = AstroCatalog(
        catalog_id="test_catalog",
        name="Test Catalog",
        objects=[obj],
        query_filters={"type": "star"},
    )
    assert cat.catalog_id == "test_catalog"
    assert cat.name == "Test Catalog"
    assert len(cat.objects) == 1
    assert cat.query_filters == {"type": "star"}


def test_aliases_exist():
    assert SkyObjectLike is SkyObject
    assert SkyCoordLike is SkyCoord
    assert EphemerisBodyLike is EphemerisBody
    assert ProvenanceLike is Provenance
