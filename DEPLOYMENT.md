# Deployment Guide - Digital Twin Fluid Simulation

This guide explains how to deploy the Digital Twin Fluid Simulation system on AWS or other cloud platforms.

## Overview

The refactored system consists of the following services:
- **Web App** (Port 5273): React frontend with file upload interface
- **Kit App** (Ports 8011, 8111, 47995-48012, 49000-49007): Omniverse visualization engine
- **Upload Service** (Port 8080): FastAPI service for uploading STL files and streamline JSON
- **ZMQ Service** (Ports 5555-5564): Data bridge between Upload Service and Kit App

**Key Changes:**
- ✅ No longer requires Physics NIM (NVIDIA Inference Microservice)
- ✅ No longer requires GPU 1 (only GPU 0 for Omniverse rendering)
- ✅ Upload custom STL files and streamline JSON data
- ✅ Simplified architecture suitable for cloud deployment

## System Requirements

### Minimum Requirements
- **GPU**: 1x NVIDIA GPU with 24GB+ VRAM (e.g., RTX A5000, L40S, A6000)
  - Only GPU 0 is needed for Omniverse rendering
  - No second GPU required (Physics NIM removed)
- **CPU**: 16+ cores
- **RAM**: 64GB
- **Storage**: 50GB
- **OS**: Ubuntu 22.04 or 24.04
- **Docker**: With NVIDIA Container Toolkit

### Recommended for Production
- **GPU**: 1x NVIDIA RTX A6000 (48GB) or L40S (48GB)
- **CPU**: 32+ cores
- **RAM**: 128GB
- **Storage**: 100GB SSD

## AWS Deployment

### Recommended Instance Types

| Instance Type | vCPUs | RAM | GPU | Use Case |
|--------------|-------|-----|-----|----------|
| g5.4xlarge | 16 | 64GB | 1x A10G (24GB) | Development/Testing |
| g5.12xlarge | 48 | 192GB | 4x A10G (96GB total) | Production (use 1 GPU) |
| g4dn.12xlarge | 48 | 192GB | 4x T4 (64GB total) | Budget Production |
| p3.2xlarge | 8 | 61GB | 1x V100 (16GB) | Light Testing |

**Note:** For production, we recommend **g5.4xlarge** or **g5.12xlarge** (using only 1 GPU).

### Step 1: Launch EC2 Instance

1. Go to AWS EC2 Console
2. Click **Launch Instance**
3. Configure:
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance Type**: g5.4xlarge (or g5.12xlarge for production)
   - **Storage**: 100GB gp3 SSD
   - **Security Group**:
     - SSH (22) from your IP
     - TCP 5273 (web app) from 0.0.0.0/0
     - TCP 8080 (upload API) from 0.0.0.0/0
     - TCP 8011, 8111 (Kit app) from 0.0.0.0/0
     - UDP 1024 (streaming) from 0.0.0.0/0
     - TCP/UDP 47995-48012, 49000-49007 (Omniverse) from 0.0.0.0/0

4. Launch and connect via SSH

### Step 2: Install NVIDIA Drivers and Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install NVIDIA drivers (AWS provides optimized drivers)
sudo apt install -y ubuntu-drivers-common
sudo ubuntu-drivers autoinstall

# Reboot
sudo reboot

# After reboot, verify GPU
nvidia-smi

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Step 3: Clone and Configure

```bash
# Clone repository
git clone https://github.com/NVIDIA-Omniverse-blueprints/digital-twins-for-fluid-simulation.git
cd digital-twins-for-fluid-simulation

# Create .env file
cat > .env << EOF
# Omniverse credentials (optional, for accessing Nucleus)
OMNI_USER=your_email@example.com
OMNI_PASS=your_password

# Kit app configuration
KIT_APP=omni.rtwt.app.webrtc.kit
USD_URL=/home/ubuntu/usd/world_rtwt_Main_v1.usda

# ZMQ configuration
ZMQ_IP=127.0.0.1
ZMQ_FIRST_PORT=5555
ZMQ_REQUEST_TIMEOUT=5000
ZMQ_REQUEST_QUEUE_SIZE=1

# GPU configuration (only GPU 0 needed now)
CUDA_VISIBLE_DEVICES=0

# Streaming configuration
STREAMSDK_SENDER_TIMEOUT=100000
EOF

# Create uploaded files directory
mkdir -p uploaded_files/stl uploaded_files/streamlines
```

### Step 4: Build and Run

```bash
# Build Docker images
./build-docker.sh

# Start services
docker compose up -d

# Check logs
docker compose logs -f web
docker compose logs -f kit
docker compose logs -f upload
docker compose logs -f zmq

# Verify all services are running
docker compose ps
```

### Step 5: Access the Application

1. Get your EC2 public IP: `curl -s http://169.254.169.254/latest/meta-data/public-ipv4`
2. Open in browser: `http://<PUBLIC_IP>:5273`
3. You should see the Digital Twin interface with an upload button

### Step 6: Upload Your Files

1. Click the **Upload** button (📤 icon) in the bottom-left
2. Upload your STL file (vehicle geometry)
3. Upload your streamlines JSON file (see format below)
4. Files will be stored in the container and visible in the visualization

## Streamline JSON Format

Create a JSON file with this structure:

```json
{
  "streamlines": [
    {
      "path": [
        [-5.0, 0.0, 0.5],
        [-4.5, 0.1, 0.52],
        [-4.0, 0.15, 0.55]
      ],
      "scalar": [30.0, 31.2, 32.5],
      "color": [1.0, 0.0, 0.0]
    }
  ],
  "metadata": {
    "units": "m/s",
    "domain_bounds": [[-6.0, -2.0, -1.0], [6.0, 2.0, 2.0]],
    "description": "Airflow streamlines"
  }
}
```

