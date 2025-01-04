import { useState, useEffect } from 'react';
import axios from 'axios';
import { IoSend } from "react-icons/io5";
import { CiLogout } from "react-icons/ci";
import ChatMessage from './ChatMessage';
import ChatSession from './ChatSession';
import './Chat.css';
import { useNavigate } from 'react-router-dom';

function Chat() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [input, setInput] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const token = localStorage.getItem('token');

  useEffect(() => {
    axios.get('http://localhost:5000/api/sessions', {
      headers: { Authorization: `Bearer ${token}` }
    }).then(response => {
      console.log('Sessions:', response.data); // Log response for debugging
      setSessions(response.data);
    }).catch(error => {
      console.error('Error fetching chat sessions:', error.response?.data || error.message);
    });
  }, [token]);
  
  const handleSessionChange = (session) => {
    setCurrentSession(session);
    axios.get(`http://localhost:5000/api/history/${session.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(response => {
      setChatLog(response.data);
    }).catch(error => {
      console.error('Error fetching chat history:', error);
    });
  };

  const handleNewSession = async () => {
    const sessionName = prompt('Enter session name:');
    if (sessionName) {
      try {
        const response = await axios.post('http://localhost:5000/api/sessions', { name: sessionName }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const newSession = response.data;
        setSessions([...sessions, newSession]);
        handleSessionChange(newSession);
      } catch (error) {
        console.error('Error creating new session:', error);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (input && currentSession) {
      const newMessage = { id: Date.now(), role: 'user', content: input };
      const updatedChatLog = [...chatLog, newMessage];
      setChatLog(updatedChatLog);
      setInput('');

      try {
        setIsLoading(true);
        const response = await axios.post('http://localhost:5000/api/chat', { session_id: currentSession.id, messages: updatedChatLog }, {
          headers: { Authorization: `Bearer ${token}` }
        });

        const aiMessage = { id: Date.now(), role: 'AI', content: response.data.response };
        setChatLog((prevChatLog) => [...prevChatLog, aiMessage]);
        setIsLoading(false);
      } catch (error) {
        console.error('Fetch error:', error);
        setIsLoading(false);
      }
    }
  };

  const handleLogOut = () => {
    localStorage.removeItem('token');
    navigate('/signin');
  }

  return (
    <div className="chat-container">
      <aside className="sidemenu">
        <div className="sidemenu-button" role="button" onClick={handleNewSession}>
          <span>+</span> New chat
        </div>
        <div className="session-list">
          {[...sessions].reverse().map((session) => (
            <ChatSession 
              key={session.id} 
              session={session} 
              onClick={() => handleSessionChange(session)} 
              isActive={currentSession?.id === session.id} 
            />
          ))}
        </div>
        <div className="logout-button" role="button" onClick={handleLogOut}>
          <CiLogout className="logout-button-icon"/>
          <div className="logout-button-text">Log out</div>
        </div>
      </aside>
      <section className="chat">
        <div className="chat-log">
          {chatLog.map((message) => (
            <ChatMessage key={message.id} 
            message={message} 
            />
          ))}
        </div>
        <div className="chat-input-div">
          <form onSubmit={handleSubmit} className="input-form">
            <input
              className="chat-input"
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <button type="submit" className="send-button">
              <IoSend />
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}

export default Chat;