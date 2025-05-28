---
layout: home
---

<div class="hero">
  <h1>TI-CSC</h1>
  <p>Temporal Interference - Computational Stimulation Core</p>
  <p>A comprehensive toolbox for temporal interference stimulation research, providing end-to-end neuroimaging and simulation capabilities</p>
  <div class="hero-buttons">
    <a href="/downloads" class="btn">Download Now</a>
    <a href="/documentation" class="btn btn-secondary">Get Started</a>
  </div>
</div>

<div class="features">
  <div class="feature-card">
    <div class="feature-icon">🧠</div>
    <h3>Pre-processing Pipeline</h3>
    <p>Complete neuroimaging pipeline including DICOM to NIfTI conversion, FreeSurfer cortical reconstruction, and SimNIBS head modeling</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">⚡</div>
    <h3>TI Field Simulation</h3>
    <p>Advanced FEM-based temporal interference field calculations with enhanced control over simulation parameters</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🎯</div>
    <h3>Optimization Algorithms</h3>
    <p>Evolution-based and exhaustive search algorithms for optimal electrode placement and stimulation parameters</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">📊</div>
    <h3>Comprehensive Analysis</h3>
    <p>Atlas-based and arbitrary ROI analysis tools for detailed examination of stimulation effects</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🖼️</div>
    <h3>Interactive Visualization</h3>
    <p>Advanced NIfTI and mesh viewers with overlay capabilities and real-time 3D rendering</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🐳</div>
    <h3>Docker-based</h3>
    <p>Fully containerized environment ensuring reproducibility and easy deployment across platforms</p>
  </div>
</div>

## Quick Start

1. **Install Docker Desktop** - Required for running TI-CSC
2. **Download TI-CSC** - Get the executable for your platform
3. **Launch the Application** - Start the launcher and select your project directory
4. **Start Docker Containers** - Click to download and start the TI-CSC environment
5. **Launch CLI or GUI** - Choose your preferred interface

## What is Temporal Interference?

Temporal Interference (TI) is a non-invasive brain stimulation technique that uses multiple high-frequency electric fields to create a low-frequency envelope at their intersection point. This allows for deep brain stimulation without affecting superficial tissues.

## Key Features

- **BIDS-compliant**: Works with Brain Imaging Data Structure formatted datasets
- **Multi-platform**: Runs on macOS, Linux, and Windows
- **GPU Support**: Accelerated processing for compatible systems
- **Extensible**: Modular architecture allows for custom extensions
- **Open Source**: Free and open for research use

## System Requirements

- **Operating System**: macOS 10.14+, Ubuntu 18.04+, Windows 10+
- **Docker Desktop**: Latest version required
- **RAM**: Minimum 16GB (32GB recommended)
- **Storage**: 50GB free space for Docker images
- **GPU**: NVIDIA GPU with CUDA support (optional, for acceleration)

## Latest Release

**Version 2.0.0** - Released December 2024

Major update with improved Docker integration, new GUI launcher, and enhanced optimization algorithms.

[View all releases →](/releases)

## Community

- [GitHub Repository](https://github.com/idossha/TI-CSC-2.0)
- [Issue Tracker](https://github.com/idossha/TI-CSC-2.0/issues)
- [Discussions](https://github.com/idossha/TI-CSC-2.0/discussions)

## Citation

If you use TI-CSC in your research, please cite:

```bibtex
@software{ticsc2024,
  title = {TI-CSC: Temporal Interference - Computational Stimulation Core},
  author = {Your Name and Contributors},
  year = {2024},
  version = {2.0.0},
  url = {https://github.com/idossha/TI-CSC-2.0}
}
``` 