import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { IoSend } from "react-icons/io5";
import { CiLogout } from "react-icons/ci";
import { FaUser, FaRobot } from "react-icons/fa";
import { FaMagnifyingGlass } from "react-icons/fa6";
import ChatMessage from './ChatMessage';
import ChatSession from './ChatSession';
import NewSessionModal from './NewSessionModal';
import RenameSessionModal from './RenameSessionModal';
import DeleteSessionModal from './DeleteSessionModal';
import ChatContextModal from './ChatContextModal';
import './Chat.css';
import { useNavigate } from 'react-router-dom';

const sleep = (ms) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

function Chat() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [input, setInput] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [isNewSessionModalOpen, setIsNewSessionModalOpen] = useState(false);
  const [isRenameSessionModalOpen, setIsRenameSessionModalOpen] = useState(false);
  const [isDeleteSessionModalOpen, setIsDeleteSessionModalOpen] = useState(false);
  const [isChatContextModalOpen, setIsChatContextModalOpen] = useState(false);
  const [sessionToRename, setSessionToRename] = useState(null);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [userEmail, setUserEmail] = useState('');
  const token = localStorage.getItem('token');
  const textareaRef = useRef(null);

  useEffect(() => {
    axios.get('http://localhost:5000/api/sessions', {
      headers: { Authorization: `Bearer ${token}` }
    }).then(response => {
      setSessions(response.data);
    }).catch(error => {
      console.error('Error fetching chat sessions:', error.response?.data || error.message);
    });

    axios.get('http://localhost:5000/api/profile', {
      headers: { Authorization: `Bearer ${token}` }
    }).then(response => {
      setUserEmail(response.data.email);
    }).catch(error => {
      console.error('Error fetching user profile:', error.response?.data || error.message);
    });
  }, [token]);

  const handleKeyDown = (e) => {
    if (e.shiftKey && e.key === 'Enter') {
      e.preventDefault();
      setInput(`${input}\n`);
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea.scrollHeight > 61) {
      textarea.style.height = `45px`;
      textarea.style.padding= `12px 5px 12px 40px`;
    }
    if (input === '') {
      textarea.style.height = '36px';
      textarea.style.padding = '19px 5px 5px 40px';
    }
  };


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

  const handleNewSession = async (sessionName) => {
    setIsNewSessionModalOpen(true);
    if (sessionName) {
      try {
        const response = await axios.post('http://localhost:5000/api/sessions', { name: sessionName }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const newSession = response.data;
        setSessions([...sessions, newSession]);
        window.location.reload();
      } catch (error) {
        console.error('Error creating new session:', error);
      }
    }
  };

  const handleRenameSession = (session) => {
    setSessionToRename(session);
    setIsRenameSessionModalOpen(true);
  };

  const submitRenameSession = async (newName) => {
    if (newName && newName !== sessionToRename.name) {
      try {
        const response = await axios.put(`http://localhost:5000/api/sessions/${sessionToRename.id}`, { name: newName }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const updatedSession = response.data;
        setSessions(sessions.map(s => s.id === sessionToRename.id ? updatedSession : s));
        if (currentSession.id === sessionToRename.id) {
          setCurrentSession(updatedSession);
        }
        setIsRenameSessionModalOpen(false);
        setSessionToRename(null);
      } catch (error) {
        console.error('Error renaming session:', error);
      }
    }
  };

  const handleDeleteSession = (session) => {
    setSessionToDelete(session);
    setIsDeleteSessionModalOpen(true);
  };

  const confirmDeleteSession = async (session) => {
    try {
      await axios.delete(`http://localhost:5000/api/sessions/${session.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSessions(sessions.filter(s => s.id !== session.id));
      if (currentSession.id === session.id) {
        setCurrentSession(null);
        setChatLog([]);
      }
      setIsDeleteSessionModalOpen(false);
      setSessionToDelete(null);
    } catch (error) {
      console.error('Error deleting session:', error);
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
    <div className={`chat-container ${isNewSessionModalOpen || isRenameSessionModalOpen || isDeleteSessionModalOpen || isChatContextModalOpen ? 'dark-overlay' : ''}`}>
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
              onRename={handleRenameSession}
              onDelete={handleDeleteSession}
            />
          ))}
        </div>
        <div className="logout-button" role="button" onClick={handleLogOut}>
          <CiLogout className="logout-button-icon"/>
          <div className="logout-button-text">Log out</div>
        </div>
      </aside>
      <div className="chat-header">
        <div className="chat-header-user">
          <span>{`${userEmail}`}</span>
          <div className="chat-avatar">
            <FaUser className='icon'/>
          </div>
        </div>
      </div>
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
            <textarea
                ref={textareaRef}
                className="chat-input"
                placeholder="Type a message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                onInput={adjustTextareaHeight}
                disabled={isLoading}
              />
            <button type="submit" className="send-button">
              <IoSend />
            </button>
            <button 
              type="button" 
              className="search-button"
              onClick={() => setIsChatContextModalOpen(true)}
            >
              <FaMagnifyingGlass />
            </button>
          </form>
        </div>
      </section>
      <NewSessionModal
        isOpen={isNewSessionModalOpen}
        onRequestClose={() => setIsNewSessionModalOpen(false)}
        onSubmit={handleNewSession}
      />
      <RenameSessionModal
        isOpen={isRenameSessionModalOpen}
        onRequestClose={() => setIsRenameSessionModalOpen(false)}
        onSubmit={submitRenameSession}
        session={sessionToRename}
      />
      <DeleteSessionModal
        isOpen={isDeleteSessionModalOpen}
        onRequestClose={() => setIsDeleteSessionModalOpen(false)}
        onDelete={confirmDeleteSession}
        session={sessionToDelete}
      />
      <ChatContextModal
        isOpen={isChatContextModalOpen}
        onRequestClose={() => setIsChatContextModalOpen(false)}
        message={chatLog[chatLog.length - 1]}
        />
    </div>
  );
}

export default Chat;