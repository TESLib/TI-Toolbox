# TI-CSC Pipeline Templates

This directory contains pre-built pipeline templates for common temporal interference workflows. These templates can be loaded into the Pipeline Builder tab to quickly set up complete workflows.

## Available Templates

### 1. `complete_ti_pipeline.json`
**Complete End-to-End Pipeline**

A comprehensive workflow that takes raw DICOM files through the entire temporal interference analysis pipeline:

- **Input**: Raw DICOM files in subject directories
- **Pre-processing**: DICOM → NIfTI conversion, FreeSurfer reconstruction, SimNIBS m2m folder creation
- **Optimization**: Flex Search electrode optimization targeting right angular gyrus
- **Simulation**: Temporal interference simulation with optimized electrodes
- **Analysis**: Spherical ROI analysis of the target region
- **Output**: NIfTI results with comprehensive reports

**Target Region**: Right Angular Gyrus (45, -65, 35) - important for spatial attention and numerical cognition

**Estimated Runtime**: 8-24 hours per subject (depending on hardware)

### 2. `simulation_only_pipeline.json`
**Simulation and Analysis Only**

A streamlined workflow for subjects that already have preprocessed data:

- **Input**: Subjects with existing FreeSurfer and SimNIBS m2m folders
- **Simulation**: TI simulation with predefined montages
- **Analysis**: Both spherical and cortical region analysis for comparison
- **Output**: Archived results with detailed reports

**Use Cases**:
- Testing different montages on preprocessed subjects
- Comparing analysis methods
- Parameter sensitivity studies
- Quick research iterations

**Estimated Runtime**: 30 minutes - 2 hours per subject

## How to Use Pipeline Templates

### Loading a Template

1. Open the **Pipeline Builder** tab in TI-CSC
2. Click the **Load** button in the Pipeline Controls section
3. Navigate to the `pipelines/` directory
4. Select the desired template file (`.json`)
5. Click **Open**

The pipeline will be loaded with all blocks and connections pre-configured.

### Customizing Templates

After loading a template, you can:

1. **Select any block** to edit its parameters in the Properties panel
2. **Modify coordinates** for ROI analysis or optimization targets
3. **Adjust simulation parameters** like current values or electrode properties
4. **Add or remove blocks** by dragging from the Block Palette
5. **Create new connections** by dragging between block ports
6. **Save your modifications** as a new pipeline file

### Creating Your Own Pipeline

1. Start with **New** to create a blank pipeline
2. **Add blocks** from the Block Palette:
   - 📁 **Subject Input**: Define which subjects to process
   - 🔧 **Pre-processing**: DICOM conversion and FreeSurfer
   - 🎯 **Optimization**: Flex Search or Ex Search electrode optimization
   - ⚡ **Simulation**: Run TI simulations
   - 📊 **Analysis**: Analyze simulation results
   - 💾 **Output**: Save and archive results
3. **Connect blocks** by dragging between output and input ports
4. **Configure parameters** for each block using the Properties panel
5. **Validate** your pipeline using the Validate button
6. **Save** your pipeline for future use

## Pipeline Validation

Before running a pipeline, use the **Validate Pipeline** button to check for:

- Missing input blocks
- Disconnected blocks
- Circular dependencies
- Invalid parameter configurations

## Execution

1. Ensure your pipeline is valid
2. Click **▶️ Run Pipeline** to start execution
3. Monitor progress in the Execution Console
4. Blocks will change color to indicate status:
   - **Gray**: Pending
   - **Orange**: Running
   - **Green**: Completed
   - **Red**: Failed
5. Use **⏹️ Stop** to halt execution if needed

## Tips for Efficient Pipelines

- **Start small**: Test with one subject before processing entire datasets
- **Use parallel processing**: Enable parallel options where available
- **Monitor resources**: Watch CPU, memory, and disk usage during execution
- **Save frequently**: Save pipeline configurations before running
- **Use descriptive names**: Name blocks clearly for easy identification

## Troubleshooting

- **Pipeline won't validate**: Check all blocks are connected and have required inputs
- **Execution fails**: Check the console output for error messages
- **Slow performance**: Consider reducing parallel processes or enabling quiet mode
- **Out of memory**: Process fewer subjects simultaneously or increase system RAM

## Advanced Features

- **Parameter sweeps**: Create multiple similar blocks with different parameters
- **Conditional execution**: Use multiple analysis blocks for different regions
- **Template sharing**: Save and share pipeline configurations with collaborators
- **Automated workflows**: Set up pipelines for batch processing

For more information, consult the TI-CSC documentation or contact support. 