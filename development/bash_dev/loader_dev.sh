#!/bin/bash

# Set script directory
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR"

# Default paths file
DEFAULT_PATHS_FILE="$SCRIPT_DIR/.default_paths.dev"

# Function to load default paths
load_default_paths() {
  if [[ -f "$DEFAULT_PATHS_FILE" ]]; then
    source "$DEFAULT_PATHS_FILE"
  fi
}

# Function to save default paths
save_default_paths() {
  echo "LOCAL_PROJECT_DIR=\"$LOCAL_PROJECT_DIR\"" > "$DEFAULT_PATHS_FILE"
  echo "DEV_CODEBASE_DIR=\"$DEV_CODEBASE_DIR\"" >> "$DEFAULT_PATHS_FILE"
}

# Function to initialize required Docker volumes
initialize_volumes() {
  echo "Initializing required Docker volumes..."
  
  # Check and create FSL volume if it doesn't exist
  if ! docker volume inspect ti_csc_fsl_data >/dev/null 2>&1; then
    echo "Creating FSL volume..."
    docker volume create ti_csc_fsl_data
  fi
  
  # Check and create FreeSurfer volume if it doesn't exist
  if ! docker volume inspect ti_csc_freesurfer_data >/dev/null 2>&1; then
    echo "Creating FreeSurfer volume..."
    docker volume create ti_csc_freesurfer_data
  fi

  # Check and create MATLAB Runtime volume if it doesn't exist
  if ! docker volume inspect matlab_runtime >/dev/null 2>&1; then
    echo "Creating MATLAB Runtime volume..."
    docker volume create matlab_runtime
  fi
}

# Function to check allocated Docker resources (CPU, memory)
check_docker_resources() {
  echo "Checking Docker resource allocation..."

  if docker info >/dev/null 2>&1; then
    # Get Docker's memory and CPU allocation
    MEMORY=$(docker info --format '{{.MemTotal}}')
    CPU=$(docker info --format '{{.NCPU}}')

    # Convert memory from bytes to GB
    MEMORY_GB=$(echo "scale=2; $MEMORY / (1024^3)" | bc)

    echo "Docker Memory Allocation: ${MEMORY_GB} GB"
    echo "Docker CPU Allocation: $CPU CPUs"
  else
    echo "Docker is not running or not installed. Please start Docker and try again."
    exit 1
  fi
}

# Function to enable directory path autocompletion
setup_path_completion() {
  bind "set completion-ignore-case on"
  bind "TAB:menu-complete"
  bind "set show-all-if-ambiguous on"
  bind "set menu-complete-display-prefix on"
}

# Function to validate and prompt for the project directory
get_project_directory() {
  while true; do
    if [[ -n "$LOCAL_PROJECT_DIR" ]]; then
      echo "Current project directory: $LOCAL_PROJECT_DIR"
      echo "Press Enter to use this directory or enter a new path:"
      read -e -r new_path
      if [[ -z "$new_path" ]]; then
        break
      else
        LOCAL_PROJECT_DIR="$new_path"
      fi
    else
      echo "Give path to local project dir:"
      read -e -r LOCAL_PROJECT_DIR
    fi

    if [[ -d "$LOCAL_PROJECT_DIR" ]]; then
      echo "Project directory found."
      break
    else
      echo "Invalid directory. Please provide a valid path."
    fi
  done
}

# Function to get development codebase directory
get_dev_codebase_directory() {
  while true; do
    if [[ -n "$DEV_CODEBASE_DIR" ]]; then
      echo "Current development codebase directory: $DEV_CODEBASE_DIR"
      echo "Press Enter to use this directory or enter a new path:"
      read -e -r new_path
      if [[ -z "$new_path" ]]; then
        break
      else
        DEV_CODEBASE_DIR="$new_path"
      fi
    else
      echo "Enter path to development codebase:"
      read -e -r DEV_CODEBASE_DIR
    fi

    if [[ -d "$DEV_CODEBASE_DIR" ]]; then
      echo "Development codebase directory found."
      break
    else
      echo "Invalid directory. Please provide a valid path."
    fi
  done
}

# Function to get the IP address of the host machine
get_host_ip() {
  case "$(uname -s)" in
  Darwin)
    # Get the local IP address on macOS
    HOST_IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
    ;;
  Linux)
    # On Linux, we don't need to calculate HOST_IP for DISPLAY
    HOST_IP=""
    ;;
  *)
    echo "Unsupported OS. Please use macOS or Linux."
    exit 1
    ;;
  esac
  echo "Host IP: $HOST_IP"
}

