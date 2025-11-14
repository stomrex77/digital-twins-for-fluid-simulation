# Troubleshooting Guide

## Simulation Display Issues

If you can see the control UI but not the actual simulation rendering, this is likely a WebRTC streaming issue.

### How the Simulation Display Works

1. **Kit App (Omniverse)**: Runs the actual 3D simulation and renders it
2. **WebRTC Streaming**: The Kit App streams the rendered video to the web browser
3. **Web Frontend**: Displays the video stream in the browser via a `<video>` element

### Common Issues and Solutions

#### Issue 1: Kit App Not Running

**Symptom**: You see controls but no video stream

**Solution**: Ensure the Kit App is running:
```bash
# Check if the Kit App container is running
docker ps | grep kit-app

# If not running, start all services
docker compose up -d
```

#### Issue 2: WebRTC Streaming Not Configured

**Symptom**: Video element shows but remains black

**Check the browser console** (F12 → Console tab) for errors related to:
- WebRTC connection failures
- Streaming library errors
- Network connection issues

**Configuration**:
The streaming configuration is in `web-app/src/OmniverseApiContext.tsx` (lines 42-46):
```typescript
const server = queryParamOrDefault("server", window.location.hostname);
const width = queryParamOrDefault("width", 1920);
const height = queryParamOrDefault("height", 1080);
const fps = queryParamOrDefault("fps", 60);
```

You can override these via URL parameters:
```
http://localhost:3000/?server=localhost&width=1920&height=1080&fps=60
```

#### Issue 3: Network/Port Configuration

**Required Ports**:
- `3000`: Web frontend
- `8080`: Upload service
- `8011`: Kit App WebRTC streaming (default Omniverse streaming port)
- `49100`: Kit App streaming signaling

**Verify ports are open and accessible**:
```bash
# Check if ports are listening
netstat -tulpn | grep -E '3000|8080|8011|49100'
```

#### Issue 4: Docker Network Issues

If running in Docker, ensure all services are on the same network:

```bash
# Check Docker network configuration
docker network inspect digital-twins-for-fluid-simulation_default

# Verify all containers can communicate
docker exec <web-container> ping kit-app
```

### Debugging Steps

1. **Check Container Logs**:
```bash
# Kit App logs
docker logs <kit-app-container-name>

# Web app logs
docker logs <web-app-container-name>
```

2. **Check Browser Console**:
- Open Developer Tools (F12)
- Look for WebRTC connection errors
- Check the Network tab for failed requests

3. **Verify Streaming Configuration**:
The OmniverseAPI connects using the WebRTC streaming library:
- File: `web-app/src/OmniverseApi.ts`
- Uses `@nvidia/omniverse-webrtc-streaming-library`

4. **Check Kit App Configuration**:
The Kit App must be configured to stream via WebRTC. Check:
- Kit App extension configuration
- Streaming settings in the USD stage

### Quick Fix Checklist

- [ ] All Docker containers are running (`docker ps`)
- [ ] Kit App is rendering (check logs for rendering activity)
- [ ] WebRTC ports are accessible (8011, 49100)
- [ ] Browser console shows no errors
- [ ] Server URL is correct in the web app
- [ ] Try refreshing the browser page
- [ ] Try restarting all Docker containers

## STL Upload Issues

If STL uploads are not working:

### Now Fixed!

The STL upload functionality has been fixed with the following changes:

1. **Kit App API Handler**: Added `load_uploaded_files` request handler in `rtwt.py:759-821`
   - Loads STL files from `/data/uploads/stl/`
   - Loads streamlines from `/data/uploads/streamlines/`
   - Creates USD mesh/curve primitives in the scene

2. **Web Frontend**: Updated `FileUploadMenu.tsx` to add "Load" buttons
   - Click "Upload" to upload the file to the server
   - Click "Load" next to an uploaded file to load it into the Kit App
   - Status messages show upload/load progress

### How to Use

1. **Upload a file**:
   - Click "Browse" and select an STL or JSON file
   - Click "Upload STL" or "Upload Streamlines"
   - File is uploaded to the upload service

2. **Load into scene**:
   - Find your uploaded file in the list
   - Click the "Load" button next to it
   - The file will be loaded into the Omniverse scene
   - Check the viewport to see your geometry

### File Paths

- **STL files**: Loaded as mesh at `/World/UploadedSTL`
- **Streamlines**: Loaded as curves at `/World/UploadedStreamlines/Curves`

### Upload Directory

Files are stored in `/data/uploads/`:
```
/data/uploads/
  ├── stl/          # STL files
  └── streamlines/  # JSON streamline files
```

### Supported Formats

- **STL**: Binary or ASCII STL format
- **Streamlines**: JSON format (see `upload-service/STREAMLINE_FORMAT.md`)

## Getting Help

If issues persist:
1. Check all Docker container logs
2. Verify network connectivity between services
3. Review browser console for JavaScript errors
4. Check Kit App logs for USD/rendering errors
5. Ensure all required dependencies are installed in containers
