import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import requests
import json
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.header import decode_header
from document_processor import process_document_folder, RAGSystem
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail IMAP Login Function
def connect_to_gmail_imap(user, password):
    imap_url = 'imap.gmail.com'
    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(user, password)
        mail.select('inbox')
        logger.info("Connected successfully to Gmail IMAP!")
        return mail
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        raise

def safe_decode(payload, default_charset='utf-8'):
    """Safely decode bytes with fallback to windows-1252 if the default charset fails."""
    if not isinstance(payload, bytes):
        return payload  # Already decoded or a string
    try:
        return payload.decode(default_charset)
    except UnicodeDecodeError:
        logger.info(f"Failed to decode with {default_charset}, falling back to windows-1252")
        return payload.decode('windows-1252', errors='replace')

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Email AI")
        self.root.geometry("900x600")

        # Apply a modern theme using ttkbootstrap (darkly for dark mode)
        self.style = ttkb.Style(theme="darkly")

        # Initialize RAG system
        self.rag_system = RAGSystem()
        self.document_folder = None

        # Main container using PanedWindow for resizable panels
        self.paned_window = ttkb.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left Panel (Email List)
        self.left_frame = ttkb.Frame(self.paned_window, padding="10")
        self.paned_window.add(self.left_frame, weight=1)

        self.email_listbox = tk.Listbox(
            self.left_frame,
            height=20,
            width=30,
            font=("Helvetica", 10),
            bg=self.style.colors.get("secondary"),
            fg=self.style.colors.get("light"),
            selectbackground=self.style.colors.get("info"),
            selectforeground=self.style.colors.get("light"),
            activestyle="none"
        )
        self.email_listbox.pack(fill=tk.BOTH, expand=True)
        self.email_listbox.bind("<<ListboxSelect>>", self.on_email_select)

        # Right Panel (Main Content)
        self.right_frame = ttkb.Frame(self.paned_window, padding="10")
        self.paned_window.add(self.right_frame, weight=3)

        # Incoming Message Section
        self.incoming_frame = ttkb.LabelFrame(self.right_frame, text="Incoming Message", padding="10")
        self.incoming_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.message_box = scrolledtext.ScrolledText(
            self.incoming_frame, height=8, width=60, wrap=tk.WORD, font=("Helvetica", 10)
        )
        self.message_box.pack(fill=tk.BOTH, expand=True)
        self.message_box.configure(bg=self.style.colors.get("dark"), fg=self.style.colors.get("light"))

        # Draft Reply Section
        self.reply_frame = ttkb.LabelFrame(self.right_frame, text="Draft Reply", padding="10")
        self.reply_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.reply_box = scrolledtext.ScrolledText(
            self.reply_frame, height=8, width=60, wrap=tk.WORD, font=("Helvetica", 10)
        )
        self.reply_box.pack(fill=tk.BOTH, expand=True)
        self.reply_box.configure(bg=self.style.colors.get("dark"), fg=self.style.colors.get("light"))

        # Buttons Section
        self.button_frame = ttkb.Frame(self.right_frame)
        self.button_frame.pack(fill=tk.X, pady=10)

        self.fetch_email_btn = ttkb.Button(
            self.button_frame, text="Fetch Emails", command=self.fetch_emails, style="primary.TButton"
        )
        self.fetch_email_btn.pack(side=tk.LEFT, padx=5)

        self.generate_btn = ttkb.Button(
            self.button_frame, text="Generate Reply", command=self.generate_reply, style="info.TButton"
        )
        self.generate_btn.pack(side=tk.LEFT, padx=5)

        self.approve_btn = ttkb.Button(
            self.button_frame, text="Approve & Send", command=self.approve_reply, style="success.TButton"
        )
        self.approve_btn.pack(side=tk.LEFT, padx=5)

        # Add Document Folder Button
        self.folder_btn = ttkb.Button(
            self.button_frame, text="Select Docs", command=self.select_document_folder, style="warning.TButton"
        )
        self.folder_btn.pack(side=tk.LEFT, padx=5)

        # Status Bar
        self.status_frame = ttkb.Frame(self.root, relief=tk.SUNKEN, padding="5")
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = ttkb.Label(
            self.status_frame, text="Ready", font=("Helvetica", 10), anchor=tk.W
        )
        self.status_label.pack(fill=tk.X)

        # Email configuration for Gmail
        self.email_config = {
            "username": "your email here",
            "password": "app password here",
            "imap_server": "imap.gmail.com",
            "smtp_server": "smtp.gmail.com"
        }

        # Store emails and current message
        self.emails = []
        self.current_message = None

    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update()

    def select_document_folder(self):
        self.update_status("Selecting document folder...")
        folder = tk.filedialog.askdirectory(title="Select Document Folder")
        if folder:
            self.document_folder = folder
            self.update_status(f"Processing documents from {folder}...")
            chunks = process_document_folder(folder, chunk_size=200)  # Add chunk_size here
            success = self.rag_system.build_index(chunks)
            if success:
                self.update_status(f"Loaded {len(chunks)} document chunks")
            else:
                self.update_status("No valid documents found")

    def fetch_emails(self):
        self.update_status("Fetching emails...")
        self.email_listbox.delete(0, tk.END)
        self.emails = []

        try:
            mail = connect_to_gmail_imap(self.email_config["username"], self.email_config["password"])
            _, data = mail.search(None, "UNSEEN")
            email_ids = data[0].split()

            if not email_ids:
                self.message_box.delete("1.0", tk.END)
                self.message_box.insert(tk.END, "No unread emails found.")
                mail.logout()
                self.update_status("No unread emails found.")
                return

            email_ids = email_ids[-10:]  # Limit to last 10 unread emails
            for i, email_id in enumerate(email_ids):
                _, msg_data = mail.fetch(email_id, "(RFC822)")
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)

                # Decode From header
                from_decoded, from_charset = decode_header(email_message["From"])[0]
                from_header = safe_decode(from_decoded, from_charset or 'utf-8')
                sender = from_header

                # Decode Subject header
                subject_decoded, subject_charset = decode_header(email_message["Subject"])[0]
                subject = safe_decode(subject_decoded, subject_charset or 'utf-8')

                # Decode email body
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            charset = part.get_content_charset() or 'utf-8'
                            logger.info(f"Email charset (multipart): {charset}")
                            payload = part.get_payload(decode=True)
                            body = safe_decode(payload, charset)
                            break
                else:
                    charset = email_message.get_content_charset() or 'utf-8'
                    logger.info(f"Email charset (non-multipart): {charset}")
                    payload = email_message.get_payload(decode=True)
                    body = safe_decode(payload, charset)

                snippet = body.split("\n")[0][:50] + ("..." if len(body.split("\n")[0]) > 50 else "")

                self.emails.append({
                    "id": email_id,
                    "sender": sender,
                    "subject": subject,
                    "body": body,
                    "snippet": snippet
                })

                self.email_listbox.insert(tk.END, f"{sender}\n{subject}\n{snippet}\n")

                mail.logout()
                self.update_status(f"Fetched {len(email_ids)} emails.")

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            self.message_box.delete("1.0", tk.END)
            self.message_box.insert(tk.END, f"Error fetching emails: {str(e)}")
            self.update_status("Error fetching emails.")

    def on_email_select(self, event):
        selection = self.email_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        email_data = self.emails[index]

        email_content = f"From: {email_data['sender']}\nSubject: {email_data['subject']}\n\n{email_data['body']}"
        self.message_box.delete("1.0", tk.END)
        self.message_box.insert(tk.END, email_content)

        self.current_message = {
            "sender": email_data["sender"],
            "subject": email_data["subject"],
            "body": email_data["body"]
        }

        self.update_status("Email selected.")

    def generate_reply(self):
        self.update_status("Generating reply...")
        message = self.message_box.get("1.0", tk.END).strip()
        if not message:
            self.reply_box.delete("1.0", tk.END)
            self.reply_box.insert(tk.END, "No message to generate a reply for.")
            self.update_status("No message to generate a reply for.")
            return

        try:
            # Retrieve relevant document chunks if RAG is set up
            context = ""
            if self.rag_system.index:
                relevant_chunks = self.rag_system.retrieve_relevant_chunks(message)
                if relevant_chunks:
                    context = "\n\nRelevant Document Context:\n" + "\n".join(relevant_chunks)

            # Construct prompt with email and document context
            prompt = f"Generate a reply to this message: {message}{context}"
            payload = {"model": "deepseek-r1:1.5b", "prompt": prompt}
            response = requests.post("http://localhost:11434/api/generate", json=payload, stream=True)
            response.raise_for_status()

            full_reply = ""
            for line in response.iter_lines():
                if line:
                    json_data = json.loads(line.decode('utf-8'))
                    logger.debug(f"Received line: {json_data}")
                    if "response" in json_data:
                        full_reply += json_data["response"]

            logger.info(f"Full reply from DeepSeek: {full_reply}")

            # Simplified parsing: Use the full reply as-is if no <think> tag
            if "<think>" in full_reply and "</think>" in full_reply:
                reply = full_reply.split("</think>")[1].strip()
            else:
                reply = full_reply.strip()

            # Fallback if reply is empty
            reply = reply if reply else "Error: No response content from DeepSeek"
        except Exception as e:
            reply = f"Error: {str(e)}"
            logger.error(f"Error generating reply: {e}")
            self.update_status("Error generating reply.")

        self.reply_box.delete("1.0", tk.END)
        self.reply_box.insert(tk.END, reply)
        if "Error" not in reply:
            self.update_status("Reply generated successfully.")

    def approve_reply(self):
        self.update_status("Sending email...")
        if not self.current_message:
            self.reply_box.delete("1.0", tk.END)
            self.reply_box.insert(tk.END, "No message selected to reply to.")
            self.update_status("No message selected to reply to.")
            return

        reply_text = self.reply_box.get("1.0", tk.END).strip()
        if not reply_text:
            self.reply_box.delete("1.0", tk.END)
            self.reply_box.insert(tk.END, "No reply to send.")
            self.update_status("No reply to send.")
            return

        try:
            msg = MIMEText(reply_text)
            msg["Subject"] = f"Re: {self.current_message['subject']}"
            msg["From"] = self.email_config["username"]
            msg["To"] = self.current_message["sender"]

            with smtplib.SMTP(self.email_config["smtp_server"], 587, timeout=30) as server:
                server.starttls()
                server.login(self.email_config["username"], self.email_config["password"])
                server.send_message(msg)

            self.reply_box.delete("1.0", tk.END)
            self.reply_box.insert(tk.END, "Email reply sent successfully!")
            self.current_message = None
            self.update_status("Email sent successfully.")

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            self.reply_box.delete("1.0", tk.END)
            self.reply_box.insert(tk.END, f"Error sending email: {str(e)}")
            self.update_status("Error sending email.")

if __name__ == "__main__":
    root = ttkb.Window()
    app = MainWindow(root)
    root.mainloop()