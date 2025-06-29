const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const API_HOST = process.env.API_HOST || 'http://localhost:8080';

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Basic route
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        timestamp: new Date().toISOString(),
        service: 'ti-csc-webapp'
    });
});

// Proxy route to communicate with PyQt GUI
app.post('/api/gui/:endpoint', async (req, res) => {
    try {
        console.log(`[PROXY] ${req.method} ${API_HOST}/api/${req.params.endpoint}`);
        console.log(`[PROXY] Body:`, req.body);
        
        const response = await axios({
            method: req.method,
            url: `${API_HOST}/api/${req.params.endpoint}`,
            data: req.body,
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log(`[PROXY] Response:`, response.data);
        res.json(response.data);
        
    } catch (error) {
        console.error(`[PROXY] Error:`, error.message);
        
        if (error.code === 'ECONNREFUSED') {
            res.status(503).json({ 
                error: 'GUI API not available', 
                message: 'PyQt GUI is not running or API server is not started',
                details: error.message
            });
        } else if (error.response) {
            res.status(error.response.status).json({
                error: 'GUI API error',
                message: error.response.data || error.message
            });
        } else {
            res.status(500).json({ 
                error: 'Proxy error', 
                message: error.message 
            });
        }
    }
});

// GET proxy route
app.get('/api/gui/:endpoint', async (req, res) => {
    try {
        console.log(`[PROXY] ${req.method} ${API_HOST}/api/${req.params.endpoint}`);
        
        const response = await axios({
            method: req.method,
            url: `${API_HOST}/api/${req.params.endpoint}`,
            timeout: 10000
        });
        
        console.log(`[PROXY] Response:`, response.data);
        res.json(response.data);
        
    } catch (error) {
        console.error(`[PROXY] Error:`, error.message);
        
        if (error.code === 'ECONNREFUSED') {
            res.status(503).json({ 
                error: 'GUI API not available', 
                message: 'PyQt GUI is not running or API server is not started'
            });
        } else if (error.response) {
            res.status(error.response.status).json({
                error: 'GUI API error',
                message: error.response.data || error.message
            });
        } else {
            res.status(500).json({ 
                error: 'Proxy error', 
                message: error.message 
            });
        }
    }
});

// Test route that doesn't require GUI
app.get('/api/test', (req, res) => {
    res.json({
        message: 'Web app is working!',
        timestamp: new Date().toISOString(),
        environment: process.env.NODE_ENV || 'development',
        api_host: API_HOST
    });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({ error: 'Internal server error' });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 TI-CSC Web App running on port ${PORT}`);
    console.log(`📡 GUI API Host: ${API_HOST}`);
    console.log(`🌐 Web Interface: http://localhost:${PORT}`);
    console.log(`🔧 Environment: ${process.env.NODE_ENV || 'development'}`);
}); 