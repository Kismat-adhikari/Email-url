import React, { useState, useEffect } from 'react';
import { FiSend, FiUsers, FiMail, FiCheck, FiAlertCircle, FiSettings, FiExternalLink } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import './EmailComposer.css';

const EmailComposer = () => {
  const navigate = useNavigate();
  const [emailData, setEmailData] = useState({
    recipients: '',
    subject: '',
    content: '',
    contentType: 'text/html',
    fromEmail: '',
    fromName: ''
  });
  
  const [sendMode, setSendMode] = useState('single'); // 'single' or 'batch'
  const [templates, setTemplates] = useState({});
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState(null);
  const [configStatus, setConfigStatus] = useState(null);

  useEffect(() => {
    loadTemplates();
    testEmailConfig();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/email/templates');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates || {});
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const testEmailConfig = async () => {
    try {
      const response = await fetch('/api/email/config/test', { method: 'POST' });
      const data = await response.json();
      setConfigStatus(data);
    } catch (error) {
      setConfigStatus({ valid: false, error: 'Connection failed' });
    }
  };

  const handleTemplateSelect = (templateKey) => {
    if (templateKey && templates[templateKey]) {
      const template = templates[templateKey];
      setEmailData(prev => ({
        ...prev,
        subject: template.subject,
        content: template.content
      }));
      setSelectedTemplate(templateKey);
    }
  };

  const parseRecipients = (recipientsText) => {
    return recipientsText
      .split(/[,;\n]/)
      .map(email => email.trim())
      .filter(email => email.length > 0);
  };

  // Removed unused checkBounceHistory function

  const sendEmail = async () => {
    if (!emailData.recipients || !emailData.subject || !emailData.content) {
      setSendResult({
        success: false,
        error: 'Please fill in all required fields'
      });
      return;
    }

    setSending(true);
    setSendResult(null);

    try {
      let endpoint, payload;

      if (sendMode === 'single') {
        endpoint = '/api/email/send';
        payload = {
          to_email: emailData.recipients.trim(),
          subject: emailData.subject,
          content: emailData.content,
          content_type: emailData.contentType,
          from_email: emailData.fromEmail || undefined,
          from_name: emailData.fromName || undefined
        };
      } else {
        endpoint = '/api/email/send/batch';
        const recipients = parseRecipients(emailData.recipients);
        
        if (recipients.length === 0) {
          setSendResult({
            success: false,
            error: 'No valid recipients found'
          });
          setSending(false);
          return;
        }

        payload = {
          recipients: recipients,
          subject: emailData.subject,
          content: emailData.content,
          content_type: emailData.contentType,
          from_email: emailData.fromEmail || undefined,
          from_name: emailData.fromName || undefined
        };
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': localStorage.getItem('anon_user_id') || 'unknown'
        },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      setSendResult(result);

      if (result.success) {
        // Clear form on success
        setEmailData({
          recipients: '',
          subject: '',
          content: '',
          contentType: 'text/html',
          fromEmail: emailData.fromEmail, // Keep sender info
          fromName: emailData.fromName
        });
        setSelectedTemplate('');
      }

    } catch (error) {
      setSendResult({
        success: false,
        error: 'Failed to send email: ' + error.message
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="email-composer">
      <div className="composer-header">
        <h2>📧 Email Composer</h2>
        <p>Compose and send emails to validated addresses</p>
      </div>

      {/* Configuration Status */}
      {configStatus && (
        <div className={`config-status ${configStatus.valid ? 'valid' : 'invalid'}`}>
          {configStatus.valid ? (
            <div className="config-success">
              <FiCheck /> SendGrid configured: {configStatus.username}
              <span className="config-ready">Ready to send emails!</span>
            </div>
          ) : (
            <div className="config-setup-needed">
              <div className="config-error">
                <FiAlertCircle /> SendGrid API Key Required
              </div>
              <div className="config-message">
                To send emails, you need to configure your SendGrid API key in your profile settings.
              </div>
              <div className="config-actions">
                <button 
                  className="setup-btn primary"
                  onClick={() => navigate('/profile')}
                >
                  <FiSettings /> Configure API Key
                </button>
                <a 
                  href="https://sendgrid.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="setup-btn secondary"
                >
                  <FiExternalLink /> Get SendGrid Account
                </a>
              </div>
              <div className="config-help">
                <h4>Quick Setup:</h4>
                <ol>
                  <li>Create a free SendGrid account at <a href="https://sendgrid.com" target="_blank" rel="noopener noreferrer">sendgrid.com</a></li>
                  <li>Generate an API key in your SendGrid dashboard</li>
                  <li>Copy the API key (starts with "SG.")</li>
                  <li>Click "Configure API Key" above to add it to your profile</li>
                </ol>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Send Mode Selector */}
      <div className="send-mode-selector">
        <button
          className={`mode-btn ${sendMode === 'single' ? 'active' : ''}`}
          onClick={() => setSendMode('single')}
        >
          <FiMail /> Single Email
        </button>
        <button
          className={`mode-btn ${sendMode === 'batch' ? 'active' : ''}`}
          onClick={() => setSendMode('batch')}
        >
          <FiUsers /> Batch Emails
        </button>
      </div>

      <div className="composer-form">
        {/* Template Selector */}
        <div className="form-group">
          <label>Email Template (Optional)</label>
          <select
            value={selectedTemplate}
            onChange={(e) => handleTemplateSelect(e.target.value)}
            className="template-select"
          >
            <option value="">Choose a template...</option>
            {Object.keys(templates).map(key => (
              <option key={key} value={key}>
                {key.charAt(0).toUpperCase() + key.slice(1)} Template
              </option>
            ))}
          </select>
        </div>

        {/* Recipients */}
        <div className="form-group">
          <label>
            {sendMode === 'single' ? 'Recipient Email' : 'Recipients'}
            <span className="required">*</span>
          </label>
          {sendMode === 'single' ? (
            <input
              type="email"
              placeholder="user@example.com"
              value={emailData.recipients}
              onChange={(e) => setEmailData(prev => ({ ...prev, recipients: e.target.value }))}
              className="form-input"
            />
          ) : (
            <textarea
              placeholder="Enter email addresses separated by commas, semicolons, or new lines&#10;user1@example.com&#10;user2@example.com&#10;user3@example.com"
              value={emailData.recipients}
              onChange={(e) => setEmailData(prev => ({ ...prev, recipients: e.target.value }))}
              className="form-textarea"
              rows="4"
            />
          )}
          {sendMode === 'batch' && emailData.recipients && (
            <div className="recipient-count">
              {parseRecipients(emailData.recipients).length} recipients
            </div>
          )}
        </div>

        {/* Sender Info */}
        <div className="form-row">
          <div className="form-group">
            <label>From Email</label>
            <input
              type="email"
              placeholder="sender@yourdomain.com (optional)"
              value={emailData.fromEmail}
              onChange={(e) => setEmailData(prev => ({ ...prev, fromEmail: e.target.value }))}
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label>From Name</label>
            <input
              type="text"
              placeholder="Your Name (optional)"
              value={emailData.fromName}
              onChange={(e) => setEmailData(prev => ({ ...prev, fromName: e.target.value }))}
              className="form-input"
            />
          </div>
        </div>

        {/* Subject */}
        <div className="form-group">
          <label>
            Subject <span className="required">*</span>
          </label>
          <input
            type="text"
            placeholder="Email subject"
            value={emailData.subject}
            onChange={(e) => setEmailData(prev => ({ ...prev, subject: e.target.value }))}
            className="form-input"
          />
        </div>

        {/* Content Type */}
        <div className="form-group">
          <label>Content Type</label>
          <select
            value={emailData.contentType}
            onChange={(e) => setEmailData(prev => ({ ...prev, contentType: e.target.value }))}
            className="form-select"
          >
            <option value="text/html">HTML</option>
            <option value="text/plain">Plain Text</option>
          </select>
        </div>

        {/* Content */}
        <div className="form-group">
          <label>
            Email Content <span className="required">*</span>
          </label>
          <textarea
            placeholder={emailData.contentType === 'text/html' 
              ? '<h1>Hello!</h1><p>Your email content here...</p>' 
              : 'Your email content here...'}
            value={emailData.content}
            onChange={(e) => setEmailData(prev => ({ ...prev, content: e.target.value }))}
            className="form-textarea content-editor"
            rows="10"
          />
        </div>

        {/* Send Button */}
        <button
          onClick={sendEmail}
          disabled={sending || !configStatus?.valid}
          className="send-btn"
        >
          {sending ? (
            <>
              <div className="spinner"></div>
              Sending...
            </>
          ) : (
            <>
              <FiSend />
              {sendMode === 'single' ? 'Send Email' : 'Send Batch'}
            </>
          )}
        </button>
      </div>

      {/* Send Result */}
      {sendResult && (
        <div className={`send-result ${sendResult.success ? 'success' : 'error'}`}>
          {sendResult.success ? (
            <div>
              <FiCheck className="result-icon" />
              <div className="result-content">
                <strong>Email sent successfully!</strong>
                {sendMode === 'single' ? (
                  <p>Sent to: {sendResult.to_email}</p>
                ) : (
                  <div>
                    <p>Total recipients: {sendResult.total_recipients}</p>
                    <p>Successfully sent: {sendResult.total_sent}</p>
                    {sendResult.total_failed > 0 && (
                      <p>Failed: {sendResult.total_failed}</p>
                    )}
                  </div>
                )}
                {sendResult.message_id && (
                  <p className="message-id">Message ID: {sendResult.message_id}</p>
                )}
              </div>
            </div>
          ) : (
            <div>
              <FiAlertCircle className="result-icon" />
              <div className="result-content">
                <strong>Send failed</strong>
                <p>{sendResult.error}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Help Text */}
      <div className="composer-help">
        <h4>💡 Tips:</h4>
        <ul>
          <li>Validate your recipients first using the email validator</li>
          <li>Use HTML content for rich formatting and styling</li>
          <li>Test with a single email before sending to large batches</li>
          <li>Configure your SendGrid API key in the environment settings</li>
        </ul>
      </div>
    </div>
  );
};

export default EmailComposer;