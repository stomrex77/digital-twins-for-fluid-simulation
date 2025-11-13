# Major Changes - Custom STL and Streamlines Upload

This document summarizes the changes made to enable custom STL file and streamline JSON uploads, removing the dependency on Physics NIM.

## Summary of Changes

### What Changed

✅ **Removed Physics NIM Dependency**
- No longer requires the NVIDIA Inference Microservice (DoMINO-Automotive-Aero)
- No longer requires a second GPU (GPU 1)
- Removed Triton inference calls from ZMQ service

✅ **Added File Upload Capability**
- New upload service API (FastAPI) for STL and JSON files
- Web UI now has an upload button (📤 icon)
- Files are stored in `uploaded_files/` directory

✅ **Custom Streamline Support**
- Define streamlines in simple JSON format
- No need to run CFD simulations
- Upload pre-computed streamline data

✅ **Simplified Architecture**
- Reduced from 4 services to 4 services (but simpler)
- Only requires 1 GPU instead of 2
- Easier to deploy on cloud platforms (AWS, GCP, Azure)

### Architecture Before and After

#### Before (Original)
```
Browser → Web App → Kit App (GPU 0) → ZMQ Service → Physics NIM (GPU 1)
                                              ↑
                                        Triton Inference
                                        (CFD Surrogate Model)
```

**Requirements:**
- 2x GPUs (40GB each) = 80GB total
- NGC API Key for Physics NIM
- Complex setup with Triton inference

#### After (Current)
```
Browser → Web App → Kit App (GPU 0) → ZMQ Service → Upload Service
              ↓                            ↑              ↑
        Upload UI                   Load Files      Store Files
                                                (STL + JSON)
```

**Requirements:**
- 1x GPU (24GB+) = 24GB minimum
- No NGC API Key needed
- Simple file-based workflow

### Cost Savings

| Resource | Before | After | Savings |
|----------|--------|-------|---------|
| GPUs | 2x (80GB) | 1x (24GB) | -50% GPUs, -70% VRAM |
| AWS Instance | g5.12xlarge | g5.4xlarge | -66% cost |
| Monthly Cost (On-Demand) | ~$3,500 | ~$1,166 | **$2,334/month** |
| Monthly Cost (Spot) | ~$1,050 | ~$353 | **$697/month** |

### File Structure Changes

**New Files:**
```
upload-service/
├── Dockerfile
├── requirements.txt
├── app.py                      # FastAPI upload service
└── STREAMLINE_FORMAT.md        # JSON format documentation

kit-app/source/extensions/ov.cgns/ov/cgns/
└── json_streamlines.py         # JSON streamline loader

web-app/src/Menus/FileUpload/
├── FileUploadMenu.tsx          # Upload UI component
└── FileUploadMenu.css          # Upload UI styles

DEPLOYMENT.md                   # Cloud deployment guide
CHANGES.md                      # This file
examples/
├── sample_streamlines.json     # Example streamline data
└── sample_vehicle.stl          # Example STL file (if available)
```

**Modified Files:**
```
compose.yml                     # Removed aeronim, added upload service
service_network/src_py/inference_service/service.py  # Load from files instead of Triton
web-app/src/App.tsx             # Added upload button
web-app/src/App.css             # Upload button styles
```

## Usage Guide

### 1. Upload STL File

1. Click the upload button (📤 icon) in bottom-left of web interface
2. Select your STL file (vehicle geometry)
3. Click "Upload STL"
4. File is stored in `uploaded_files/stl/`

### 2. Upload Streamlines JSON

1. Create a JSON file with this structure:
```json
{
  "streamlines": [
    {
      "path": [
        [-5.0, 0.0, 0.5],
        [-4.5, 0.1, 0.52],
        [-4.0, 0.15, 0.55]
      ],
      "scalar": [30.0, 31.2, 32.5]
    }
  ],
  "metadata": {
    "units": "m/s",
    "description": "Airflow streamlines"
  }
}
```

2. Click upload button in web interface
3. Select your JSON file
4. Click "Upload Streamlines"
5. File is stored in `uploaded_files/streamlines/`

### 3. Visualize

- Streamlines are automatically loaded and rendered in the 3D viewport
- Color-coded by scalar values (e.g., velocity magnitude)
- STL mesh is displayed with streamlines

See `upload-service/STREAMLINE_FORMAT.md` for detailed JSON format documentation.

## Migration from Original Version

If you have the original version running, here's how to migrate:

### Step 1: Backup Data

```bash
# Backup existing configuration
cp .env .env.backup
cp compose.yml compose.yml.backup
```

### Step 2: Pull Latest Changes

```bash
git pull origin main
```

### Step 3: Update Configuration

```bash
# Remove NGC_API_KEY (no longer needed)
sed -i '/NGC_API_KEY/d' .env

# Update compose.yml to only use GPU 0
# This is already done in the new version
```

### Step 4: Rebuild and Restart

```bash
# Stop old services
docker compose down

# Remove old images
docker compose rm -f aeronim

# Build new images
./build-docker.sh

# Start new services
docker compose up -d

# Verify
docker compose ps
curl http://localhost:8080/health
```

