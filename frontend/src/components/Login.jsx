import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (isSubmitting) return;

    const sanitizedUsername = username.trim();
    const sanitizedPassword = password.trim();

    if (!sanitizedUsername || !sanitizedPassword) {
      setError('Credentials parameters cannot be blank.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      
      const sessionProfile = await login(sanitizedUsername, sanitizedPassword);
      
      if (sessionProfile && sessionProfile.role_details) {
        // FIXED: Dynamic landing zone mapping aligned with backend operational nodes
        const roleName = sessionProfile.role_details.name;
        
        if (roleName === 'Supervisor' || roleName === 'Admin') {
          navigate('/admin/roles', { replace: true });
        } else {
          // Default fallbacks for operational tiers (PM / Student dashboards)
          navigate('/dashboard', { replace: true });
        }
      } else {
        setError('Profile resolution structural anomaly: Missing role metadata.');
      }
    } catch (err) {
      console.error('Authentication lifecycle rejection:', err);
      setError(
        err.response?.data?.detail || 
        err.response?.data?.non_field_errors?.[0] || 
        'Invalid username or password.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', backgroundColor: '#f4f6f8', fontFamily: 'sans-serif' }}>
      <div style={{ width: '100%', maxWidth: '400px', padding: '40px', backgroundColor: '#ffffff', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '24px', color: '#1a1a1a' }}>AcademiCollab</h2>
        <p style={{ textAlign: 'center', color: '#666', fontSize: '14px', marginBottom: '24px' }}>Identity Access Portal</p>

        {error && (
          <div style={{ padding: '12px', backgroundColor: '#ffebe9', color: '#ce3c2e', border: '1px solid #ffc8c4', borderRadius: '6px', marginBottom: '20px', fontSize: '14px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 'bold', color: '#495057' }}>Username</label>
            <input
              type="text"
              value={username}
              disabled={isSubmitting}
              onChange={(e) => setUsername(e.target.value)}
              style={{ width: '100%', padding: '10px 14px', boxSizing: 'border-box', border: '1px solid #ccd0d4', borderRadius: '6px', fontSize: '14px', outline: 'none' }}
              placeholder="Enter system identifier"
              maxLength={150}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 'bold', color: '#495057' }}>Password</label>
            <input
              type="password"
              value={password}
              disabled={isSubmitting}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%', padding: '10px 14px', boxSizing: 'border-box', border: '1px solid #ccd0d4', borderRadius: '6px', fontSize: '14px', outline: 'none' }}
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: isSubmitting ? '#a5c4ff' : '#2563eb',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              transition: 'background 0.2s'
            }}
          >
            {isSubmitting ? 'Authenticating Profile...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}