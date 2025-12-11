import React, { useState, useEffect } from 'react';
import { Mail, Shield, Zap, Database, Check, X, ChevronDown, ArrowRight, Sparkles, Lock, Globe, User, LogIn } from 'lucide-react';

function Testing() {
  const [email, setEmail] = useState('');
  const [validationResult, setValidationResult] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [openFaq, setOpenFaq] = useState(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [particles, setParticles] = useState([]);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    const newParticles = Array.from({ length: isMobile ? 15 : 30 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 4 + 2,
      duration: Math.random() * 15 + 10
    }));
    setParticles(newParticles);
  }, [isMobile]);

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePosition({
      x: ((e.clientX - rect.left) / rect.width) * 100,
      y: ((e.clientY - rect.top) / rect.height) * 100
    });
  };

  const handleValidate = () => {
    setIsValidating(true);
    setTimeout(() => {
      const isValid = email.includes('@') && email.includes('.');
      setValidationResult(isValid);
      setIsValidating(false);
    }, 1500);
  };

  const features = [
    {
      icon: <Shield className="w-10 h-10" />,
      title: "SMTP-Level Validation",
      description: "Real-time server checks to verify mailbox existence without sending emails. Connect directly to mail servers for 99.9% accuracy.",
      gradient: "linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)"
    },
    {
      icon: <Sparkles className="w-10 h-10" />,
      title: "AI-Powered Detection",
      description: "Identify temporary emails, disposables, and generic role addresses using advanced pattern recognition and machine learning.",
      gradient: "linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)"
    },
    {
      icon: <Globe className="w-10 h-10" />,
      title: "Global DNS Network",
      description: "Comprehensive validation covering format, domain records, and MX entries across worldwide DNS infrastructure.",
      gradient: "linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)"
    },
    {
      icon: <Database className="w-10 h-10" />,
      title: "Enterprise Scale",
      description: "Process millions of emails with CSV import, real-time API, and detailed analytics dashboards for your team.",
      gradient: "linear-gradient(135deg, #10b981 0%, #059669 100%)"
    }
  ];

  const faqs = [
    {
      q: "What checks does the validator perform?",
      a: "We perform syntax validation, DNS/MX record checks, SMTP verification, and detect disposable/role-based emails using advanced AI algorithms."
    },
    {
      q: "Do you store emails?",
      a: "No. We process emails in real-time and don't store any personal data. Your privacy is our priority and we're fully GDPR compliant."
    },
    {
      q: "How accurate is the SMTP check?",
      a: "Our SMTP validation achieves 99.9% accuracy by connecting to mail servers and verifying mailbox existence in real-time."
    }
  ];

  return (
    <div style={{ background: 'linear-gradient(180deg, #f8fafc 0%, #ffffff 50%, #f1f5f9 100%)', color: '#1e293b', minHeight: '100vh', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      
      {/* Navigation Bar */}
      <nav style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(226, 232, 240, 0.8)',
        padding: '12px 0'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          {/* Logo */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            fontSize: '1.5rem',
            fontWeight: '700',
            color: '#1e293b'
          }}>
            <Mail style={{ width: '32px', height: '32px', color: '#3b82f6' }} />
            <span>EmailValidator</span>
            <span style={{
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontSize: '0.75rem',
              fontWeight: '600',
              padding: '2px 8px',
              border: '1px solid #e2e8f0',
              borderRadius: '12px',
              marginLeft: '8px'
            }}>
              PRO
            </span>
          </div>

          {/* Navigation Links */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '32px'
          }}>
            <a href="#features" style={{
              color: '#64748b',
              textDecoration: 'none',
              fontWeight: '500',
              transition: 'color 0.2s'
            }}>Features</a>
            <a href="#pricing" style={{
              color: '#64748b',
              textDecoration: 'none',
              fontWeight: '500',
              transition: 'color 0.2s'
            }}>Pricing</a>
            <a href="#api" style={{
              color: '#64748b',
              textDecoration: 'none',
              fontWeight: '500',
              transition: 'color 0.2s'
            }}>API</a>

            {/* Auth Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <button 
                onClick={() => window.location.href = '/login'}
                style={{
                  background: 'transparent',
                  border: '1px solid #e2e8f0',
                  color: '#64748b',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.9rem',
                  fontWeight: '500',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.target.style.borderColor = '#3b82f6';
                  e.target.style.color = '#3b82f6';
                }}
                onMouseOut={(e) => {
                  e.target.style.borderColor = '#e2e8f0';
                  e.target.style.color = '#64748b';
                }}
              >
                <LogIn style={{ width: '16px', height: '16px' }} />
                Login
              </button>
              
              <button 
                onClick={() => window.location.href = '/signup'}
                style={{
                  background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                  border: 'none',
                  color: 'white',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.9rem',
                  fontWeight: '500',
                  transition: 'all 0.2s',
                  boxShadow: '0 2px 4px rgba(59, 130, 246, 0.3)'
                }}
                onMouseOver={(e) => {
                  e.target.style.transform = 'translateY(-1px)';
                  e.target.style.boxShadow = '0 4px 8px rgba(59, 130, 246, 0.4)';
                }}
                onMouseOut={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 2px 4px rgba(59, 130, 246, 0.3)';
                }}
              >
                <User style={{ width: '16px', height: '16px' }} />
                Sign Up
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section 
        onMouseMove={handleMouseMove}
        style={{ 
          minHeight: '100vh', 
          display: 'flex', 
          alignItems: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          position: 'relative',
          overflow: 'hidden',
          paddingTop: '80px'
        }}
      >
        <div style={{
          position: 'absolute',
          top: '-50%',
          left: '-50%',
          width: '200%',
          height: '200%',
          background: 'radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.2) 0%, transparent 50%)',
          animation: 'rotate 20s linear infinite',
          pointerEvents: 'none'
        }} />

        {particles.map(particle => (
          <div
            key={particle.id}
            style={{
              position: 'absolute',
              left: `${particle.x}%`,
              top: `${particle.y}%`,
              width: `${particle.size}px`,
              height: `${particle.size}px`,
              borderRadius: '50%',
              background: 'rgba(255, 255, 255, 0.6)',
              animation: `float ${particle.duration}s ease-in-out infinite`,
              animationDelay: `${particle.id * 0.1}s`,
              boxShadow: '0 0 10px rgba(255, 255, 255, 0.5)'
            }}
          />
        ))}

        <div style={{
          position: 'absolute',
          width: '600px',
          height: '600px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 70%)',
          top: `${mousePosition.y}%`,
          left: `${mousePosition.x}%`,
          transform: 'translate(-50%, -50%)',
          transition: 'all 0.3s ease',
          pointerEvents: 'none'
        }} />
        
        <div style={{ 
          maxWidth: '1400px', 
          margin: '0 auto', 
          padding: '2rem',
          position: 'relative',
          zIndex: 1,
          width: '100%'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1.2fr 1fr', gap: isMobile ? '3rem' : '6rem', alignItems: 'center' }}>
            <div>
              <div style={{
                display: 'inline-block',
                padding: '0.5rem 1.5rem',
                background: 'rgba(255, 255, 255, 0.25)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '50px',
                marginBottom: '2rem',
                fontSize: '0.875rem',
                fontWeight: '600',
                color: '#fff',
                animation: 'slideDown 0.6s ease-out',
                boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)'
              }}>
                <Sparkles style={{ width: '14px', height: '14px', display: 'inline', marginRight: '0.5rem' }} />
                Trusted by 10,000+ businesses worldwide
              </div>

              <h1 style={{ 
                fontSize: isMobile ? '2.5rem' : '5rem', 
                fontWeight: '900', 
                marginBottom: '1.5rem',
                lineHeight: '1.1',
                letterSpacing: '-0.02em',
                animation: 'slideUp 0.8s ease-out',
                color: '#fff',
                textShadow: '0 2px 20px rgba(0, 0, 0, 0.2)'
              }}>
                Email Verification
                <br />
                <span style={{ 
                  background: 'linear-gradient(135deg, #fff 0%, rgba(255, 255, 255, 0.8) 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}>
                  That Actually Works
                </span>
              </h1>
              
              <p style={{ 
                fontSize: isMobile ? '1.1rem' : '1.5rem', 
                color: 'rgba(255, 255, 255, 0.95)', 
                marginBottom: '3rem',
                lineHeight: '1.6',
                maxWidth: '600px',
                animation: 'slideUp 1s ease-out',
                textShadow: '0 1px 10px rgba(0, 0, 0, 0.1)'
              }}>
                Stop wasting money on invalid emails. Our AI-powered validation ensures every email reaches a real inbox.
              </p>

              <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: '1.5rem', alignItems: isMobile ? 'stretch' : 'center', marginBottom: '3rem', animation: 'slideUp 1.2s ease-out' }}>
                <button 
                  style={{
                    background: '#fff',
                    color: '#667eea',
                    border: 'none',
                    padding: '1.25rem 2.5rem',
                    fontSize: '1.125rem',
                    borderRadius: '14px',
                    cursor: 'pointer',
                    fontWeight: '700',
                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.2)',
                    transition: 'all 0.3s',
                    position: 'relative'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.transform = 'translateY(-2px) scale(1.02)';
                    e.target.style.boxShadow = '0 15px 40px rgba(0, 0, 0, 0.3)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.transform = 'translateY(0) scale(1)';
                    e.target.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.2)';
                  }}
                >
                  Start Free Trial →
                </button>
                <a href="#api" style={{ 
                  color: '#fff', 
                  textDecoration: 'none', 
                  fontSize: '1.125rem', 
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s',
                  textShadow: '0 1px 10px rgba(0, 0, 0, 0.2)'
                }}>
                  View API Docs
                  <ArrowRight style={{ width: '18px', height: '18px' }} />
                </a>
              </div>

              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', 
                gap: '2rem',
                animation: 'slideUp 1.4s ease-out'
              }}>
                {[
                  { value: '99.9%', label: 'Accuracy Rate' },
                  { value: '<100ms', label: 'Avg Response' },
                  { value: '50M+', label: 'Emails Validated' }
                ].map((stat, idx) => (
                  <div key={idx}>
                    <div style={{ fontSize: '2rem', fontWeight: '800', color: '#fff', marginBottom: '0.25rem', textShadow: '0 2px 10px rgba(0, 0, 0, 0.2)' }}>
                      {stat.value}
                    </div>
                    <div style={{ fontSize: '0.875rem', color: 'rgba(255, 255, 255, 0.9)', fontWeight: '500' }}>
                      {stat.label}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Desktop decorative element */}
            {!isMobile && <div style={{ 
              position: 'relative',
              height: '600px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <div style={{
                width: '280px',
                height: '280px',
                background: 'rgba(255, 255, 255, 0.25)',
                backdropFilter: 'blur(20px)',
                borderRadius: '30% 70% 70% 30% / 30% 30% 70% 70%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                animation: 'morph 8s ease-in-out infinite, float 6s ease-in-out infinite',
                boxShadow: '0 30px 60px rgba(0, 0, 0, 0.2), inset 0 0 60px rgba(255, 255, 255, 0.1)',
                border: '2px solid rgba(255, 255, 255, 0.3)',
                position: 'relative'
              }}>
                <Mail style={{ width: '120px', height: '120px', color: '#fff', position: 'relative', zIndex: 1, filter: 'drop-shadow(0 10px 20px rgba(0, 0, 0, 0.2))' }} />
              </div>

              {[
                { icon: <Sparkles style={{ width: '16px', height: '16px' }} />, text: 'Free Trial', top: '10%', left: '5%' },
                { icon: <Zap style={{ width: '16px', height: '16px' }} />, text: 'Instant Results', top: '20%', right: '5%' },
                { icon: <Check style={{ width: '16px', height: '16px' }} />, text: 'No Signup', bottom: '15%', left: '10%' }
              ].map((badge, idx) => (
                <div
                  key={idx}
                  style={{
                    position: 'absolute',
                    ...badge,
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.5)',
                    borderRadius: '50px',
                    padding: '0.75rem 1.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: '#667eea',
                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.15)',
                    animation: `float ${3 + idx}s ease-in-out infinite`
                  }}
                >
                  {badge.icon}
                  {badge.text}
                </div>
              ))}
            </div>}

            {/* Mobile decorative element */}
            {isMobile && <div style={{ 
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              padding: '3rem 1rem',
              marginTop: '2rem'
            }}>
              {/* Floating rings */}
              <div style={{
                position: 'absolute',
                width: '280px',
                height: '280px',
                borderRadius: '50%',
                border: '2px solid rgba(255, 255, 255, 0.2)',
                animation: 'rotate 20s linear infinite'
              }}>
                <div style={{
                  position: 'absolute',
                  top: '-8px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: '16px',
                  height: '16px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #fff, rgba(255, 255, 255, 0.8))',
                  boxShadow: '0 4px 15px rgba(255, 255, 255, 0.5)'
                }} />
              </div>
              
              <div style={{
                position: 'absolute',
                width: '220px',
                height: '220px',
                borderRadius: '50%',
                border: '2px solid rgba(255, 255, 255, 0.15)',
                animation: 'rotate 15s linear infinite reverse'
              }}>
                <div style={{
                  position: 'absolute',
                  bottom: '-8px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: '16px',
                  height: '16px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #fff, rgba(255, 255, 255, 0.8))',
                  boxShadow: '0 4px 15px rgba(255, 255, 255, 0.5)'
                }} />
              </div>

              {/* Main icon container */}
              <div style={{
                position: 'relative',
                width: '160px',
                height: '160px',
                background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.15))',
                backdropFilter: 'blur(20px)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 25px 50px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.5)',
                border: '2px solid rgba(255, 255, 255, 0.4)',
                animation: 'float 4s ease-in-out infinite',
                zIndex: 1
              }}>
                <div style={{
                  position: 'absolute',
                  inset: '-20px',
                  background: 'radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 70%)',
                  borderRadius: '50%',
                  filter: 'blur(20px)',
                  animation: 'pulse 3s ease-in-out infinite'
                }} />
                <Mail style={{ 
                  width: '70px', 
                  height: '70px', 
                  color: '#fff', 
                  filter: 'drop-shadow(0 8px 20px rgba(0, 0, 0, 0.3))',
                  position: 'relative',
                  zIndex: 1
                }} />
              </div>

              {/* Feature cards */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '0.75rem',
                marginTop: '2.5rem',
                width: '100%',
                maxWidth: '340px'
              }}>
                {[
                  { icon: <Sparkles style={{ width: '18px', height: '18px' }} />, text: 'Free', label: 'Trial', gradient: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' },
                  { icon: <Check style={{ width: '18px', height: '18px' }} />, text: 'No', label: 'Signup', gradient: 'linear-gradient(135deg, #10b981, #059669)' },
                  { icon: <Zap style={{ width: '18px', height: '18px' }} />, text: 'Instant', label: 'Results', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)' }
                ].map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'rgba(255, 255, 255, 0.95)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(255, 255, 255, 0.5)',
                      borderRadius: '16px',
                      padding: '1rem 0.5rem',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '0.5rem',
                      boxShadow: '0 8px 20px rgba(0, 0, 0, 0.15)',
                      animation: `slideUp ${0.6 + idx * 0.1}s ease-out`
                    }}
                  >
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '10px',
                      background: item.gradient,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#fff',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)'
                    }}>
                      {item.icon}
                    </div>
                    <div style={{
                      fontSize: '0.95rem',
                      fontWeight: '800',
                      color: '#1e293b'
                    }}>
                      {item.text}
                    </div>
                    <div style={{
                      fontSize: '0.7rem',
                      fontWeight: '600',
                      color: '#64748b'
                    }}>
                      {item.label}
                    </div>
                  </div>
                ))}
              </div>
            </div>}
          </div>
        </div>
      </section>

      {/* Trust Indicators */}
      <section style={{ 
        padding: isMobile ? '3rem 1rem' : '4rem 2rem',
        background: 'linear-gradient(180deg, #f8fafc 0%, #e0e7ff 100%)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{
          position: 'absolute',
          top: '0',
          left: '0',
          right: '0',
          bottom: '0',
          backgroundImage: 'radial-gradient(circle at 20% 50%, rgba(139, 92, 246, 0.08) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.08) 0%, transparent 50%)',
          pointerEvents: 'none'
        }} />
        <div style={{ 
          maxWidth: '1400px', 
          margin: '0 auto',
          display: 'grid',
          gridTemplateColumns: isMobile ? '1fr' : 'repeat(5, 1fr)',
          gap: isMobile ? '1rem' : '2rem',
          position: 'relative',
          zIndex: 1
        }}>
          {[
            { value: '99.9%', label: 'Accuracy', icon: <Check style={{ width: '24px', height: '24px' }} />, color: '#10b981', gradient: 'linear-gradient(135deg, #10b981, #059669)' },
            { value: '<100ms', label: 'Response Time', icon: <Zap style={{ width: '24px', height: '24px' }} />, color: '#f59e0b', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)' },
            { value: 'GDPR', label: 'Compliant', icon: <Lock style={{ width: '24px', height: '24px' }} />, color: '#3b82f6', gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)' },
            { value: '24/7', label: 'Support', icon: <Shield style={{ width: '24px', height: '24px' }} />, color: '#8b5cf6', gradient: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' },
            { value: '10K+', label: 'Customers', icon: <Sparkles style={{ width: '24px', height: '24px' }} />, color: '#ec4899', gradient: 'linear-gradient(135deg, #ec4899, #db2777)' }
          ].map((item, idx) => (
            <div 
              key={idx} 
              style={{ 
                textAlign: 'center',
                padding: '2rem 1.5rem',
                background: 'rgba(255, 255, 255, 0.8)',
                backdropFilter: 'blur(10px)',
                borderRadius: '20px',
                border: '1px solid rgba(255, 255, 255, 0.5)',
                transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                boxShadow: '0 4px 15px rgba(0, 0, 0, 0.05)',
                animation: `slideUp ${0.6 + idx * 0.1}s ease-out`
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px) scale(1.02)';
                e.currentTarget.style.boxShadow = `0 20px 40px ${item.color}30`;
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.95)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0) scale(1)';
                e.currentTarget.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.05)';
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.8)';
              }}
            >
              <div style={{ 
                width: '56px',
                height: '56px',
                margin: '0 auto 1rem',
                borderRadius: '14px',
                background: item.gradient,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                boxShadow: `0 8px 20px ${item.color}40`
              }}>
                {item.icon}
              </div>
              <div style={{ fontSize: '2.25rem', fontWeight: '800', color: '#1e293b', marginBottom: '0.5rem' }}>
                {item.value}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#64748b', fontWeight: '600' }}>
                {item.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Live Demo */}
      <section style={{ 
        padding: isMobile ? '4rem 1rem' : '8rem 2rem', 
        background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%)', 
        position: 'relative', 
        overflow: 'hidden' 
      }}>
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255, 255, 255, 0.1) 1px, transparent 0)',
          backgroundSize: '40px 40px',
          opacity: 0.3
        }} />
        <div style={{
          position: 'absolute',
          top: '10%',
          right: '10%',
          width: '400px',
          height: '400px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%)',
          filter: 'blur(60px)'
        }} />
        <div style={{
          position: 'absolute',
          bottom: '10%',
          left: '10%',
          width: '400px',
          height: '400px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, transparent 70%)',
          filter: 'blur(60px)'
        }} />
        
        <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <div style={{
            display: 'inline-block',
            padding: '0.5rem 1.5rem',
            background: 'rgba(255, 255, 255, 0.15)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '50px',
            marginBottom: '2rem',
            fontSize: '0.875rem',
            fontWeight: '600',
            color: '#fff',
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.2)'
          }}>
            ⚡ Live Demo
          </div>

          <h2 style={{ 
            fontSize: isMobile ? '2rem' : '3.5rem', 
            fontWeight: '900', 
            marginBottom: '1rem',
            letterSpacing: '-0.02em',
            color: '#fff',
            textShadow: '0 2px 20px rgba(0, 0, 0, 0.3)'
          }}>
            Try It Right Now
          </h2>
          <p style={{ 
            fontSize: isMobile ? '1rem' : '1.25rem', 
            color: 'rgba(255, 255, 255, 0.9)', 
            marginBottom: '4rem', 
            maxWidth: '600px', 
            margin: '0 auto 4rem',
            textShadow: '0 1px 10px rgba(0, 0, 0, 0.2)'
          }}>
            See instant validation results. No signup required.
          </p>
          
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: '24px',
            padding: '3rem',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            boxShadow: '0 25px 50px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
          }}>
            <div style={{ marginBottom: '2rem' }}>
              <div style={{ position: 'relative' }}>
                <input
                  type="email"
                  placeholder="Enter any email address..."
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && email && !isValidating && handleValidate()}
                  style={{
                    width: '100%',
                    padding: isMobile ? '1.25rem 1.25rem 1.25rem 3rem' : '1.5rem 1.5rem 1.5rem 3.5rem',
                    fontSize: isMobile ? '16px' : '1.125rem',
                    borderRadius: '16px',
                    border: '2px solid #e2e8f0',
                    background: '#fff',
                    color: '#1e293b',
                    outline: 'none',
                    marginBottom: '1.5rem',
                    transition: 'all 0.2s',
                    boxSizing: 'border-box'
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#667eea';
                    e.target.style.boxShadow = '0 0 0 4px rgba(102, 126, 234, 0.1)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = '#e2e8f0';
                    e.target.style.boxShadow = 'none';
                  }}
                />
                <Mail style={{
                  position: 'absolute',
                  left: '1.25rem',
                  top: '1.5rem',
                  width: '20px',
                  height: '20px',
                  color: '#94a3b8'
                }} />
              </div>
              
              <button
                onClick={handleValidate}
                disabled={!email || isValidating}
                style={{
                  width: '100%',
                  background: email && !isValidating ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#e2e8f0',
                  color: email && !isValidating ? '#fff' : '#94a3b8',
                  border: 'none',
                  padding: '1.5rem',
                  fontSize: '1.125rem',
                  borderRadius: '16px',
                  cursor: email && !isValidating ? 'pointer' : 'not-allowed',
                  fontWeight: '700',
                  transition: 'all 0.3s',
                  boxShadow: email && !  isValidating ? '0 10px 30px rgba(102, 126, 234, 0.3)' : 'none'
                }}
                onMouseEnter={(e) => {
                  if (email && !isValidating) {
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 15px 40px rgba(102, 126, 234, 0.4)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = email && !isValidating ? '0 10px 30px rgba(102, 126, 234, 0.3)' : 'none';
                }}
              >
                {isValidating ? 'Validating...' : 'Validate Email →'}
              </button>
            </div>

            {validationResult !== null && (
              <div style={{
                padding: '2rem',
                borderRadius: '16px',
                background: validationResult ? '#f0fdf4' : '#fef2f2',
                border: `2px solid ${validationResult ? '#86efac' : '#fca5a5'}`,
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                animation: 'slideUp 0.3s ease-out'
              }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '12px',
                  background: validationResult ? '#dcfce7' : '#fee2e2',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  {validationResult ? (
                    <Check style={{ width: '28px', height: '28px', color: '#16a34a' }} />
                  ) : (
                    <X style={{ width: '28px', height: '28px', color: '#dc2626' }} />
                  )}
                </div>
                <div style={{ textAlign: 'left', flex: 1 }}>
                  <div style={{ 
                    color: validationResult ? '#16a34a' : '#dc2626', 
                    fontWeight: '700',
                    fontSize: '1.125rem',
                    marginBottom: '0.25rem'
                  }}>
                    {validationResult ? 'Valid Email Address' : 'Invalid Email Address'}
                  </div>
                  <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                    {validationResult ? 'This email passed all validation checks' : 'This email failed our validation checks'}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ 
        padding: isMobile ? '4rem 1rem' : '8rem 2rem', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)', 
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Animated gradient orbs */}
        <div style={{
          position: 'absolute',
          top: '10%',
          left: '5%',
          width: '400px',
          height: '400px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 70%)',
          filter: 'blur(60px)',
          animation: 'float 10s ease-in-out infinite'
        }} />
        <div style={{
          position: 'absolute',
          bottom: '10%',
          right: '5%',
          width: '500px',
          height: '500px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(240, 147, 251, 0.4) 0%, transparent 70%)',
          filter: 'blur(80px)',
          animation: 'float 12s ease-in-out infinite reverse'
        }} />
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '600px',
          height: '600px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(118, 75, 162, 0.2) 0%, transparent 70%)',
          filter: 'blur(100px)',
          animation: 'pulse 8s ease-in-out infinite'
        }} />
        {/* Grid pattern overlay */}
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px)',
          backgroundSize: '50px 50px',
          pointerEvents: 'none',
          opacity: 0.5
        }} />
        <div style={{ maxWidth: '1400px', margin: '0 auto', position: 'relative', zIndex: 1 }}>
          <div style={{ textAlign: 'center', marginBottom: '5rem' }}>
            <div style={{
              display: 'inline-block',
              padding: '0.5rem 1.5rem',
              background: 'rgba(255, 255, 255, 0.25)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '50px',
              marginBottom: '2rem',
              fontSize: '0.875rem',
              fontWeight: '600',
              color: '#fff',
              boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)'
            }}>
              ✨ Features
            </div>
            <h2 style={{ 
              fontSize: isMobile ? '2rem' : '3.5rem', 
              fontWeight: '900',
              marginBottom: '1rem',
              letterSpacing: '-0.02em',
              color: '#fff',
              textShadow: '0 2px 20px rgba(0, 0, 0, 0.2)'
            }}>
              Everything You Need
            </h2>
            <p style={{ 
              fontSize: isMobile ? '1rem' : '1.25rem', 
              color: 'rgba(255, 255, 255, 0.95)', 
              maxWidth: '600px', 
              margin: '0 auto',
              textShadow: '0 1px 10px rgba(0, 0, 0, 0.1)'
            }}>
              Built for developers, designed for scale
            </p>
          </div>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
            gap: isMobile ? '1.5rem' : '2rem'
          }}>
            {features.map((feature, idx) => (
              <div
                key={idx}
                style={{
                  padding: isMobile ? '2rem' : '3rem',
                  background: 'rgba(255, 255, 255, 0.9)',
                  backdropFilter: 'blur(20px)',
                  borderRadius: '28px',
                  border: '2px solid rgba(255, 255, 255, 0.8)',
                  transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: '0 10px 40px rgba(0, 0, 0, 0.08)',
                  animation: `slideUp ${0.6 + idx * 0.15}s ease-out`
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-12px) scale(1.03)';
                  e.currentTarget.style.boxShadow = '0 35px 70px rgba(0, 0, 0, 0.2)';
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 1)';
                  e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0) scale(1)';
                  e.currentTarget.style.boxShadow = '0 10px 40px rgba(0, 0, 0, 0.08)';
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.9)';
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.8)';
                }}
              >
                <div style={{
                  position: 'absolute',
                  top: '-50px',
                  right: '-50px',
                  width: '150px',
                  height: '150px',
                  borderRadius: '50%',
                  background: feature.gradient,
                  opacity: 0.1,
                  filter: 'blur(40px)',
                  pointerEvents: 'none'
                }} />
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: '5px',
                  background: feature.gradient
                }} />
                <div style={{ position: 'relative', display: 'inline-block', marginBottom: '1.5rem' }}>
                  <div style={{
                    position: 'absolute',
                    inset: '-8px',
                    borderRadius: '20px',
                    background: feature.gradient,
                    opacity: 0.2,
                    filter: 'blur(15px)',
                    animation: 'pulse 3s ease-in-out infinite'
                  }} />
                  <div style={{
                    width: isMobile ? '64px' : '80px',
                    height: isMobile ? '64px' : '80px',
                    borderRadius: '20px',
                    background: feature.gradient,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fff',
                    boxShadow: '0 15px 35px rgba(0, 0, 0, 0.25)',
                    position: 'relative',
                    transform: 'rotate(-5deg)',
                    transition: 'transform 0.3s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.transform = 'rotate(0deg) scale(1.1)'}
                  onMouseLeave={(e) => e.currentTarget.style.transform = 'rotate(-5deg) scale(1)'}
                  >
                    {feature.icon}
                  </div>
                </div>
                <h3 style={{ fontSize: isMobile ? '1.5rem' : '1.85rem', fontWeight: '800', marginBottom: '1rem', color: '#1e293b', lineHeight: '1.2' }}>
                  {feature.title}
                </h3>
                <p style={{ fontSize: isMobile ? '0.95rem' : '1.05rem', color: '#64748b', lineHeight: '1.7', marginBottom: '1.5rem' }}>
                  {feature.description}
                </p>
                <div style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  color: '#8b5cf6',
                  fontWeight: '600',
                  fontSize: '0.95rem',
                  cursor: 'pointer',
                  transition: 'gap 0.3s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.gap = '0.75rem'}
                onMouseLeave={(e) => e.currentTarget.style.gap = '0.5rem'}
                >
                  Learn more
                  <ArrowRight style={{ width: '16px', height: '16px' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section style={{ 
        padding: isMobile ? '4rem 1rem' : '8rem 2rem', 
        background: 'linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(circle at 80% 20%, rgba(59, 130, 246, 0.1) 0%, transparent 50%)',
          pointerEvents: 'none'
        }} />
        <div style={{ maxWidth: '900px', margin: '0 auto', position: 'relative', zIndex: 1 }}>
          <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
            <div style={{
              display: 'inline-block',
              padding: '0.5rem 1.5rem',
              background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
              borderRadius: '50px',
              marginBottom: '2rem',
              fontSize: '0.875rem',
              fontWeight: '600',
              color: '#fff',
              boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)'
            }}>
              💬 FAQ
            </div>
            <h2 style={{ 
              fontSize: isMobile ? '2rem' : '3.5rem', 
              fontWeight: '900',
              marginBottom: '1rem',
              letterSpacing: '-0.02em',
              color: '#1e293b'
            }}>
              Common Questions
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {faqs.map((faq, idx) => (
              <div
                key={idx}
                style={{
                  background: 'rgba(255, 255, 255, 0.8)',
                  backdropFilter: 'blur(10px)',
                  borderRadius: '16px',
                  border: '1px solid rgba(255, 255, 255, 0.5)',
                  overflow: 'hidden',
                  transition: 'all 0.3s',
                  boxShadow: '0 4px 15px rgba(0, 0, 0, 0.05)',
                  animation: `slideUp ${0.6 + idx * 0.1}s ease-out`
                }}
              >
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  style={{
                    width: '100%',
                    padding: '1.5rem 2rem',
                    background: 'transparent',
                    border: 'none',
                    color: '#1e293b',
                    fontSize: '1.125rem',
                    fontWeight: '600',
                    textAlign: 'left',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  {faq.q}
                  <ChevronDown 
                    style={{ 
                      width: '20px', 
                      height: '20px',
                      transition: 'transform 0.3s',
                      transform: openFaq === idx ? 'rotate(180deg)' : 'rotate(0deg)',
                      color: '#667eea'
                    }} 
                  />
                </button>
                {openFaq === idx && (
                  <div style={{
                    padding: '0 2rem 1.5rem 2rem',
                    color: '#64748b',
                    fontSize: '1rem',
                    lineHeight: '1.6',
                    animation: 'slideDown 0.3s ease-out'
                  }}>
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section style={{ 
        padding: isMobile ? '4rem 1rem' : '8rem 2rem', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255, 255, 255, 0.15) 1px, transparent 0)',
          backgroundSize: '50px 50px',
          opacity: 0.4
        }} />
        <div style={{
          position: 'absolute',
          top: '20%',
          left: '10%',
          width: '300px',
          height: '300px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255, 255, 255, 0.2) 0%, transparent 70%)',
          filter: 'blur(60px)',
          animation: 'float 8s ease-in-out infinite'
        }} />
        <div style={{
          position: 'absolute',
          bottom: '20%',
          right: '10%',
          width: '300px',
          height: '300px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255, 255, 255, 0.2) 0%, transparent 70%)',
          filter: 'blur(60px)',
          animation: 'float 6s ease-in-out infinite reverse'
        }} />
        <div style={{ 
          maxWidth: '900px', 
          margin: '0 auto', 
          textAlign: 'center',
          position: 'relative',
          zIndex: 1
        }}>
          <h2 style={{ 
            fontSize: isMobile ? '2.25rem' : '4rem', 
            fontWeight: '900',
            marginBottom: '1.5rem',
            letterSpacing: '-0.02em',
            color: '#fff',
            textShadow: '0 2px 20px rgba(0, 0, 0, 0.2)'
          }}>
            Ready to Get Started?
          </h2>
          <p style={{ fontSize: isMobile ? '1.1rem' : '1.5rem', color: 'rgba(255, 255, 255, 0.95)', marginBottom: '3rem', maxWidth: '600px', margin: '0 auto 3rem', textShadow: '0 1px 10px rgba(0, 0, 0, 0.2)' }}>
            Join thousands of businesses using our email validation API
          </p>
          
          <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: '1.5rem', justifyContent: 'center', alignItems: isMobile ? 'stretch' : 'center' }}>
            <button 
              style={{
                background: '#fff',
                color: '#667eea',
                border: 'none',
                padding: '1.25rem 2.5rem',
                fontSize: '1.125rem',
                borderRadius: '14px',
                cursor: 'pointer',
                fontWeight: '700',
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.2)',
                transition: 'all 0.3s'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px) scale(1.02)';
                e.target.style.boxShadow = '0 15px 40px rgba(0, 0, 0, 0.3)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0) scale(1)';
                e.target.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.2)';
              }}
            >
              Start Free Trial →
            </button>
            <a href="#contact" style={{ 
              color: '#fff', 
              textDecoration: 'none', 
              fontSize: '1.125rem', 
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              Contact Sales
              <ArrowRight style={{ width: '18px', height: '18px' }} />
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ 
        padding: '3rem 2rem', 
        background: '#fff',
        borderTop: '1px solid #e2e8f0',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
            © 2024 Email Validator. Built with ❤️ for developers.
          </p>
        </div>
      </footer>

      <style>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes rotate {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-20px);
          }
        }

        @keyframes morph {
          0%, 100% {
            border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%;
          }
          25% {
            border-radius: 58% 42% 75% 25% / 76% 46% 54% 24%;
          }
          50% {
            border-radius: 50% 50% 33% 67% / 55% 27% 73% 45%;
          }
          75% {
            border-radius: 33% 67% 58% 42% / 63% 68% 32% 37%;
          }
        }

        @keyframes gradient {
          0% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
          100% {
            background-position: 0% 50%;
          }
        }

        @keyframes pulse {
          0%, 100% {
            opacity: 0.6;
            transform: scale(1);
          }
          50% {
            opacity: 1;
            transform: scale(1.1);
          }
        }

        /* Mobile Responsive Styles */
        @media (max-width: 768px) {
          /* Hero section adjustments */
          section > div > div {
            grid-template-columns: 1fr !important;
            gap: 3rem !important;
          }

          /* Hide decorative elements on mobile */
          section > div > div > div:last-child {
            display: none;
          }

          /* Text size adjustments */
          h1 {
            font-size: 2.5rem !important;
          }

          h2 {
            font-size: 2rem !important;
          }

          p {
            font-size: 1rem !important;
          }

          /* Trust indicators - stack vertically */
          section > div > div[style*="grid-template-columns: repeat(5, 1fr)"] {
            grid-template-columns: 1fr !important;
            gap: 1rem !important;
          }

          /* Features - single column */
          section > div > div > div[style*="grid-template-columns: repeat(2, 1fr)"] {
            grid-template-columns: 1fr !important;
            gap: 1.5rem !important;
          }

          /* Button adjustments */
          button {
            width: 100% !important;
            padding: 1rem 1.5rem !important;
            font-size: 1rem !important;
          }

          /* Flex containers */
          div[style*="display: flex"] {
            flex-direction: column !important;
            gap: 1rem !important;
          }

          /* Stats grid */
          div[style*="grid-template-columns: repeat(3, 1fr)"] {
            grid-template-columns: 1fr !important;
            gap: 1.5rem !important;
          }

          /* Padding adjustments */
          section {
            padding: 4rem 1rem !important;
          }

          /* Input fields */
          input {
            font-size: 16px !important;
          }
        }

        @media (max-width: 480px) {
          h1 {
            font-size: 2rem !important;
          }

          h2 {
            font-size: 1.75rem !important;
          }

          section {
            padding: 3rem 1rem !important;
          }
        }
      `}</style>
    </div>
  );
}

export default Testing;