# Function to set DISPLAY environment variable based on OS and processor type
set_display_env() {
  echo "Setting DISPLAY environment variable..."

  if [[ "$(uname -s)" == "Linux" ]]; then
    # If Linux, use the existing DISPLAY
    export DISPLAY=$DISPLAY
    echo "Using system's DISPLAY: $DISPLAY"
  else
    # For macOS, dynamically obtain the host IP and set DISPLAY
    get_host_ip # Get the IP address dynamically
    export DISPLAY="$HOST_IP:0"
    echo "DISPLAY set to $DISPLAY"
  fi
}

# Function to allow connections from XQuartz or X11
allow_xhost() {
  echo "Allowing connections from XQuartz or X11..."

  if [[ "$(uname -s)" == "Linux" ]]; then
    # Allow connections for Linux
    xhost +local:root
  else
    # Use the dynamically obtained IP for macOS xhost
    xhost + "$HOST_IP"
  fi
}

# Function to validate docker-compose.yml existence
validate_docker_compose() {
  if [[ ! -f "$SCRIPT_DIR/docker-compose.dev.yml" ]]; then
    echo "Error: docker-compose.dev.yml not found in $SCRIPT_DIR. Please make sure the file is present."
    exit 1
  fi
}

# Function to display welcome message
display_welcome() {
  echo " "
  echo "#####################################################################"
  echo "Welcome to the TI toolbox from the Center for Sleep and Consciousness"
  echo "Developed by Ido Haber as a wrapper around Modified SimNIBS"
  echo " "
  echo "Make sure you have XQuartz (on macOS), X11 (on Linux), or Xming/VcXsrv (on Windows) running."
  echo "If you wish to use the optimizer, consider allocating more RAM to Docker."
  echo "#####################################################################"
  echo " "
}