### Step 5: Convert Existing Data (If Applicable)

If you have existing CFD data from Physics NIM, you can convert it to the new JSON format:

```python
import numpy as np
import json

# Load your existing CFD data (.npy or .npz)
data = np.load("your_cfd_data.npz")
coordinates = data["coordinates"]
velocity = data["velocity"]

# Generate streamlines from velocity field
# (You'll need a streamline tracer - see STREAMLINE_FORMAT.md for examples)

# Convert to JSON format
streamlines_json = {
    "streamlines": [
        # ... your streamline data ...
    ],
    "metadata": {
        "description": "Converted from CFD simulation"
    }
}

# Save
with open("streamlines.json", "w") as f:
    json.dump(streamlines_json, f, indent=2)
```

## API Reference

### Upload Service Endpoints

**Base URL:** `http://localhost:8080`

#### POST /upload/stl
Upload an STL file

**Request:**
```bash
curl -X POST http://localhost:8080/upload/stl \
  -F "file=@vehicle.stl" \
  -F "name=my_vehicle.stl"
```

**Response:**
```json
{
  "success": true,
  "filename": "my_vehicle.stl",
  "path": "/app/uploaded_files/stl/my_vehicle.stl",
  "size_bytes": 1048576
}
```

#### POST /upload/streamlines
Upload a streamlines JSON file

**Request:**
```bash
curl -X POST http://localhost:8080/upload/streamlines \
  -F "file=@streamlines.json" \
  -F "name=my_streamlines.json"
```

**Response:**
```json
{
  "success": true,
  "filename": "my_streamlines.json",
  "path": "/app/uploaded_files/streamlines/my_streamlines.json",
  "size_bytes": 2048,
  "num_streamlines": 50
}
```

#### GET /files
List all uploaded files

**Request:**
```bash
curl http://localhost:8080/files
```

**Response:**
```json
{
  "stl_files": [
    {
      "name": "vehicle.stl",
      "path": "/app/uploaded_files/stl/vehicle.stl",
      "size_bytes": 1048576
    }
  ],
  "streamline_files": [
    {
      "name": "streamlines.json",
      "path": "/app/uploaded_files/streamlines/streamlines.json",
      "size_bytes": 2048,
      "num_streamlines": 50
    }
  ],
  "total_stl": 1,
  "total_streamlines": 1
}
```

#### DELETE /files/stl/{filename}
Delete an STL file

```bash
curl -X DELETE http://localhost:8080/files/stl/vehicle.stl
```

#### DELETE /files/streamlines/{filename}
Delete a streamlines file

```bash
curl -X DELETE http://localhost:8080/files/streamlines/streamlines.json
```

#### GET /health
Health check

```bash
curl http://localhost:8080/health
# {"status": "healthy"}
```

## Troubleshooting

### Upload Service Not Accessible

**Problem:** Can't access http://localhost:8080

**Solution:**
```bash
# Check service is running
docker compose ps upload

# Check logs
docker compose logs upload

# Verify port is open
netstat -tulpn | grep 8080

# Restart service
docker compose restart upload
```

### Streamlines Not Visible

**Problem:** Uploaded streamlines but don't see them in viewport

**Solution:**
1. Check JSON format is correct:
   ```bash
   curl -X POST http://localhost:8080/upload/streamlines -F "file=@streamlines.json"
   ```
2. Check Kit app logs:
   ```bash
   docker compose logs kit | grep streamline
   ```
3. Enable Curve Trace mode in web UI
4. Verify streamlines are within the visible domain bounds

### STL Not Loading

**Problem:** Uploaded STL but it's not visible

**Solution:**
1. Verify STL file is valid:
   ```bash
   # Install meshlab or similar tool
   meshlab vehicle.stl
   ```
2. Check file size (should be < 50MB for best performance)
3. Check ZMQ service logs:
   ```bash
   docker compose logs zmq
   ```

### Out of Memory

**Problem:** Kit app crashes with OOM error

**Solution:**
1. Reduce streamline count in JSON (< 10,000 total points)
2. Simplify STL geometry (reduce triangle count)
3. Increase Docker memory limit:
   ```bash
   docker compose up -d --memory=32g
   ```

## Performance Tips

1. **Streamline Count**: Keep total points < 50,000 for smooth rendering
2. **STL Complexity**: Aim for < 100,000 triangles
3. **File Size**: STL < 50MB, JSON < 10MB
4. **Scalar Values**: Normalize to similar ranges for better visualization

## Next Steps

- See `DEPLOYMENT.md` for cloud deployment instructions
- See `upload-service/STREAMLINE_FORMAT.md` for JSON format details
- See examples in `examples/` directory for sample files
- Check [NVIDIA Omniverse docs](https://docs.omniverse.nvidia.com/) for advanced features

## Support

- **GitHub Issues**: https://github.com/NVIDIA-Omniverse-blueprints/digital-twins-for-fluid-simulation/issues
- **Documentation**: Check `DEPLOYMENT.md` and `STREAMLINE_FORMAT.md`
- **Examples**: See `examples/` directory

## License

See LICENSE file for details.
