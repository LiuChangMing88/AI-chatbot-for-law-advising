import React from 'react';
import Modal from 'react-modal';
import './Chat.css';

Modal.setAppElement('#root');

const ChatContextModal = ({ isOpen, onRequestClose, message }) => {
    let response = message?.content;
    let context = '';
    if (response?.includes("### Context:")) {
        context = response?.split("### Context:")[1].split("### Human")[0].trim();
    }

    if (context == '') {
        context = "No context available";
    }
  
return (
    <Modal
        isOpen={isOpen}
        onRequestClose={onRequestClose}
        contentLabel="Context of last message"
        className="chat-session-modal context-modal"
        overlayClassName="custom-modal-overlay"
    >
        <h2>Context of last message</h2>
        <div className='context-message-box'>
            <p className='context-message'>{context}</p>
        </div>
        <div className="modal-button-div">
            <button onClick={onRequestClose}>Close</button>
        </div>
    </Modal>
);
};

export default ChatContextModal;