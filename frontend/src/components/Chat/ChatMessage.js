import { FaUser, FaRobot } from "react-icons/fa";
import './Chat.css';

const ChatMessage = ({ message }) => {
  const isAI = message.role === "AI";
  let response = message.content;
  if (response.includes("### Assistant:")) {
    response = response.split("### Assistant:").pop().trim();
  } else {
    response = response.trim();
  }
  return (
    <div className={`chat-message ${isAI ? "AI" : "user"}`}>
      <div className="chat-avatar">
        {isAI ? <FaRobot className="icon" /> : <FaUser className="icon" />}
      </div>
      <div className={`chat-content ${isAI ? "AI-chat" : "user-chat"}`}>
        {response}
      </div>
    </div>
  );
}

export default ChatMessage;