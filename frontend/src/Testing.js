import React, { useState, useEffect } from 'react';
import { Mail, Shield, Zap, Database, Check, X, ChevronDown, ArrowRight, Sparkles, Lock, Globe } from 'lucide-react';

function Testing() {
  const [email, setEmail] = useState('');
  const [validationResult, setValidationResult] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [openFaq, setOpenFaq] = useState(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    const newParticles = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      duration: Math.random() * 20 + 10
    }));
    setParticles(newParticles);
  }, []);

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
      color: "from-cyan-500 to-blue-500"
    },
    {
      icon: <Sparkles className="w-10 h-10" />,
      title: "AI-Powered Detection",
      description: "Identify temporary emails, disposables, and generic role addresses using advanced pattern recognition and machine learning.",
      color: "from-purple-500 to-pink-500"
    },
    {
      icon: <Globe className="w-10 h-10" />,
      title: "Global DNS Network",
      description: "Comprehensive validation covering format, domain records, and MX entries across worldwide DNS infrastructure.",
      color: "from-orange-500 to-red-500"
    },
    {
      icon: <Database className="w-10 h-10" />,
      title: "Enterprise Scale",
      description: "Process millions of emails with CSV import, real-time API, and detailed analytics dashboards for your team.",
      color: "from-green-500 to-emerald-500"
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
    <div style={{ background: '#000', color: '#fff', minHeight: '100vh', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* Hero Section */}
      <section 
        onMouseMove={handleMouseMove}
        style={{ 
          minHeight: '100vh', 
          display: 'flex', 
          alignItems: 'center',
          background: '#000',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <div style={{
          position: 'absolute',
          top: '-50%',
          left: '-50%',
          width: '200%',
          height: '200%',
          background: 'radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.15) 0%, transparent 50%)',
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
              background: 'rgba(139, 92, 246, 0.5)',
              animation: `float ${particle.duration}s ease-in-out infinite`,
              animationDelay: `${particle.id * 0.1}s`
            }}
          />
        ))}

        <div style={{
          position: 'absolute',
          width: '800px',
          height: '800px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.2) 0%, transparent 70%)',
          top: `${mousePosition.y}%`,
          left: `${mousePosition.x}%`,
          transform: 'translate(-50%, -50%)',
          transition: 'all 0.3s ease',
          pointerEvents: 'none'
        }} />

        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'linear-gradient(rgba(139, 92, 246, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(139, 92, 246, 0.03) 1px, transparent 1px)',
          backgroundSize: '50px 50px',
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
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '6rem', alignItems: 'center' }}>
            <div>
              <div style={{
                display: 'inline-block',
                padding: '0.5rem 1.5rem',
                background: 'rgba(139, 92, 246, 0.1)',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                borderRadius: '50px',
                marginBottom: '2rem',
                fontSize: '0.875rem',
                fontWeight: '600',
                color: '#a78bfa',
                animation: 'slideDown 0.6s ease-out'
              }}>
                <Sparkles style={{ width: '14px', height: '14px', display: 'inline', marginRight: '0.5rem' }} />
                Trusted by 10,000+ businesses worldwide
              </div>

              <h1 style={{ 
                fontSize: '5rem', 
                fontWeight: '900', 
                marginBottom: '1.5rem',
                lineHeight: '1.1',
                letterSpacing: '-0.02em',
                animation: 'slideUp 0.8s ease-out'
              }}>
                <span style={{
                  background: 'linear-gradient(135deg, #fff 0%, #a78bfa 50%, #ec4899 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundSize: '200% 200%',
                  animation: 'gradient 3s ease infinite'
                }}>
                  Email Verification
                </span>
                <br />
                <span style={{ color: '#71717a' }}>That Actually Works</span>
              </h1>
              
              <p style={{ 
                fontSize: '1.5rem', 
                color: '#a1a1aa', 
                marginBottom: '3rem',
                lineHeight: '1.6',
                maxWidth: '600px',
                animation: 'slideUp 1s ease-out'
              }}>
                Stop wasting money on invalid emails. Our AI-powered validation ensures every email reaches a real inbox.
              </p>

              <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', marginBottom: '3rem', animation: 'slideUp 1.2s ease-out' }}>
                <button 
                  style={{
                    background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
                    color: '#fff',
                    border: 'none',
                    padding: '1.25rem 2.5rem',
                    fontSize: '1.125rem',
                    borderRadius: '14px',
                    cursor: 'pointer',
                    fontWeight: '700',
                    boxShadow: '0 20px 60px rgba(139, 92, 246, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1) inset',
                    transition: 'all 0.3s',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.transform = 'translateY(-2px) scale(1.02)';
                    e.target.style.boxShadow = '0 25px 70px rgba(139, 92, 246, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.2) inset';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.transform = 'translateY(0) scale(1)';
                    e.target.style.boxShadow = '0 20px 60px rgba(139, 92, 246, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1) inset';
                  }}
                >
                  Start Free Trial →
                </button>
                <a href="#api" style={{ 
                  color: '#a78bfa', 
                  textDecoration: 'none', 
                  fontSize: '1.125rem', 
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s'
                }}>
                  View API Docs
                  <ArrowRight style={{ width: '18px', height: '18px' }} />
                </a>
              </div>

              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(3, 1fr)', 
                gap: '2rem',
                animation: 'slideUp 1.4s ease-out'
              }}>
                {[
                  { value: '99.9%', label: 'Accuracy Rate' },
                  { value: '<100ms', label: 'Avg Response' },
                  { value: '50M+', label: 'Emails Validated' }
                ].map((stat, idx) => (
                  <div key={idx}>
                    <div style={{ fontSize: '2rem', fontWeight: '800', color: '#fff', marginBottom: '0.25rem' }}>
                      {stat.value}
                    </div>
                    <div style={{ fontSize: '0.875rem', color: '#71717a', fontWeight: '500' }}>
                      {stat.label}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div style={{ 
              position: 'relative',
              height: '600px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <div style={{
                position: 'absolute',
                width: '500px',
                height: '500px',
                border: '1px solid rgba(139, 92, 246, 0.2)',
                borderRadius: '50%',
                animation: 'rotate 30s linear infinite'
              }}>
                <div style={{
                  position: 'absolute',
                  top: '-20px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 10px 30px rgba(139, 92, 246, 0.5)'
                }}>
                  <Check style={{ width: '20px', height: '20px', color: '#fff' }} />
                </div>
              </div>

              <div style={{
                position: 'absolute',
                width: '400px',
                height: '400px',
                border: '1px solid rgba(139, 92, 246, 0.15)',
                borderRadius: '50%',
                animation: 'rotate 20s linear infinite reverse'
              }}>
                <div style={{
                  position: 'absolute',
                  bottom: '-20px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  background: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 10px 30px rgba(59, 130, 246, 0.5)'
                }}>
                  <Shield style={{ width: '20px', height: '20px', color: '#fff' }} />
                </div>
              </div>

              <div style={{
                width: '280px',
                height: '280px',
                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(236, 72, 153, 0.2) 100%)',
                borderRadius: '30% 70% 70% 30% / 30% 30% 70% 70%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                animation: 'morph 8s ease-in-out infinite, float 6s ease-in-out infinite',
                boxShadow: '0 30px 90px rgba(139, 92, 246, 0.4), inset 0 0 60px rgba(139, 92, 246, 0.2)',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                position: 'relative'
              }}>
                <div style={{
                  position: 'absolute',
                  inset: '-2px',
                  background: 'linear-gradient(135deg, #8b5cf6, #ec4899, #06b6d4)',
                  borderRadius: '30% 70% 70% 30% / 30% 30% 70% 70%',
                  opacity: 0.5,
                  filter: 'blur(20px)',
                  animation: 'morph 8s ease-in-out infinite'
                }} />
                <Mail style={{ width: '120px', height: '120px', color: '#fff', position: 'relative', zIndex: 1, filter: 'drop-shadow(0 10px 20px rgba(0, 0, 0, 0.3))' }} />
              </div>

              {[
                { icon: <Lock style={{ width: '16px', height: '16px' }} />, text: 'GDPR', top: '10%', left: '5%' },
                { icon: <Zap style={{ width: '16px', height: '16px' }} />, text: 'Real-time', top: '20%', right: '5%' },
                { icon: <Globe style={{ width: '16px', height: '16px' }} />, text: 'Global', bottom: '15%', left: '10%' }
              ].map((badge, idx) => (
                <div
                  key={idx}
                  style={{
                    position: 'absolute',
                    ...badge,
                    background: 'rgba(0, 0, 0, 0.8)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                    borderRadius: '50px',
                    padding: '0.75rem 1.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: '#fff',
                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
                    animation: `float ${3 + idx}s ease-in-out infinite`
                  }}
                >
                  {badge.icon}
                  {badge.text}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Trust Indicators */}
      <section style={{ 
        padding: '4rem 2rem',
        background: 'linear-gradient(180deg, #000 0%, #0a0a0a 100%)',
        borderTop: '1px solid rgba(139, 92, 246, 0.1)',
        position: 'relative'
      }}>
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(circle at 50% 0%, rgba(139, 92, 246, 0.05) 0%, transparent 50%)'
        }} />
        <div style={{ 
          maxWidth: '1400px', 
          margin: '0 auto',
          display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)',
          gap: '3rem',
          position: 'relative',
          zIndex: 1
        }}>
          {[
            { value: '99.9%', label: 'Accuracy', icon: <Check style={{ width: '24px', height: '24px' }} /> },
            { value: '<100ms', label: 'Response Time', icon: <Zap style={{ width: '24px', height: '24px' }} /> },
            { value: 'GDPR', label: 'Compliant', icon: <Lock style={{ width: '24px', height: '24px' }} /> },
            { value: '24/7', label: 'Support', icon: <Shield style={{ width: '24px', height: '24px' }} /> },
            { value: '10K+', label: 'Customers', icon: <Sparkles style={{ width: '24px', height: '24px' }} /> }
          ].map((item, idx) => (
            <div 
              key={idx} 
              style={{ 
                textAlign: 'center',
                padding: '2rem 1rem',
                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%)',
                borderRadius: '16px',
                border: '1px solid rgba(139, 92, 246, 0.1)',
                transition: 'all 0.3s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-5px)';
                e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.1)';
              }}
            >
              <div style={{ color: '#8b5cf6', marginBottom: '1rem', display: 'flex', justifyContent: 'center' }}>
                {item.icon}
              </div>
              <div style={{ fontSize: '2rem', fontWeight: '800', color: '#fff', marginBottom: '0.5rem' }}>
                {item.value}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#71717a', fontWeight: '600' }}>
                {item.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Live Demo */}
      <section style={{ padding: '8rem 2rem', background: '#000', position: 'relative', overflow: 'hidden' }}>
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '800px',
          height: '800px',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%)',
          pointerEvents: 'none'
        }} />
        
        <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <div style={{
            display: 'inline-block',
            padding: '0.5rem 1.5rem',
            background: 'rgba(139, 92, 246, 0.1)',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            borderRadius: '50px',
            marginBottom: '2rem',
            fontSize: '0.875rem',
            fontWeight: '600',
            color: '#a78bfa'
          }}>
            Live Demo
          </div>

          <h2 style={{ 
            fontSize: '3.5rem', 
            fontWeight: '900', 
            marginBottom: '1rem',
            letterSpacing: '-0.02em',
            background: 'linear-gradient(135deg, #fff 0%, #a78bfa 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Try It Right Now
          </h2>
          <p style={{ fontSize: '1.25rem', color: '#a1a1aa', marginBottom: '4rem', maxWidth: '600px', margin: '0 auto 4rem' }}>
            See instant validation results. No signup required.
          </p>
          
          <div style={{
            background: 'rgba(0, 0, 0, 0.4)',
            backdropFilter: 'blur(20px)',
            borderRadius: '24px',
            padding: '3rem',
            border: '1px solid rgba(139, 92, 246, 0.2)',
            boxShadow: '0 25px 50px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
          }}>
            <div style={{ marginBottom: '2rem' }}>
              <div style={{ position: 'relative' }}>
                <input
                  type="email"
                  placeholder="Enter any email address..."
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && email && !isValidating && handleValidate()}
                  style={{
                    width: '100%',
                    padding: '1.5rem 1.5rem 1.5rem 3.5rem',
                    fontSize: '1.125rem',
                    borderRadius: '16px',
                    border: '2px solid rgba(139, 92, 246, 0.2)',
                    background: 'rgba(0, 0, 0, 0.5)',
                    color: '#fff',
                    outline: 'none',
                    marginBottom: '1.5rem',
                    transition: 'all 0.2s',
                    boxSizing: 'border-box'
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#8b5cf6';
                    e.target.style.boxShadow = '0 0 0 4px rgba(139, 92, 246, 0.1)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = 'rgba(139, 92, 246, 0.2)';
                    e.target.style.boxShadow = 'none';
                  }}
                />
                <Mail style={{
                  position: 'absolute',
                  left: '1.25rem',
                  top: '1.5rem',
                  width: '20px',
                  height: '20px',
                  color: '#71717a'
                }} />
              </div>
              
              <button
                onClick={handleValidate}
                disabled={!email || isValidating}
                style={{
                  width: '100%',
                  background: email && !isValidating ? 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)' : 'rgba(139, 92, 246, 0.2)',
                  color: '#fff',
                  border: 'none',
                  padding: '1.5rem',
                  fontSize: '1.125rem',
                  borderRadius: '16px',
                  cursor: email && !isValidating ? 'pointer' : 'not-allowed',
                  fontWeight: '700',
                  transition: 'all 0.3s',
                  boxShadow: email && !isValidating ? '0 20px 40px rgba(139, 92, 246, 0.3)' : 'none'
                }}
                onMouseEnter={(e) => {
                  if (email && !isValidating) {
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 25px 50px rgba(139, 92, 246, 0.4)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = email && !isValidating ? '0 20px 40px rgba(139, 92, 246, 0.3)' : 'none';
                }}
              >
                {isValidating ? 'Validating...' : 'Validate Email →'}
              </button>
            </div>

            {validationResult !== null && (
              <div style={{
                padding: '2rem',
                borderRadius: '16px',
                background: validationResult ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                border: `2px solid ${validationResult ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)'}`,
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                animation: 'slideUp 0.3s ease-out'
              }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '12px',
                  background: validationResult ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  {validationResult ? (
                    <Check style={{ width: '28px', height: '28px', color: '#22c55e' }} />
                  ) : (
                    <X style={{ width: '28px', height: '28px', color: '#ef4444' }} />
                  )}
                </div>
                <div style={{ textAlign: 'left', flex: 1 }}>
                  <div style={{ 
                    color: validationResult ? '#22c55e' : '#ef4444', 
                    fontWeight: '700',
                    fontSize: '1.125rem',
                    marginBottom: '0.25rem'
                  }}>
                    {validationResult ? 'Valid Email Address' : 'Invalid Email Address'}
                  </div>
                  <div style={{ fontSize: '0.875rem', color: '#a1a1aa' }}>
                    {validationResult ? 'This email passed all validation checks' : 'This email failed our validation checks'}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ padding: '8rem 2rem', background: '#0a0a0a', position: 'relative' }}>
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(139, 92, 246, 0.05) 1px, transparent 0)',
          backgroundSize: '40px 40px'
        }} />
        
        <div style={{ maxWidth: '1400px', margin: '0 auto', position: 'relative', zIndex: 1 }}>
          <div style={{ textAlign: 'center', marginBottom: '5rem' }}>
            <div style={{
              display: 'inline-block',
              padding: '0.5rem 1.5rem',
              background: 'rgba(139, 92, 246, 0.1)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              borderRadius: '50px',
              marginBottom: '2rem',
              fontSize: '0.875rem',
              fontWeight: '600',
              color: '#a78bfa'
            }}>
              Features
            </div>
            <h2 style={{ 
              fontSize: '3.5rem', 
              fontWeight: '900',
              marginBottom: '1rem',
              letterSpacing: '-0.02em'
            }}>
              Everything You Need
            </h2>
            <p style={{ fontSize: '1.25rem', color: '#a1a1aa', maxWidth: '600px', margin: '0 auto' }}>
              Built for developers, designed for scale
            </p>
          </div>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '2rem'
          }}>
            {features.map((feature, idx) => (
              <div
                key={idx}
                style={{
                  padding: '3rem',
                  background: 'rgba(0, 0, 0, 0.4)',
                  backdropFilter: 'blur(20px)',
                  borderRadius: '24px',
                  border: '1px solid rgba(139, 92, 246, 0.2)',
                  transition: 'all 0.3s',
                  position: 'relative',
                  overflow: 'hidden'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-8px)';
                  e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.5)';
                  e.currentTarget.style.boxShadow = '0 25px 50px rgba(139, 92, 246, 0.3)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.2)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: '4px',
                  background: `linear-gradient(90deg, ${feature.color.replace('from-', '').replace('to-', '').split(' ').join(', ')})`
                }} />
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '16px',
                  background: `linear-gradient(135deg, ${feature.color.replace('from-', '').replace('to-', '').split(' ').join(', ')})`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '1.5rem',
                  color: '#fff'
                }}>
                  {feature.icon}
                </div>
                <h3 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '1rem', color: '#fff' }}>
                  {feature.title}
                </h3>
                <p style={{ fontSize: '1rem', color: '#a1a1aa', lineHeight: '1.6' }}>
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section style={{ padding: '8rem 2rem', background: '#000' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
            <div style={{
              display: 'inline-block',
              padding: '0.5rem 1.5rem',
              background: 'rgba(139, 92, 246, 0.1)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              borderRadius: '50px',
              marginBottom: '2rem',
              fontSize: '0.875rem',
              fontWeight: '600',
              color: '#a78bfa'
            }}>
              FAQ
            </div>
            <h2 style={{ 
              fontSize: '3.5rem', 
              fontWeight: '900',
              marginBottom: '1rem',
              letterSpacing: '-0.02em'
            }}>
              Common Questions
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {faqs.map((faq, idx) => (
              <div
                key={idx}
                style={{
                  background: 'rgba(0, 0, 0, 0.4)',
                  backdropFilter: 'blur(20px)',
                  borderRadius: '16px',
                  border: '1px solid rgba(139, 92, 246, 0.2)',
                  overflow: 'hidden',
                  transition: 'all 0.3s'
                }}
              >
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  style={{
                    width: '100%',
                    padding: '1.5rem 2rem',
                    background: 'transparent',
                    border: 'none',
                    color: '#fff',
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
                      transform: openFaq === idx ? 'rotate(180deg)' : 'rotate(0deg)'
                    }} 
                  />
                </button>
                {openFaq === idx && (
                  <div style={{
                    padding: '0 2rem 1.5rem 2rem',
                    color: '#a1a1aa',
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
        padding: '8rem 2rem', 
        background: 'linear-gradient(135deg, #0a0a0a 0%, #000 100%)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.15) 0%, transparent 70%)'
        }} />
        
        <div style={{ 
          maxWidth: '900px', 
          margin: '0 auto', 
          textAlign: 'center',
          position: 'relative',
          zIndex: 1
        }}>
          <h2 style={{ 
            fontSize: '4rem', 
            fontWeight: '900',
            marginBottom: '1.5rem',
            letterSpacing: '-0.02em',
            background: 'linear-gradient(135deg, #fff 0%, #a78bfa 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Ready to Get Started?
          </h2>
          <p style={{ fontSize: '1.5rem', color: '#a1a1aa', marginBottom: '3rem', maxWidth: '600px', margin: '0 auto 3rem' }}>
            Join thousands of businesses using our email validation API
          </p>
          
          <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', alignItems: 'center' }}>
            <button 
              style={{
                background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
                color: '#fff',
                border: 'none',
                padding: '1.25rem 2.5rem',
                fontSize: '1.125rem',
                borderRadius: '14px',
                cursor: 'pointer',
                fontWeight: '700',
                boxShadow: '0 20px 60px rgba(139, 92, 246, 0.4)',
                transition: 'all 0.3s'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px) scale(1.02)';
                e.target.style.boxShadow = '0 25px 70px rgba(139, 92, 246, 0.5)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0) scale(1)';
                e.target.style.boxShadow = '0 20px 60px rgba(139, 92, 246, 0.4)';
              }}
            >
              Start Free Trial →
            </button>
            <a href="#contact" style={{ 
              color: '#a78bfa', 
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
        background: '#000',
        borderTop: '1px solid rgba(139, 92, 246, 0.1)',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <p style={{ color: '#71717a', fontSize: '0.875rem' }}>
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
      `}</style>
    </div>
  );
}

export default Testing;