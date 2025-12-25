import React from 'react';
import { useNavigate } from 'react-router-dom';

function HomePage() {
  const navigate = useNavigate();

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'white',
      fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
      textAlign: 'center',
      padding: '2rem'
    }}>
      <h1 style={{ fontSize: '3rem', marginBottom: '1rem', fontWeight: '800' }}>
        EmailValidator
      </h1>
      <p style={{ fontSize: '1.2rem', marginBottom: '2rem', opacity: '0.9' }}>
        Professional Email Validation Platform - 2000x Faster Than Competitors
      </p>
      
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        <button 
          onClick={() => navigate('/testing')}
          style={{
            padding: '1rem 2rem',
            fontSize: '1rem',
            fontWeight: '600',
            border: 'none',
            borderRadius: '50px',
            background: 'linear-gradient(135deg, #ffd700, #ffed4e)',
            color: '#333',
            cursor: 'pointer',
            transition: 'transform 0.3s ease'
          }}
          onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
          onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
        >
          🚀 Try Demo
        </button>
        
        <button 
          onClick={() => navigate('/signup')}
          style={{
            padding: '1rem 2rem',
            fontSize: '1rem',
            fontWeight: '600',
            border: '2px solid rgba(255,255,255,0.3)',
            borderRadius: '50px',
            background: 'rgba(255,255,255,0.2)',
            color: 'white',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
          }}
          onMouseOver={(e) => {
            e.target.style.background = 'rgba(255,255,255,0.3)';
            e.target.style.transform = 'translateY(-2px)';
          }}
          onMouseOut={(e) => {
            e.target.style.background = 'rgba(255,255,255,0.2)';
            e.target.style.transform = 'translateY(0)';
          }}
        >
          📧 Sign Up Free
        </button>
        
        <button 
          onClick={() => navigate('/login')}
          style={{
            padding: '1rem 2rem',
            fontSize: '1rem',
            fontWeight: '600',
            border: '2px solid rgba(255,255,255,0.5)',
            borderRadius: '50px',
            background: 'transparent',
            color: 'white',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
          }}
          onMouseOver={(e) => {
            e.target.style.background = 'white';
            e.target.style.color = '#667eea';
          }}
          onMouseOut={(e) => {
            e.target.style.background = 'transparent';
            e.target.style.color = 'white';
          }}
        >
          🔐 Login
        </button>
      </div>
      
      <div style={{ marginTop: '3rem', opacity: '0.8' }}>
        <p style={{ fontSize: '0.9rem' }}>
          ✅ 74ms validation speed • ✅ 15+ validation layers • ✅ Enterprise security
        </p>
      </div>
    </div>
  );
}

export default HomePage;