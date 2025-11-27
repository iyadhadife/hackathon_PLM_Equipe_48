import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, X, Minimize2 } from 'lucide-react';
import { sendChatMessage } from '../services/api.js';

/**
 * Composant Chatbot - Widget flottant en bas à droite
 * Permet d'interroger les fichiers Excel via Gemini + Pandas
 */
export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: "👋 Bonjour ! Je peux répondre à vos questions sur les fichiers Excel. Par exemple : 'Quels sont les assemblages qui prennent le plus de temps ?'",
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll vers le bas quand de nouveaux messages arrivent
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus sur l'input quand le chat s'ouvre
  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  const handleSendMessage = async () => {
    const question = inputValue.trim();
    if (!question || isLoading) return;

    // Ajouter le message utilisateur
    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: question,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Appel à l'API backend
      const response = await sendChatMessage(question);

      // Ajouter la réponse du bot
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: response.answer,
        code: response.code, // Code Pandas généré (optionnel à afficher)
        error: response.error,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);

    } catch (error) {
      // Gérer les erreurs réseau
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: `❌ Erreur : ${error.message}`,
        error: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Fonction pour formatter le texte avec sauts de ligne et mise en forme
  const formatMessageText = (text) => {
    if (!text) return null;

    // Convertir les sauts de ligne en <br />
    let formatted = text.split('\n').map((line, i) => {
      // Gérer les lignes vides
      if (line.trim() === '') {
        return <br key={i} />;
      }

      // Détecter et formatter les titres avec émojis
      if (line.match(/^[🏆🚨📊⚠️👥💡ℹ️✅❌]/)) {
        return (
          <div key={i} className="message-title">
            {formatInlineStyles(line)}
          </div>
        );
      }

      // Détecter les listes numérotées
      if (line.match(/^\d+\.\s/)) {
        return (
          <div key={i} className="message-list-item numbered">
            {formatInlineStyles(line)}
          </div>
        );
      }

      // Détecter les puces
      if (line.match(/^[•·→►]\s/) || line.trim().startsWith('•')) {
        return (
          <div key={i} className="message-list-item bullet">
            {formatInlineStyles(line)}
          </div>
        );
      }

      // Détecter les sous-items (indentation)
      if (line.match(/^\s{2,}[•·⏱️📋⚠️👉]/)) {
        return (
          <div key={i} className="message-sub-item">
            {formatInlineStyles(line.trim())}
          </div>
        );
      }

      // Ligne normale
      return (
        <div key={i} className="message-line">
          {formatInlineStyles(line)}
        </div>
      );
    });

    return <>{formatted}</>;
  };

  // Fonction pour formatter les styles inline (gras, etc.)
  const formatInlineStyles = (text) => {
    // Convertir **texte** en gras
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  // Bouton flottant pour ouvrir/fermer le chat
  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="chatbot-fab"
        title="Ouvrir le chatbot"
      >
        <MessageCircle size={24} />
        <style>{chatbotStyles}</style>
      </button>
    );
  }

  // Widget de chat ouvert
  return (
    <>
      <style>{chatbotStyles}</style>
      <div className={`chatbot-container ${isMinimized ? 'minimized' : ''}`}>
        {/* Header */}
        <div className="chatbot-header">
          <div className="chatbot-header-title">
            <MessageCircle size={20} />
            <span>Assistant Excel</span>
          </div>
          <div className="chatbot-header-actions">
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="chatbot-icon-btn"
              title={isMinimized ? 'Agrandir' : 'Réduire'}
            >
              <Minimize2 size={16} />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="chatbot-icon-btn"
              title="Fermer"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Messages */}
        {!isMinimized && (
          <>
            <div className="chatbot-messages">
              {messages.map((msg) => (
                <div key={msg.id} className={`chatbot-message ${msg.type}`}>
                  <div className={`message-bubble ${msg.error ? 'error' : ''}`}>
                    {/* Rendu HTML si le message contient du HTML (tableaux) */}
                    {msg.text.includes('<table') ? (
                      <div dangerouslySetInnerHTML={{ __html: msg.text }} />
                    ) : (
                      <div className="message-text">
                        {formatMessageText(msg.text)}
                      </div>
                    )}
                    
                    {/* Afficher le code Pandas si disponible (optionnel) */}
                    {msg.code && (
                      <details className="message-code-details">
                        <summary>Code Pandas généré</summary>
                        <pre className="message-code">{msg.code}</pre>
                      </details>
                    )}
                  </div>
                  <div className="message-time">
                    {msg.timestamp.toLocaleTimeString('fr-FR', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="chatbot-message bot">
                  <div className="message-bubble loading">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="chatbot-input-area">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Posez votre question sur les fichiers Excel..."
                className="chatbot-input"
                disabled={isLoading}
              />
              <button
                onClick={handleSendMessage}
                className="chatbot-send-btn"
                disabled={!inputValue.trim() || isLoading}
                title="Envoyer"
              >
                <Send size={18} />
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
}

// Styles CSS pour le chatbot
const chatbotStyles = `
/* Bouton flottant (FAB) */
.chatbot-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  z-index: 1000;
}

.chatbot-fab:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

/* Container du chatbot */
.chatbot-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 380px;
  height: 600px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  transition: height 0.3s ease;
}

.chatbot-container.minimized {
  height: 60px;
}

/* Header */
.chatbot-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px;
  border-radius: 16px 16px 0 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.chatbot-header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 1rem;
}

.chatbot-header-actions {
  display: flex;
  gap: 8px;
}

.chatbot-icon-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.chatbot-icon-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Zone de messages */
.chatbot-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f8f9fa;
}

.chatbot-message {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 85%;
}

.chatbot-message.user {
  align-self: flex-end;
  align-items: flex-end;
}

.chatbot-message.bot {
  align-self: flex-start;
  align-items: flex-start;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 12px;
  word-wrap: break-word;
  line-height: 1.4;
  font-size: 0.9rem;
}

.chatbot-message.user .message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.chatbot-message.bot .message-bubble {
  background: white;
  color: #333;
  border: 1px solid #e9ecef;
  border-bottom-left-radius: 4px;
}

.message-bubble.error {
  background: #fff5f5;
  border-color: #ff6b6b;
  color: #c92a2a;
}

.message-bubble.loading {
  padding: 16px;
}

.message-time {
  font-size: 0.7rem;
  color: #adb5bd;
  padding: 0 4px;
}

/* Formatage du texte des messages */
.message-text {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-title {
  font-weight: 600;
  font-size: 1rem;
  margin-bottom: 8px;
  color: #2d3748;
  line-height: 1.5;
}

.message-line {
  line-height: 1.6;
  margin: 2px 0;
}

.message-list-item {
  line-height: 1.6;
  margin: 6px 0;
  padding-left: 4px;
}

.message-list-item.numbered {
  font-weight: 500;
  color: #2d3748;
}

.message-list-item.bullet {
  padding-left: 8px;
  color: #4a5568;
}

.message-sub-item {
  padding-left: 24px;
  line-height: 1.5;
  margin: 4px 0;
  color: #4a5568;
  font-size: 0.88rem;
}

.message-text strong {
  font-weight: 600;
  color: #2d3748;
}

/* Espacement pour les émojis */
.message-title::before,
.message-list-item::before,
.message-sub-item::before {
  margin-right: 6px;
}

/* Indicateur de frappe */
.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #adb5bd;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

/* Code Pandas (détails repliables) */
.message-code-details {
  margin-top: 8px;
  border-top: 1px solid #e9ecef;
  padding-top: 8px;
}

.message-code-details summary {
  cursor: pointer;
  font-size: 0.8rem;
  color: #667eea;
  font-weight: 500;
}

.message-code {
  background: #f1f3f5;
  padding: 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  margin-top: 6px;
  overflow-x: auto;
  border: 1px solid #dee2e6;
}

/* Tableaux HTML dans les messages */
.message-bubble table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
  font-size: 0.8rem;
}

.message-bubble table th,
.message-bubble table td {
  padding: 6px 8px;
  text-align: left;
  border: 1px solid #dee2e6;
}

.message-bubble table th {
  background: #f1f3f5;
  font-weight: 600;
}

/* Zone d'input */
.chatbot-input-area {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: white;
  border-top: 1px solid #e9ecef;
  border-radius: 0 0 16px 16px;
  flex-shrink: 0;
}

.chatbot-input {
  flex: 1;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s;
}

.chatbot-input:focus {
  border-color: #667eea;
}

.chatbot-input:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
}

.chatbot-send-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.chatbot-send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.chatbot-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Scrollbar personnalisée */
.chatbot-messages::-webkit-scrollbar {
  width: 6px;
}

.chatbot-messages::-webkit-scrollbar-track {
  background: #f1f3f5;
}

.chatbot-messages::-webkit-scrollbar-thumb {
  background: #adb5bd;
  border-radius: 3px;
}

.chatbot-messages::-webkit-scrollbar-thumb:hover {
  background: #868e96;
}

/* Responsive */
@media (max-width: 480px) {
  .chatbot-container {
    width: calc(100vw - 32px);
    height: calc(100vh - 100px);
    bottom: 16px;
    right: 16px;
  }
  
  .chatbot-fab {
    bottom: 16px;
    right: 16px;
  }
}
`;
