import './Chat.css';
import { CiChat2 } from "react-icons/ci";
import { BsThreeDotsVertical } from "react-icons/bs";


const ChatSession = ({ session, isActive, onClick }) => {
    return (
        <div className={`chat-session ${isActive ? 'chat-session-active' : ''}`} onClick={onClick}>
            <CiChat2 className={`chat-session-icon ${isActive ? 'chat-session-icon-active' : ''}`}/>
            <div className={`chat-session-name ${isActive ? 'chat-session-name-active' : ''}`}>
                {session.name}
            </div>
            <BsThreeDotsVertical className={`chat-session-options ${isActive ? 'chat-session-options-active' : ''}`}/>
        </div>
    );
}

export default ChatSession;