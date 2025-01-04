import { FaUser, FaRobot } from "react-icons/fa";
import './Chat.css';

const ChatMessage = ({ message }) => {
  const isAI = message.role === "AI";
  return (
    <div className={`chat-message ${isAI ? "AI" : "user"}`}>
      <div className="chat-avatar">
        {isAI ? <FaRobot className="icon" /> : <FaUser className="icon" />}
      </div>
      <div className="chat-content">
        {message.content}
      </div>
    </div>
  );
}

export default ChatMessage;