**Required fields:**
- `streamlines`: Array of streamline objects
- `streamlines[].path`: Array of [x, y, z] coordinates

**Optional fields:**
- `streamlines[].scalar`: Values for color-coding (e.g., velocity magnitude)
- `streamlines[].color`: Custom RGB color [r, g, b] in range [0, 1]
- `metadata`: Descriptive information

See `upload-service/STREAMLINE_FORMAT.md` for detailed format documentation.

## Cost Estimation (AWS)

### g5.4xlarge (Recommended for Production)
- **On-Demand**: ~$1.62/hour = ~$1,166/month (24/7)
- **Spot Instance**: ~$0.49/hour = ~$353/month (24/7)
- **Reserved (1 year)**: ~$0.97/hour = ~$699/month (24/7)

### Cost Optimization Tips
1. Use **Spot Instances** for development (70% savings)
2. Use **Reserved Instances** for production (40% savings)
3. Stop instances when not in use
4. Use **Auto Scaling** to scale down during off-peak hours
5. Consider **Graviton instances** for web/upload services (ARM-based, cheaper)

## Alternative Cloud Platforms

### Google Cloud Platform (GCP)

**Recommended Instance**: n1-standard-16 with 1x NVIDIA T4

```bash
# Create instance
gcloud compute instances create digital-twin \
  --zone=us-central1-a \
  --machine-type=n1-standard-16 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --boot-disk-size=100GB \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --maintenance-policy=TERMINATE

# Install NVIDIA drivers
gcloud compute ssh digital-twin
sudo /opt/deeplearning/install-driver.sh

# Continue with Step 3 above
```

### Microsoft Azure

**Recommended Instance**: NC6s_v3 (1x V100)

```bash
# Create instance
az vm create \
  --resource-group myResourceGroup \
  --name digital-twin \
  --image UbuntuLTS \
  --size Standard_NC6s_v3 \
  --admin-username azureuser \
  --generate-ssh-keys

# Install NVIDIA drivers
ssh azureuser@<PUBLIC_IP>
# Continue with Step 2 above
```

## Monitoring and Troubleshooting

### Check Service Health

```bash
# Check all containers
docker compose ps

# Check upload service
curl http://localhost:8080/health
# Should return: {"status": "healthy"}

# Check logs
docker compose logs upload --tail=50
docker compose logs kit --tail=50
docker compose logs zmq --tail=50

# Check GPU usage
nvidia-smi -l 1
```

### Common Issues

**Issue**: Kit app fails to start
- **Solution**: Ensure only GPU 0 is required. Check `docker compose logs kit`

**Issue**: Upload service not accessible
- **Solution**: Check security group allows port 8080. Verify with `curl localhost:8080`

**Issue**: Streamlines not visible
- **Solution**: Check JSON format is correct. Use validation endpoint:
  ```bash
  curl -X POST http://localhost:8080/upload/streamlines -F "file=@streamlines.json"
  ```

**Issue**: Out of memory
- **Solution**: Reduce streamline count or simplify STL geometry

### Performance Tuning

```bash
# Increase shared memory for Docker
echo '{"default-shm-size": "8G"}' | sudo tee -a /etc/docker/daemon.json
sudo systemctl restart docker

# Limit container memory usage
docker compose up -d --scale kit=1 --memory=32g
```

## Security Best Practices

1. **Firewall**: Restrict ports to your IP only
   ```bash
   # Update security group to allow only your IP
   # AWS Console > EC2 > Security Groups > Edit Inbound Rules
   ```

2. **HTTPS**: Use reverse proxy with SSL certificate
   ```bash
   # Install nginx and certbot
   sudo apt install nginx certbot python3-certbot-nginx

   # Configure nginx as reverse proxy
   sudo nano /etc/nginx/sites-available/digital-twin

   # Get SSL certificate
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Authentication**: Add authentication to upload service
   - Modify `upload-service/app.py` to add API key verification
   - Set environment variable: `UPLOAD_API_KEY=your-secret-key`

## Backup and Persistence

```bash
# Backup uploaded files
docker run --rm -v $(pwd)/uploaded_files:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/uploaded_files_backup.tar.gz /data

# Restore uploaded files
tar xzf uploaded_files_backup.tar.gz -C uploaded_files/

# Use Docker volumes for persistence
docker volume create uploaded-files-vol
# Update compose.yml to use named volume instead of bind mount
```

## Scaling for Multiple Users

For production with multiple concurrent users:

1. **Load Balancer**: Use AWS ELB to distribute traffic
2. **Multiple Kit Instances**: Run multiple Kit app containers on separate GPUs
3. **Database**: Add PostgreSQL for user management and file metadata
4. **Object Storage**: Use S3 for uploaded files instead of local storage

Example architecture:
```
Internet → ELB → [Web1, Web2, Web3]
                     ↓
                 S3 (STL/JSON files)
                     ↓
         [Kit1(GPU0), Kit2(GPU1), Kit3(GPU2)]
```

## Support and Resources

- **Documentation**: `upload-service/STREAMLINE_FORMAT.md`
- **Example Files**: `examples/` directory
- **Issues**: https://github.com/NVIDIA-Omniverse-blueprints/digital-twins-for-fluid-simulation/issues
- **NVIDIA Omniverse**: https://docs.omniverse.nvidia.com/

## License

See LICENSE file for details.
