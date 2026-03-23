import React, { useState, useEffect, useRef } from 'react';
import { Users, Clock, Check, X, AlertCircle } from 'lucide-react';

const ConnectionRequests = ({ peerStatus }) => {
  const [requests, setRequests] = useState([]);
  const [responding, setResponding] = useState(null);
  const containerRef = useRef(null);
  const previousScrollTop = useRef(0);

  const API_BASE = process.env.REACT_APP_PEER_API || 'http://localhost:8080';

  useEffect(() => {
    if (peerStatus.running) {
      fetchRequests();
      const interval = setInterval(fetchRequests, 2000);
      return () => clearInterval(interval);
    }
  }, [peerStatus.running]);

  const fetchRequests = async () => {
    // Save current scroll position before update
    if (containerRef.current) {
      previousScrollTop.current = containerRef.current.scrollTop;
    }

    try {
      const response = await fetch(`${API_BASE}/api/connection/requests`);
      const data = await response.json();
      setRequests(data.requests || []);
    } catch (error) {
      console.error('Failed to fetch requests:', error);
    }
  };

  // Restore scroll position after render
  useEffect(() => {
    if (containerRef.current && previousScrollTop.current > 0) {
      containerRef.current.scrollTop = previousScrollTop.current;
    }
  }, [requests]);

  const respondToRequest = async (requestId, action) => {
    setResponding(requestId);
    try {
      const response = await fetch(`${API_BASE}/api/connection/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: requestId, action })
      });
      
      const data = await response.json();
      
      if (data.status === 'accepted' || data.status === 'rejected') {
        fetchRequests(); // Refresh list
        if (data.status === 'accepted') {
          // Refresh parent component to show connected status
          window.location.reload();
        }
      } else {
        alert(`Failed to ${action} request: ${data.message}`);
      }
    } catch (error) {
      console.error(`Failed to ${action} request:`, error);
      alert(`Failed to ${action} request: Network error`);
    } finally {
      setResponding(null);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
  };

  if (!peerStatus.running) {
    return null;
  }

  return (
    <div className="space-y-4">
      {requests.length > 0 && (
        <div className="card">
          <div className="flex items-center space-x-3 mb-4">
            <AlertCircle className="h-6 w-6 text-warning-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Incoming Connection Requests
              </h3>
              <p className="text-sm text-gray-500">
                {requests.length} peer{requests.length !== 1 ? 's' : ''} want to connect
              </p>
            </div>
          </div>

          <div
            ref={containerRef}
            className="space-y-3 max-h-96 overflow-y-auto scroll-smooth"
            style={{ scrollBehavior: 'smooth' }}
          >
            {requests.map((request) => (
              <div
                key={request.id}
                className="flex items-center justify-between p-4 border border-warning-200 bg-warning-50 rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-warning-100 rounded-full flex items-center justify-center">
                    <Users className="h-5 w-5 text-warning-600" />
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900">
                      Connection Request
                    </h4>
                    <p className="text-sm text-gray-600">
                      From: {request.requester_id}
                    </p>
                    <div className="flex items-center space-x-1 text-xs text-gray-500 mt-1">
                      <Clock className="h-3 w-3" />
                      <span>Received: {formatTime(request.received_at)}</span>
                      <span>({Math.floor(request.age_seconds)}s ago)</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => respondToRequest(request.id, 'accept')}
                    disabled={responding === request.id}
                    className="flex items-center space-x-2 px-3 py-1.5 bg-success-600 text-white rounded-md text-sm font-medium hover:bg-success-700 disabled:opacity-50"
                  >
                    <Check className="h-4 w-4" />
                    <span>{responding === request.id ? 'Accepting...' : 'Accept'}</span>
                  </button>
                  
                  <button
                    onClick={() => respondToRequest(request.id, 'reject')}
                    disabled={responding === request.id}
                    className="flex items-center space-x-2 px-3 py-1.5 bg-danger-600 text-white rounded-md text-sm font-medium hover:bg-danger-700 disabled:opacity-50"
                  >
                    <X className="h-4 w-4" />
                    <span>{responding === request.id ? 'Rejecting...' : 'Reject'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectionRequests;