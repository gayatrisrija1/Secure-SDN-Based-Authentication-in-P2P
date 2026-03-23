import React, { useState, useEffect } from 'react';
import { AlertTriangle, Zap, Shield, Target } from 'lucide-react';

const AttackPanel = ({ peerStatus }) => {
  const [selectedAttack, setSelectedAttack] = useState('replay');
  const [selectedIntensity, setSelectedIntensity] = useState('low');
  const [selectedTarget, setSelectedTarget] = useState('auto');
  const [isLaunching, setIsLaunching] = useState(false);
  const [lastAttack, setLastAttack] = useState(null);
  const [activeSessions, setActiveSessions] = useState([]);

  const API_BASE = process.env.REACT_APP_PEER_API || 'http://localhost:8082';
  const isIsolated = peerStatus?.is_isolated || false;

  // Fetch active sessions for targeting
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/flows');
        if (response.ok) {
          const sessions = await response.json();
          setActiveSessions(sessions);
        }
      } catch (error) {
        console.error('Failed to fetch sessions:', error);
      }
    };

    fetchSessions();
    const interval = setInterval(fetchSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  const attackTypes = [
    { value: 'replay', label: 'Replay Attack', icon: '🔄', description: 'Resend captured authentication packets' },
    { value: 'flooding', label: 'Network Flooding', icon: '🌊', description: 'Overwhelm network with traffic' },
    { value: 'auth_flooding', label: 'Auth Flooding', icon: '🔐', description: 'Rapid authentication attempts' }
  ];

  const intensityLevels = [
    { value: 'low', label: 'Low', color: 'text-yellow-600', description: 'Monitoring & Warning' },
    { value: 'medium', label: 'Medium', color: 'text-orange-600', description: 'Session Termination' },
    { value: 'high', label: 'High', color: 'text-red-600', description: 'Key Destruction' },
    { value: 'critical', label: 'Critical', color: 'text-red-800', description: 'Peer Isolation' }
  ];

  const launchAttack = async () => {
    setIsLaunching(true);
    try {
      const response = await fetch(`${API_BASE}/api/attack/launch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          attack_type: selectedAttack,
          intensity: selectedIntensity,
          target_session: selectedTarget === 'auto' ? null : selectedTarget
        }),
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        setLastAttack({
          type: selectedAttack,
          intensity: selectedIntensity,
          severity: data.severity,
          timestamp: new Date(),
          success: true
        });
      } else {
        setLastAttack({
          type: selectedAttack,
          intensity: selectedIntensity,
          timestamp: new Date(),
          success: false,
          error: data.message
        });
      }
    } catch (error) {
      setLastAttack({
        type: selectedAttack,
        intensity: selectedIntensity,
        timestamp: new Date(),
        success: false,
        error: error.message
      });
    } finally {
      setIsLaunching(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Warning Header */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-5 w-5 text-red-600" />
          <h2 className="text-lg font-semibold text-red-800">Malicious Peer - Attack Simulation</h2>
        </div>
        <p className="text-sm text-red-600 mt-2">
          This panel simulates a compromised peer launching attacks to demonstrate the progressive self-destruct mechanism.
        </p>
      </div>

      {/* Attack Configuration */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
          <Target className="h-5 w-5" />
          <span>Attack Configuration</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Attack Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Attack Type
            </label>
            <div className="space-y-2">
              {attackTypes.map((attack) => (
                <label key={attack.value} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="attackType"
                    value={attack.value}
                    checked={selectedAttack === attack.value}
                    onChange={(e) => setSelectedAttack(e.target.value)}
                    className="text-red-600"
                  />
                  <span className="text-lg">{attack.icon}</span>
                  <div>
                    <div className="font-medium text-gray-900">{attack.label}</div>
                    <div className="text-sm text-gray-500">{attack.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Target Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Attack Target
            </label>
            <div className="space-y-2">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name="target"
                  value="auto"
                  checked={selectedTarget === 'auto'}
                  onChange={(e) => setSelectedTarget(e.target.value)}
                  className="text-red-600"
                />
                <div>
                  <div className="font-medium text-gray-900">Auto Target</div>
                  <div className="text-sm text-gray-500">Attack first available session</div>
                </div>
              </label>
              
              {activeSessions.map((session) => (
                <label key={session.id} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="target"
                    value={session.id}
                    checked={selectedTarget === session.id}
                    onChange={(e) => setSelectedTarget(e.target.value)}
                    className="text-red-600"
                  />
                  <div>
                    <div className="font-medium text-gray-900">
                      {session.source} ↔ {session.destination}
                    </div>
                    <div className="text-sm text-gray-500">
                      {session.packet_count} packets, {Math.round(session.duration)}s active
                    </div>
                  </div>
                </label>
              ))}
              
              {activeSessions.length === 0 && (
                <div className="text-sm text-gray-500 italic">
                  No active sessions to target
                </div>
              )}
            </div>
          </div>

          {/* Intensity Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Attack Intensity
            </label>
            <div className="space-y-2">
              {intensityLevels.map((level) => (
                <label key={level.value} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="intensity"
                    value={level.value}
                    checked={selectedIntensity === level.value}
                    onChange={(e) => setSelectedIntensity(e.target.value)}
                    className="text-red-600"
                  />
                  <div>
                    <div className={`font-medium ${level.color}`}>{level.label}</div>
                    <div className="text-sm text-gray-500">{level.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Launch Button */}
        <div className="mt-6 flex flex-col items-center space-y-3">
          {isIsolated && (
            <div className="bg-red-900 text-red-100 px-4 py-2 rounded-lg text-sm font-medium flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4" />
              <span>Attack functionality disabled - peer has been isolated</span>
            </div>
          )}
          <button
            onClick={launchAttack}
            disabled={isLaunching || isIsolated}
            className={`flex items-center space-x-2 px-6 py-3 rounded-lg transition-colors ${
              isIsolated
                ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                : 'bg-red-600 text-white hover:bg-red-700'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            <Zap className="h-5 w-5" />
            <span>
              {isIsolated ? 'Attack Disabled (Isolated)' : isLaunching ? 'Launching Attack...' : 'Launch Attack'}
            </span>
          </button>
        </div>
      </div>

      {/* Attack Status */}
      {lastAttack && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>Last Attack Status</span>
          </h3>

          <div className={`p-4 rounded-lg ${lastAttack.success ? 'bg-red-50 border border-red-200' : 'bg-gray-50 border border-gray-200'}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900">
                  {attackTypes.find(a => a.value === lastAttack.type)?.label} - {lastAttack.intensity.toUpperCase()}
                </div>
                <div className="text-sm text-gray-500">
                  {lastAttack.timestamp.toLocaleTimeString()}
                </div>
              </div>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                lastAttack.success 
                  ? 'bg-red-100 text-red-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {lastAttack.success ? `${lastAttack.severity} Alert Created` : 'Failed'}
              </div>
            </div>
            
            {lastAttack.success ? (
              <div className="mt-2 text-sm text-red-600">
                ✅ Attack launched successfully! Check Controller Dashboard for progressive response.
              </div>
            ) : (
              <div className="mt-2 text-sm text-gray-600">
                ❌ Attack failed: {lastAttack.error}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Progressive Response Info */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Progressive Self-Destruct Levels</h3>
        <div className="space-y-3">
          <div className="flex items-center space-x-3 p-3 bg-yellow-50 rounded-lg">
            <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center text-yellow-800 font-bold">1</div>
            <div>
              <div className="font-medium text-yellow-800">LOW - Monitoring & Warning</div>
              <div className="text-sm text-yellow-600">System monitors suspicious activity and logs warnings</div>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-3 bg-orange-50 rounded-lg">
            <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center text-orange-800 font-bold">2</div>
            <div>
              <div className="font-medium text-orange-800">MEDIUM - Session Termination</div>
              <div className="text-sm text-orange-600">Active sessions terminated, peers can reconnect</div>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-3 bg-red-50 rounded-lg">
            <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center text-red-800 font-bold">3</div>
            <div>
              <div className="font-medium text-red-800">HIGH - Key Destruction</div>
              <div className="text-sm text-red-600">Session keys destroyed, re-authentication required</div>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-3 bg-red-100 rounded-lg">
            <div className="w-8 h-8 bg-red-200 rounded-full flex items-center justify-center text-red-900 font-bold">4</div>
            <div>
              <div className="font-medium text-red-900">CRITICAL - Peer Isolation</div>
              <div className="text-sm text-red-700">Attacker peer completely isolated from network</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AttackPanel;