#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import PyPDF2
import subprocess
import threading
import os
import time

class PDFVoiceReader:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Voice Reader")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        self.pdf_path = None
        self.total_pages = 0
        self.is_reading = False
        self.current_process = None
        
        self.setup_ui()
        self.test_speech()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="PDF Voice Reader", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # PDF Selection
        pdf_frame = ttk.LabelFrame(main_frame, text="PDF File", padding="10")
        pdf_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.pdf_label = ttk.Label(pdf_frame, text="No PDF selected", foreground="red")
        self.pdf_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(pdf_frame, text="Choose PDF", 
                  command=self.choose_pdf).grid(row=0, column=1, padx=(10, 0))
        
        # Page Selection
        page_frame = ttk.LabelFrame(main_frame, text="Reading Range", padding="10")
        page_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(page_frame, text="From Page:").grid(row=0, column=0)
        self.start_spin = ttk.Spinbox(page_frame, from_=1, to=100, width=8)
        self.start_spin.grid(row=0, column=1, padx=(5, 20))
        self.start_spin.insert(0, "1")
        
        ttk.Label(page_frame, text="To Page:").grid(row=0, column=2)
        self.end_spin = ttk.Spinbox(page_frame, from_=1, to=100, width=8)
        self.end_spin.grid(row=0, column=3, padx=(5, 0))
        self.end_spin.insert(0, "1")
        
        self.page_count_label = ttk.Label(page_frame, text="Total pages: 0")
        self.page_count_label.grid(row=1, column=0, columnspan=4, pady=(10, 0))
        
        # Voice Selection
        voice_frame = ttk.LabelFrame(main_frame, text="Voice Settings", padding="10")
        voice_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(voice_frame, text="Voice:").grid(row=0, column=0)
        self.voice_var = tk.StringVar(value="Alex")
        voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var, 
                                  values=["Alex", "Samantha", "Victoria", "Daniel"], 
                                  state="readonly")
        voice_combo.grid(row=0, column=1, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        self.read_button = ttk.Button(button_frame, text="Start Reading", 
                                     command=self.start_reading)
        self.read_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                    command=self.stop_reading, state="disabled")
        self.stop_button.grid(row=0, column=1)
        
        # Test Button
        ttk.Button(button_frame, text="Test Voice", 
                  command=self.test_speech).grid(row=0, column=2, padx=(10, 0))
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Ready to read PDFs")
        self.status_label.grid(row=5, column=0, columnspan=2)
        
        # Current Page Display
        self.current_page_label = ttk.Label(main_frame, text="", font=("Arial", 10))
        self.current_page_label.grid(row=6, column=0, columnspan=2)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        pdf_frame.columnconfigure(0, weight=1)
        page_frame.columnconfigure(1, weight=1)
        page_frame.columnconfigure(3, weight=1)
        voice_frame.columnconfigure(1, weight=1)
        
    def test_speech(self):
        """Test if speech works"""
        try:
            # Use full path to say command
            result = subprocess.run(["/usr/bin/say", "-v", self.voice_var.get(), "Test voice is working"], 
                                  capture_output=True, text=True, timeout=5)
            self.status_label.config(text="Voice test successful!", foreground="green")
        except subprocess.TimeoutExpired:
            self.status_label.config(text="Voice test: Timed out", foreground="orange")
        except Exception as e:
            self.status_label.config(text=f"Voice test failed: {str(e)}", foreground="red")
        
    def choose_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            self.pdf_path = file_path
            self.pdf_label.config(text=os.path.basename(file_path), foreground="green")
            self.load_pdf_info()
            
    def load_pdf_info(self):
        try:
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                self.total_pages = len(reader.pages)
                
                self.start_spin.config(to=self.total_pages)
                self.end_spin.config(to=self.total_pages)
                self.start_spin.delete(0, tk.END)
                self.start_spin.insert(0, "1")
                self.end_spin.delete(0, tk.END)
                self.end_spin.insert(0, str(self.total_pages))
                
                self.page_count_label.config(text=f"Total pages: {self.total_pages}")
                self.status_label.config(text="PDF loaded successfully - Ready to read")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF: {str(e)}")
            
    def start_reading(self):
        if not self.pdf_path:
            messagebox.showwarning("Warning", "Please select a PDF file first")
            return
            
        try:
            start_page = int(self.start_spin.get())
            end_page = int(self.end_spin.get())
            
            if start_page < 1 or end_page > self.total_pages or start_page > end_page:
                messagebox.showwarning("Warning", "Invalid page range")
                return
                
            self.is_reading = True
            self.read_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_label.config(text="Starting to read...")
            
            # Run reading in separate thread
            thread = threading.Thread(target=self.read_pages, args=(start_page, end_page))
            thread.daemon = True
            thread.start()
            
        except ValueError:
            messagebox.showwarning("Warning", "Please enter valid page numbers")
            
    def stop_reading(self):
        self.is_reading = False
        if self.current_process:
            self.current_process.terminate()
            self.current_process = None
        self.read_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Stopped")
        self.current_page_label.config(text="")
        
    def read_pages(self, start_page, end_page):
        try:
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                for page_num in range(start_page - 1, end_page):
                    if not self.is_reading:
                        break
                        
                    current_page = page_num + 1
                    self.root.after(0, lambda p=current_page: self.current_page_label.config(
                        text=f"Reading Page {p}"))
                    
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"Reading page {current_page} of {end_page}"))
                    
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    
                    if text and text.strip():
                        # Clean up the text
                        text = ' '.join(text.split())
                        print(f"Page {current_page} text: {text[:100]}...")  # Debug
                        
                        # Speak this page using direct subprocess call
                        self.speak_text_direct(text)
                    
                    # Check if we should continue after speaking
                    if not self.is_reading:
                        break
                
                if self.is_reading:
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"Finished reading pages {start_page}-{end_page}"))
                    self.root.after(0, lambda: self.current_page_label.config(text=""))
                        
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(
                text=f"Error: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Reading failed: {str(e)}"))
        
        self.root.after(0, self.reset_ui)
        
    def speak_text_direct(self, text):
        """Use direct subprocess call to say command - SIMPLE AND RELIABLE"""
        try:
            # Split text into chunks if it's too long (avoid command line limits)
            chunks = self.split_text(text, 1000)  # 1000 characters per chunk
            
            for chunk in chunks:
                if not self.is_reading:
                    break
                    
                # Use the full path to say command with explicit voice
                cmd = ["/usr/bin/say", "-v", self.voice_var.get(), chunk]
                
                print(f"Speaking chunk: {chunk[:50]}...")  # Debug
                
                # Run say command and wait for completion
                self.current_process = subprocess.Popen(cmd)
                self.current_process.wait()  # Wait for this chunk to finish
                
                if not self.is_reading:
                    self.current_process.terminate()
                    break
                    
            return True
            
        except Exception as e:
            print(f"Speech error: {e}")
            self.root.after(0, lambda: self.status_label.config(
                text=f"Speech error: {str(e)}"))
            return False
    
    def split_text(self, text, max_length):
        """Split text into chunks without breaking words"""
        words = text.split()
        chunks = []
        current_chunk = ""
        
        for word in words:
            if len(current_chunk) + len(word) + 1 <= max_length:
                current_chunk += " " + word if current_chunk else word
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = word
        
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
        
    def reset_ui(self):
        self.is_reading = False
        self.read_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.current_process = None

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFVoiceReader(root)
    root.mainloop()
