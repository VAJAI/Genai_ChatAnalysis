"use client";
import React, { useEffect, useRef, useState } from "react";
import Navebar from './components/Navebar';

export default function Page() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState([]);
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);

  const chatContainerRef = useRef(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleFileUpload = async () => {
    if (!file) return alert("Please select a file to upload");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to upload file");
      }

      const data = await response.json();
      setUploadedFile(data.filename);
      alert("File uploaded successfully");
    } catch (error) {
      console.error(error);
      alert("Error uploading file");
    }
  };

  const handleSubmit = async (e) => {
    if (!question.trim()) return;
    e.preventDefault();
    setLoading(true);
    setAnswer((prev) => [...prev, { question, answer: "..." }]);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: question, file: uploadedFile }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch response");
      }

      const data = await response.json();
      const answer = data.answer || "No response received";

      setAnswer((prev) => {
        const updatedAnswer = [...prev];
        updatedAnswer[updatedAnswer.length - 1].answer = answer;
        return updatedAnswer;
      });
    } catch (error) {
      console.error(error);
      setAnswer((prev) => {
        const updatedAnswer = [...prev];
        updatedAnswer[updatedAnswer.length - 1].answer =
          "Error occurred, please try again";
        return updatedAnswer;
      });
    } finally {
      setLoading(false);
      setQuestion("");
    }
  };

  const clearChat = () => {
    setAnswer([]);
  };

  return (
    <div>
      <Navebar />
      
      <div className="upload_file">
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleFileUpload}>Upload File</button>
      </div>

      <div ref={chatContainerRef}  className="conversion_box">
        {answer.length === 0 ? (
          <div className="chat_st">"No messages yet. Start your conversation."</div>
        ) : (
          answer.map((entry, index) => (
            <div key={index}>
              <br />
              <div className="chat_you"> You: {entry.question}</div>
              <br />
              <div className="chat_ai"> AI: {entry.answer}</div>
              <br />
            </div>
          ))
        )}
        {loading && <div>AI is typing ....</div>}
      </div>

      <div className="chatbox">
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Ask anything..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? "Submitting..." : "Submit"}
          </button>
          <button type="button" onClick={clearChat}>
            Clear Chat
          </button>
        </form>
      </div>
    </div>
  );
}