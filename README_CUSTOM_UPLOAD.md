# Digital Twin for Fluid Simulation - Custom Upload Version

This version enables uploading custom STL files and streamline data instead of using Physics NIM.

## 🚀 Quick Start

### What's New

✅ **No Physics NIM Required** - Upload your own streamline data in JSON format
✅ **Custom STL Support** - Visualize any vehicle or geometry
✅ **Simplified Architecture** - Only 1 GPU needed (down from 2)
✅ **AWS-Ready** - Optimized for cloud deployment
✅ **Cost Effective** - Save ~$2,300/month on AWS vs original version

### Changes from Original

| Feature | Original | Custom Upload |
|---------|----------|---------------|
| GPUs Required | 2x (80GB) | 1x (24GB+) |
| Physics NIM | ✅ Required | ❌ Not needed |
| NGC API Key | ✅ Required | ❌ Not needed |
| Streamline Source | AI Inference | JSON Upload |
| AWS Instance | g5.12xlarge | g5.4xlarge |
| Monthly Cost (Spot) | ~$1,050 | ~$353 |

## 📋 Requirements

**Hardware:**
- 1x NVIDIA GPU (24GB+ VRAM) - RTX A5000, L40S, A6000, or similar
- 64GB RAM (128GB recommended)
- 16+ CPU cores
- 50GB storage

**Software:**
- Ubuntu 22.04 or 24.04
- Docker with NVIDIA Container Toolkit
- Git, Git LFS

**No longer required:**
- ❌ Second GPU
- ❌ NGC API Key
- ❌ Physics NIM container

## 🏃 Quick Start

### 1. Clone and Build

```bash
git clone https://github.com/NVIDIA-Omniverse-blueprints/digital-twins-for-fluid-simulation.git
cd digital-twins-for-fluid-simulation

# Create configuration
cat > .env << EOF
OMNI_USER=your_email@example.com
OMNI_PASS=your_password
KIT_APP=omni.rtwt.app.webrtc.kit
USD_URL=/home/ubuntu/usd/world_rtwt_Main_v1.usda
ZMQ_IP=127.0.0.1
ZMQ_FIRST_PORT=5555
CUDA_VISIBLE_DEVICES=0
EOF

# Build images
./build-docker.sh

# Start services
docker compose up -d
```

### 2. Access Web Interface

Open http://localhost:5273 in your browser

### 3. Upload Files

Click the upload button (📤 icon) in the bottom-left:

1. **Upload STL**: Select your vehicle/geometry file
2. **Upload Streamlines**: Select your JSON streamlines file

### 4. Visualize

- Streamlines are automatically rendered
- Use "Curve Trace" mode for best visibility
- Adjust view with View menu

## 📂 Streamline JSON Format

```json
{
  "streamlines": [
    {
      "path": [[x1, y1, z1], [x2, y2, z2], ...],
      "scalar": [v1, v2, ...],
      "color": [r, g, b]
    }
  ],
  "metadata": {
    "units": "m/s",
    "description": "..."
  }
}
```

**Required:**
- `streamlines[].path`: Array of [x, y, z] coordinates

**Optional:**
- `streamlines[].scalar`: Values for color-coding
- `streamlines[].color`: Custom RGB color
- `metadata`: Descriptive information

See [`upload-service/STREAMLINE_FORMAT.md`](upload-service/STREAMLINE_FORMAT.md) for full format specification.

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`CHANGES.md`](CHANGES.md) | What changed from the original version |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) | AWS/cloud deployment guide |
| [`upload-service/STREAMLINE_FORMAT.md`](upload-service/STREAMLINE_FORMAT.md) | JSON format specification |
| [`examples/README.md`](examples/README.md) | Sample files and tutorials |
| `README.md` | Original documentation |

## 🔌 API Reference

**Upload Service** (Port 8080)

