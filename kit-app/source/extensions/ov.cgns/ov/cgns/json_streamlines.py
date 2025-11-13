"""
JSON Streamline Loader
Loads streamlines from JSON format and creates USD BasisCurves primitives
"""

import json
import numpy as np
from pxr import Usd, UsdGeom, Vt, Gf
import carb


def load_streamlines_from_json(json_path, stage, parent_prim_path="/World/Streamlines",
                                curve_prim_path="/World/Streamlines/StreamLines",
                                width=0.5):
    """
    Load streamlines from a JSON file and create USD BasisCurves

    Args:
        json_path: Path to the JSON file
        stage: USD stage
        parent_prim_path: Path to the parent prim for streamlines
        curve_prim_path: Path to the curves prim
        width: Line width for visualization

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        carb.log_info(f"Loading streamlines from JSON: {json_path}")

        # Read JSON file
        with open(json_path, 'r') as f:
            data = json.load(f)

        if "streamlines" not in data:
            carb.log_error("JSON file must contain 'streamlines' array")
            return False

        streamlines = data["streamlines"]
        if len(streamlines) == 0:
            carb.log_warn("No streamlines found in JSON file")
            return False

        # Ensure parent prim exists
        parent_prim = stage.GetPrimAtPath(parent_prim_path)
        if not parent_prim.IsValid():
            parent_prim = stage.DefinePrim(parent_prim_path, "Xform")

        # Create or get BasisCurves prim
        curves_prim = stage.GetPrimAtPath(curve_prim_path)
        if curves_prim.IsValid():
            # Clear existing curves
            stage.RemovePrim(curve_prim_path)

        curves_prim = stage.DefinePrim(curve_prim_path, "BasisCurves")
        basis_curves = UsdGeom.BasisCurves(curves_prim)

        # Collect all vertices and curve counts
        all_vertices = []
        curve_vertex_counts = []
        all_scalars = []
        has_scalars = False

        for i, streamline in enumerate(streamlines):
            path = streamline.get("path", [])
            if len(path) < 2:
                carb.log_warn(f"Streamline {i} has fewer than 2 points, skipping")
                continue

            # Convert path to numpy array
            path_array = np.array(path, dtype=np.float32)

            # Convert to 100cm scale (USD uses cm by default in Omniverse)
            # path_array *= 100.0

            all_vertices.extend(path_array.tolist())
            curve_vertex_counts.append(len(path))

            # Get scalar values if available
            if "scalar" in streamline:
                scalars = streamline["scalar"]
                if len(scalars) == len(path):
                    all_scalars.extend(scalars)
                    has_scalars = True
                else:
                    # Pad with zeros if length doesn't match
                    all_scalars.extend([0.0] * len(path))
            else:
                # No scalars for this streamline
                all_scalars.extend([0.0] * len(path))

        if len(all_vertices) == 0:
            carb.log_error("No valid streamlines found")
            return False

        # Set curve attributes
        basis_curves.GetCurveVertexCountsAttr().Set(curve_vertex_counts)
        basis_curves.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*v) for v in all_vertices]))
        basis_curves.GetTypeAttr().Set("linear")  # Linear curves (straight lines between points)
        basis_curves.GetWrapAttr().Set("nonperiodic")

        # Set curve width
        width_array = [width] * len(curve_vertex_counts)
        basis_curves.GetWidthsAttr().Set(width_array)

        # Set display color based on scalar values
        if has_scalars and len(all_scalars) > 0:
            # Normalize scalars to [0, 1] range
            scalars_array = np.array(all_scalars)
            scalar_min = np.min(scalars_array)
            scalar_max = np.max(scalars_array)

            if scalar_max > scalar_min:
                normalized_scalars = (scalars_array - scalar_min) / (scalar_max - scalar_min)
            else:
                normalized_scalars = np.zeros_like(scalars_array)

            # Create color map (blue -> cyan -> green -> yellow -> red)
            colors = []
            for s in normalized_scalars:
                if s < 0.25:
                    # Blue to cyan
                    t = s / 0.25
                    color = Gf.Vec3f(0.0, t, 1.0)
                elif s < 0.5:
                    # Cyan to green
                    t = (s - 0.25) / 0.25
                    color = Gf.Vec3f(0.0, 1.0, 1.0 - t)
                elif s < 0.75:
                    # Green to yellow
                    t = (s - 0.5) / 0.25
                    color = Gf.Vec3f(t, 1.0, 0.0)
                else:
                    # Yellow to red
                    t = (s - 0.75) / 0.25
                    color = Gf.Vec3f(1.0, 1.0 - t, 0.0)

                colors.append(color)

            basis_curves.GetDisplayColorAttr().Set(Vt.Vec3fArray(colors))
            basis_curves.GetDisplayColorPrimvar().SetInterpolation("vertex")

        else:
            # Default color: cyan
            default_color = Gf.Vec3f(0.0, 1.0, 1.0)
            basis_curves.GetDisplayColorAttr().Set(Vt.Vec3fArray([default_color]))

        carb.log_info(f"Successfully loaded {len(curve_vertex_counts)} streamlines with {len(all_vertices)} total points")

        # Make sure prims are visible
        UsdGeom.Imageable(parent_prim).MakeVisible()
        UsdGeom.Imageable(curves_prim).MakeVisible()

        return True

    except Exception as e:
        carb.log_error(f"Failed to load streamlines from JSON: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_stl_as_mesh(stl_path, stage, mesh_prim_path="/World/UploadedSTL"):
    """
    Load an STL file and create a USD mesh

    Args:
        stl_path: Path to the STL file
        stage: USD stage
        mesh_prim_path: Path for the USD mesh prim

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import trimesh

        carb.log_info(f"Loading STL file: {stl_path}")

        # Load STL using trimesh
        mesh = trimesh.load(str(stl_path))

        # Get existing prim or create new one
        mesh_prim = stage.GetPrimAtPath(mesh_prim_path)
        if mesh_prim.IsValid():
            # Clear existing mesh
            stage.RemovePrim(mesh_prim_path)

        # Create mesh prim
        mesh_prim = stage.DefinePrim(mesh_prim_path, "Mesh")
        usd_mesh = UsdGeom.Mesh(mesh_prim)

        # Convert vertices and faces
        vertices = mesh.vertices.astype(np.float32)
        faces = mesh.faces.astype(np.int32)

        # Convert to 100cm scale (USD uses cm in Omniverse)
        # vertices *= 100.0

        # Set mesh data
        usd_mesh.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*v) for v in vertices]))

        # Flatten faces array for USD
        face_vertex_counts = [3] * len(faces)  # All triangles
        face_vertex_indices = faces.flatten().tolist()

        usd_mesh.GetFaceVertexCountsAttr().Set(face_vertex_counts)
        usd_mesh.GetFaceVertexIndicesAttr().Set(face_vertex_indices)

        # Compute normals if available
        if hasattr(mesh, 'vertex_normals'):
            normals = mesh.vertex_normals.astype(np.float32)
            usd_mesh.GetNormalsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*n) for n in normals]))

        # Set display color (light gray)
        display_color = Gf.Vec3f(0.8, 0.8, 0.8)
        usd_mesh.GetDisplayColorAttr().Set(Vt.Vec3fArray([display_color]))

        # Make visible
        UsdGeom.Imageable(mesh_prim).MakeVisible()

        carb.log_info(f"Successfully loaded STL with {len(vertices)} vertices and {len(faces)} faces")

        return True

    except Exception as e:
        carb.log_error(f"Failed to load STL file: {e}")
        import traceback
        traceback.print_exc()
        return False