# Function to start browser monitor in background
start_browser_monitor() {
  echo "🖥️ Starting browser launcher monitor..."
  
  local browser_script="$SCRIPT_DIR/browser_launcher.ps1"
  
  if [[ ! -f "$browser_script" ]]; then
    echo "⚠️ Browser launcher script not found: $browser_script"
    echo "💡 Manual browser launching will be required"
    return 0
  fi
  
  # Convert WSL paths to Windows paths for PowerShell
  local win_browser_script=""
  local win_project_path=""
  
  # Convert browser script path from WSL to Windows
  if [[ "$browser_script" =~ ^/mnt/([a-z])/(.*) ]]; then
    local drive="${BASH_REMATCH[1]^^}"  # Convert to uppercase
    local path="${BASH_REMATCH[2]}"
    win_browser_script="${drive}:\\${path//\//\\}"
  else
    win_browser_script="$browser_script"
  fi
  
  # Convert project path from WSL to Windows  
  if [[ "$LOCAL_PROJECT_DIR" =~ ^/mnt/([a-z])/(.*) ]]; then
    local drive="${BASH_REMATCH[1]^^}"  # Convert to uppercase
    local path="${BASH_REMATCH[2]}"
    win_project_path="${drive}:\\${path//\//\\}"
  else
    win_project_path="$LOCAL_PROJECT_DIR"
  fi
  
  echo "🔄 Path conversion:"
  echo "   Browser script: $browser_script → $win_browser_script"
  echo "   Project path: $LOCAL_PROJECT_DIR → $win_project_path"
  
  # Detect if we're on Windows (WSL, Git Bash, etc.)
  if [[ -n "$WINDIR" ]] || [[ -n "$WSL_DISTRO_NAME" ]] || [[ "$(uname -r)" == *microsoft* ]] || command -v powershell.exe >/dev/null 2>&1; then
    echo "🪟 Windows environment detected - starting PowerShell browser monitor"
    
    # Try to start PowerShell script in background
    if command -v powershell.exe >/dev/null 2>&1; then
      # Create a completely detached PowerShell process that survives bash script exit
      echo "🚀 Starting detached PowerShell browser monitor (EARLY START)..."
      echo "🔧 DEBUG: Paths being used:"
      echo "   WSL Browser script: $browser_script"
      echo "   Win Browser script: $win_browser_script"
      echo "   WSL Project path: $LOCAL_PROJECT_DIR"
      echo "   Win Project path: $win_project_path"
      
      # Verify the script file exists
      if [[ ! -f "$browser_script" ]]; then
        echo "❌ ERROR: Browser script not found at: $browser_script"
        return 1
      fi
      echo "✅ Browser script file exists"
      
      # Build the complete command (remove problematic window title)
      local cmd_command="start /B powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Minimized -File \"$win_browser_script\" -ProjectPath \"$win_project_path\" -Verbose"
      echo "🔧 DEBUG: Full cmd.exe command:"
      echo "   cmd.exe /c \"$cmd_command\""
      
      # Try different approaches and capture output
      echo "📋 Attempting Method 1: cmd.exe with full detachment..."
      local cmd_output=""
      local cmd_exit_code=0
      
      # Method 1: Full detachment
      cmd_output=$(cmd.exe /c "$cmd_command" 2>&1) || cmd_exit_code=$?
      echo "📊 Method 1 results:"
      echo "   Exit code: $cmd_exit_code"
      echo "   Output: '$cmd_output'"
      
      # Wait and check if process started
      sleep 3
      
      # Check if PowerShell process is running with our script
      echo "🔍 Checking if PowerShell process started..."
      local ps_check=""
      ps_check=$(powershell.exe -Command "Get-Process -Name powershell -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count" 2>/dev/null || echo "0")
      echo "📈 PowerShell processes found: $ps_check"
      
      # Simple process check and verification
      echo "📋 Checking PowerShell processes..."
      powershell.exe -Command "Get-Process -Name powershell -ErrorAction SilentlyContinue | Select-Object Id, ProcessName" 2>/dev/null || echo "No PowerShell processes found"
      
      # Try to verify if our script is actually running
      echo "🔍 Verifying if browser launcher script is active..."
      local script_running=$(powershell.exe -Command "Test-Path \"$win_project_path\\.ti-csc-info\"" 2>/dev/null || echo "False")
      echo "📁 Project .ti-csc-info directory exists: $script_running"
      
      # Method 2: If first method failed, try simpler approach
      if [[ "${ps_check:-0}" == "0" ]]; then
        echo "📋 Method 1 failed, trying Method 2: Direct PowerShell start..."
        
        # Try starting PowerShell directly in background
        echo "🔧 Starting PowerShell directly..."
        powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Minimized -File "$win_browser_script" -ProjectPath "$win_project_path" -Verbose &
        local ps_pid=$!
        echo "📊 Method 2 results:"
        echo "   Bash PID: $ps_pid"
        
        # Disown the process
        disown $ps_pid 2>/dev/null || true
        
        sleep 2
        
        # Check again with simpler command
        echo "🔍 Checking processes again..."
        ps_check=$(powershell.exe -Command "Get-Process -Name powershell -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count" 2>/dev/null || echo "0")
        echo "📈 PowerShell processes after Method 2: ${ps_check:-0}"
      fi
      
      # Final status with safer comparison
      local final_count="${ps_check:-0}"
      if [[ "$final_count" != "0" && "$final_count" != "" ]]; then
        echo "✅ Browser monitor appears to be running!"
        echo "🔍 Check Task Manager for 'powershell.exe' processes"
      else
        echo "❌ Browser monitor failed to start"
        echo "💡 Try running manually in PowerShell:"
        echo "   powershell.exe -File '$win_browser_script' -ProjectPath '$win_project_path'"
      fi
      
          elif command -v pwsh >/dev/null 2>&1; then
        # Use pwsh (PowerShell Core) if available  
        echo "🚀 Starting PowerShell Core browser monitor..."
        nohup pwsh -NoProfile -ExecutionPolicy Bypass -File "$win_browser_script" -ProjectPath "$win_project_path" -Verbose >/dev/null 2>&1 &
        disown
        
        sleep 2
        echo "✅ PowerShell Core browser monitor launch attempted"
        echo "🔍 Monitor should be visible in Task Manager as 'pwsh'"
        echo "💡 If browser doesn't open automatically, manually run:"
        echo "   pwsh -File '$win_browser_script' -ProjectPath '$win_project_path'"
          else
        echo "⚠️ PowerShell not found - browser auto-launch disabled"
        echo "💡 You can manually run: powershell.exe -File '$win_browser_script' -ProjectPath '$win_project_path'"
      fi
  else
    echo "🐧 Non-Windows environment - browser monitor not applicable"
    echo "💡 Use 'Docker Chrome' option in GUI instead"
  fi
  
  echo "🌐 Browser launch system ready!"
}

