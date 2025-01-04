import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import SignIn from './components/SignIn';
import SignUp from './components/SignUp';
import Chat from './components/Chat/Chat';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/signin" element={<SignIn/>} />
        <Route path="/signup" element={<SignUp/>} />
        <Route path="/chat" element={<Chat/>} />
        <Route path="/" element={<SignIn/>} /> {/* Default route */}
      </Routes>
    </Router>
  );
}

export default App;