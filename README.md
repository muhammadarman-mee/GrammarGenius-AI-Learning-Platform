# **GrammarGenius: AI-Powered Language Learning Platform**

**GrammarGenius** is an interactive, automated system designed to bridge the gap in language acquisition by providing immediate, personalized feedback. It offers real-time grammar rectification, vocabulary tips, and voice-enabled practice to help users accelerate their journey toward conversational fluency.

---

## **🚀 Key Features**

* **Real-Time Grammar Rectification:** Automatically detects and corrects grammatical errors in user input using advanced AI.
* **Multi-Language Support:** Comprehensive tutoring for languages including **English, Spanish, French, and Urdu**.
* **Voice-to-Voice Interaction:** Integrated **Web Speech Recognition** for voice input and **Google Cloud Text-to-Speech (TTS)** for natural-sounding audio feedback.
* **Skill Level Estimation:** Dynamically evaluates the user's proficiency level based on the accuracy and complexity of their input.
* **Linguistic Insights:** Provides concise explanations for corrections and pertinent vocabulary tips to enhance learning.
* **Persistent Chat History:** Allows users to track their progress and review previous sessions.

---

## **🛠️ Technology Stack**

* **Backend:** Python with **Flask** (Robust API management).
* **AI Engine:** **Gemini AI Model** (Interfacing with `gemini-1.5-flash` for intelligent tutoring).
* **Frontend:** JavaScript-driven interface for dynamic content rendering.
* **Voice Services:** Google Cloud Text-to-Speech & Web Speech API.
* **Styling:** Responsive UI design for a seamless learning experience across devices.

---

## **📂 System Functionality**

1. **Input Layer:** Users provide input via text or voice (Speech-to-Text).
2. **Processing Layer:** The Flask backend sends data to the Gemini AI model for analysis.
3. **Output Layer:** The system returns corrected text, explains the "why" behind the correction, and reads the response aloud using TTS.

---

## **🔧 Installation & Setup**

1. **Clone the Repository:**
```bash
git clone https://github.com/your-username/GrammarGenius-AI-Learning.git
cd GrammarGenius-AI-Learning

```


2. **Install Dependencies:**
```bash
pip install -r requirements.txt

```


3. **Environment Variables:**
* Add your `GOOGLE_API_KEY` to the environment settings.


4. **Run the App:**
```bash
python app.py

```


5. **Access the Platform:** Open `http://127.0.0.1:5000/` in your browser.

---

## **🎓 Author**

**Muhammad Arman** **Software Engineer** *Bachelor of Science in Software Engineering* *University of Sahiwal*

---

### **💡 Pro-Tip for your CV:**

When you list this project on your CV, use this bullet point:

> * **GrammarGenius:** Developed an AI-driven language platform using **Python (Flask)** and **Gemini AI**, featuring real-time grammar correction and **Google Cloud TTS** for multi-language auditory feedback.
> 
>
