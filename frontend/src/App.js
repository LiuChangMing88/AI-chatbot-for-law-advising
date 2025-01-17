import { BrowserRouter as Router, Route, Routes, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import SignIn from './components/SignIn';
import SignUp from './components/SignUp';
import Chat from './components/Chat/Chat';

function App() {
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/chat');
    }
  }, [navigate]);

  return (
    <Routes>
      <Route path="/signin" element={<SignIn/>} />
      <Route path="/signup" element={<SignUp/>} />
      <Route path="/chat" element={<Chat/>} />
      <Route path="/" element={<SignIn/>} /> {/* Default route */}
    </Routes>
  );
}

function AppWrapper() {
  return (
    <Router>
      <App />
    </Router>
  );
}

export default AppWrapper;