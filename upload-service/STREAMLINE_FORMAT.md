# Streamline JSON Format

This document describes the JSON format for uploading custom streamline data.

## Basic Format

```json
{
  "streamlines": [
    {
      "path": [[x1, y1, z1], [x2, y2, z2], [x3, y3, z3], ...],
      "scalar": [v1, v2, v3, ...],
      "color": [r, g, b]
    },
    ...
  ],
  "metadata": {
    "units": "m/s",
    "domain_bounds": [[xmin, ymin, zmin], [xmax, ymax, zmax]],
    "description": "Custom streamline data"
  }
}
```

## Field Descriptions

### Required Fields

- **`streamlines`** (array): Array of streamline objects
  - **`path`** (array of [x, y, z] arrays): 3D coordinates defining the streamline path
    - Each point is `[x, y, z]` where x, y, z are floating point numbers
    - Minimum 2 points per streamline
    - Coordinates should be in meters or match your STL file units

### Optional Fields

- **`scalar`** (array of numbers): Scalar values at each point (e.g., velocity magnitude, pressure)
  - Used for color-coding the streamline
  - Must have same length as `path` array
  - If omitted, streamline will use default coloring

- **`color`** (array of 3 numbers [r, g, b]): Custom RGB color for this streamline
  - Values should be in range [0, 1]
  - Example: `[1.0, 0.0, 0.0]` for red

- **`metadata`** (object): Optional metadata about the streamlines
  - **`units`**: Units of measurement (e.g., "m/s", "ft/s")
  - **`domain_bounds`**: Bounding box as `[[xmin, ymin, zmin], [xmax, ymax, zmax]]`
  - **`description`**: Text description of the data

## Example

```json
{
  "streamlines": [
    {
      "path": [
        [-5.0, 0.0, 0.5],
        [-4.5, 0.1, 0.52],
        [-4.0, 0.15, 0.55],
        [-3.5, 0.2, 0.58],
        [-3.0, 0.25, 0.6]
      ],
      "scalar": [30.0, 31.2, 32.5, 33.1, 34.0],
      "color": [1.0, 0.0, 0.0]
    },
    {
      "path": [
        [-5.0, 1.0, 0.5],
        [-4.5, 1.05, 0.52],
        [-4.0, 1.08, 0.54],
        [-3.5, 1.1, 0.55],
        [-3.0, 1.12, 0.56]
      ],
      "scalar": [28.0, 29.5, 30.2, 31.0, 31.8]
    }
  ],
  "metadata": {
    "units": "m/s",
    "domain_bounds": [[-6.0, -2.0, -1.0], [6.0, 2.0, 2.0]],
    "description": "Airflow streamlines around vehicle"
  }
}
```

## Generating Streamlines from CFD Data

If you have CFD simulation results, you can generate streamlines using tools like:

- **ParaView**: Export streamlines as CSV, then convert to JSON
- **Python (vtk library)**: Use vtkStreamTracer
- **MATLAB**: Use `streamline()` function

### Example Python Script

```python
import json
import numpy as np

# Example: simple streamline generation
def generate_streamline(start_point, velocity_field_func, dt=0.1, num_steps=50):
    """
    Generate a streamline using Euler integration

    Args:
        start_point: [x, y, z] starting position
        velocity_field_func: function(x, y, z) -> [vx, vy, vz]
        dt: time step
        num_steps: number of integration steps
    """
    path = [start_point]
    scalars = []

    pos = np.array(start_point)
    for _ in range(num_steps):
        vel = np.array(velocity_field_func(*pos))
        scalar = np.linalg.norm(vel)  # velocity magnitude

        pos = pos + vel * dt
        path.append(pos.tolist())
        scalars.append(float(scalar))

    return {
        "path": path,
        "scalar": scalars
    }

# Example usage
def example_velocity_field(x, y, z):
    """Simple example velocity field"""
    return [30.0 + y * 0.5, x * 0.1, 0.2]

streamlines = []
for y in np.linspace(-1, 1, 10):
    streamline = generate_streamline([-5.0, y, 0.5], example_velocity_field)
    streamlines.append(streamline)

data = {
    "streamlines": streamlines,
    "metadata": {
        "units": "m/s",
        "description": "Example streamlines"
    }
}

with open("streamlines.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Generated {len(streamlines)} streamlines")
```

## Upload via API

### Using curl

```bash
# Upload streamlines
curl -X POST http://localhost:8080/upload/streamlines \
  -F "file=@streamlines.json"

# Upload STL file
curl -X POST http://localhost:8080/upload/stl \
  -F "file=@vehicle.stl"

# List files
curl http://localhost:8080/files
```

### Using Python

```python
import requests

# Upload streamlines
with open("streamlines.json", "rb") as f:
    response = requests.post(
        "http://localhost:8080/upload/streamlines",
        files={"file": f}
    )
    print(response.json())

# Upload STL
with open("vehicle.stl", "rb") as f:
    response = requests.post(
        "http://localhost:8080/upload/stl",
        files={"file": f}
    )
    print(response.json())
```

## Validation

The upload service validates:
- JSON is well-formed
- `streamlines` array exists
- Each streamline has a `path` field
- Each path point is a 3-element array [x, y, z]
- If `scalar` is provided, it matches the path length

Invalid files will be rejected with a descriptive error message.
