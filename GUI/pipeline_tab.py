#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TI-CSC-2.0 Visual Pipeline Builder Tab
This module provides a graphical pipeline builder interface where users can create
end-to-end workflows by connecting processing blocks visually.
"""

import os
import sys
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, QPointF, QRectF, QSizeF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem

# Import existing tab classes for execution
from pre_process_tab import PreProcessTab, PreProcessThread
from flex_search_tab import FlexSearchTab, FlexSearchThread
from ex_search_tab import ExSearchTab
from simulator_tab import SimulatorTab, SimulationThread
from analyzer_tab import AnalyzerTab, AnalysisThread

class BlockType(Enum):
    """Types of pipeline blocks."""
    INPUT = "input"
    PREPROCESSING = "preprocessing"
    OPTIMIZATION = "optimization"
    SIMULATION = "simulation"
    ANALYSIS = "analysis"
    OUTPUT = "output"

class ExecutionStatus(Enum):
    """Execution status of pipeline blocks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class BlockConfiguration:
    """Configuration for a pipeline block."""
    block_id: str
    block_type: BlockType
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    position: Tuple[float, float] = (0, 0)
    status: ExecutionStatus = ExecutionStatus.PENDING
    
class Connection:
    """Represents a connection between two blocks."""
    def __init__(self, source_id: str, target_id: str, output_port: str = "default", input_port: str = "default"):
        self.source_id = source_id
        self.target_id = target_id
        self.output_port = output_port
        self.input_port = input_port

class PipelineBlock(QtWidgets.QGraphicsItem):
    """A graphical block in the pipeline."""
    
    def __init__(self, config: BlockConfiguration, parent=None):
        super().__init__(parent)
        self.config = config
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Visual properties
        self.width = 180
        self.height = 140  # Increased height for config button
        self.port_radius = 8
        self.input_ports = []
        self.output_ports = []
        self.config_button_rect = QRectF(10, self.height - 35, self.width - 20, 25)
        
        # Block type colors
        self.colors = {
            BlockType.INPUT: QColor(100, 150, 255),
            BlockType.PREPROCESSING: QColor(255, 150, 100),
            BlockType.OPTIMIZATION: QColor(150, 255, 100),
            BlockType.SIMULATION: QColor(255, 255, 100),
            BlockType.ANALYSIS: QColor(255, 100, 150),
            BlockType.OUTPUT: QColor(150, 100, 255)
        }
        
        self._setup_ports()
    
    def _setup_ports(self):
        """Setup input and output ports based on block type."""
        if self.config.block_type == BlockType.INPUT:
            self.output_ports = ["subjects"]
        elif self.config.block_type == BlockType.PREPROCESSING:
            self.input_ports = ["subjects"]
            self.output_ports = ["processed_subjects"]
        elif self.config.block_type == BlockType.OPTIMIZATION:
            self.input_ports = ["processed_subjects"]
            self.output_ports = ["optimized_electrodes"]
        elif self.config.block_type == BlockType.SIMULATION:
            self.input_ports = ["processed_subjects", "electrodes"]
            self.output_ports = ["simulation_results"]
        elif self.config.block_type == BlockType.ANALYSIS:
            self.input_ports = ["simulation_results"]
            self.output_ports = ["analysis_results"]
        elif self.config.block_type == BlockType.OUTPUT:
            self.input_ports = ["analysis_results"]
    
    def boundingRect(self):
        """Return the bounding rectangle of the block including shadow."""
        shadow_offset = 3
        return QRectF(0, 0, self.width + shadow_offset, self.height + shadow_offset)
    
    def paint(self, painter, option, widget):
        """Paint the block."""
        # Enable antialiasing
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get color based on status
        base_color = self.colors.get(self.config.block_type, QColor(128, 128, 128))
        
        if self.config.status == ExecutionStatus.RUNNING:
            base_color = QColor(255, 165, 0)  # Orange
        elif self.config.status == ExecutionStatus.COMPLETED:
            base_color = QColor(144, 238, 144)  # Light green
        elif self.config.status == ExecutionStatus.FAILED:
            base_color = QColor(255, 99, 71)  # Tomato red
        
        # Draw block background with shadow
        shadow_offset = 3
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(QRectF(shadow_offset, shadow_offset, self.width, self.height), 10, 10)
        
        # Draw main block
        painter.setBrush(QBrush(base_color))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRoundedRect(QRectF(0, 0, self.width, self.height), 10, 10)
        
        # Draw block name
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        name_rect = QRectF(5, 5, self.width-10, 25)
        painter.drawText(name_rect, QtCore.Qt.AlignCenter | QtCore.Qt.TextWordWrap, self.config.name)
        
        # Draw block type
        painter.setFont(QFont("Arial", 8))
        type_rect = QRectF(5, 30, self.width-10, 15)
        painter.drawText(type_rect, QtCore.Qt.AlignCenter, self.config.block_type.value.upper())
        
        # Draw status
        status_text = self.config.status.value.upper()
        status_rect = QRectF(5, 50, self.width-10, 15)
        painter.drawText(status_rect, QtCore.Qt.AlignCenter, status_text)
        
        # Draw configuration button
        self._draw_config_button(painter)
        
        # Draw ports
        self._draw_ports(painter)
    
    def _draw_ports(self, painter):
        """Draw input and output ports."""
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        
        # Draw input ports on the left
        if self.input_ports:
            port_spacing = self.height / (len(self.input_ports) + 1)
            for i, port in enumerate(self.input_ports):
                y = port_spacing * (i + 1)
                painter.setBrush(QBrush(QColor(100, 150, 255)))
                port_rect = QRectF(-self.port_radius/2, y-self.port_radius/2, self.port_radius, self.port_radius)
                painter.drawEllipse(port_rect)
        
        # Draw output ports on the right
        if self.output_ports:
            port_spacing = self.height / (len(self.output_ports) + 1)
            for i, port in enumerate(self.output_ports):
                y = port_spacing * (i + 1)
                painter.setBrush(QBrush(QColor(255, 100, 100)))
                port_rect = QRectF(self.width - self.port_radius/2, y-self.port_radius/2, self.port_radius, self.port_radius)
                painter.drawEllipse(port_rect)
    
    def _draw_config_button(self, painter):
        """Draw the configuration button."""
        # Button background
        button_color = QColor(60, 120, 180) if self.config.status != ExecutionStatus.RUNNING else QColor(180, 180, 180)
        painter.setBrush(QBrush(button_color))
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        painter.drawRoundedRect(self.config_button_rect, 3, 3)
        
        # Button text
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(self.config_button_rect, QtCore.Qt.AlignCenter, "⚙ Configure")
    
    def get_input_port_pos(self, port_index: int = 0) -> QPointF:
        """Get the position of an input port."""
        if not self.input_ports:
            return QPointF(0, self.height/2)
        port_spacing = self.height / (len(self.input_ports) + 1)
        y = port_spacing * (port_index + 1)
        return self.scenePos() + QPointF(0, y)
    
    def get_output_port_pos(self, port_index: int = 0) -> QPointF:
        """Get the position of an output port."""
        if not self.output_ports:
            return QPointF(self.width, self.height/2)
        port_spacing = self.height / (len(self.output_ports) + 1)
        y = port_spacing * (port_index + 1)
        return self.scenePos() + QPointF(self.width, y)
    
    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            # Update position in config
            pos = value
            self.config.position = (pos.x(), pos.y())
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == QtCore.Qt.LeftButton:
            # Check if click is on config button
            local_pos = event.pos()
            
            if self.config_button_rect.contains(local_pos):
                print(f"✓ Configure button clicked for block: {self.config.name}")
                
                # Emit signal through the canvas
                scene = self.scene()
                if scene and scene.views():
                    canvas = scene.views()[0]
                    if hasattr(canvas, 'block_config_requested'):
                        canvas.block_config_requested.emit(self.config.block_id)
                        print(f"✓ Signal emitted for block {self.config.block_id}")
                    else:
                        print("✗ Canvas doesn't have block_config_requested signal")
                else:
                    print("✗ No scene or views found")
                
                event.accept()
                return
        
        # Default handling for other clicks (selection, movement)
        super().mousePressEvent(event)

class ConnectionLine(QtWidgets.QGraphicsItem):
    """A visual connection between two blocks."""
    
    def __init__(self, source_block: PipelineBlock, target_block: PipelineBlock, 
                 source_port: int = 0, target_port: int = 0, parent=None):
        super().__init__(parent)
        self.source_block = source_block
        self.target_block = target_block
        self.source_port = source_port
        self.target_port = target_port
        self.setZValue(-1)  # Draw behind blocks
    
    def boundingRect(self):
        """Return the bounding rectangle of the connection."""
        start = self.source_block.get_output_port_pos(self.source_port)
        end = self.target_block.get_input_port_pos(self.target_port)
        return QRectF(start, end).normalized().adjusted(-10, -10, 10, 10)
    
    def paint(self, painter, option, widget):
        """Paint the connection line."""
        start = self.source_block.get_output_port_pos(self.source_port)
        end = self.target_block.get_input_port_pos(self.target_port)
        
        # Draw curved line
        painter.setPen(QPen(QColor(50, 50, 50), 3))
        
        # Calculate control points for bezier curve
        dx = end.x() - start.x()
        ctrl1 = QPointF(start.x() + dx * 0.5, start.y())
        ctrl2 = QPointF(end.x() - dx * 0.5, end.y())
        
        # Draw bezier curve
        path = QtGui.QPainterPath(start)
        path.cubicTo(ctrl1, ctrl2, end)
        painter.drawPath(path)
        
        # Draw arrowhead
        self._draw_arrowhead(painter, ctrl2, end)
    
    def _draw_arrowhead(self, painter, start, end):
        """Draw an arrowhead at the end of the connection."""
        # Calculate arrow direction
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = (dx*dx + dy*dy) ** 0.5
        if length == 0:
            return
        
        # Normalize
        dx /= length
        dy /= length
        
        # Arrow size
        arrow_size = 10
        
        # Arrow points
        p1 = end - QPointF(arrow_size * dx + arrow_size * dy * 0.3, 
                          arrow_size * dy - arrow_size * dx * 0.3)
        p2 = end - QPointF(arrow_size * dx - arrow_size * dy * 0.3, 
                          arrow_size * dy + arrow_size * dx * 0.3)
        
        # Draw arrow
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        arrow = QtGui.QPolygonF([end, p1, p2])
        painter.drawPolygon(arrow)

