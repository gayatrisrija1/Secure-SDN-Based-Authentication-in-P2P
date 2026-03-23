import React, { useState, useEffect } from 'react';
import { Search, Wifi, Lock, Users, Clock } from 'lucide-react';

const PeerDiscovery = ({ peerStatus, onStatusChange }) => {
  const [peers, setPeers] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [authenticating, setAuthenticating] = useState(null);
  
  const API_BASE = process.env.REACT_APP_PEER_API || 'http://localhost:8080';

  useEffect(() => {
    if (peerStatus.running) {
      discoverPeers();
    }
  }, [peerStatus.running]);

  const discoverPeers = async () => {
    if (!peerStatus.running) return;
    
    setScanning(true);
    try {
      const response = await fetch(`${API_BASE}/api/peer/discover`, { method: 'POST' });
      const data = await response.json();
      
      if (data.status === 'success') {
        setPeers(data.peers || []);
      }
    } catch (error) {
      console.error('Peer discovery failed:', error);
    } finally {
      setScanning(false);
    }
  };

  const authenticateWithPeer = async (peerId) => {
    setAuthenticating(peerId);
    try {
      const response = await fetch(`${API_BASE}/api/peer/authenticate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ peer_id: peerId })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        onStatusChange();
      } else {
        alert(`Authentication failed: ${data.message}`);
      }
    } catch (error) {
      console.error('Authentication failed:', error);
      alert('Authentication failed: Network error');
    } finally {
      setAuthenticating(null);
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
  };

  return (
    <div className="space-y-6">
      {/* Discovery Header */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Wifi className="h-6 w-6 text-primary-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Peer Discovery</h2>
              <p className="text-sm text-gray-500">
                Find and connect to anonymous peers on the network
              </p>
            </div>
          </div>
          
          <button
            onClick={discoverPeers}
            disabled={!peerStatus.running || scanning}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md font-medium transition-colors ${
              !peerStatus.running || scanning
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'btn-primary'
            }`}
          >
            <Search className={`h-4 w-4 ${scanning ? 'animate-spin' : ''}`} />
            <span>{scanning ? 'Scanning...' : 'Scan Network'}</span>
          </button>
        </div>

        {/* Network Status */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5 text-gray-400" />
              <span className="text-sm font-medium text-gray-600">Discovered Peers</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-1">{peers.length}</p>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <Lock className="h-5 w-5 text-gray-400" />
              <span className="text-sm font-medium text-gray-600">Session Status</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {peerStatus.active_session ? 'Active' : 'None'}
            </p>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <Wifi className="h-5 w-5 text-gray-400" />
              <span className="text-sm font-medium text-gray-600">Network Status</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {peerStatus.running ? 'Online' : 'Offline'}
            </p>
          </div>
        </div>
      </div>

      {/* Peer List */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Peers</h3>
        
        {!peerStatus.running ? (
          <div className="text-center py-8">
            <Wifi className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">Start the peer service to discover other peers</p>
          </div>
        ) : peers.length === 0 ? (
          <div className="text-center py-8">
            <Search className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-2">No peers discovered yet</p>
            <button
              onClick={discoverPeers}
              disabled={scanning}
              className="btn-secondary"
            >
              {scanning ? 'Scanning...' : 'Scan for Peers'}
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {peers.map((peer) => (
              <div
                key={peer.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                    <Users className="h-5 w-5 text-primary-600" />
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900">
                      Anonymous Peer
                    </h4>
                    <p className="text-sm text-gray-500">
                      ID: {peer.pseudo_id}
                    </p>
                    <div className="flex items-center space-x-4 mt-1">
                      <span className="text-xs text-gray-400">
                        IP: {peer.ip_address}
                      </span>
                      <div className="flex items-center space-x-1 text-xs text-gray-400">
                        <Clock className="h-3 w-3" />
                        <span>Last seen: {formatTimestamp(peer.last_seen)}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <span className={`status-indicator ${
                    peer.status === 'available' ? 'status-online' : 'status-offline'
                  }`}>
                    {peer.status}
                  </span>
                  
                  <button
                    onClick={() => authenticateWithPeer(peer.id)}
                    disabled={
                      peerStatus.active_session || 
                      authenticating === peer.id || 
                      peer.status !== 'available'
                    }
                    className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                      peerStatus.active_session || peer.status !== 'available'
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : authenticating === peer.id
                        ? 'bg-warning-100 text-warning-600'
                        : 'btn-primary text-xs'
                    }`}
                  >
                    <Lock className="h-3 w-3" />
                    <span>
                      {peerStatus.active_session 
                        ? 'Session Active' 
                        : authenticating === peer.id 
                        ? 'Authenticating...' 
                        : 'Connect'
                      }
                    </span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Connection Instructions */}
      {!peerStatus.active_session && peers.length > 0 && (
        <div className="alert alert-info">
          <div className="flex items-start space-x-3">
            <Lock className="h-5 w-5 mt-0.5" />
            <div>
              <h4 className="font-medium">Anonymous Authentication</h4>
              <p className="text-sm mt-1">
                Select a peer to establish an encrypted, anonymous session. 
                Authentication uses pseudo-identities and cryptographic challenges 
                without revealing real identities.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PeerDiscovery;