```bash
# Upload STL
curl -X POST http://localhost:8080/upload/stl -F "file=@vehicle.stl"

# Upload streamlines
curl -X POST http://localhost:8080/upload/streamlines -F "file=@streamlines.json"

# List files
curl http://localhost:8080/files

# Health check
curl http://localhost:8080/health
```

**Web App** (Port 5273)
- Interactive 3D visualization
- File upload interface
- Real-time streaming

## 🎨 Example Files

```bash
# Use provided example
cd examples
curl -X POST http://localhost:8080/upload/streamlines \
  -F "file=@sample_streamlines.json"
```

See [`examples/README.md`](examples/README.md) for creating your own files.

## 🌩️ Cloud Deployment

### AWS g5.4xlarge (Recommended)

```bash
# Launch instance
# - AMI: Ubuntu 22.04 LTS
# - Instance: g5.4xlarge
# - Storage: 100GB gp3
# - Ports: 5273, 8080, 8011, 8111, 1024/udp

# Install and run
ssh ubuntu@<PUBLIC_IP>
git clone <repo>
cd digital-twins-for-fluid-simulation
./build-docker.sh
docker compose up -d

# Access
http://<PUBLIC_IP>:5273
```

**Cost:** ~$353/month (Spot), ~$1,166/month (On-Demand)

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for detailed deployment instructions.

## 🔧 Troubleshooting

**Upload service not accessible:**
```bash
docker compose logs upload
curl http://localhost:8080/health
```

**Streamlines not visible:**
- Enable "Curve Trace" mode in web UI
- Check JSON format validity
- Verify coordinates are within bounds

**Kit app crashes:**
- Reduce streamline count (< 50,000 points)
- Simplify STL geometry (< 100,000 triangles)
- Increase Docker memory limit

See [`DEPLOYMENT.md`](DEPLOYMENT.md#troubleshooting) for more solutions.

## 💡 Performance Tips

1. **Streamlines**: Keep total points < 50,000
2. **STL Files**: Aim for < 100,000 triangles
3. **File Sizes**: STL < 50MB, JSON < 10MB
4. **Colors**: Normalize scalar values for better visualization

## 🏗️ Architecture

```
Browser (5273)
    ↓
Web App ←→ Kit App (GPU 0) ←→ ZMQ Service ←→ Upload Service (8080)
                ↓                                    ↓
          Visualization                     uploaded_files/
                                            ├── stl/
                                            └── streamlines/
```

**Services:**
- **web**: React frontend with upload UI
- **kit**: Omniverse rendering engine (GPU 0)
- **upload**: FastAPI file upload service
- **zmq**: Data bridge between services

## 📊 Comparison

### Original Version
- **Purpose**: Real-time CFD inference with AI
- **GPU**: 2x 40GB (Rendering + Inference)
- **Cost**: ~$3,500/month (AWS On-Demand)
- **Use Case**: Interactive AI-driven design exploration

### Custom Upload Version
- **Purpose**: Visualize pre-computed CFD results
- **GPU**: 1x 24GB (Rendering only)
- **Cost**: ~$1,166/month (AWS On-Demand)
- **Use Case**: Present simulation results, custom data viz

**Both versions:**
- ✅ Real-time 3D visualization
- ✅ WebRTC streaming
- ✅ Interactive controls
- ✅ High-quality rendering

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📝 License

See [LICENSE](LICENSE) for details.

## 🆘 Support

- **Issues**: https://github.com/NVIDIA-Omniverse-blueprints/digital-twins-for-fluid-simulation/issues
- **Docs**: Check documentation in this repository
- **Examples**: See [`examples/`](examples/) directory

## 🎯 Next Steps

1. **Deploy**: Follow [`DEPLOYMENT.md`](DEPLOYMENT.md) to deploy on AWS
2. **Create Data**: Use [`examples/README.md`](examples/README.md) to generate streamlines
3. **Customize**: Modify web UI or add new features
4. **Scale**: Set up load balancing for multiple users

---

**Note**: This is the custom upload version. For the original Physics NIM version, see `README.md`.
