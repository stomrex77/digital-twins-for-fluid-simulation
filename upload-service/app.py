#!/usr/bin/env python3
"""
File Upload Service for Digital Twin Fluid Simulation
Handles uploads of STL files and JSON streamline data
"""
import os
import json
import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Digital Twin Upload Service")

# Enable CORS for web app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("/app/uploaded_files")
STL_DIR = UPLOAD_DIR / "stl"
STREAMLINES_DIR = UPLOAD_DIR / "streamlines"

# Ensure directories exist
STL_DIR.mkdir(parents=True, exist_ok=True)
STREAMLINES_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
async def root():
    return {
        "service": "Digital Twin Upload Service",
        "version": "1.0.0",
        "endpoints": {
            "upload_stl": "/upload/stl",
            "upload_streamlines": "/upload/streamlines",
            "list_files": "/files",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/upload/stl")
async def upload_stl(file: UploadFile = File(...), name: Optional[str] = Form(None)):
    """
    Upload an STL file for visualization

    Args:
        file: STL file to upload
        name: Optional custom name (defaults to original filename)

    Returns:
        JSON with file path and metadata
    """
    # Validate file extension
    if not file.filename.lower().endswith('.stl'):
        raise HTTPException(status_code=400, detail="File must be an STL file (.stl)")

    # Use custom name or original filename
    filename = name if name else file.filename
    if not filename.endswith('.stl'):
        filename += '.stl'

    file_path = STL_DIR / filename

    try:
        # Save uploaded file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = file_path.stat().st_size

        return JSONResponse(content={
            "success": True,
            "filename": filename,
            "path": str(file_path),
            "size_bytes": file_size,
            "message": f"STL file '{filename}' uploaded successfully"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@app.post("/upload/streamlines")
async def upload_streamlines(file: UploadFile = File(...), name: Optional[str] = Form(None)):
    """
    Upload a JSON file containing streamline data

    Expected JSON format:
    {
        "streamlines": [
            {
                "path": [[x1, y1, z1], [x2, y2, z2], ...],
                "scalar": [v1, v2, ...],  // Optional: velocity magnitude or other scalar
                "color": [r, g, b]        // Optional: custom color
            },
            ...
        ],
        "metadata": {              // Optional metadata
            "units": "m/s",
            "domain_bounds": [[xmin, ymin, zmin], [xmax, ymax, zmax]],
            "description": "..."
        }
    }

    Args:
        file: JSON file containing streamline data
        name: Optional custom name (defaults to original filename)

    Returns:
        JSON with file path and validation results
    """
    # Validate file extension
    if not file.filename.lower().endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a JSON file (.json)")

    # Use custom name or original filename
    filename = name if name else file.filename
    if not filename.endswith('.json'):
        filename += '.json'

    file_path = STREAMLINES_DIR / filename

    try:
        # Read and validate JSON
        content = await file.read()
        data = json.loads(content)

        # Validate structure
        if "streamlines" not in data:
            raise HTTPException(
                status_code=400,
                detail="JSON must contain 'streamlines' array"
            )

        streamlines = data["streamlines"]
        if not isinstance(streamlines, list):
            raise HTTPException(
                status_code=400,
                detail="'streamlines' must be an array"
            )

        # Validate each streamline
        for i, streamline in enumerate(streamlines):
            if "path" not in streamline:
                raise HTTPException(
                    status_code=400,
                    detail=f"Streamline {i} missing 'path' field"
                )

            path = streamline["path"]
            if not isinstance(path, list) or len(path) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Streamline {i} 'path' must be a non-empty array"
                )

            # Check first point is [x, y, z]
            if len(path[0]) != 3:
                raise HTTPException(
                    status_code=400,
                    detail=f"Streamline {i} path points must be [x, y, z] arrays"
                )

        # Save validated JSON
        with file_path.open("w") as f:
            json.dump(data, f, indent=2)

        file_size = file_path.stat().st_size
        num_streamlines = len(streamlines)

        return JSONResponse(content={
            "success": True,
            "filename": filename,
            "path": str(file_path),
            "size_bytes": file_size,
            "num_streamlines": num_streamlines,
            "message": f"Streamlines file '{filename}' uploaded successfully with {num_streamlines} streamlines"
        })

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@app.get("/files")
async def list_files():
    """
    List all uploaded files

    Returns:
        JSON with lists of STL and streamline files
    """
    try:
        stl_files = [
            {
                "name": f.name,
                "path": str(f),
                "size_bytes": f.stat().st_size
            }
            for f in STL_DIR.glob("*.stl")
        ]

        streamline_files = []
        for f in STREAMLINES_DIR.glob("*.json"):
            try:
                with f.open() as json_file:
                    data = json.load(json_file)
                    num_streamlines = len(data.get("streamlines", []))
            except:
                num_streamlines = 0

            streamline_files.append({
                "name": f.name,
                "path": str(f),
                "size_bytes": f.stat().st_size,
                "num_streamlines": num_streamlines
            })

        return {
            "stl_files": stl_files,
            "streamline_files": streamline_files,
            "total_stl": len(stl_files),
            "total_streamlines": len(streamline_files)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@app.delete("/files/stl/{filename}")
async def delete_stl(filename: str):
    """Delete an uploaded STL file"""
    file_path = STL_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")

    try:
        file_path.unlink()
        return {"success": True, "message": f"Deleted '{filename}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@app.delete("/files/streamlines/{filename}")
async def delete_streamlines(filename: str):
    """Delete an uploaded streamlines file"""
    file_path = STREAMLINES_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")

    try:
        file_path.unlink()
        return {"success": True, "message": f"Deleted '{filename}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
