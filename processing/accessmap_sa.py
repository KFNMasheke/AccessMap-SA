"""AccessMap SA: dependency-free distance engine and QGIS Processing algorithm.

All coordinates passed to the engine must share a suitable projected metre CRS.
SPDX-License-Identifier: MIT. See LICENSE.
"""
from dataclasses import dataclass
from math import hypot, isfinite


@dataclass(frozen=True)
class Facility:
    id: str
    name: str
    category: str
    x: float
    y: float

    def __post_init__(self):
        if not self.id or not self.name or not self.category:
            raise ValueError("Facility ID, name and category are required.")
        validate_xy(self.x, self.y)


def validate_xy(x, y):
    if not isfinite(x) or not isfinite(y):
        raise ValueError("Coordinates must be finite numbers in a projected metre CRS.")


def validate_thresholds(near, far):
    if not isfinite(near) or not isfinite(far) or not 0 < near < far:
        raise ValueError("Thresholds must be finite and satisfy 0 < near < far.")


class NearestIndex:
    """Balanced 2-D KD tree. Ties resolve by stable facility ID.

    Uses exact Euclidean distance in the input CRS. No route inference.
    """
    def __init__(self, facilities):
        items = list(facilities)
        if len({f.id for f in items}) != len(items):
            raise ValueError("Facility IDs must be unique.")

        def build(rows, depth=0):
            if not rows:
                return None
            axis = depth % 2
            rows.sort(key=lambda f: ((f.x, f.y)[axis], f.id))
            mid = len(rows) // 2
            return (rows[mid], axis, build(rows[:mid], depth + 1),
                    build(rows[mid + 1:], depth + 1))

        self.root = build(items)

    def nearest(self, x, y):
        validate_xy(x, y)
        best = None

        def visit(node):
            nonlocal best
            if node is None:
                return
            facility, axis, left, right = node
            candidate = (hypot(facility.x - x, facility.y - y), facility.id, facility)
            if best is None or candidate[:2] < best[:2]:
                best = candidate
            delta = (x, y)[axis] - (facility.x, facility.y)[axis]
            first, second = (left, right) if delta <= 0 else (right, left)
            visit(first)
            if abs(delta) <= best[0]:
                visit(second)

        visit(self.root)
        return None if best is None else (best[2], best[0])


def assess(index, x, y, near=1000.0, far=3000.0):
    """Inclusive thresholds; missing facilities mean unknown, never zero distance."""
    validate_thresholds(near, far)
    match = index.nearest(x, y)
    if match is None:
        return {"nearest_id": None, "nearest_name": None,
                "distance_m": None, "access_band": "unknown"}
    facility, distance = match
    band = "near" if distance <= near else "moderate" if distance <= far else "far"
    return {"nearest_id": facility.id, "nearest_name": facility.name,
            "distance_m": distance, "access_band": band}


# The same file works as a pure Python library outside QGIS.
try:
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import (
        QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsFeature,
        QgsFeatureSink, QgsField, QgsFields, QgsGeometry, QgsPointXY,
        QgsProcessing, QgsProcessingAlgorithm, QgsProcessingException,
        QgsProcessingParameterCrs, QgsProcessingParameterFeatureSink,
        QgsProcessingParameterFeatureSource, QgsProcessingParameterField,
        QgsProcessingParameterNumber, QgsProcessingParameterString,
        QgsUnitTypes, QgsWkbTypes,
    )
except ModuleNotFoundError as exc:
    if exc.name != "qgis":
        raise
