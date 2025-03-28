# Dobby the Email Elf

Meet Dobby, a sprightly Tkinter-crafted elf who flits through Gmail fetching unread scrolls (emails), conjures clever replies with DeepSeek’s magic (via Ollama), and sprinkles document wisdom using a RAG system (sentence-transformers + FAISS). He’s Thorin’s lightweight cousin—less beard, more bounce—here to save you hours with his nimble tricks!

## Elf Tricks Up His Sleeve
- **Scroll-Snatching**: Nabs unread emails via IMAP and flings replies back with SMTP.
- **Word-Weaving**: Brews context-aware responses with DeepSeek (1.5B model) magic.
- **Tome-Taming**: Mines PDFs into ~10-15 chunks of lore with RAG, for replies with a scholarly twist.
- **Cottage Charm**: A dark-themed Tkinter lair with stretchy panels and a chattering status bar.



## Installation
1. Clone the repo:
   ```bash
   git clone https://github.com/yourusername/Email-AI-App.git
   cd Email-AI-App

## Install dependencies:
bash

pip install -r requirements.txt

## Set up DeepSeek:
Install Ollama, then run ollama pull deepseek-r1:1.5b to use it locally.

## Update Gmail credentials:
In main.py, replace email_config with your Gmail email and app password (generate one via Google Account settings).

## Usage
Run the app:
python main.py

Click "Select Docs" to load a folder with documents (e.g., PDFs).

Click "Fetch Emails" to see unread Gmail emails.

Select an email, click "Generate Reply" to draft a response, then "Approve & Send" to send it.