class PipelineCanvas(QGraphicsView):
    """The main canvas for the pipeline builder."""
    
    connection_created = pyqtSignal(str, str)  # source_id, target_id
    block_config_requested = pyqtSignal(str)  # block_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Canvas properties
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Set up scene
        self.scene.setSceneRect(0, 0, 2000, 1000)
        self.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        
        # Add grid background
        self.draw_grid()
        
        # Set initial view
        self.centerOn(500, 300)  # Center on a reasonable area
        
        # Connection state
        self.connecting = False
        self.connection_start = None
        self.connection_start_port = None
        self.temp_line = None
        
        # Block storage
        self.blocks = {}  # block_id -> PipelineBlock
        self.connections = []  # List of ConnectionLine objects
    
    def draw_grid(self):
        """Draw a grid background on the canvas."""
        grid_size = 20
        scene_rect = self.scene.sceneRect()
        
        # Create grid lines
        pen = QPen(QColor(220, 220, 220), 1, QtCore.Qt.DotLine)
        
        # Vertical lines
        x = scene_rect.left()
        while x <= scene_rect.right():
            line = self.scene.addLine(x, scene_rect.top(), x, scene_rect.bottom(), pen)
            line.setZValue(-10)  # Behind everything
            x += grid_size
        
        # Horizontal lines
        y = scene_rect.top()
        while y <= scene_rect.bottom():
            line = self.scene.addLine(scene_rect.left(), y, scene_rect.right(), y, pen)
            line.setZValue(-10)  # Behind everything
            y += grid_size
    
    def add_block(self, config: BlockConfiguration):
        """Add a block to the canvas."""
        block = PipelineBlock(config)
        block.setPos(config.position[0], config.position[1])
        block.setZValue(1)  # Ensure blocks are above grid
        self.scene.addItem(block)
        self.blocks[config.block_id] = block
        
        # Force scene update
        self.scene.update()
        
        return block
    
    def remove_block(self, block_id: str):
        """Remove a block from the canvas."""
        if block_id in self.blocks:
            block = self.blocks[block_id]
            # Remove connections involving this block
            self.connections = [conn for conn in self.connections 
                             if conn.source_block != block and conn.target_block != block]
            self.scene.removeItem(block)
            del self.blocks[block_id]
    
    def add_connection(self, source_id: str, target_id: str, source_port: int = 0, target_port: int = 0):
        """Add a connection between two blocks."""
        if source_id in self.blocks and target_id in self.blocks:
            source_block = self.blocks[source_id]
            target_block = self.blocks[target_id]
            
            connection = ConnectionLine(source_block, target_block, source_port, target_port)
            self.scene.addItem(connection)
            self.connections.append(connection)
            return connection
        return None
    
    def clear_canvas(self):
        """Clear all blocks and connections from the canvas."""
        self.scene.clear()
        self.blocks.clear()
        self.connections.clear()
    
    def mousePressEvent(self, event):
        """Handle mouse press events for creating connections."""
        if event.button() == QtCore.Qt.LeftButton:
            # Check if we clicked on a port to start a connection
            item = self.itemAt(event.pos())
            scene_pos = self.mapToScene(event.pos())
            
            # Find if we clicked on a block and which port
            for block_id, block in self.blocks.items():
                block_rect = block.boundingRect()
                block_scene_pos = block.scenePos()
                
                # Check if click is within block bounds
                if (block_scene_pos.x() <= scene_pos.x() <= block_scene_pos.x() + block_rect.width() and
                    block_scene_pos.y() <= scene_pos.y() <= block_scene_pos.y() + block_rect.height()):
                    
                    # Check output ports (right side)
                    if block.output_ports:
                        port_spacing = block.height / (len(block.output_ports) + 1)
                        for i, port in enumerate(block.output_ports):
                            port_y = block_scene_pos.y() + port_spacing * (i + 1)
                            port_x = block_scene_pos.x() + block.width
                            
                            # Check if click is near this output port
                            if (abs(scene_pos.x() - port_x) < 15 and abs(scene_pos.y() - port_y) < 15):
                                self.start_connection(block_id, i, True)  # True = output port
                                event.accept()
                                return
                    
                    # Check input ports (left side)
                    if block.input_ports:
                        port_spacing = block.height / (len(block.input_ports) + 1)
                        for i, port in enumerate(block.input_ports):
                            port_y = block_scene_pos.y() + port_spacing * (i + 1)
                            port_x = block_scene_pos.x()
                            
                            # Check if click is near this input port
                            if (abs(scene_pos.x() - port_x) < 15 and abs(scene_pos.y() - port_y) < 15):
                                if self.connecting:
                                    self.finish_connection(block_id, i)  # Finish connection to input port
                                    event.accept()
                                    return
        
        # If we're in connection mode and clicked elsewhere, cancel
        if self.connecting and event.button() == QtCore.Qt.RightButton:
            self.cancel_connection()
            event.accept()
            return
        
        super().mousePressEvent(event)
    
    def start_connection(self, block_id: str, port_index: int, is_output: bool):
        """Start creating a connection from an output port."""
        if is_output and block_id in self.blocks:
            self.connecting = True
            self.connection_start = block_id
            self.connection_start_port = port_index
            
            # Change cursor to indicate connection mode
            self.setCursor(QtCore.Qt.CrossCursor)
            print(f"✓ Started connection from {block_id} port {port_index}")
    
    def finish_connection(self, target_block_id: str, target_port: int):
        """Finish creating a connection to an input port."""
        if self.connecting and self.connection_start and target_block_id in self.blocks:
            # Create the connection
            success = self.add_connection(self.connection_start, target_block_id, 
                                        self.connection_start_port, target_port)
            if success:
                self.connection_created.emit(self.connection_start, target_block_id)
                print(f"✓ Connected {self.connection_start} to {target_block_id}")
            else:
                print(f"✗ Failed to connect {self.connection_start} to {target_block_id}")
        
        self.cancel_connection()
    
    def cancel_connection(self):
        """Cancel the current connection operation."""
        self.connecting = False
        self.connection_start = None
        self.connection_start_port = None
        if self.temp_line:
            self.scene.removeItem(self.temp_line)
            self.temp_line = None
        
        # Reset cursor
        self.setCursor(QtCore.Qt.ArrowCursor)
        print("✓ Connection cancelled")
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for connection preview."""
        if self.connecting and self.connection_start:
            # Show preview line while connecting
            scene_pos = self.mapToScene(event.pos())
            
            if self.connection_start in self.blocks:
                start_block = self.blocks[self.connection_start]
                start_pos = start_block.get_output_port_pos(self.connection_start_port or 0)
                
                # Remove previous temp line
                if self.temp_line:
                    self.scene.removeItem(self.temp_line)
                
                # Draw temp line
                pen = QtGui.QPen(QtCore.Qt.DashLine)
                pen.setColor(QtGui.QColor(100, 100, 100))
                pen.setWidth(2)
                self.temp_line = self.scene.addLine(start_pos.x(), start_pos.y(), 
                                                  scene_pos.x(), scene_pos.y(), pen)
        
        super().mouseMoveEvent(event)
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        # Zoom in/out
        zoom_factor = 1.25
        if event.angleDelta().y() < 0:
            zoom_factor = 1 / zoom_factor
        
        self.scale(zoom_factor, zoom_factor)

class PipelineExecutor(QtCore.QObject):
    """Executes pipeline workflows."""
    
    execution_started = pyqtSignal(str)  # block_id
    execution_completed = pyqtSignal(str, bool)  # block_id, success
    execution_progress = pyqtSignal(str, str)  # block_id, message
    pipeline_completed = pyqtSignal(bool)  # success
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = False
        self.current_pipeline = None
        self.execution_thread = None
        
    def execute_pipeline(self, pipeline_config: Dict[str, Any], project_dir: str):
        """Execute a complete pipeline."""
        if self.is_running:
            return False
        
        self.is_running = True
        self.current_pipeline = pipeline_config
        
        # Start execution in separate thread
        self.execution_thread = PipelineExecutionThread(pipeline_config, project_dir)
        self.execution_thread.block_started.connect(self.execution_started)
        self.execution_thread.block_completed.connect(self.execution_completed)
        self.execution_thread.block_progress.connect(self.execution_progress)
        self.execution_thread.pipeline_finished.connect(self._on_pipeline_finished)
        self.execution_thread.start()
        
        return True
    
    def stop_execution(self):
        """Stop the current pipeline execution."""
        if self.execution_thread and self.execution_thread.isRunning():
            self.execution_thread.stop()
            self.execution_thread.wait(5000)  # Wait up to 5 seconds
        self.is_running = False
    
    def _on_pipeline_finished(self, success):
        """Handle pipeline completion."""
        self.is_running = False
        self.current_pipeline = None
        self.execution_thread = None
        self.pipeline_completed.emit(success)

class PipelineExecutionThread(QtCore.QThread):
    """Thread for executing pipeline steps."""
    
    block_started = pyqtSignal(str)
    block_completed = pyqtSignal(str, bool)
    block_progress = pyqtSignal(str, str)
    pipeline_finished = pyqtSignal(bool)
    
    def __init__(self, pipeline_config: Dict[str, Any], project_dir: str, parent=None):
        super().__init__(parent)
        self.pipeline_config = pipeline_config
        self.project_dir = project_dir
        self.should_stop = False
    
    def stop(self):
        """Stop the execution."""
        self.should_stop = True
    
    def run(self):
        """Execute the pipeline."""
        try:
            blocks = self.pipeline_config.get('blocks', {})
            connections = self.pipeline_config.get('connections', [])
            
            # Build execution order based on dependencies
            execution_order = self._build_execution_order(blocks, connections)
            
            # Execute blocks in order
            for block_id in execution_order:
                if self.should_stop:
                    break
                
                block_config = blocks[block_id]
                self.block_started.emit(block_id)
                
                success = self._execute_block(block_config)
                self.block_completed.emit(block_id, success)
                
                if not success:
                    self.pipeline_finished.emit(False)
                    return
            
            self.pipeline_finished.emit(not self.should_stop)
            
        except Exception as e:
            self.block_progress.emit("", f"Pipeline execution error: {str(e)}")
            self.pipeline_finished.emit(False)
    
    def _build_execution_order(self, blocks: Dict[str, Any], connections: List[Dict[str, Any]]) -> List[str]:
        """Build the execution order based on block dependencies."""
        # Simple topological sort
        dependencies = {block_id: [] for block_id in blocks}
        
        for conn in connections:
            source_id = conn.get('source_id')
            target_id = conn.get('target_id')
            if target_id not in dependencies[source_id]:
                dependencies[target_id].append(source_id)
        
        # Topological sort
        visited = set()
        order = []
        
        def visit(block_id):
            if block_id in visited:
                return
            visited.add(block_id)
            for dep in dependencies[block_id]:
                visit(dep)
            order.append(block_id)
        
        for block_id in blocks:
            visit(block_id)
        
        return order
    
    def _execute_block(self, block_config: Dict[str, Any]) -> bool:
        """Execute a single block."""
        try:
            block_type = block_config.get('block_type')
            block_id = block_config.get('block_id')
            parameters = block_config.get('parameters', {})
            
            self.block_progress.emit(block_id, f"Starting {block_type} execution...")
            
            if block_type == 'preprocessing':
                return self._execute_preprocessing(block_id, parameters)
            elif block_type == 'optimization':
                return self._execute_optimization(block_id, parameters)
            elif block_type == 'simulation':
                return self._execute_simulation(block_id, parameters)
            elif block_type == 'analysis':
                return self._execute_analysis(block_id, parameters)
            else:
                self.block_progress.emit(block_id, f"Unknown block type: {block_type}")
                return False
                
        except Exception as e:
            self.block_progress.emit(block_id, f"Block execution error: {str(e)}")
            return False
    
    def _execute_preprocessing(self, block_id: str, parameters: Dict[str, Any]) -> bool:
        """Execute preprocessing block."""
        # Implementation details for preprocessing execution
        self.block_progress.emit(block_id, "Running DICOM conversion and FreeSurfer...")
        # This would interface with the existing preprocessing functionality
        return True
    
    def _execute_optimization(self, block_id: str, parameters: Dict[str, Any]) -> bool:
        """Execute optimization block."""
        self.block_progress.emit(block_id, "Running electrode optimization...")
        # This would interface with the existing optimization functionality
        return True
    
    def _execute_simulation(self, block_id: str, parameters: Dict[str, Any]) -> bool:
        """Execute simulation block."""
        self.block_progress.emit(block_id, "Running simulation...")
        # This would interface with the existing simulation functionality
        return True
    
    def _execute_analysis(self, block_id: str, parameters: Dict[str, Any]) -> bool:
        """Execute analysis block."""
        self.block_progress.emit(block_id, "Running analysis...")
        # This would interface with the existing analysis functionality
        return True 

class PipelineTab(QtWidgets.QWidget):
    """Main pipeline builder tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.project_dir = self._detect_project_dir()
        
        # Pipeline state
        self.current_pipeline = {
            'blocks': {},
            'connections': [],
            'metadata': {
                'name': 'Untitled Pipeline',
                'description': '',
                'created': '',
                'modified': ''
            }
        }
        
        # Execution state
        self.executor = PipelineExecutor(self)
        self.executor.execution_started.connect(self.on_block_execution_started)
        self.executor.execution_completed.connect(self.on_block_execution_completed)
        self.executor.execution_progress.connect(self.on_execution_progress)
        self.executor.pipeline_completed.connect(self.on_pipeline_completed)
        
        # Block counter for unique IDs
        self.block_counter = 0
        
        self.setup_ui()
        
    def _detect_project_dir(self):
        """Detect the project directory."""
        project_dir = os.environ.get('PROJECT_DIR')
        if project_dir and os.path.isdir(project_dir):
            return project_dir
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QtWidgets.QHBoxLayout(self)
        
        # Left panel for block palette only
        left_panel = QtWidgets.QWidget()
        left_panel.setFixedWidth(250)
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        
        # Pipeline Type Selection
        pipeline_type_group = QtWidgets.QGroupBox("Pipeline Type")
        pipeline_type_layout = QtWidgets.QVBoxLayout(pipeline_type_group)
        
        # Pipeline type radio buttons
        self.full_pipeline_rb = QtWidgets.QRadioButton("Full Pipeline (DICOM → Analysis)")
        self.full_pipeline_rb.setChecked(True)
        self.full_pipeline_rb.toggled.connect(self.on_pipeline_type_changed)
        pipeline_type_layout.addWidget(self.full_pipeline_rb)
        
        full_desc = QtWidgets.QLabel("Complete workflow from DICOM files:\nDICOM → Pre-processing → Optimization → Simulation → Analysis")
        full_desc.setStyleSheet("color: #666; font-size: 11px; margin-left: 20px; margin-bottom: 10px;")
        full_desc.setWordWrap(True)
        pipeline_type_layout.addWidget(full_desc)
        
        self.opt_pipeline_rb = QtWidgets.QRadioButton("Optimization Pipeline (m2m → Analysis)")
        self.opt_pipeline_rb.toggled.connect(self.on_pipeline_type_changed)
        pipeline_type_layout.addWidget(self.opt_pipeline_rb)
        
        opt_desc = QtWidgets.QLabel("For preprocessed subjects with existing m2m folders:\nOptimization → Simulation → Analysis")
        opt_desc.setStyleSheet("color: #666; font-size: 11px; margin-left: 20px; margin-bottom: 10px;")
        opt_desc.setWordWrap(True)
        pipeline_type_layout.addWidget(opt_desc)
        
        left_layout.addWidget(pipeline_type_group)
        
        # Subject Selection
        subjects_group = QtWidgets.QGroupBox("Subject Selection")
        subjects_layout = QtWidgets.QVBoxLayout(subjects_group)
        
        # Auto-detect button
        detect_layout = QtWidgets.QHBoxLayout()
        self.detect_subjects_btn = QtWidgets.QPushButton("🔍 Detect Available Subjects")
        self.detect_subjects_btn.clicked.connect(self.detect_available_subjects)
        detect_layout.addWidget(self.detect_subjects_btn)
        
        refresh_btn = QtWidgets.QPushButton("🔄")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.setToolTip("Refresh subject list")
        refresh_btn.clicked.connect(self.detect_available_subjects)
        detect_layout.addWidget(refresh_btn)
        
        subjects_layout.addLayout(detect_layout)
        
        # Subject list
        self.subjects_list = QtWidgets.QListWidget()
        self.subjects_list.setMaximumHeight(150)
        self.subjects_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        subjects_layout.addWidget(self.subjects_list)
        
        # Select all/none buttons
        select_layout = QtWidgets.QHBoxLayout()
        select_all_btn = QtWidgets.QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: self.select_all_subjects(True))
        select_layout.addWidget(select_all_btn)
        
        select_none_btn = QtWidgets.QPushButton("Select None")
        select_none_btn.clicked.connect(lambda: self.select_all_subjects(False))
        select_layout.addWidget(select_none_btn)
        
        select_layout.addStretch()
        subjects_layout.addLayout(select_layout)
        
        # Subject status info
        self.subject_status_label = QtWidgets.QLabel("Select pipeline type to detect subjects")
        self.subject_status_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        self.subject_status_label.setWordWrap(True)
        subjects_layout.addWidget(self.subject_status_label)
        
        left_layout.addWidget(subjects_group)
        
        # Pipeline Configuration
        config_group = QtWidgets.QGroupBox("Pipeline Configuration")
        config_layout = QtWidgets.QVBoxLayout(config_group)
        
        # Create pipeline button
        self.create_pipeline_btn = QtWidgets.QPushButton("📋 Create Pipeline")
        self.create_pipeline_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 12px 16px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.create_pipeline_btn.clicked.connect(self.create_selected_pipeline)
        config_layout.addWidget(self.create_pipeline_btn)
        
        # Configure blocks button
        self.configure_blocks_btn = QtWidgets.QPushButton("⚙️ Configure Pipeline Blocks")
        self.configure_blocks_btn.setEnabled(False)
        self.configure_blocks_btn.clicked.connect(self.open_pipeline_configuration)
        config_layout.addWidget(self.configure_blocks_btn)
        
        left_layout.addWidget(config_group)
        
        # Pipeline controls
        controls_group = QtWidgets.QGroupBox("Pipeline Controls")
        controls_layout = QtWidgets.QVBoxLayout(controls_group)
        
        # File operations
        file_layout = QtWidgets.QHBoxLayout()
        
        new_btn = QtWidgets.QPushButton("New")
        new_btn.clicked.connect(self.new_pipeline)
        file_layout.addWidget(new_btn)
        
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.clicked.connect(self.save_pipeline)
        file_layout.addWidget(save_btn)
        
        load_btn = QtWidgets.QPushButton("Load")
        load_btn.clicked.connect(self.load_pipeline)
        file_layout.addWidget(load_btn)
        
        controls_layout.addLayout(file_layout)
        
        # Execution controls
        exec_layout = QtWidgets.QHBoxLayout()
        
        self.run_btn = QtWidgets.QPushButton("► Run Pipeline")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.run_btn.clicked.connect(self.run_pipeline)
        exec_layout.addWidget(self.run_btn)
        
        self.stop_btn = QtWidgets.QPushButton("■ Stop")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_pipeline)
        self.stop_btn.setEnabled(False)
        exec_layout.addWidget(self.stop_btn)
        
        controls_layout.addLayout(exec_layout)
        
        # Validate button
        validate_btn = QtWidgets.QPushButton("✓ Validate Pipeline")
        validate_btn.clicked.connect(self.validate_pipeline)
        controls_layout.addWidget(validate_btn)
        
        left_layout.addWidget(controls_group)
        
        # Right panel for canvas and console
        right_panel = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        
        # Canvas
        canvas_group = QtWidgets.QGroupBox("Pipeline Canvas")
        canvas_layout = QtWidgets.QVBoxLayout(canvas_group)
        
        # Canvas toolbar
        canvas_toolbar = QtWidgets.QHBoxLayout()
        
        zoom_in_btn = QtWidgets.QPushButton("Zoom In")
        zoom_in_btn.clicked.connect(self.zoom_in)
        canvas_toolbar.addWidget(zoom_in_btn)
        
        zoom_out_btn = QtWidgets.QPushButton("Zoom Out")
        zoom_out_btn.clicked.connect(self.zoom_out)
        canvas_toolbar.addWidget(zoom_out_btn)
        
        fit_btn = QtWidgets.QPushButton("Fit All")
        fit_btn.clicked.connect(self.fit_all)
        canvas_toolbar.addWidget(fit_btn)
        
        clear_btn = QtWidgets.QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_pipeline)
        canvas_toolbar.addWidget(clear_btn)
        
        canvas_toolbar.addStretch()
        canvas_layout.addLayout(canvas_toolbar)
        
        # Main canvas
        self.canvas = PipelineCanvas(self)
        self.canvas.connection_created.connect(self.on_connection_created)
        self.canvas.block_config_requested.connect(self.open_block_configuration)
        self.canvas.setMinimumSize(600, 400)
        self.canvas.show()  # Ensure canvas is visible
        canvas_layout.addWidget(self.canvas)
        
        right_layout.addWidget(canvas_group)
        
        # Console output
        console_group = QtWidgets.QGroupBox("Execution Console")
        console_layout = QtWidgets.QVBoxLayout(console_group)
        
        self.console = QtWidgets.QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(150)
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #555555;
            }
        """)
        console_layout.addWidget(self.console)
        
        # Console controls
        console_controls = QtWidgets.QHBoxLayout()
        
        clear_console_btn = QtWidgets.QPushButton("Clear")
        clear_console_btn.clicked.connect(self.clear_console)
        console_controls.addWidget(clear_console_btn)
        
        console_controls.addStretch()
        console_layout.addLayout(console_controls)
        
        right_layout.addWidget(console_group)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
        
        # Set up initial state
        self.log_message("🚀 TI-CSC Pipeline Builder Ready!")
        self.log_message("📋 QUICK START:")
        self.log_message("1️⃣ Select pipeline type (Full or Optimization)")
        self.log_message("2️⃣ Detect available subjects")
        self.log_message("3️⃣ Select subjects to process")
        self.log_message("4️⃣ Create pipeline")
        self.log_message("5️⃣ Configure blocks (optional)")
        self.log_message("6️⃣ Run pipeline")
        self.log_message("—" * 60)
        
        # Initialize with full pipeline selected
        self.on_pipeline_type_changed()
    

    def add_block(self, block_type: BlockType, name: str = None):
        """Add a new block to the pipeline."""
        self.block_counter += 1
        block_id = f"{block_type.value}_{self.block_counter}"
        
        if name is None:
            name = f"{block_type.value.title()} {self.block_counter}"
        
        # Create block configuration
        config = BlockConfiguration(
            block_id=block_id,
            block_type=block_type,
            name=name,
            position=(50 + (self.block_counter * 200) % 800, 50 + (self.block_counter // 4) * 150)
        )
        
        # Add to pipeline
        self.current_pipeline['blocks'][block_id] = {
            'block_id': block_id,
            'block_type': block_type.value,
            'name': name,
            'parameters': self._get_default_parameters(block_type),
            'position': config.position,
            'status': 'pending'
        }
        
        # Add to canvas
        self.canvas.add_block(config)
        
        self.log_message(f"Added {name} block to pipeline")
    
    def open_block_configuration(self, block_id: str):
        """Open configuration dialog for the specified block."""
        print(f"✓ open_block_configuration called for block_id: {block_id}")
        
        if block_id not in self.current_pipeline['blocks']:
            print(f"✗ Block {block_id} not found in current pipeline blocks")
            print(f"Available blocks: {list(self.current_pipeline['blocks'].keys())}")
            return
        
        block_data = self.current_pipeline['blocks'][block_id]
        block_type = block_data['block_type']
        
        print(f"✓ Opening {block_type} configuration dialog for {block_data['name']}")
        
        if block_type == 'preprocessing':
            self.open_preprocessing_dialog(block_data)
        elif block_type == 'optimization':
            self.open_optimization_dialog(block_data)
        elif block_type == 'simulation':
            self.open_simulation_dialog(block_data)
        elif block_type == 'analysis':
            self.open_analysis_dialog(block_data)
        else:
            # For input and output blocks, show a simple dialog
            self.open_generic_dialog(block_data)
    
    def _get_default_parameters(self, block_type: BlockType) -> Dict[str, Any]:
        """Get default parameters for a block type."""
        defaults = {
            BlockType.INPUT: {
                'subjects': [],
                'subject_selection': 'all'
            },
            BlockType.PREPROCESSING: {
                'convert_dicom': True,
                'run_freesurfer': True,
                'create_m2m': True,
                'create_atlas': True,
                'parallel': False,
                'quiet': False
            },
            BlockType.OPTIMIZATION: {
                'method': 'flex_search',
                'goal': 'mean',
                'postproc': 'max_TI',
                'roi_method': 'spherical',
                'roi_coords': [0, 0, 0],
                'roi_radius': 10,
                'max_iterations': 500,
                'population_size': 13,
                'electrode_radius': 10,
                'electrode_current': 2
            },
            BlockType.SIMULATION: {
                'simulation_type': 'scalar',
                'simulation_mode': 'unipolar',
                'current_ch1': 1.0,
                'current_ch2': 1.0,
                'electrode_shape': 'ellipse',
                'electrode_dimensions': '8,8',
                'electrode_thickness': 8
            },
            BlockType.ANALYSIS: {
                'analysis_space': 'mesh',
                'analysis_type': 'spherical',
                'coordinates': [0, 0, 0],
                'radius': 5,
                'generate_visualizations': True
            },
            BlockType.OUTPUT: {
                'output_format': 'nifti',
                'generate_report': True,
                'archive_results': False
            }
        }
        return defaults.get(block_type, {})
    
    def update_block_parameter(self, block_id: str, parameter: str, value: Any):
        """Update a block parameter."""
        if block_id in self.current_pipeline['blocks']:
            if parameter == 'name':
                self.current_pipeline['blocks'][block_id]['name'] = value
                # Update canvas block name
                if block_id in self.canvas.blocks:
                    self.canvas.blocks[block_id].config.name = value
                    self.canvas.blocks[block_id].update()
            else:
                self.current_pipeline['blocks'][block_id]['parameters'][parameter] = value
    
    def update_roi_coordinate(self, block_id: str, coord_index: int, value: float):
        """Update ROI coordinate."""
        if block_id in self.current_pipeline['blocks']:
            coords = self.current_pipeline['blocks'][block_id]['parameters'].get('roi_coords', [0, 0, 0])
            if coord_index < len(coords):
                coords[coord_index] = value
            else:
                coords.extend([0] * (coord_index + 1 - len(coords)))
                coords[coord_index] = value
            self.current_pipeline['blocks'][block_id]['parameters']['roi_coords'] = coords
    
    def update_analysis_coordinate(self, block_id: str, coord_index: int, value: float):
        """Update analysis coordinate."""
        if block_id in self.current_pipeline['blocks']:
            coords = self.current_pipeline['blocks'][block_id]['parameters'].get('coordinates', [0, 0, 0])
            if coord_index < len(coords):
                coords[coord_index] = value
            else:
                coords.extend([0] * (coord_index + 1 - len(coords)))
                coords[coord_index] = value
            self.current_pipeline['blocks'][block_id]['parameters']['coordinates'] = coords
    
    def on_connection_created(self, source_id: str, target_id: str):
        """Handle connection creation."""
        # Check if connection already exists
        for conn in self.current_pipeline['connections']:
            if conn['source_id'] == source_id and conn['target_id'] == target_id:
                self.log_message(f"⚠️ Connection already exists: {source_id} → {target_id}")
                return
        
        # Add connection to pipeline configuration
        connection = {
            'source_id': source_id,
            'target_id': target_id,
            'source_port': 'default',
            'target_port': 'default'
        }
        self.current_pipeline['connections'].append(connection)
        
        # Get block names for user-friendly message
        source_name = self.current_pipeline['blocks'].get(source_id, {}).get('name', source_id)
        target_name = self.current_pipeline['blocks'].get(target_id, {}).get('name', target_id)
        
        self.log_message(f"✅ Connected: {source_name} → {target_name}")
    
    def new_pipeline(self):
        """Create a new pipeline."""
        self.current_pipeline = {
            'blocks': {},
            'connections': [],
            'metadata': {
                'name': 'Untitled Pipeline',
                'description': '',
                'created': '',
                'modified': ''
            }
        }
        self.canvas.clear_canvas()
        self.block_counter = 0
        self.pipeline_name_input.setText("Untitled Pipeline")
        self.pipeline_description_input.clear()
        self.log_message("Created new pipeline")
    
    def save_pipeline(self):
        """Save the current pipeline."""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Pipeline", f"{self.project_dir}/pipelines", "JSON Files (*.json)"
        )
        
        if filename:
            try:
                # Update metadata
                self.current_pipeline['metadata']['name'] = self.pipeline_name_input.text()
                self.current_pipeline['metadata']['description'] = self.pipeline_description_input.toPlainText()
                
                # Save to file
                with open(filename, 'w') as f:
                    json.dump(self.current_pipeline, f, indent=2)
                
                self.log_message(f"Pipeline saved to {filename}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save pipeline: {str(e)}")
    
    def load_pipeline(self):
        """Load a pipeline from file."""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Pipeline", f"{self.project_dir}/pipelines", "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    pipeline_data = json.load(f)
                
                # Clear current pipeline
                self.canvas.clear_canvas()
                
                # Load pipeline data
                self.current_pipeline = pipeline_data
                
                # Update UI
                metadata = pipeline_data.get('metadata', {})
                self.pipeline_name_input.setText(metadata.get('name', 'Untitled Pipeline'))
                self.pipeline_description_input.setPlainText(metadata.get('description', ''))
                
                # Recreate blocks
                for block_id, block_data in pipeline_data.get('blocks', {}).items():
                    config = BlockConfiguration(
                        block_id=block_id,
                        block_type=BlockType(block_data['block_type']),
                        name=block_data['name'],
                        parameters=block_data.get('parameters', {}),
                        position=block_data.get('position', (0, 0)),
                        status=ExecutionStatus(block_data.get('status', 'pending'))
                    )
                    self.canvas.add_block(config)
                
                # Recreate connections
                for conn in pipeline_data.get('connections', []):
                    self.canvas.add_connection(conn['source_id'], conn['target_id'])
                
                # Update block counter
                self.block_counter = len(pipeline_data.get('blocks', {}))
                
                self.log_message(f"Pipeline loaded from {filename}")
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load pipeline: {str(e)}")
    
    def validate_pipeline(self):
        """Validate the current pipeline."""
        issues = []
        
        # Check for blocks
        if not self.current_pipeline['blocks']:
            issues.append("Pipeline has no blocks")
        
        # Check for input block
        has_input = any(block['block_type'] == 'input' for block in self.current_pipeline['blocks'].values())
        if not has_input:
            issues.append("Pipeline needs an input block")
        
        # Check for connectivity
        blocks = self.current_pipeline['blocks']
        connections = self.current_pipeline['connections']
        
        # Build dependency graph
        dependencies = {block_id: [] for block_id in blocks}
        for conn in connections:
            if conn['target_id'] in dependencies:
                dependencies[conn['target_id']].append(conn['source_id'])
        
        # Check for disconnected blocks (except input blocks)
        for block_id, block_data in blocks.items():
            if block_data['block_type'] != 'input' and not dependencies[block_id]:
                issues.append(f"Block '{block_data['name']}' has no inputs")
        
        # Check for cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in [conn['target_id'] for conn in connections if conn['source_id'] == node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for block_id in blocks:
            if block_id not in visited:
                if has_cycle(block_id):
                    issues.append("Pipeline contains cycles")
                    break
        
        # Show validation results
        if issues:
            message = "Pipeline validation failed:\n\n" + "\n".join(f"• {issue}" for issue in issues)
            QtWidgets.QMessageBox.warning(self, "Validation Issues", message)
            self.log_message("Pipeline validation failed")
        else:
            QtWidgets.QMessageBox.information(self, "Validation", "Pipeline is valid!")
            self.log_message("Pipeline validation passed")
    
    def run_pipeline(self):
        """Run the current pipeline."""
        # Validate first
        self.validate_pipeline()
        
        # Check if already running
        if self.executor.is_running:
            QtWidgets.QMessageBox.warning(self, "Warning", "Pipeline is already running")
            return
        
        # Update UI
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Start execution
        success = self.executor.execute_pipeline(self.current_pipeline, self.project_dir)
        
        if success:
            self.log_message("Pipeline execution started")
        else:
            self.log_message("Failed to start pipeline execution")
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def stop_pipeline(self):
        """Stop the current pipeline execution."""
        self.executor.stop_execution()
        self.log_message("Pipeline execution stopped")
        
        # Update UI
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def on_block_execution_started(self, block_id: str):
        """Handle block execution start."""
        if block_id in self.current_pipeline['blocks']:
            self.current_pipeline['blocks'][block_id]['status'] = 'running'
            if block_id in self.canvas.blocks:
                self.canvas.blocks[block_id].config.status = ExecutionStatus.RUNNING
                self.canvas.blocks[block_id].update()
        
        block_name = self.current_pipeline['blocks'].get(block_id, {}).get('name', block_id)
        self.log_message(f"Started executing: {block_name}")
    
    def on_block_execution_completed(self, block_id: str, success: bool):
        """Handle block execution completion."""
        if block_id in self.current_pipeline['blocks']:
            status = 'completed' if success else 'failed'
            self.current_pipeline['blocks'][block_id]['status'] = status
            
            if block_id in self.canvas.blocks:
                canvas_status = ExecutionStatus.COMPLETED if success else ExecutionStatus.FAILED
                self.canvas.blocks[block_id].config.status = canvas_status
                self.canvas.blocks[block_id].update()
        
        block_name = self.current_pipeline['blocks'].get(block_id, {}).get('name', block_id)
        status_text = "completed" if success else "failed"
        self.log_message(f"Block {block_name} {status_text}")
    
    def on_execution_progress(self, block_id: str, message: str):
        """Handle execution progress updates."""
        if block_id:
            block_name = self.current_pipeline['blocks'].get(block_id, {}).get('name', block_id)
            self.log_message(f"[{block_name}] {message}")
        else:
            self.log_message(message)
    
    def on_pipeline_completed(self, success: bool):
        """Handle pipeline completion."""
        # Update UI
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        status_text = "completed successfully" if success else "failed"
        self.log_message(f"Pipeline execution {status_text}")
        
        if success:
            QtWidgets.QMessageBox.information(self, "Success", "Pipeline completed successfully!")
        else:
            QtWidgets.QMessageBox.warning(self, "Warning", "Pipeline execution failed. Check the console for details.")
    
    def zoom_in(self):
        """Zoom in on the canvas."""
        self.canvas.scale(1.25, 1.25)
    
    def zoom_out(self):
        """Zoom out on the canvas."""
        self.canvas.scale(0.8, 0.8)
    
    def fit_all(self):
        """Fit all blocks in the view."""
        if self.canvas.blocks:
            self.canvas.fitInView(self.canvas.scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
        else:
            # If no blocks, show the main area
            self.canvas.fitInView(0, 0, 1000, 500, QtCore.Qt.KeepAspectRatio)
        self.log_message("Canvas view fitted to content")
    
    def clear_pipeline(self):
        """Clear the current pipeline."""
        reply = QtWidgets.QMessageBox.question(
            self, "Clear Pipeline", "Are you sure you want to clear the entire pipeline?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.new_pipeline()
    
    def clear_console(self):
        """Clear the console output."""
        self.console.clear()
    
    def log_message(self, message: str):
        """Log a message to the console."""
        timestamp = QtCore.QDateTime.currentDateTime().toString("hh:mm:ss")
        self.console.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def open_preprocessing_dialog(self, block_data: Dict[str, Any]):
        """Open preprocessing settings dialog - full interface like preprocessing tab."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Preprocessing Configuration - {block_data['name']}")
        dialog.setMinimumSize(600, 500)
        dialog.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Title and description
        title_label = QtWidgets.QLabel("Pre-processing Pipeline Configuration")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        description_label = QtWidgets.QLabel(
            "Convert DICOM files to NIfTI format, run FreeSurfer reconstruction, "
            "and create SimNIBS m2m folders for selected subjects."
        )
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        layout.addSpacing(10)
        
        # Create scroll area for main content
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        
        parameters = block_data.get('parameters', {})
        
        # Subject Selection Section
        subjects_group = QtWidgets.QGroupBox("Subject Selection")
        subjects_layout = QtWidgets.QVBoxLayout(subjects_group)
        
        # Subject processing mode
        all_subjects_rb = QtWidgets.QRadioButton("Process all available subjects")
        all_subjects_rb.setChecked(True)
        subjects_layout.addWidget(all_subjects_rb)
        
        specific_subjects_rb = QtWidgets.QRadioButton("Process specific subjects")
        subjects_layout.addWidget(specific_subjects_rb)
        
        # Subject list (would be populated based on available subjects)
        subject_list_label = QtWidgets.QLabel("Available subjects will be automatically detected from sourcedata/")
        subject_list_label.setStyleSheet("color: #666; font-style: italic; margin-left: 20px;")
        subjects_layout.addWidget(subject_list_label)
        
        scroll_layout.addWidget(subjects_group)
        
        # Processing Options Section
        processing_group = QtWidgets.QGroupBox("Processing Options")
        processing_layout = QtWidgets.QVBoxLayout(processing_group)
        
        # DICOM conversion
        dicom_cb = QtWidgets.QCheckBox("Convert DICOM files to NIfTI (auto-detects T1w/T2w)")
        dicom_cb.setChecked(parameters.get('convert_dicom', True))
        dicom_cb.setToolTip("Automatically converts DICOM files to NIfTI format and organizes them in BIDS structure")
        processing_layout.addWidget(dicom_cb)
        
        # FreeSurfer reconstruction
        fs_cb = QtWidgets.QCheckBox("Run FreeSurfer recon-all")
        fs_cb.setChecked(parameters.get('run_freesurfer', True))
        fs_cb.setToolTip("Runs complete FreeSurfer cortical reconstruction including surface generation")
        processing_layout.addWidget(fs_cb)
        
        # Parallel FreeSurfer
        parallel_cb = QtWidgets.QCheckBox("Run FreeSurfer reconstruction in parallel")
        parallel_cb.setChecked(parameters.get('parallel', False))
        parallel_cb.setToolTip("Uses parallel processing to speed up FreeSurfer reconstruction")
        processing_layout.addWidget(parallel_cb)
        
        # SimNIBS m2m folder creation
        m2m_cb = QtWidgets.QCheckBox("Create SimNIBS m2m folder")
        m2m_cb.setChecked(parameters.get('create_m2m', True))
        m2m_cb.setToolTip("Creates SimNIBS mesh-to-mesh folder for electromagnetic simulations")
        processing_layout.addWidget(m2m_cb)
        
        # Atlas segmentation
        atlas_cb = QtWidgets.QCheckBox("Create atlas segmentation (requires m2m folder)")
        atlas_cb.setChecked(parameters.get('create_atlas', True))
        atlas_cb.setToolTip("Creates cortical and subcortical atlas segmentations for ROI analysis")
        processing_layout.addWidget(atlas_cb)
        
        # Quiet mode
        quiet_cb = QtWidgets.QCheckBox("Run in quiet mode")
        quiet_cb.setChecked(parameters.get('quiet', False))
        quiet_cb.setToolTip("Reduces console output during processing")
        processing_layout.addWidget(quiet_cb)
        
        scroll_layout.addWidget(processing_group)
        
        # Resource Management Section
        resource_group = QtWidgets.QGroupBox("Resource Management")
        resource_layout = QtWidgets.QFormLayout(resource_group)
        
        # CPU cores for parallel processing
        cpu_spin = QtWidgets.QSpinBox()
        cpu_spin.setRange(1, os.cpu_count() or 8)
        cpu_spin.setValue(parameters.get('cpu_cores', 1))
        cpu_spin.setToolTip("Number of CPU cores to use for parallel processing")
        resource_layout.addRow("CPU Cores:", cpu_spin)
        
        # Memory considerations info
        memory_info = QtWidgets.QLabel("Note: FreeSurfer reconstruction requires ~4-8GB RAM per subject")
        memory_info.setStyleSheet("color: #666; font-style: italic;")
        resource_layout.addRow("Memory:", memory_info)
        
        scroll_layout.addWidget(resource_group)
        
        # Advanced Options Section
        advanced_group = QtWidgets.QGroupBox("Advanced Options")
        advanced_layout = QtWidgets.QVBoxLayout(advanced_group)
        
        # Skip existing outputs
        skip_existing_cb = QtWidgets.QCheckBox("Skip subjects with existing outputs")
        skip_existing_cb.setChecked(parameters.get('skip_existing', True))
        skip_existing_cb.setToolTip("Skip processing for subjects that already have completed outputs")
        advanced_layout.addWidget(skip_existing_cb)
        
        # Force reprocessing
        force_cb = QtWidgets.QCheckBox("Force reprocessing (overwrite existing)")
        force_cb.setChecked(parameters.get('force_reprocess', False))
        force_cb.setToolTip("Force reprocessing even if outputs already exist")
        advanced_layout.addWidget(force_cb)
        
        scroll_layout.addWidget(advanced_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Button section
        button_layout = QtWidgets.QHBoxLayout()
        
        # Test button to validate settings
        test_btn = QtWidgets.QPushButton("Test Configuration")
        test_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 8px 16px; border: none; border-radius: 4px; }")
        test_btn.setToolTip("Test the configuration without running full processing")
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        # Save button
        save_btn = QtWidgets.QPushButton("Save Configuration")
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; font-weight: bold; }")
        save_btn.clicked.connect(lambda: self.save_preprocessing_settings(
            block_data['block_id'], dicom_cb.isChecked(), fs_cb.isChecked(), 
            parallel_cb.isChecked(), m2m_cb.isChecked(), atlas_cb.isChecked(), 
            quiet_cb.isChecked(), cpu_spin.value(), skip_existing_cb.isChecked(),
            force_cb.isChecked(), dialog
        ))
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def save_preprocessing_settings(self, block_id, convert_dicom, run_freesurfer, 
                                  parallel, create_m2m, create_atlas, quiet, cpu_cores, 
                                  skip_existing, force_reprocess, dialog):
        """Save preprocessing settings."""
        if block_id in self.current_pipeline['blocks']:
            params = self.current_pipeline['blocks'][block_id]['parameters']
            params.update({
                'convert_dicom': convert_dicom,
                'run_freesurfer': run_freesurfer,
                'parallel': parallel,
                'create_m2m': create_m2m,
                'create_atlas': create_atlas,
                'quiet': quiet,
                'cpu_cores': cpu_cores,
                'skip_existing': skip_existing,
                'force_reprocess': force_reprocess
            })
            self.log_message(f"Updated preprocessing configuration for {self.current_pipeline['blocks'][block_id]['name']}")
        dialog.accept()
    
    def open_optimization_dialog(self, block_data: Dict[str, Any]):
        """Open optimization settings dialog with interface similar to flex_search_tab."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Optimization Settings - {block_data['name']}")
        dialog.setMinimumSize(600, 500)
        dialog.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Create tabs for different optimization methods
        tab_widget = QtWidgets.QTabWidget()
        
        # Flex Search Tab
        flex_tab = QtWidgets.QWidget()
        flex_layout = QtWidgets.QVBoxLayout(flex_tab)
        
        parameters = block_data.get('parameters', {})
        
        # Basic Parameters
        basic_group = QtWidgets.QGroupBox("Basic Parameters")
        basic_layout = QtWidgets.QFormLayout(basic_group)
        
        # Goal
        goal_combo = QtWidgets.QComboBox()
        goal_combo.addItems(["mean", "max", "focality"])
        goal_combo.setCurrentText(parameters.get('goal', 'mean'))
        basic_layout.addRow("Optimization Goal:", goal_combo)
        
        # Post-processing
        postproc_combo = QtWidgets.QComboBox()
        postproc_combo.addItems(["max_TI", "dir_TI_normal", "dir_TI_tangential"])
        postproc_combo.setCurrentText(parameters.get('postproc', 'max_TI'))
        basic_layout.addRow("Post-processing Method:", postproc_combo)
        
        flex_layout.addWidget(basic_group)
        
        # ROI Definition
        roi_group = QtWidgets.QGroupBox("ROI Definition")
        roi_layout = QtWidgets.QVBoxLayout(roi_group)
        
        # ROI method selection
        roi_method_layout = QtWidgets.QHBoxLayout()
        spherical_rb = QtWidgets.QRadioButton("Spherical (coordinates and radius)")
        cortical_rb = QtWidgets.QRadioButton("Cortical (atlas-based)")
        subcortical_rb = QtWidgets.QRadioButton("Subcortical (volume)")
        spherical_rb.setChecked(True)
        
        roi_method_layout.addWidget(spherical_rb)
        roi_method_layout.addWidget(cortical_rb)
        roi_method_layout.addWidget(subcortical_rb)
        roi_layout.addLayout(roi_method_layout)
        
        # ROI coordinates
        coord_layout = QtWidgets.QFormLayout()
        coords = parameters.get('roi_coords', [0, 0, 0])
        
        coord_widget = QtWidgets.QWidget()
        coord_widget_layout = QtWidgets.QHBoxLayout(coord_widget)
        
        x_spin = QtWidgets.QDoubleSpinBox()
        x_spin.setRange(-200, 200)
        x_spin.setValue(coords[0] if len(coords) > 0 else 0)
        
        y_spin = QtWidgets.QDoubleSpinBox()
        y_spin.setRange(-200, 200)
        y_spin.setValue(coords[1] if len(coords) > 1 else 0)
        
        z_spin = QtWidgets.QDoubleSpinBox()
        z_spin.setRange(-200, 200)
        z_spin.setValue(coords[2] if len(coords) > 2 else 0)
        
        coord_widget_layout.addWidget(QtWidgets.QLabel("X:"))
        coord_widget_layout.addWidget(x_spin)
        coord_widget_layout.addWidget(QtWidgets.QLabel("Y:"))
        coord_widget_layout.addWidget(y_spin)
        coord_widget_layout.addWidget(QtWidgets.QLabel("Z:"))
        coord_widget_layout.addWidget(z_spin)
        
        coord_layout.addRow("ROI Center (RAS):", coord_widget)
        
        radius_spin = QtWidgets.QDoubleSpinBox()
        radius_spin.setRange(1, 50)
        radius_spin.setValue(parameters.get('roi_radius', 10))
        coord_layout.addRow("ROI Radius (mm):", radius_spin)
        
        roi_layout.addLayout(coord_layout)
        flex_layout.addWidget(roi_group)
        
        # Electrode Parameters
        electrode_group = QtWidgets.QGroupBox("Electrode Parameters")
        electrode_layout = QtWidgets.QFormLayout(electrode_group)
        
        elec_radius_spin = QtWidgets.QDoubleSpinBox()
        elec_radius_spin.setRange(1, 30)
        elec_radius_spin.setValue(parameters.get('electrode_radius', 10))
        electrode_layout.addRow("Electrode Radius (mm):", elec_radius_spin)
        
        elec_current_spin = QtWidgets.QDoubleSpinBox()
        elec_current_spin.setRange(0.1, 100)
        elec_current_spin.setValue(parameters.get('electrode_current', 2))
        electrode_layout.addRow("Electrode Current (mA):", elec_current_spin)
        
        flex_layout.addWidget(electrode_group)
        
        # Optimization Parameters
        opt_group = QtWidgets.QGroupBox("Optimization Parameters")
        opt_layout = QtWidgets.QFormLayout(opt_group)
        
        iter_spin = QtWidgets.QSpinBox()
        iter_spin.setRange(50, 2000)
        iter_spin.setValue(parameters.get('max_iterations', 500))
        opt_layout.addRow("Max Iterations:", iter_spin)
        
        pop_spin = QtWidgets.QSpinBox()
        pop_spin.setRange(4, 100)
        pop_spin.setValue(parameters.get('population_size', 13))
        opt_layout.addRow("Population Size:", pop_spin)
        
        cpu_spin = QtWidgets.QSpinBox()
        cpu_spin.setRange(1, os.cpu_count() or 16)
        cpu_spin.setValue(parameters.get('cpus', 1))
        opt_layout.addRow("Number of CPUs:", cpu_spin)
        
        flex_layout.addWidget(opt_group)
        
        tab_widget.addTab(flex_tab, "Flex Search")
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        save_btn = QtWidgets.QPushButton("Save Settings")
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; font-weight: bold; }")
        save_btn.clicked.connect(lambda: self.save_optimization_settings(
            block_data['block_id'], goal_combo.currentText(), postproc_combo.currentText(),
            [x_spin.value(), y_spin.value(), z_spin.value()], radius_spin.value(),
            elec_radius_spin.value(), elec_current_spin.value(), iter_spin.value(),
            pop_spin.value(), cpu_spin.value(), dialog
        ))
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def save_optimization_settings(self, block_id, goal, postproc, roi_coords, roi_radius,
                                 electrode_radius, electrode_current, max_iterations, 
                                 population_size, cpus, dialog):
        """Save optimization settings."""
        if block_id in self.current_pipeline['blocks']:
            params = self.current_pipeline['blocks'][block_id]['parameters']
            params.update({
                'goal': goal,
                'postproc': postproc,
                'roi_coords': roi_coords,
                'roi_radius': roi_radius,
                'electrode_radius': electrode_radius,
                'electrode_current': electrode_current,
                'max_iterations': max_iterations,
                'population_size': population_size,
                'cpus': cpus
            })
            self.log_message(f"Updated optimization settings for {self.current_pipeline['blocks'][block_id]['name']}")
        dialog.accept()
    
    def open_simulation_dialog(self, block_data: Dict[str, Any]):
        """Open simulation settings dialog."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Simulation Settings - {block_data['name']}")
        dialog.setMinimumSize(500, 400)
        dialog.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        parameters = block_data.get('parameters', {})
        
        # Simulation Configuration
        config_group = QtWidgets.QGroupBox("Simulation Configuration")
        config_layout = QtWidgets.QFormLayout(config_group)
        
        # Simulation type
        sim_type_combo = QtWidgets.QComboBox()
        sim_type_combo.addItems(["scalar", "vn", "dir", "mc"])
        sim_type_combo.setCurrentText(parameters.get('simulation_type', 'scalar'))
        config_layout.addRow("Simulation Type:", sim_type_combo)
        
        # Simulation mode
        mode_layout = QtWidgets.QHBoxLayout()
        unipolar_rb = QtWidgets.QRadioButton("Unipolar")
        multipolar_rb = QtWidgets.QRadioButton("Multipolar")
        unipolar_rb.setChecked(parameters.get('simulation_mode', 'unipolar') == 'unipolar')
        multipolar_rb.setChecked(parameters.get('simulation_mode', 'unipolar') == 'multipolar')
        mode_layout.addWidget(unipolar_rb)
        mode_layout.addWidget(multipolar_rb)
        config_layout.addRow("Mode:", mode_layout)
        
        layout.addWidget(config_group)
        
        # Electrode Parameters
        electrode_group = QtWidgets.QGroupBox("Electrode Parameters")
        electrode_layout = QtWidgets.QFormLayout(electrode_group)
        
        # Current values
        current1_spin = QtWidgets.QDoubleSpinBox()
        current1_spin.setRange(0.1, 100)
        current1_spin.setValue(parameters.get('current_ch1', 1.0))
        electrode_layout.addRow("Current Ch1 (mA):", current1_spin)
        
        current2_spin = QtWidgets.QDoubleSpinBox()
        current2_spin.setRange(0.1, 100)
        current2_spin.setValue(parameters.get('current_ch2', 1.0))
        electrode_layout.addRow("Current Ch2 (mA):", current2_spin)
        
        # Electrode shape
        shape_layout = QtWidgets.QHBoxLayout()
        rect_rb = QtWidgets.QRadioButton("Rectangle")
        ellipse_rb = QtWidgets.QRadioButton("Ellipse")
        ellipse_rb.setChecked(parameters.get('electrode_shape', 'ellipse') == 'ellipse')
        rect_rb.setChecked(parameters.get('electrode_shape', 'ellipse') == 'rectangle')
        shape_layout.addWidget(rect_rb)
        shape_layout.addWidget(ellipse_rb)
        electrode_layout.addRow("Shape:", shape_layout)
        
        # Dimensions
        dim_input = QtWidgets.QLineEdit()
        dim_input.setText(parameters.get('electrode_dimensions', '8,8'))
        electrode_layout.addRow("Dimensions (mm, x,y):", dim_input)
        
        # Thickness
        thickness_spin = QtWidgets.QDoubleSpinBox()
        thickness_spin.setRange(1, 20)
        thickness_spin.setValue(parameters.get('electrode_thickness', 8))
        electrode_layout.addRow("Thickness (mm):", thickness_spin)
        
        layout.addWidget(electrode_group)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        save_btn = QtWidgets.QPushButton("Save Settings")
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; font-weight: bold; }")
        save_btn.clicked.connect(lambda: self.save_simulation_settings(
            block_data['block_id'], sim_type_combo.currentText(),
            'unipolar' if unipolar_rb.isChecked() else 'multipolar',
            current1_spin.value(), current2_spin.value(),
            'ellipse' if ellipse_rb.isChecked() else 'rectangle',
            dim_input.text(), thickness_spin.value(), dialog
        ))
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def save_simulation_settings(self, block_id, sim_type, sim_mode, current1, current2,
                               shape, dimensions, thickness, dialog):
        """Save simulation settings."""
        if block_id in self.current_pipeline['blocks']:
            params = self.current_pipeline['blocks'][block_id]['parameters']
            params.update({
                'simulation_type': sim_type,
                'simulation_mode': sim_mode,
                'current_ch1': current1,
                'current_ch2': current2,
                'electrode_shape': shape,
                'electrode_dimensions': dimensions,
                'electrode_thickness': thickness
            })
            self.log_message(f"Updated simulation settings for {self.current_pipeline['blocks'][block_id]['name']}")
        dialog.accept()
    
    def open_analysis_dialog(self, block_data: Dict[str, Any]):
        """Open analysis settings dialog."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Analysis Settings - {block_data['name']}")
        dialog.setMinimumSize(500, 400)
        dialog.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        parameters = block_data.get('parameters', {})
        
        # Analysis Configuration
        config_group = QtWidgets.QGroupBox("Analysis Configuration")
        config_layout = QtWidgets.QFormLayout(config_group)
        
        # Analysis space
        space_layout = QtWidgets.QHBoxLayout()
        mesh_rb = QtWidgets.QRadioButton("Mesh")
        voxel_rb = QtWidgets.QRadioButton("Voxel")
        mesh_rb.setChecked(parameters.get('analysis_space', 'mesh') == 'mesh')
        voxel_rb.setChecked(parameters.get('analysis_space', 'mesh') == 'voxel')
        space_layout.addWidget(mesh_rb)
        space_layout.addWidget(voxel_rb)
        config_layout.addRow("Analysis Space:", space_layout)
        
        # Analysis type
        type_layout = QtWidgets.QHBoxLayout()
        spherical_rb = QtWidgets.QRadioButton("Spherical")
        cortical_rb = QtWidgets.QRadioButton("Cortical")
        spherical_rb.setChecked(parameters.get('analysis_type', 'spherical') == 'spherical')
        cortical_rb.setChecked(parameters.get('analysis_type', 'spherical') == 'cortical')
        type_layout.addWidget(spherical_rb)
        type_layout.addWidget(cortical_rb)
        config_layout.addRow("Analysis Type:", type_layout)
        
        layout.addWidget(config_group)
        
        # ROI Definition
        roi_group = QtWidgets.QGroupBox("ROI Definition")
        roi_layout = QtWidgets.QFormLayout(roi_group)
        
        # Coordinates
        coords = parameters.get('coordinates', [0, 0, 0])
        coord_widget = QtWidgets.QWidget()
        coord_layout = QtWidgets.QHBoxLayout(coord_widget)
        
        x_spin = QtWidgets.QDoubleSpinBox()
        x_spin.setRange(-200, 200)
        x_spin.setValue(coords[0] if len(coords) > 0 else 0)
        
        y_spin = QtWidgets.QDoubleSpinBox()
        y_spin.setRange(-200, 200)
        y_spin.setValue(coords[1] if len(coords) > 1 else 0)
        
        z_spin = QtWidgets.QDoubleSpinBox()
        z_spin.setRange(-200, 200)
        z_spin.setValue(coords[2] if len(coords) > 2 else 0)
        
        coord_layout.addWidget(QtWidgets.QLabel("X:"))
        coord_layout.addWidget(x_spin)
        coord_layout.addWidget(QtWidgets.QLabel("Y:"))
        coord_layout.addWidget(y_spin)
        coord_layout.addWidget(QtWidgets.QLabel("Z:"))
        coord_layout.addWidget(z_spin)
        
        roi_layout.addRow("Coordinates (RAS):", coord_widget)
        
        # Radius
        radius_spin = QtWidgets.QDoubleSpinBox()
        radius_spin.setRange(1, 50)
        radius_spin.setValue(parameters.get('radius', 5))
        roi_layout.addRow("Radius (mm):", radius_spin)
        
        layout.addWidget(roi_group)
        
        # Visualization Options
        viz_group = QtWidgets.QGroupBox("Visualization")
        viz_layout = QtWidgets.QVBoxLayout(viz_group)
        
        viz_cb = QtWidgets.QCheckBox("Generate visualizations")
        viz_cb.setChecked(parameters.get('generate_visualizations', True))
        viz_layout.addWidget(viz_cb)
        
        layout.addWidget(viz_group)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        save_btn = QtWidgets.QPushButton("Save Settings")
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; font-weight: bold; }")
        save_btn.clicked.connect(lambda: self.save_analysis_settings(
            block_data['block_id'], 'mesh' if mesh_rb.isChecked() else 'voxel',
            'spherical' if spherical_rb.isChecked() else 'cortical',
            [x_spin.value(), y_spin.value(), z_spin.value()],
            radius_spin.value(), viz_cb.isChecked(), dialog
        ))
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def save_analysis_settings(self, block_id, analysis_space, analysis_type, coordinates,
                             radius, generate_viz, dialog):
        """Save analysis settings."""
        if block_id in self.current_pipeline['blocks']:
            params = self.current_pipeline['blocks'][block_id]['parameters']
            params.update({
                'analysis_space': analysis_space,
                'analysis_type': analysis_type,
                'coordinates': coordinates,
                'radius': radius,
                'generate_visualizations': generate_viz
            })
            self.log_message(f"Updated analysis settings for {self.current_pipeline['blocks'][block_id]['name']}")
        dialog.accept()
    
    def open_generic_dialog(self, block_data: Dict[str, Any]):
        """Open a settings dialog for input/output blocks."""
        block_type = block_data['block_type']
        
        if block_type == 'input':
            self.open_input_dialog(block_data)
        else:
            self.open_output_dialog(block_data)
    
    def open_input_dialog(self, block_data: Dict[str, Any]):
        """Open subject input configuration dialog."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Subject Input - {block_data['name']}")
        dialog.setMinimumSize(600, 500)
        dialog.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Title
        title_label = QtWidgets.QLabel("Subject Input Configuration")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        
        # Create scroll area for content
        scroll_area = QtWidgets.QScrollArea()
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        
        # Project directory section
        project_group = QtWidgets.QGroupBox("Project Directory")
        project_layout = QtWidgets.QVBoxLayout(project_group)
        
        # Current project directory
        self.project_dir_label = QtWidgets.QLabel(f"Current: {self.project_dir}")
        self.project_dir_label.setStyleSheet("font-family: monospace; background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
        project_layout.addWidget(self.project_dir_label)
        
        # Change project directory button
        change_dir_btn = QtWidgets.QPushButton("Change Project Directory")
        change_dir_btn.clicked.connect(lambda: self.change_project_directory(dialog))
        project_layout.addWidget(change_dir_btn)
        
        scroll_layout.addWidget(project_group)
        
        # Subject selection section
        subjects_group = QtWidgets.QGroupBox("Subject Selection")
        subjects_layout = QtWidgets.QVBoxLayout(subjects_group)
        
        # Auto-detect subjects
        detect_layout = QtWidgets.QHBoxLayout()
        detect_btn = QtWidgets.QPushButton("🔍 Detect Subjects")
        detect_btn.clicked.connect(lambda: self.detect_subjects(subjects_list))
        detect_layout.addWidget(detect_btn)
        
        refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(lambda: self.detect_subjects(subjects_list))
        detect_layout.addWidget(refresh_btn)
        
        detect_layout.addStretch()
        subjects_layout.addLayout(detect_layout)
        
        # Subject list with checkboxes
        subjects_list = QtWidgets.QListWidget()
        subjects_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        subjects_list.setMaximumHeight(200)
        subjects_layout.addWidget(subjects_list)
        
        # Select all/none buttons
        select_layout = QtWidgets.QHBoxLayout()
        select_all_btn = QtWidgets.QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: self.select_all_subjects(subjects_list, True))
        select_layout.addWidget(select_all_btn)
        
        select_none_btn = QtWidgets.QPushButton("Select None")
        select_none_btn.clicked.connect(lambda: self.select_all_subjects(subjects_list, False))
        select_layout.addWidget(select_none_btn)
        
        select_layout.addStretch()
        subjects_layout.addLayout(select_layout)
        
        # Manual subject entry
        manual_layout = QtWidgets.QVBoxLayout()
        manual_layout.addWidget(QtWidgets.QLabel("Or enter subject IDs manually (one per line):"))
        
        manual_subjects = QtWidgets.QTextEdit()
        manual_subjects.setMaximumHeight(100)
        manual_subjects.setPlaceholderText("subject_001\nsubject_002\nsubject_003")
        manual_layout.addWidget(manual_subjects)
        
        subjects_layout.addLayout(manual_layout)
        scroll_layout.addWidget(subjects_group)
        
        # Data format section
        format_group = QtWidgets.QGroupBox("Data Format")
        format_layout = QtWidgets.QFormLayout(format_group)
        
        # Input data type
        data_type_combo = QtWidgets.QComboBox()
        data_type_combo.addItems(["DICOM", "NIfTI", "Both"])
        parameters = block_data.get('parameters', {})
        data_type_combo.setCurrentText(parameters.get('data_type', 'DICOM'))
        format_layout.addRow("Input Data Type:", data_type_combo)
        
        # Expected directory structure info
        structure_info = QtWidgets.QLabel(
            "Expected structure:\n"
            "• DICOM: PROJECT_DIR/subject_id/DICOM/\n"
            "• NIfTI: PROJECT_DIR/subject_id/T1_images/\n"
            "• Both: Both directories present"
        )
        structure_info.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        format_layout.addRow("Directory Structure:", structure_info)
        
        scroll_layout.addWidget(format_group)
        
        # Validation section
        validation_group = QtWidgets.QGroupBox("Validation")
        validation_layout = QtWidgets.QVBoxLayout(validation_group)
        
        validate_btn = QtWidgets.QPushButton("🔍 Validate Selected Subjects")
        validate_btn.clicked.connect(lambda: self.validate_subjects(subjects_list, manual_subjects, data_type_combo.currentText()))
        validation_layout.addWidget(validate_btn)
        
        self.validation_result = QtWidgets.QLabel("Click 'Validate' to check subject data availability")
        self.validation_result.setStyleSheet("padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9;")
        self.validation_result.setWordWrap(True)
        validation_layout.addWidget(self.validation_result)
        
        scroll_layout.addWidget(validation_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Button section
        button_layout = QtWidgets.QHBoxLayout()
        
        # Test button
        test_btn = QtWidgets.QPushButton("Test Configuration")
        test_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 8px 16px; border: none; border-radius: 4px; }")
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        # Save button
        save_btn = QtWidgets.QPushButton("Save Configuration")
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; font-weight: bold; }")
        save_btn.clicked.connect(lambda: self.save_input_settings(
            block_data['block_id'], subjects_list, manual_subjects, 
            data_type_combo.currentText(), dialog
        ))
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        # Initial subject detection
        self.detect_subjects(subjects_list)
        
        dialog.exec_()
    
    def open_output_dialog(self, block_data: Dict[str, Any]):
        """Open output configuration dialog."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Output Settings - {block_data['name']}")
        dialog.setMinimumSize(400, 300)
        dialog.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        info_label = QtWidgets.QLabel("Output configuration is managed automatically based on the connected analysis blocks.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
        layout.addWidget(info_label)
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def change_project_directory(self, parent_dialog):
        """Change the project directory."""
        new_dir = QtWidgets.QFileDialog.getExistingDirectory(
            parent_dialog, "Select Project Directory", self.project_dir
        )
        if new_dir:
            self.project_dir = new_dir
            self.project_dir_label.setText(f"Current: {self.project_dir}")
            self.log_message(f"Project directory changed to: {new_dir}")
    
    def detect_subjects(self, subjects_list):
        """Detect available subjects in the project directory."""
        subjects_list.clear()
        
        if not os.path.exists(self.project_dir):
            return
        
        # Look for directories that might contain subject data
        potential_subjects = []
        for item in os.listdir(self.project_dir):
            item_path = os.path.join(self.project_dir, item)
            if os.path.isdir(item_path):
                # Check if it looks like a subject directory
                has_dicom = os.path.exists(os.path.join(item_path, "DICOM"))
                has_t1 = os.path.exists(os.path.join(item_path, "T1_images"))
                has_mri = os.path.exists(os.path.join(item_path, "mri"))
                
                if has_dicom or has_t1 or has_mri:
                    potential_subjects.append(item)
        
        # Add subjects to list
        for subject in sorted(potential_subjects):
            item = QtWidgets.QListWidgetItem(subject)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)  # Default to selected
            subjects_list.addItem(item)
        
        if potential_subjects:
            self.log_message(f"Detected {len(potential_subjects)} potential subjects")
        else:
            self.log_message("No subjects detected. Check your project directory structure.")
    
    def select_all_subjects(self, subjects_list, select_all=True):
        """Select or deselect all subjects."""
        state = QtCore.Qt.Checked if select_all else QtCore.Qt.Unchecked
        for i in range(subjects_list.count()):
            item = subjects_list.item(i)
            item.setCheckState(state)
    
    def validate_subjects(self, subjects_list, manual_subjects, data_type):
        """Validate that selected subjects have the required data."""
        # Get selected subjects
        selected_subjects = []
        
        # From list widget
        for i in range(subjects_list.count()):
            item = subjects_list.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                selected_subjects.append(item.text())
        
        # From manual entry
        manual_text = manual_subjects.toPlainText().strip()
        if manual_text:
            manual_list = [s.strip() for s in manual_text.split('\n') if s.strip()]
            selected_subjects.extend(manual_list)
        
        # Remove duplicates
        selected_subjects = list(set(selected_subjects))
        
        if not selected_subjects:
            self.validation_result.setText("❌ No subjects selected")
            self.validation_result.setStyleSheet("padding: 10px; border: 1px solid #f44336; background-color: #ffebee; color: #c62828;")
            return
        
        # Validate each subject
        valid_subjects = []
        invalid_subjects = []
        
        for subject in selected_subjects:
            subject_path = os.path.join(self.project_dir, subject)
            if not os.path.exists(subject_path):
                invalid_subjects.append(f"{subject} (directory not found)")
                continue
            
            # Check data availability based on type
            valid = False
            if data_type in ["DICOM", "Both"]:
                dicom_path = os.path.join(subject_path, "DICOM")
                if os.path.exists(dicom_path) and os.listdir(dicom_path):
                    valid = True
            
            if data_type in ["NIfTI", "Both"]:
                t1_path = os.path.join(subject_path, "T1_images")
                if os.path.exists(t1_path) and os.listdir(t1_path):
                    valid = True
            
            if valid:
                valid_subjects.append(subject)
            else:
                invalid_subjects.append(f"{subject} (no {data_type} data)")
        
        # Show results
        result_text = f"✅ {len(valid_subjects)} valid subjects\n"
        if valid_subjects:
            result_text += f"Valid: {', '.join(valid_subjects[:5])}"
            if len(valid_subjects) > 5:
                result_text += f" and {len(valid_subjects) - 5} more"
        
        if invalid_subjects:
            result_text += f"\n\n❌ {len(invalid_subjects)} invalid subjects:\n"
            result_text += '\n'.join(invalid_subjects[:5])
            if len(invalid_subjects) > 5:
                result_text += f"\n... and {len(invalid_subjects) - 5} more"
        
        self.validation_result.setText(result_text)
        
        if invalid_subjects:
            self.validation_result.setStyleSheet("padding: 10px; border: 1px solid #ff9800; background-color: #fff3e0; color: #f57c00;")
        else:
            self.validation_result.setStyleSheet("padding: 10px; border: 1px solid #4caf50; background-color: #e8f5e9; color: #2e7d32;")
    
    def save_input_settings(self, block_id, subjects_list, manual_subjects, data_type, dialog):
        """Save input block settings."""
        # Get selected subjects
        selected_subjects = []
        
        # From list widget
        for i in range(subjects_list.count()):
            item = subjects_list.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                selected_subjects.append(item.text())
        
        # From manual entry
        manual_text = manual_subjects.toPlainText().strip()
        if manual_text:
            manual_list = [s.strip() for s in manual_text.split('\n') if s.strip()]
            selected_subjects.extend(manual_list)
        
        # Remove duplicates
        selected_subjects = list(set(selected_subjects))
        
        if block_id in self.current_pipeline['blocks']:
            params = self.current_pipeline['blocks'][block_id]['parameters']
            params.update({
                'selected_subjects': selected_subjects,
                'data_type': data_type,
                'project_directory': self.project_dir
            })
            self.log_message(f"Updated input settings: {len(selected_subjects)} subjects selected")
        
        dialog.accept()
    
    def on_pipeline_type_changed(self):
        """Handle pipeline type selection change."""
        if self.full_pipeline_rb.isChecked():
            self.log_message("📋 Full Pipeline selected: DICOM → Pre-processing → Optimization → Simulation → Analysis")
            self.subject_status_label.setText("Full pipeline processes DICOM files from /project_dir/sourcedata/")
        else:
            self.log_message("📋 Optimization Pipeline selected: Optimization → Simulation → Analysis")
            self.subject_status_label.setText("Optimization pipeline uses preprocessed subjects with m2m folders")
        
        # Clear current subjects and detect new ones
        self.subjects_list.clear()
        self.detect_available_subjects()
    
    def detect_available_subjects(self):
        """Detect available subjects based on selected pipeline type."""
        self.subjects_list.clear()
        
        if not os.path.exists(self.project_dir):
            self.subject_status_label.setText("❌ Project directory not found")
            return
        
        available_subjects = []
        
        if self.full_pipeline_rb.isChecked():
            # Full pipeline: look for DICOM files in sourcedata
            sourcedata_path = os.path.join(self.project_dir, "sourcedata")
            if os.path.exists(sourcedata_path):
                for subject_dir in os.listdir(sourcedata_path):
                    subject_path = os.path.join(sourcedata_path, subject_dir)
                    if os.path.isdir(subject_path):
                        # Check for DICOM data
                        dicom_found = False
                        for root, dirs, files in os.walk(subject_path):
                            # Look for .dcm files or DICOM directories
                            if any(f.lower().endswith('.dcm') for f in files) or 'DICOM' in dirs:
                                dicom_found = True
                                break
                        
                        if dicom_found:
                            available_subjects.append(subject_dir)
        else:
            # Optimization pipeline: look for m2m folders
            for item in os.listdir(self.project_dir):
                if item.startswith('m2m_'):
                    subject_id = item[4:]  # Remove 'm2m_' prefix
                    m2m_path = os.path.join(self.project_dir, item)
                    if os.path.isdir(m2m_path):
                        # Verify it's a valid m2m folder (has required files)
                        if self.validate_m2m_folder(m2m_path):
                            available_subjects.append(subject_id)
        
        # Populate subject list
        available_subjects.sort()
        for subject in available_subjects:
            item = QtWidgets.QListWidgetItem(subject)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)  # Default to selected
            self.subjects_list.addItem(item)
        
        # Update status
        if available_subjects:
            pipeline_type = "Full" if self.full_pipeline_rb.isChecked() else "Optimization"
            self.subject_status_label.setText(f"✅ {len(available_subjects)} subjects available for {pipeline_type} pipeline")
            self.log_message(f"🔍 Detected {len(available_subjects)} subjects: {', '.join(available_subjects[:3])}" + 
                           (f" and {len(available_subjects)-3} more" if len(available_subjects) > 3 else ""))
        else:
            pipeline_type = "Full" if self.full_pipeline_rb.isChecked() else "Optimization"
            if pipeline_type == "Full":
                self.subject_status_label.setText("❌ No DICOM subjects found in /sourcedata/")
            else:
                self.subject_status_label.setText("❌ No m2m folders found (need m2m_subjectID directories)")
    
    def validate_m2m_folder(self, m2m_path):
        """Validate that an m2m folder contains required files.""" 
        required_files = ['T1fs_conform.nii.gz', 'T2.nii.gz']  # Basic check
        mesh_files = ['skin.stl', 'skull.stl', 'csf.stl', 'gm.stl', 'wm.stl']
        
        # Check for at least some required files
        found_files = []
        for root, dirs, files in os.walk(m2m_path):
            found_files.extend(files)
        
        has_basic = any(f in found_files for f in required_files)
        has_mesh = any(f in found_files for f in mesh_files)
        
        return has_basic or has_mesh  # At least one type should be present
    
    def select_all_subjects(self, select_all=True):
        """Select or deselect all subjects."""
        state = QtCore.Qt.Checked if select_all else QtCore.Qt.Unchecked
        for i in range(self.subjects_list.count()):
            item = self.subjects_list.item(i)
            item.setCheckState(state)
        
        selected_count = len(self.get_selected_subjects())
        action = "selected" if select_all else "deselected"
        self.log_message(f"📝 All subjects {action} ({selected_count} total)")
    
    def get_selected_subjects(self):
        """Get list of selected subjects."""
        selected = []
        for i in range(self.subjects_list.count()):
            item = self.subjects_list.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                selected.append(item.text())
        return selected
    
    def create_selected_pipeline(self):
        """Create the selected pipeline type with chosen subjects."""
        selected_subjects = self.get_selected_subjects()
        
        if not selected_subjects:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select at least one subject")
            return
        
        # Clear current pipeline
        self.canvas.clear_canvas()
        self.current_pipeline = {
            'blocks': {},
            'connections': [],
            'metadata': {
                'pipeline_type': 'full' if self.full_pipeline_rb.isChecked() else 'optimization',
                'selected_subjects': selected_subjects,
                'created': QtCore.QDateTime.currentDateTime().toString(),
            }
        }
        
        if self.full_pipeline_rb.isChecked():
            self.create_full_pipeline(selected_subjects)
        else:
            self.create_optimization_pipeline(selected_subjects)
        
        # Enable configuration button
        self.configure_blocks_btn.setEnabled(True)
        
        pipeline_type = "Full" if self.full_pipeline_rb.isChecked() else "Optimization"
        self.log_message(f"✅ Created {pipeline_type} pipeline with {len(selected_subjects)} subjects")
    
    def create_full_pipeline(self, subjects):
        """Create a full pipeline: Input → Pre-processing → Optimization → Simulation → Analysis → Output."""
        self.block_counter = 0
        
        # Input block
        input_config = BlockConfiguration(
            block_id="input_1",
            block_type=BlockType.INPUT,
            name="DICOM Input",
            position=(50, 100),
            parameters={
                'selected_subjects': subjects,
                'data_type': 'DICOM',
                'source_directory': os.path.join(self.project_dir, 'sourcedata')
            }
        )
        self.add_block_to_pipeline(input_config)
        
        # Pre-processing block
        preproc_config = BlockConfiguration(
            block_id="preprocessing_1",
            block_type=BlockType.PREPROCESSING,
            name="Pre-processing",
            position=(300, 100),
            parameters=self._get_default_parameters(BlockType.PREPROCESSING)
        )
        self.add_block_to_pipeline(preproc_config)
        
        # Optimization block
        opt_config = BlockConfiguration(
            block_id="optimization_1",
            block_type=BlockType.OPTIMIZATION,
            name="Flex Search",
            position=(550, 100),
            parameters=self._get_default_parameters(BlockType.OPTIMIZATION)
        )
        self.add_block_to_pipeline(opt_config)
        
        # Simulation block
        sim_config = BlockConfiguration(
            block_id="simulation_1",
            block_type=BlockType.SIMULATION,
            name="TI Simulation",
            position=(800, 100),
            parameters=self._get_default_parameters(BlockType.SIMULATION)
        )
        self.add_block_to_pipeline(sim_config)
        
        # Analysis block
        analysis_config = BlockConfiguration(
            block_id="analysis_1",
            block_type=BlockType.ANALYSIS,
            name="Analysis",
            position=(1050, 100),
            parameters=self._get_default_parameters(BlockType.ANALYSIS)
        )
        self.add_block_to_pipeline(analysis_config)
        
        # Output block
        output_config = BlockConfiguration(
            block_id="output_1",
            block_type=BlockType.OUTPUT,
            name="Output",
            position=(1300, 100),
            parameters={}
        )
        self.add_block_to_pipeline(output_config)
        
        # Create connections
        connections = [
            ("input_1", "preprocessing_1"),
            ("preprocessing_1", "optimization_1"),
            ("optimization_1", "simulation_1"),
            ("simulation_1", "analysis_1"),
            ("analysis_1", "output_1")
        ]
        
        for source_id, target_id in connections:
            self.canvas.add_connection(source_id, target_id)
            self.on_connection_created(source_id, target_id)
    
    def create_optimization_pipeline(self, subjects):
        """Create optimization pipeline: Input → Optimization → Simulation → Analysis → Output."""
        self.block_counter = 0
        
        # Input block (m2m subjects)
        input_config = BlockConfiguration(
            block_id="input_1", 
            block_type=BlockType.INPUT,
            name="m2m Input",
            position=(50, 100),
            parameters={
                'selected_subjects': subjects,
                'data_type': 'm2m',
                'source_directory': self.project_dir
            }
        )
        self.add_block_to_pipeline(input_config)
        
        # Optimization block
        opt_config = BlockConfiguration(
            block_id="optimization_1",
            block_type=BlockType.OPTIMIZATION,
            name="Flex Search",
            position=(300, 100),
            parameters=self._get_default_parameters(BlockType.OPTIMIZATION)
        )
        self.add_block_to_pipeline(opt_config)
        
        # Simulation block
        sim_config = BlockConfiguration(
            block_id="simulation_1",
            block_type=BlockType.SIMULATION,
            name="TI Simulation",
            position=(550, 100),
            parameters=self._get_default_parameters(BlockType.SIMULATION)
        )
        self.add_block_to_pipeline(sim_config)
        
        # Analysis block
        analysis_config = BlockConfiguration(
            block_id="analysis_1",
            block_type=BlockType.ANALYSIS,
            name="Analysis",  
            position=(800, 100),
            parameters=self._get_default_parameters(BlockType.ANALYSIS)
        )
        self.add_block_to_pipeline(analysis_config)
        
        # Output block
        output_config = BlockConfiguration(
            block_id="output_1",
            block_type=BlockType.OUTPUT,
            name="Output",
            position=(1050, 100),
            parameters={}
        )
        self.add_block_to_pipeline(output_config)
        
        # Create connections
        connections = [
            ("input_1", "optimization_1"),
            ("optimization_1", "simulation_1"),
            ("simulation_1", "analysis_1"),
            ("analysis_1", "output_1")
        ]
        
        for source_id, target_id in connections:
            self.canvas.add_connection(source_id, target_id)
            self.on_connection_created(source_id, target_id)
    
    def add_block_to_pipeline(self, config: BlockConfiguration):
        """Add a block to both the pipeline configuration and canvas."""
        # Add to pipeline config
        self.current_pipeline['blocks'][config.block_id] = {
            'block_id': config.block_id,
            'name': config.name,
            'block_type': config.block_type.value,
            'position': config.position,
            'parameters': config.parameters,
            'inputs': config.inputs,
            'outputs': config.outputs
        }
        
        # Add to canvas
        self.canvas.add_block(config)
    
    def open_pipeline_configuration(self):
        """Open a dialog to configure all pipeline blocks."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Pipeline Configuration")
        dialog.setMinimumSize(400, 500)
        dialog.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Title
        title_label = QtWidgets.QLabel("Configure Pipeline Blocks")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        
        # Block list
        scroll_area = QtWidgets.QScrollArea()
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        
        # Add configuration button for each block
        for block_id, block_data in self.current_pipeline['blocks'].items():
            block_group = QtWidgets.QGroupBox(f"{block_data['name']} ({block_data['block_type'].title()})")
            block_layout = QtWidgets.QHBoxLayout(block_group)
            
            # Block info
            info_label = QtWidgets.QLabel(f"Block ID: {block_id}")
            info_label.setStyleSheet("color: #666;")
            block_layout.addWidget(info_label)
            
            block_layout.addStretch()
            
            # Configure button
            config_btn = QtWidgets.QPushButton("⚙ Configure")
            config_btn.clicked.connect(lambda checked, bid=block_id: self.open_block_configuration(bid))
            block_layout.addWidget(config_btn)
            
            scroll_layout.addWidget(block_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_() 