else:
    class AccessMapAlgorithm(QgsProcessingAlgorithm):
        def name(self):
            return "service_access"

        def displayName(self):
            return "AccessMap SA: distance to essential services"

        def group(self):
            return "AccessMap SA"

        def groupId(self):
            return "accessmap_sa"

        def createInstance(self):
            return AccessMapAlgorithm()

        def shortHelpString(self):
            return (
                "Measures straight-line distance from representative community points "
                "to the nearest recorded facility of one category. Requires a local "
                "projected metre CRS (default UTM 35S suits Gauteng). Thresholds are "
                "exploratory, not government standards. Does not measure walking time, "
                "safety, affordability, opening hours or capacity. Keep facilities outside "
                "your study boundary to avoid edge effects. No facilities = unknown. "
                "Input attributes are not copied to outputs. Reapply a band style to new outputs."
            )

        def initAlgorithm(self, config=None):
            self.addParameter(QgsProcessingParameterFeatureSource(
                "ORIGINS", "Community representative points", [QgsProcessing.TypeVectorPoint]))
            self.addParameter(QgsProcessingParameterFeatureSource(
                "SERVICES", "Facility points (include surrounding area)", [QgsProcessing.TypeVectorPoint]))
            for key, title in [("ID", "Unique facility ID"), ("NAME", "Facility name"),
                               ("CATEGORY", "Service category")]:
                self.addParameter(QgsProcessingParameterField(
                    key, title, parentLayerParameterName="SERVICES"))
            self.addParameter(QgsProcessingParameterString("VALUE", "Category to assess", "clinic"))
            self.addParameter(QgsProcessingParameterCrs(
                "CRS", "Local projected metre CRS", "EPSG:32735"))
            self.addParameter(QgsProcessingParameterNumber(
                "NEAR", "Near threshold (metres)", type=QgsProcessingParameterNumber.Double,
                defaultValue=1000, minValue=0.001))
            self.addParameter(QgsProcessingParameterNumber(
                "FAR", "Far threshold (metres)", type=QgsProcessingParameterNumber.Double,
                defaultValue=3000, minValue=0.002))
            self.addParameter(QgsProcessingParameterFeatureSink("OUTPUT", "Service access points"))

        def processAlgorithm(self, parameters, context, feedback):
            origins = self.parameterAsSource(parameters, "ORIGINS", context)
            services = self.parameterAsSource(parameters, "SERVICES", context)
            if origins is None or services is None:
                raise QgsProcessingException("Both input point layers are required.")
            crs = self.parameterAsCrs(parameters, "CRS", context)
            if not crs.isValid() or crs.isGeographic() or crs.mapUnits() != QgsUnitTypes.DistanceMeters:
                raise QgsProcessingException("Choose a suitable projected CRS with metre units.")
            near = self.parameterAsDouble(parameters, "NEAR", context)
            far = self.parameterAsDouble(parameters, "FAR", context)
            try:
                validate_thresholds(near, far)
            except ValueError as exc:
                raise QgsProcessingException(str(exc)) from exc
            category = self.parameterAsString(parameters, "VALUE", context).strip().casefold()
            if not category:
                raise QgsProcessingException("A non-empty category is required.")
            keys = [self.parameterAsString(parameters, k, context) for k in ("ID", "NAME", "CATEGORY")]
            if any(services.fields().indexFromName(k) < 0 for k in keys):
                raise QgsProcessingException("Choose valid ID, name and category fields.")

            def point(feature, source):
                geometry = feature.geometry()
                if geometry.isNull() or geometry.isEmpty() or geometry.isMultipart():
                    raise QgsProcessingException(
                        f"Feature {feature.id()}: a non-empty single point is required.")
                if not source.sourceCrs().isValid():
                    raise QgsProcessingException("Input layer CRS is missing.")
                geometry = QgsGeometry(geometry)
                geometry.transform(QgsCoordinateTransform(source.sourceCrs(), crs, context.transformContext()))
                p = geometry.asPoint()
                validate_xy(p.x(), p.y())
                return p

            rows = []
            for feature in services.getFeatures():
                if feedback.isCanceled():
                    raise QgsProcessingException("Canceled; output is incomplete. Discard it.")
                if str(feature[keys[2]]).strip().casefold() != category:
                    continue
                try:
                    p = point(feature, services)
                    from qgis.core import NULL
                    if any(feature[k] == NULL or not str(feature[k]).strip() for k in keys):
                        raise ValueError("Selected facilities need non-empty ID, name and category.")
                    rows.append(Facility(str(feature[keys[0]]).strip(), str(feature[keys[1]]).strip(),
                                         category, p.x(), p.y()))
                except ValueError as exc:
                    raise QgsProcessingException(str(exc)) from exc
            try:
                index = NearestIndex(rows)
            except ValueError as exc:
                raise QgsProcessingException(str(exc)) from exc
            if not rows:
                feedback.pushWarning("No matching facilities. All results will be unknown.")
            fields = QgsFields()
            for name, typ in [("origin_id", QVariant.LongLong), ("nearest_id", QVariant.String),
                              ("nearest_name", QVariant.String), ("distance_m", QVariant.Double),
                              ("access_band", QVariant.String), ("category", QVariant.String),
                              ("near_m", QVariant.Double), ("far_m", QVariant.Double),
                              ("method", QVariant.String), ("metric_crs", QVariant.String)]:
                fields.append(QgsField(name, typ))
            sink, destination = self.parameterAsSink(
                parameters, "OUTPUT", context, fields, QgsWkbTypes.Point, crs)
            if sink is None:
                raise QgsProcessingException("Cannot create output layer.")
            count = max(origins.featureCount(), 1)
            for n, feature in enumerate(origins.getFeatures()):
                if feedback.isCanceled():
                    raise QgsProcessingException("Canceled; output is incomplete. Discard it.")
                p = point(feature, origins)
                result = assess(index, p.x(), p.y(), near, far)
                output = QgsFeature(fields)
                output.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(p)))
                output.setAttributes([feature.id(), result["nearest_id"], result["nearest_name"],
                                      result["distance_m"], result["access_band"], category,
                                      near, far, "projected_straight_line", crs.authid() or crs.toWkt()])
                if not sink.addFeature(output, QgsFeatureSink.FastInsert):
                    raise QgsProcessingException("Failed writing output; discard incomplete results.")
                feedback.setProgress(100 * (n + 1) / count)
            feedback.pushInfo(f"Assessed against {len(rows)} recorded {category} facilities.")
            return {"OUTPUT": destination}