# Function to stop browser monitor
stop_browser_monitor() {
  echo "🛑 Stopping browser monitor..."
  
  # Kill PowerShell processes running the browser launcher
  if command -v powershell.exe >/dev/null 2>&1; then
    echo "🔍 Looking for PowerShell browser monitor processes..."
    # Simplified approach - just stop all powershell processes (safer)
    local killed=$(powershell.exe -Command "Get-Process -Name powershell -ErrorAction SilentlyContinue | Stop-Process -Force -PassThru | Measure-Object | Select-Object -ExpandProperty Count" 2>/dev/null || echo "0")
    
    local kill_count="${killed:-0}"
    if [[ "$kill_count" != "0" && "$kill_count" != "" ]]; then
      echo "✅ Stopped $kill_count PowerShell browser monitor process(es)"
    else
      echo "ℹ️ No PowerShell browser monitor processes found"
    fi
  fi
  
  if command -v pwsh >/dev/null 2>&1; then
    echo "🔍 Looking for PowerShell Core browser monitor processes..."
    # Simplified approach - just stop all pwsh processes
    local killed_core=$(pwsh -Command "Get-Process -Name pwsh -ErrorAction SilentlyContinue | Stop-Process -Force -PassThru | Measure-Object | Select-Object -ExpandProperty Count" 2>/dev/null || echo "0")
    
    local core_count="${killed_core:-0}"
    if [[ "$core_count" != "0" && "$core_count" != "" ]]; then
      echo "✅ Stopped $core_count PowerShell Core browser monitor process(es)"
    else
      echo "ℹ️ No PowerShell Core browser monitor processes found"
    fi
  fi
  
  echo "✅ Browser monitor cleanup completed"
}

# Function to run Docker Compose and attach to simnibs container
run_docker_compose() {
  # Pull images if they don't exist
  echo "Pulling required Docker images..."
  docker compose -f "$SCRIPT_DIR/docker-compose.dev.yml" pull

  # Run Docker Compose
  docker compose -f "$SCRIPT_DIR/docker-compose.dev.yml" up --build -d

  # Wait for containers to initialize
  echo "Waiting for services to initialize..."
  sleep 3

  # Check if simnibs service is up
  if ! docker compose -f "$SCRIPT_DIR/docker-compose.dev.yml" ps | grep -q "simnibs"; then
    echo "Error: simnibs service is not running. Please check your docker-compose.dev.yml and container logs."
    docker compose -f "$SCRIPT_DIR/docker-compose.dev.yml" logs
    exit 1
  fi

  # Attach to the simnibs container with an interactive terminal
  echo "Attaching to the simnibs_container..."
  docker exec -ti simnibs_container bash

  # Stop and remove all containers when done
  docker compose -f "$SCRIPT_DIR/docker-compose.dev.yml" down

  # Stop browser monitor if running
  stop_browser_monitor

  # Revert X server access permissions
  xhost -local:root
}

# Function to get version from version.py
get_version() {
    local version_file="$SCRIPT_DIR/../../version.py"
    if [ -f "$version_file" ]; then
        # Extract version using grep and sed
        grep "__version__" "$version_file" | sed 's/.*"\(.*\)".*/\1/'
    else
        echo "Error: version.py not found at $version_file"
        exit 1
    fi
}

# Function to write system info to a hidden folder in the user's project directory
write_system_info() {
  INFO_DIR="$LOCAL_PROJECT_DIR/.ti-csc-info"
  INFO_FILE="$INFO_DIR/system_info.txt"
  
  # Create directory with error checking
  if ! mkdir -p "$INFO_DIR" 2>/dev/null; then
    echo "Error: Could not create directory $INFO_DIR"
    return 1
  fi

  # Create and write to file with error checking
  if ! {
    echo "# TI-CSC System Info"
    echo "Date: $(date)"
    echo "User: $(whoami)"
    echo "Host: $(hostname)"
    echo "OS: $(uname -a)"
    echo ""
    echo "## Disk Space (project dir)"
    df -h "$LOCAL_PROJECT_DIR"
    echo ""
    echo "## Docker Version"
    if command -v docker &>/dev/null; then
      docker --version
      echo ""
      echo "## Docker Resource Allocation"
      docker info --format 'CPUs: {{.NCPU}}\nMemory: {{.MemTotal}} bytes'
      echo ""
      echo "## Docker Volumes"
      docker volume ls --format '{{.Name}}'
    else
      echo "Docker not found"
    fi
    echo ""
    echo "## DISPLAY"
    echo "$DISPLAY"
    echo ""
    echo "## Environment Variables (TI-CSC relevant)"
    env | grep -Ei '^(FSL|FREESURFER|SIMNIBS|PROJECT_DIR|DEV_CODEBASE|SUBJECTS_DIR|FS_LICENSE|FSFAST|MNI|POSSUM|DISPLAY|USER|PATH|LD_LIBRARY_PATH|XAPPLRESDIR)='
    echo ""
  } > "$INFO_FILE" 2>/dev/null; then
    echo "Error: Could not write to $INFO_FILE"
    return 1
  fi

  echo "System info written to $INFO_FILE"
  return 0
}

