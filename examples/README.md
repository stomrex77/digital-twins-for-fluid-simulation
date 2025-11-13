# Example Files

This directory contains sample files for testing the Digital Twin Fluid Simulation system.

## Files

### sample_streamlines.json

A sample streamlines file demonstrating the JSON format.

**Contents:**
- 5 streamlines representing airflow around a vehicle
- Each streamline has 21 points
- Scalar values represent velocity magnitude (26-37 m/s)
- Covers a domain from -6m to 6m in X, -2m to 2m in Y, -1m to 2m in Z

**Usage:**
```bash
# Upload via web UI
# 1. Open http://localhost:5273
# 2. Click upload button (📤)
# 3. Select sample_streamlines.json
# 4. Click "Upload Streamlines"

# Or upload via curl
curl -X POST http://localhost:8080/upload/streamlines \
  -F "file=@sample_streamlines.json"
```

## Creating Your Own Files

### Streamlines from CFD Simulation (ParaView)

If you have CFD simulation results, you can generate streamlines using ParaView:

1. Open your CFD results in ParaView
2. Apply **Filters → Stream Tracer**
3. Configure seed points (line, plane, or point cloud)
4. Export as CSV: **File → Save Data → CSV**
5. Convert CSV to JSON using the provided Python script (see below)

### Python Script to Convert CSV to JSON

```python
import pandas as pd
import json
import numpy as np

# Read ParaView CSV export
df = pd.read_csv("streamlines.csv")

# Group by streamline ID
streamlines = []
for streamline_id in df["StreamTracer ID"].unique():
    streamline_df = df[df["StreamTracer ID"] == streamline_id]

    path = streamline_df[["Points:0", "Points:1", "Points:2"]].values.tolist()

    # Extract scalar field (e.g., velocity magnitude)
    if "U:Magnitude" in streamline_df.columns:
        scalar = streamline_df["U:Magnitude"].tolist()
    else:
        scalar = [0.0] * len(path)

    streamlines.append({
        "path": path,
        "scalar": scalar
    })

# Create JSON structure
data = {
    "streamlines": streamlines,
    "metadata": {
        "units": "m/s",
        "description": "Streamlines from CFD simulation",
        "source": "ParaView export"
    }
}

# Save to file
with open("streamlines.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Converted {len(streamlines)} streamlines to JSON")
```

### Streamlines from Python (NumPy/SciPy)

Generate streamlines programmatically:

```python
import numpy as np
import json

def velocity_field(x, y, z):
    """Example velocity field: uniform flow with slight vertical component"""
    return np.array([30.0, 0.1 * y, 0.05 * z])

def euler_integrate(start, velocity_func, dt=0.1, num_steps=20):
    """Simple Euler integration for streamline tracing"""
    path = [start.tolist()]
    scalars = []

    pos = start.copy()
    for _ in range(num_steps):
        vel = velocity_func(*pos)
        scalar = np.linalg.norm(vel)

        pos = pos + vel * dt
        path.append(pos.tolist())
        scalars.append(float(scalar))

    return path, scalars

# Generate multiple streamlines
streamlines = []
for y in np.linspace(-1, 1, 5):
    for z in np.linspace(0.2, 0.8, 3):
        start = np.array([-5.0, y, z])
        path, scalars = euler_integrate(start, velocity_field)
        streamlines.append({
            "path": path,
            "scalar": scalars
        })

# Save to JSON
data = {
    "streamlines": streamlines,
    "metadata": {
        "units": "m/s",
        "description": "Programmatically generated streamlines"
    }
}

with open("generated_streamlines.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Generated {len(streamlines)} streamlines")
```

### STL Files

For STL files, you can:

1. **Use existing CAD models** - Export as STL from:
   - SolidWorks: File → Save As → STL
   - Fusion 360: File → Export → STL
   - Blender: File → Export → STL

2. **Download from repositories**:
   - Thingiverse (https://www.thingiverse.com/)
   - GrabCAD (https://grabcad.com/)
   - Free3D (https://free3d.com/)

3. **Create simple shapes** with Python (trimesh):

```python
import trimesh
import numpy as np

# Create a simple box
box = trimesh.creation.box(extents=[4.0, 2.0, 1.5])

# Add some detail (chamfer edges)
mesh = box

# Save as STL
mesh.export("simple_vehicle.stl")

print(f"Created STL with {len(mesh.vertices)} vertices")
```

## Testing

After uploading your files:

1. **Check upload status**: Look for success message in upload UI
2. **View in 3D**: Enable "Curve Trace" mode in web interface
3. **Adjust view**: Use View menu to change camera angle
4. **Check colors**: Streamlines should be color-coded by scalar values

## Troubleshooting

**Streamlines not visible:**
- Check JSON format is valid
- Verify coordinates are within reasonable bounds (-10 to 10 meters)
- Enable "Curve Trace" mode in web UI

**STL not loading:**
- Verify file is valid STL format
- Check file size (< 50MB recommended)
- Ensure mesh is manifold (no holes or errors)

**Upload fails:**
- Check file size limits
- Verify upload service is running: `curl http://localhost:8080/health`
- Check logs: `docker compose logs upload`

## Additional Resources

- **JSON Format**: See `../upload-service/STREAMLINE_FORMAT.md`
- **Deployment**: See `../DEPLOYMENT.md`
- **Changes**: See `../CHANGES.md`
