import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Shield, Users, MessageCircle, AlertTriangle, Power, Zap } from 'lucide-react';
import PeerDiscovery from './components/PeerDiscovery';
import SecureChat from './components/SecureChat';
import SecurityAlerts from './components/SecurityAlerts';
import ConnectionRequests from './components/ConnectionRequests';
import AttackPanel from './components/AttackPanel';
import './index.css';

function App() {
  const [peerStatus, setPeerStatus] = useState({
    running: false,
    pseudo_id: '',
    active_session: false,
    discovered_peers: 0,
    peer_name: ''
  });
  
  const [alerts, setAlerts] = useState([]);
  const [currentView, setCurrentView] = useState('discovery');
  
  // Check if this is Peer 3 (attacker)
  const API_BASE = process.env.REACT_APP_PEER_API || 'http://localhost:8080';
  const isPeer3 = API_BASE.includes('8082') || peerStatus.peer_name?.includes('Attacker');

  useEffect(() => {
    fetchPeerStatus();
    fetchAlerts();
    
    const interval = setInterval(() => {
      fetchPeerStatus();
      fetchAlerts();
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchPeerStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/peer/status`);
      const data = await response.json();
      setPeerStatus(data);
    } catch (error) {
      console.error('Failed to fetch peer status:', error);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/peer/alerts`);
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    }
  };

  const startPeer = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/peer/start`, { method: 'POST' });
      const data = await response.json();
      if (data.status === 'success') {
        fetchPeerStatus();
      }
    } catch (error) {
      console.error('Failed to start peer:', error);
    }
  };

  const getStatusColor = () => {
    if (!peerStatus.running) return 'status-offline';
    if (alerts.some(alert => alert.severity === 'HIGH')) return 'status-danger';
    if (peerStatus.active_session) return 'status-online';
    return 'status-warning';
  };

  const getActiveAlerts = () => {
    return alerts.filter(alert => 
      Date.now() - (alert.timestamp * 1000) < 300000 // Last 5 minutes
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Shield className="h-8 w-8 text-primary-600" />
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  {isPeer3 ? 'Malicious Peer - Attack Simulator' : 'Anonymous P2P Communication'}
                </h1>
                <p className="text-sm text-gray-500">
                  Peer ID: {peerStatus.pseudo_id || 'Not initialized'} {isPeer3 ? '(Attacker)' : ''}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Status Indicator */}
              <div className="flex items-center space-x-2">
                <span className={`status-indicator ${getStatusColor()}`}>
                  <div className="w-2 h-2 bg-current rounded-full mr-2"></div>
                  {peerStatus.running ? 
                    (peerStatus.active_session ? 'Connected' : 'Discovering') : 
                    'Offline'
                  }
                </span>
              </div>
              
              {/* Active Alerts */}
              {getActiveAlerts().length > 0 && (
                <div className="flex items-center space-x-1 text-danger-600">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm font-medium">
                    {getActiveAlerts().length} Alert{getActiveAlerts().length !== 1 ? 's' : ''}
                  </span>
                </div>
              )}
              
              {/* Start/Stop Button */}
              <button
                onClick={startPeer}
                disabled={peerStatus.running}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md font-medium transition-colors ${
                  peerStatus.running 
                    ? 'bg-success-50 text-success-600 cursor-not-allowed' 
                    : 'btn-primary'
                }`}
              >
                <Power className="h-4 w-4" />
                <span>{peerStatus.running ? 'Running' : 'Start Peer'}</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setCurrentView('discovery')}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                currentView === 'discovery'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Users className="h-4 w-4" />
              <span>Peer Discovery</span>
            </button>
            
            <button
              onClick={() => setCurrentView('chat')}
              disabled={!peerStatus.active_session}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                currentView === 'chat' && peerStatus.active_session
                  ? 'border-primary-500 text-primary-600'
                  : peerStatus.active_session
                  ? 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 cursor-pointer'
                  : 'border-transparent text-gray-400 cursor-not-allowed'
              }`}
            >
              <MessageCircle className="h-4 w-4" />
              <span>Secure Chat</span>
            </button>
            
            <button
              onClick={() => setCurrentView('alerts')}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                currentView === 'alerts'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <AlertTriangle className="h-4 w-4" />
              <span>Security Alerts</span>
              {getActiveAlerts().length > 0 && (
                <span className="bg-danger-500 text-white text-xs rounded-full px-2 py-0.5 min-w-[1.25rem] text-center">
                  {getActiveAlerts().length}
                </span>
              )}
            </button>
            
            {/* Attack Panel - Only for Peer 3 */}
            {isPeer3 && (
              <button
                onClick={() => setCurrentView('attack')}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  currentView === 'attack'
                    ? 'border-red-500 text-red-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Zap className="h-4 w-4" />
                <span>Launch Attack</span>
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Isolation Warning Banner - Only for isolated peers */}
      {peerStatus.is_isolated && (
        <div className="bg-red-900 border-b-4 border-red-950">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-8 w-8 text-red-200 animate-pulse" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-white mb-1">
                  🚫 YOUR PEER HAS BEEN ISOLATED FROM THE NETWORK
                </h3>
                <p className="text-red-100 text-sm mb-2">
                  {peerStatus.isolation_reason || 'Blocked by network security - detected malicious activity'}
                </p>
                <div className="bg-red-950 rounded-md p-3 text-red-200 text-xs space-y-1">
                  <p>• You cannot establish new connections with other peers</p>
                  <p>• Your peer has been removed from network discovery</p>
                  <p>• Attack functionality has been disabled by the security system</p>
                  <p className="text-red-300 font-semibold mt-2">This peer is permanently banned from the network</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Connection Requests - Always visible when running */}
        <ConnectionRequests peerStatus={peerStatus} />
        
        {!peerStatus.running && (
          <div className="alert alert-info mb-6">
            <div className="flex items-center">
              <Shield className="h-5 w-5 mr-3" />
              <div>
                <h3 className="font-medium">Peer Service Not Running</h3>
                <p className="text-sm mt-1">
                  Click "Start Peer" to begin anonymous peer discovery and secure communication.
                </p>
              </div>
            </div>
          </div>
        )}

        {currentView === 'discovery' && (
          <PeerDiscovery 
            peerStatus={peerStatus} 
            onStatusChange={fetchPeerStatus}
          />
        )}
        
        {currentView === 'chat' && peerStatus.active_session && (
          <SecureChat 
            peerStatus={peerStatus}
            onStatusChange={fetchPeerStatus}
          />
        )}
        
        {currentView === 'alerts' && (
          <SecurityAlerts alerts={alerts} />
        )}
        
        {currentView === 'attack' && isPeer3 && (
          <AttackPanel peerStatus={peerStatus} />
        )}
      </main>
    </div>
  );
}

export default App;