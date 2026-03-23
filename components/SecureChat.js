import React, { useState, useEffect, useRef } from 'react';
import { Send, Shield, Lock, LogOut, MessageCircle } from 'lucide-react';

const SecureChat = ({ peerStatus, onStatusChange }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);

  const API_BASE = process.env.REACT_APP_PEER_API || 'http://localhost:8080';

  useEffect(() => {
    fetchMessages();
    const interval = setInterval(fetchMessages, 2000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll removed - allows user to manually scroll and read chat history
  // useEffect(() => {
  //   scrollToBottom();
  // }, [messages]);

  const fetchMessages = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/peer/messages`);
      const data = await response.json();
      setMessages(data.messages || []);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      const response = await fetch(`${API_BASE}/api/peer/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: newMessage.trim() })
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        setNewMessage('');
        fetchMessages();
        // Scroll to bottom only when user sends a message
        setTimeout(() => scrollToBottom(), 100);
      } else {
        alert(`Failed to send message: ${data.message}`);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message: Network error');
    } finally {
      setSending(false);
    }
  };

  const terminateSession = async () => {
    if (!window.confirm('Are you sure you want to terminate this secure session?')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/peer/terminate`, { method: 'POST' });
      const data = await response.json();
      
      if (data.status === 'success') {
        onStatusChange();
      }
    } catch (error) {
      console.error('Failed to terminate session:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
  };

  return (
    <div className="space-y-6">
      {/* Session Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-success-100 rounded-full flex items-center justify-center">
              <Shield className="h-6 w-6 text-success-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Secure Session Active</h2>
              <p className="text-sm text-gray-500">
                End-to-end encrypted • Anonymous • Session-only
              </p>
            </div>
          </div>
          
          <button
            onClick={terminateSession}
            className="flex items-center space-x-2 btn-danger"
          >
            <LogOut className="h-4 w-4" />
            <span>End Session</span>
          </button>
        </div>

        {/* Security Indicators */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="bg-success-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <Lock className="h-5 w-5 text-success-600" />
              <span className="text-sm font-medium text-success-700">Encryption</span>
            </div>
            <p className="text-sm text-success-600 mt-1">AES-256 Active</p>
          </div>
          
          <div className="bg-primary-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <Shield className="h-5 w-5 text-primary-600" />
              <span className="text-sm font-medium text-primary-700">Identity</span>
            </div>
            <p className="text-sm text-primary-600 mt-1">Anonymous</p>
          </div>
          
          <div className="bg-warning-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <MessageCircle className="h-5 w-5 text-warning-600" />
              <span className="text-sm font-medium text-warning-700">Storage</span>
            </div>
            <p className="text-sm text-warning-600 mt-1">No History Saved</p>
          </div>
        </div>
      </div>

      {/* Chat Interface */}
      <div className="card">
        <div className="flex flex-col h-96">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 rounded-lg">
            {messages.length === 0 ? (
              <div className="text-center py-8">
                <MessageCircle className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No messages yet. Start the conversation!</p>
                <p className="text-xs text-gray-400 mt-2">
                  All messages are encrypted and will be deleted when the session ends
                </p>
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.type === 'sent' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.type === 'sent'
                        ? 'bg-primary-600 text-white'
                        : 'bg-white text-gray-900 border border-gray-200'
                    }`}
                  >
                    <p className="text-sm">{message.content}</p>
                    <div className="flex items-center justify-between mt-1">
                      <span
                        className={`text-xs ${
                          message.type === 'sent' ? 'text-primary-100' : 'text-gray-400'
                        }`}
                      >
                        {formatTimestamp(message.timestamp)}
                      </span>
                      {message.encrypted && (
                        <Lock
                          className={`h-3 w-3 ${
                            message.type === 'sent' ? 'text-primary-200' : 'text-gray-400'
                          }`}
                        />
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input */}
          <form onSubmit={sendMessage} className="mt-4">
            <div className="flex space-x-3">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type your encrypted message..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                disabled={sending}
              />
              <button
                type="submit"
                disabled={!newMessage.trim() || sending}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md font-medium transition-colors ${
                  !newMessage.trim() || sending
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'btn-primary'
                }`}
              >
                <Send className="h-4 w-4" />
                <span>{sending ? 'Sending...' : 'Send'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Security Notice */}
      <div className="alert alert-warning">
        <div className="flex items-start space-x-3">
          <Shield className="h-5 w-5 mt-0.5" />
          <div>
            <h4 className="font-medium">Security Notice</h4>
            <p className="text-sm mt-1">
              This session is monitored by the SDN security controller for attack detection. 
              Message content remains encrypted and private. All chat history will be 
              permanently deleted when the session ends.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SecureChat;