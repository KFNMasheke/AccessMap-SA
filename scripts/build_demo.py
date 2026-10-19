#!/usr/bin/env python3
"""Rebuild fictional sample data, portable QGIS project and printable layouts.

Run with QGIS's Python interpreter and QT_QPA_PLATFORM=offscreen if headless.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "processing"))
from accessmap_sa import Facility, NearestIndex, assess
from qgis.core import (
    QgsApplication, QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsFeature, QgsField, QgsFillSymbol, QgsGeometry,
    QgsLayoutExporter, QgsLayoutItemLabel, QgsLayoutItemMap, QgsLayoutItemScaleBar,
    QgsLayoutPoint, QgsLayoutSize, QgsMarkerSymbol, QgsPointXY, QgsPrintLayout,
    QgsProject, QgsRectangle, QgsRendererCategory, QgsUnitTypes, QgsVectorFileWriter,
    QgsVectorLayer, Qgis,
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor, QFont

COLORS = {"near": "#168575", "moderate": "#e9b95b", "far": "#c86b58", "unknown": "#aab4bc"}
BAND_NAMES = {"near": "Near: up to 1 km", "moderate": "Moderate: over 1 to 3 km",
              "far": "Far: over 3 km", "unknown": "Unknown: no recorded facility"}


def csv_write(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def memory(name, geom, fields):
    layer = QgsVectorLayer(f"{geom}?crs=EPSG:32735", name, "memory")
    layer.dataProvider().addAttributes([QgsField(k, t) for k, t in fields])
    layer.updateFields()
    return layer


def add(layer, geometry, attributes):
    feature = QgsFeature(layer.fields())
    feature.setGeometry(geometry)
    feature.setAttributes(attributes)
    assert layer.dataProvider().addFeatures([feature])[0]


def persist(layer, name, first=False):
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = name
    if not first:
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    target = ROOT / "data" / "accessmap_demo.gpkg"
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, str(target), QgsProject.instance().transformContext(), options)
    if result[0] != QgsVectorFileWriter.NoError:
        raise RuntimeError(str(result))
    saved = QgsVectorLayer(f"{target}|layername={name}", layer.name(), "ogr")
    assert saved.isValid()
    return saved


def category_style(layer, polygon=False):
    categories = []
    for band, color in COLORS.items():
        symbol = (QgsFillSymbol.createSimple({"color": color, "outline_color": "#f7f7f2",
                                             "outline_width": "0.15"}) if polygon else
                  QgsMarkerSymbol.createSimple({"color": color, "size": "2.8",
                                                 "outline_color": "#ffffff", "outline_width": "0.25"}))
        categories.append(QgsRendererCategory(band, symbol, BAND_NAMES[band]))
    layer.setRenderer(QgsCategorizedSymbolRenderer("access_band", categories))


def label(layout, text, x, y, w, h, size=10, color="#233b43", bold=False):
    item = QgsLayoutItemLabel(layout)
    item.setText(text)
    item.setFont(QFont("DejaVu Sans", size, QFont.Bold if bold else QFont.Normal))
    item.setFontColor(QColor(color))
    item.attemptMove(QgsLayoutPoint(x, y))
    item.attemptResize(QgsLayoutSize(w, h))
    layout.addLayoutItem(item)
    return item


def build():
    project = QgsProject.instance()
    project.clear()
    project.setCrs(QgsCoordinateReferenceSystem("EPSG:32735"))
    project.setTitle("AccessMap SA | Fictional Gauteng service-access demonstration")
    project.setFilePathStorage(Qgis.FilePathType.Relative)
    project.setBackgroundColor(QColor("#f6f7f2"))
    origins = [{"id": f"C{r:02d}{c:02d}", "x": 590250 + c*500, "y": 7112250 + r*500}
               for r in range(16) for c in range(20)]
    facilities = [
        Facility("D-C1", "Demo West Clinic", "clinic", 591000, 7113500),
        Facility("D-C2", "Demo North Clinic", "clinic", 595000, 7118500),
        Facility("D-C3", "Demo Boundary Clinic", "clinic", 588500, 7116000),
        Facility("D-L1", "Demo Learning Library", "library", 592000, 7118000),
        Facility("D-L2", "Demo East Library", "library", 600500, 7112500),
    ]
    csv_write(ROOT / "data/demo_origins.csv", ["id", "x", "y"], origins)
    csv_write(ROOT / "data/demo_facilities.csv", ["id", "name", "category", "x", "y"],
              [f.__dict__ for f in facilities])
    fields = [("id", QVariant.String), ("name", QVariant.String), ("category", QVariant.String)]
    layer = memory("Facilities | FICTIONAL", "Point", fields)
    for f in facilities:
        add(layer, QgsGeometry.fromPointXY(QgsPointXY(f.x, f.y)), [f.id, f.name, f.category])
    facilities_layer = persist(layer, "facilities", first=True)
    cats = []
    for category, color, shape in [("clinic", "#193c50", "cross_fill"), ("library", "#744a86", "diamond")]:
        cats.append(QgsRendererCategory(category, QgsMarkerSymbol.createSimple(
            {"name": shape, "color": color, "size": "4", "outline_color": "#ffffff",
             "outline_width": "0.4"}), category.title()))
    facilities_layer.setRenderer(QgsCategorizedSymbolRenderer("category", cats))
    project.addMapLayer(facilities_layer)
    layer = memory("Community sample points | FICTIONAL", "Point", [("id", QVariant.String)])
    for row in origins:
        add(layer, QgsGeometry.fromPointXY(QgsPointXY(row["x"], row["y"])), [row["id"]])
    origin_layer = persist(layer, "origins")
    project.addMapLayer(origin_layer)
    project.layerTreeRoot().findLayer(origin_layer.id()).setItemVisibilityChecked(False)
    fields = [("origin_id", QVariant.String), ("nearest_id", QVariant.String),
              ("nearest_name", QVariant.String), ("distance_m", QVariant.Double),
              ("access_band", QVariant.String), ("category", QVariant.String)]
    all_layers = {}
    all_results = {}
    point_layers = []
    for category in ["clinic", "library"]:
        index = NearestIndex(f for f in facilities if f.category == category)
        points = memory(f"{category.title()} access points | FICTIONAL", "Point", fields)
        cells = memory(f"{category.title()} sample grid | FICTIONAL", "Polygon", fields)
        results = []
        for row in origins:
            result = assess(index, row["x"], row["y"])
            attributes = [row["id"], result["nearest_id"], result["nearest_name"],
                          result["distance_m"], result["access_band"], category]
            add(points, QgsGeometry.fromPointXY(QgsPointXY(row["x"], row["y"])), attributes)
            add(cells, QgsGeometry.fromRect(QgsRectangle(row["x"]-250, row["y"]-250,
                                                        row["x"]+250, row["y"]+250)), attributes)
            results.append({"origin_id": row["id"], **result})
        point_layer = persist(points, f"{category}_access")
        cell_layer = persist(cells, f"{category}_cells")
        category_style(point_layer)
        category_style(cell_layer, True)
        point_layer.saveNamedStyle(str(ROOT / f"data/{category}_points.qml"))
        cell_layer.saveNamedStyle(str(ROOT / f"data/{category}_cells.qml"))
        project.addMapLayer(point_layer)
        project.addMapLayer(cell_layer)
        project.layerTreeRoot().findLayer(point_layer.id()).setItemVisibilityChecked(False)
        project.layerTreeRoot().findLayer(cell_layer.id()).setItemVisibilityChecked(category == "clinic")
        all_layers[category] = cell_layer
        point_layers.append(point_layer)
        all_results[category] = results
    project.layerTreeRoot().setCustomLayerOrder([facilities_layer, origin_layer] + point_layers +
                                               [all_layers[c] for c in ["clinic", "library"]])
    project.layerTreeRoot().setHasCustomLayerOrder(True)
    extent = QgsRectangle(587700, 7111400, 601400, 7121000)
    project.viewSettings().setDefaultViewExtent(__import__("qgis.core", fromlist=["QgsReferencedRectangle"]).QgsReferencedRectangle(extent, project.crs()))
    for category in ["clinic", "library"]:
        results = all_results[category]
        counts = {band: sum(r["access_band"] == band for r in results) for band in COLORS}
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName(f"{category.title()} access | fictional demo")
        layout.pageCollection().pages()[0].setPageSize("A4", __import__("qgis.core", fromlist=["QgsLayoutItemPage"]).QgsLayoutItemPage.Landscape)
        label(layout, "ACCESSMAP SA", 12, 7, 170, 12, 22, bold=True)
        label(layout, "Find the gaps. Improve access.", 13, 20, 180, 8, 10)
        label(layout, f"{category.title()} access / fictional Gauteng demo", 13, 31, 260, 9, 13, bold=True)
        map_item = QgsLayoutItemMap(layout)
        map_item.attemptMove(QgsLayoutPoint(13, 45))
        map_item.attemptResize(QgsLayoutSize(192, 135))
        map_item.setCrs(project.crs())
        map_item.setLayers([facilities_layer, all_layers[category]])
        map_item.setKeepLayerSet(True)
        layout.addLayoutItem(map_item)
        map_item.zoomToExtent(extent)
        map_item.setBackgroundColor(QColor("#f2f5f2"))
        label(layout, "SAMPLE POINTS", 214, 47, 72, 8, 10, bold=True)
        label(layout, "320", 214, 57, 70, 17, 29, bold=True)
        label(layout, "Not a population estimate", 214, 75, 73, 8, 8)
        for n, band in enumerate(["near", "moderate", "far"]):
            text_color = {"near": "#116b59", "moderate": "#805b16", "far": "#a04130"}[band]
            label(layout, f"{counts[band]}  {BAND_NAMES[band]}", 214, 91+n*13, 73, 11, 9, text_color, True)
        label(layout, "+ Clinic     Diamond: library\nN is up / EPSG:32735\nGrid cells: 500 x 500 m", 214, 135, 76, 25, 8)
        label(layout, "STRAIGHT-LINE DISTANCE\nNo walking routes, opening hours,\ncapacity or safety assessment.", 214, 165, 76, 25, 8)
        scale = QgsLayoutItemScaleBar(layout)
        scale.setStyle("Single Box")
        scale.setLinkedMap(map_item)
        scale.setUnits(QgsUnitTypes.DistanceKilometers)
        scale.setUnitsPerSegment(1)
        scale.setNumberOfSegments(2)
        scale.setNumberOfSegmentsLeft(0)
        scale.setUnitLabel("km")
        scale.setFont(QFont("DejaVu Sans", 8))
        scale.attemptMove(QgsLayoutPoint(15, 182))
        layout.addLayoutItem(scale)
        label(layout, "FICTIONAL DATA / Demonstration only. Colours describe cell-centre distance; not whole-cell coverage.", 13, 194, 275, 8, 8)
        project.layoutManager().addLayout(layout)
        settings = QgsLayoutExporter.ImageExportSettings()
        settings.dpi = 150
        status = QgsLayoutExporter(layout).exportToImage(str(ROOT / f"outputs/{category}-map.png"), settings)
        assert status == QgsLayoutExporter.Success, status
    project.setFileName(str(ROOT / "AccessMap-SA.qgz"))
    assert project.write()
    # A small shared data pack for the mobile concept. No private/resident data.
    transform = QgsCoordinateTransform(project.crs(), QgsCoordinateReferenceSystem("EPSG:4326"), project)
    mobile_facilities = []
    for facility in facilities:
        p = transform.transform(QgsPointXY(facility.x, facility.y))
        mobile_facilities.append({**facility.__dict__, "latitude": round(p.y(), 6), "longitude": round(p.x(), 6),
                                  "verification": "Fictional demo", "hours": "Not verified"})
    pack = {"schemaVersion": 1, "id": "fictional-gauteng-v1", "title": "Gauteng demo",
            "fictional": True, "crs": "EPSG:32735", "sourceDate": "2026-10-19",
            "origin": {"id": "demo-start", "name": "Demo community centre", "x": 594000, "y": 7115000},
            "facilities": mobile_facilities}
    (ROOT / "data/mobile-pack.json").write_text(json.dumps(pack, indent=2) + "\n")
    print("Built portable QGIS project, GeoPackage, map layouts and mobile data pack.")


if __name__ == "__main__":
    app = QgsApplication([], False)
    app.initQgis()
    build()
    # Process teardown releases providers; exitQgis can crash on late Python wrapper cleanup.