# Function to write project status
write_project_status() {
  INFO_DIR="$LOCAL_PROJECT_DIR/.ti-csc-info"
  STATUS_FILE="$INFO_DIR/project_status.json"
  mkdir -p "$INFO_DIR"

  # Check if project is new and initialize configs
  IS_NEW_PROJECT=$(initialize_project_configs)

  # If it's not a new project, just update the last_updated timestamp
  if [ "$IS_NEW_PROJECT" = false ]; then
    if [ -f "$STATUS_FILE" ]; then
      # Update last_updated timestamp
      sed -i.tmp "s/\"last_updated\": \".*\"/\"last_updated\": \"$(date -u +"%Y-%m-%dT%H:%M:%S.%6N")\"/" "$STATUS_FILE"
      rm -f "${STATUS_FILE}.tmp"
    fi
  fi
}

# Function to initialize project configs with error handling
initialize_project_configs() {
  local project_ti_csc_dir="$LOCAL_PROJECT_DIR/ti-csc"
  local project_config_dir="$project_ti_csc_dir/config"
  local new_project_configs_dir="$SCRIPT_DIR/../../new_project/configs"
  local is_new_project=false

  # Create directories with error checking
  if [ ! -d "$project_ti_csc_dir" ]; then
    echo "Creating new project structure..."
    if ! mkdir -p "$project_config_dir" 2>/dev/null; then
      echo "Error: Could not create directory $project_config_dir"
      return 1
    fi
    is_new_project=true
  elif [ ! -d "$project_config_dir" ]; then
    echo "Creating config directory..."
    if ! mkdir -p "$project_config_dir" 2>/dev/null; then
      echo "Error: Could not create directory $project_config_dir"
      return 1
    fi
    is_new_project=true
  fi

  # If it's a new project, copy config files
  if [ "$is_new_project" = true ]; then
    echo "Initializing new project with default configs..."
    # Ensure source directory exists
    if [ ! -d "$new_project_configs_dir" ]; then
      echo "Error: Default configs directory not found at $new_project_configs_dir"
      return 1
    fi
    
    # Create .ti-csc-info directory with error checking
    local info_dir="$LOCAL_PROJECT_DIR/.ti-csc-info"
    if ! mkdir -p "$info_dir" 2>/dev/null; then
      echo "Error: Could not create directory $info_dir"
      return 1
    fi
    
    # Create initial project status file
    local status_file="$info_dir/project_status.json"
    if ! cat > "$status_file" << EOF 2>/dev/null; then
{
  "project_created": "$(date -u +"%Y-%m-%dT%H:%M:%S.%6N")",
  "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%S.%6N")",
  "config_created": true,
  "user_preferences": {
    "show_welcome": true
  },
  "project_metadata": {
    "name": "$(basename "$LOCAL_PROJECT_DIR")",
    "path": "$LOCAL_PROJECT_DIR",
    "version": "$(get_version)"
  }
}
EOF
      echo "Error: Could not create $status_file"
      return 1
    fi

    # Set proper permissions with error checking
    if ! chmod -R 755 "$info_dir" 2>/dev/null; then
      echo "Warning: Could not set permissions for $info_dir"
    fi
  fi

  echo "$is_new_project"
  return 0
}

# Main Script Execution

validate_docker_compose
display_welcome
load_default_paths
get_project_directory
get_dev_codebase_directory
PROJECT_DIR_NAME=$(basename "$LOCAL_PROJECT_DIR")
DEV_CODEBASE_DIR_NAME=$(basename "$DEV_CODEBASE_DIR")
check_docker_resources
initialize_volumes
set_display_env
allow_xhost # Allow X11 connections

# Set up Docker Compose environment variables
export LOCAL_PROJECT_DIR
export PROJECT_DIR_NAME
export DEV_CODEBASE_DIR
export DEV_CODEBASE_DIR_NAME
export DEV_CODEBASE_NAME="$DEV_CODEBASE_DIR_NAME"  # Add this line to fix the warning

# Save the paths for next time
save_default_paths

# Start browser launcher monitor EARLY (before Docker starts)
start_browser_monitor

# Write system info and project status with error handling
if ! write_system_info; then
  echo "Warning: Failed to write system info"
fi

if ! write_project_status; then
  echo "Warning: Failed to write project status"
fi

run_docker_compose