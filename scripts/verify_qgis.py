#!/usr/bin/env python3
"""Integration checks: portable project, processing outputs, CRS and empty cases."""
import shutil
import sys
import tempfile
from pathlib import Path
from qgis.core import (QgsApplication, QgsCoordinateReferenceSystem, QgsFeature,
                       QgsGeometry, QgsPointXY, QgsProcessingContext, QgsProcessingException,
                       QgsProcessingFeedback, QgsProcessingUtils, QgsProject, QgsVectorLayer)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "processing"))
from accessmap_sa import AccessMapAlgorithm


def verify():
    project = QgsProject.instance()
    with tempfile.TemporaryDirectory() as temp:
        relocated = Path(temp) / "relocated"
        shutil.copytree(ROOT, relocated, ignore=shutil.ignore_patterns("node_modules", ".git", "__pycache__"))
        assert project.read(str(relocated / "AccessMap-SA.qgz"))
        assert len(project.mapLayers()) == 6
        assert all(layer.isValid() for layer in project.mapLayers().values())
        assert len(project.layoutManager().layouts()) == 2
        assert all(str(relocated) in layer.source() for layer in project.mapLayers().values())
        origins = next(l for l in project.mapLayers().values() if "Community sample" in l.name())
        services = next(l for l in project.mapLayers().values() if l.name().startswith("Facilities"))
        context = QgsProcessingContext()
        context.setProject(project)
        feedback = QgsProcessingFeedback()
        algorithm = AccessMapAlgorithm()
        algorithm.initAlgorithm()
        params = {"ORIGINS": origins, "SERVICES": services, "ID": "id", "NAME": "name",
                  "CATEGORY": "category", "VALUE": "clinic", "CRS": "EPSG:32735",
                  "NEAR": 1000, "FAR": 3000, "OUTPUT": "memory:"}
        result = algorithm.processAlgorithm(params, context, feedback)
        output = QgsProcessingUtils.mapLayerFromString(result["OUTPUT"], context)
        assert output.featureCount() == 320
        assert output.crs().authid() == "EPSG:32735"
        from accessmap_sa import Facility, NearestIndex, assess
        index = NearestIndex([Facility(str(f["id"]), str(f["name"]), "clinic",
                                       f.geometry().asPoint().x(), f.geometry().asPoint().y())
                              for f in services.getFeatures() if f["category"] == "clinic"])
        for feature in output.getFeatures():
            p = feature.geometry().asPoint()
            expected = assess(index, p.x(), p.y())
            assert abs(feature["distance_m"] - expected["distance_m"]) < 1e-6
            assert feature["access_band"] == expected["access_band"]
        params["VALUE"] = "missing"
        result = algorithm.processAlgorithm(params, context, feedback)
        empty = QgsProcessingUtils.mapLayerFromString(result["OUTPUT"], context)
        assert all(f["access_band"] == "unknown" for f in empty.getFeatures())
        params["CRS"] = "EPSG:4326"
        try:
            algorithm.processAlgorithm(params, context, feedback)
        except QgsProcessingException:
            pass
        else:
            raise AssertionError("Geographic CRS was accepted")
        params["CRS"] = "EPSG:32735"
        params["FAR"] = 500
        try:
            algorithm.processAlgorithm(params, context, feedback)
        except QgsProcessingException:
            pass
        else:
            raise AssertionError("Reversed thresholds were accepted")
        # Real reprojection path: a lon/lat origin transformed to metre CRS.
        params["FAR"] = 3000
        params["VALUE"] = "clinic"
        geographic = QgsVectorLayer("Point?crs=EPSG:4326", "Geographic test", "memory")
        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(27.94, -26.08)))
        geographic.dataProvider().addFeatures([f])
        params["ORIGINS"] = geographic
        result = algorithm.processAlgorithm(params, context, feedback)
        reprojected = QgsProcessingUtils.mapLayerFromString(result["OUTPUT"], context)
        assert reprojected.featureCount() == 1
        assert next(reprojected.getFeatures()).geometry().asPoint().x() > 100000
        project.clear()
    print("PASS: relocated QGIS project, layouts, 320 results, reprojection, unknown and validation cases")


if __name__ == "__main__":
    app = QgsApplication([], False)
    app.initQgis()
    verify()
