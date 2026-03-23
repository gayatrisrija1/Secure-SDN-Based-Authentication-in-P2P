import React from 'react';
import { AlertTriangle, Shield, Clock, XCircle, AlertCircle, Info } from 'lucide-react';

const SecurityAlerts = ({ alerts }) => {
  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'HIGH':
      case 'CRITICAL':
        return <XCircle className="h-5 w-5" />;
      case 'MEDIUM':
        return <AlertTriangle className="h-5 w-5" />;
      case 'LOW':
        return <AlertCircle className="h-5 w-5" />;
      default:
        return <Info className="h-5 w-5" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'HIGH':
      case 'CRITICAL':
        return 'text-danger-600 bg-danger-50';
      case 'MEDIUM':
        return 'text-warning-600 bg-warning-50';
      case 'LOW':
        return 'text-primary-600 bg-primary-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getAlertTypeDescription = (type) => {
    const descriptions = {
      'SESSION_TERMINATION': 'Session was terminated due to suspicious activity',
      'KEY_DESTRUCTION': 'Encryption keys were destroyed as a security measure',
      'PEER_ISOLATION': 'Peer has been isolated from the network',
      'REPLAY_ATTACK': 'Replay attack pattern detected in network traffic',
      'FLOOD_ATTACK': 'Network flooding attack detected',
      'SUSPICIOUS_ACTIVITY': 'Unusual network behavior observed',
      'AUTHENTICATION_FAILURE': 'Failed authentication attempt detected'
    };
    
    return descriptions[type] || 'Security event detected';
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const getActiveAlerts = () => {
    const now = Date.now();
    return alerts.filter(alert => 
      now - (alert.timestamp * 1000) < 300000 // Last 5 minutes
    );
  };

  const getRecentAlerts = () => {
    const now = Date.now();
    return alerts.filter(alert => 
      now - (alert.timestamp * 1000) < 3600000 // Last hour
    );
  };

  const activeAlerts = getActiveAlerts();
  const recentAlerts = getRecentAlerts();

  return (
    <div className="space-y-6">
      {/* Alert Summary */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <Shield className="h-6 w-6 text-primary-600" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Security Alerts</h2>
            <p className="text-sm text-gray-500">
              Real-time security monitoring and threat detection
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-danger-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-danger-600" />
              <span className="text-sm font-medium text-danger-700">Active Alerts</span>
            </div>
            <p className="text-2xl font-bold text-danger-600 mt-1">{activeAlerts.length}</p>
            <p className="text-xs text-danger-500 mt-1">Last 5 minutes</p>
          </div>
          
          <div className="bg-warning-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-warning-600" />
              <span className="text-sm font-medium text-warning-700">Recent Alerts</span>
            </div>
            <p className="text-2xl font-bold text-warning-600 mt-1">{recentAlerts.length}</p>
            <p className="text-xs text-warning-500 mt-1">Last hour</p>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <Shield className="h-5 w-5 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">Total Alerts</span>
            </div>
            <p className="text-2xl font-bold text-gray-600 mt-1">{alerts.length}</p>
            <p className="text-xs text-gray-500 mt-1">All time</p>
          </div>
        </div>
      </div>

      {/* Active Alerts */}
      {activeAlerts.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-danger-600" />
            <span>Active Security Alerts</span>
          </h3>
          
          <div className="space-y-3">
            {activeAlerts.map((alert, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border-l-4 ${
                  alert.severity === 'HIGH' || alert.severity === 'CRITICAL'
                    ? 'border-danger-500 bg-danger-50'
                    : alert.severity === 'MEDIUM'
                    ? 'border-warning-500 bg-warning-50'
                    : 'border-primary-500 bg-primary-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className={getSeverityColor(alert.severity)}>
                      {getSeverityIcon(alert.severity)}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">
                        {alert.type.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}
                      </h4>
                      <p className="text-sm text-gray-600 mt-1">
                        {getAlertTypeDescription(alert.type)}
                      </p>
                      <p className="text-sm text-gray-700 mt-2 font-medium">
                        {alert.message}
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      alert.severity === 'HIGH' || alert.severity === 'CRITICAL'
                        ? 'bg-danger-100 text-danger-800'
                        : alert.severity === 'MEDIUM'
                        ? 'bg-warning-100 text-warning-800'
                        : 'bg-primary-100 text-primary-800'
                    }`}>
                      {alert.severity}
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatTimestamp(alert.timestamp)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alert History */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Alert History</h3>
        
        {alerts.length === 0 ? (
          <div className="text-center py-8">
            <Shield className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-2">No security alerts</p>
            <p className="text-sm text-gray-400">
              The system is monitoring network traffic for suspicious activity
            </p>
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {alerts.slice().reverse().map((alert, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-full ${getSeverityColor(alert.severity)}`}>
                    {getSeverityIcon(alert.severity)}
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 text-sm">
                      {alert.type.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}
                    </h4>
                    <p className="text-xs text-gray-500">
                      {alert.message}
                    </p>
                  </div>
                </div>
                
                <div className="text-right">
                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                    alert.severity === 'HIGH' || alert.severity === 'CRITICAL'
                      ? 'bg-danger-100 text-danger-700'
                      : alert.severity === 'MEDIUM'
                      ? 'bg-warning-100 text-warning-700'
                      : 'bg-primary-100 text-primary-700'
                  }`}>
                    {alert.severity}
                  </span>
                  <p className="text-xs text-gray-400 mt-1">
                    {formatTimestamp(alert.timestamp)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Security Information */}
      <div className="alert alert-info">
        <div className="flex items-start space-x-3">
          <Info className="h-5 w-5 mt-0.5" />
          <div>
            <h4 className="font-medium">Security Monitoring</h4>
            <p className="text-sm mt-1">
              The SDN controller continuously monitors network traffic patterns to detect:
            </p>
            <ul className="text-sm mt-2 space-y-1 list-disc list-inside ml-4">
              <li>Replay attacks and suspicious timing patterns</li>
              <li>Network flooding and DoS attempts</li>
              <li>Unusual authentication behavior</li>
              <li>Progressive response triggers based on threat severity</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SecurityAlerts;