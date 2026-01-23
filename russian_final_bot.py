"""
Ultimate Russian Tutor - TORFL A1 Preparation
Features:
- Beautiful Streamlit web interface
- Spaced repetition algorithm
- Audio pronunciation
- Vocabulary tracking with difficulty levels
- Progress visualization
"""

import streamlit as st
from groq import Groq
import json
import os
from datetime import datetime, timedelta
from gtts import gTTS
import base64
from io import BytesIO

class SpacedRepetitionTutor:
    def __init__(self, api_key):
        """Initialize the tutor with spaced repetition"""
        self.client = Groq(api_key=api_key)
        self.data_file = "russian_tutor_data.json"
        self.load_data()
    
    def load_data(self):
        """Load progress with spaced repetition data"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.vocabulary = data.get('vocabulary', [])
                self.total_sessions = data.get('total_sessions', 0)
                self.total_messages = data.get('total_messages', 0)
        else:
            self.vocabulary = []
            self.total_sessions = 0
            self.total_messages = 0
    
    def save_data(self):
        """Save all data"""
        data = {
            'vocabulary': self.vocabulary,
            'total_sessions': self.total_sessions,
            'total_messages': self.total_messages,
            'last_session': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_vocabulary(self, word, translation, example=""):
        """Add word with spaced repetition tracking"""
        # Check if exists
        for item in self.vocabulary:
            if item['word'].lower() == word.lower():
                return
        
        self.vocabulary.append({
            'word': word,
            'translation': translation,
            'example': example,
            'learned_date': datetime.now().strftime('%Y-%m-%d'),
            'last_reviewed': datetime.now().strftime('%Y-%m-%d'),
            'next_review': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'difficulty': 0,  # 0=new, 1=easy, 2=medium, 3=hard
            'correct_count': 0,
            'incorrect_count': 0,
            'total_reviews': 0
        })
        self.save_data()
    
    def get_words_to_review(self):
        """Get words that need review based on spaced repetition"""
        today = datetime.now().strftime('%Y-%m-%d')
        review_words = []
        
        for word in self.vocabulary:
            if word.get('next_review', today) <= today:
                review_words.append(word)
        
        return review_words
    
    def update_word_difficulty(self, word, is_correct):
        """Update word difficulty based on answer"""
        for item in self.vocabulary:
            if item['word'].lower() == word.lower():
                item['total_reviews'] += 1
                item['last_reviewed'] = datetime.now().strftime('%Y-%m-%d')
                
                if is_correct:
                    item['correct_count'] += 1
                    # Increase interval
                    if item['difficulty'] == 0:
                        days = 1
                    elif item['difficulty'] == 1:
                        days = 3
                    elif item['difficulty'] == 2:
                        days = 7
                    else:
                        days = 14
                    
                    # Move to easier if doing well
                    if item['correct_count'] >= 3:
                        item['difficulty'] = max(0, item['difficulty'] - 1)
                else:
                    item['incorrect_count'] += 1
                    days = 1  # Review tomorrow
                    # Move to harder
                    item['difficulty'] = min(3, item['difficulty'] + 1)
                
                item['next_review'] = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
                self.save_data()
                break
    
    def get_chat_response(self, messages):
        """Get response from Groq"""
        try:
            response = self.client.chat.completions.create(
                model='llama-3.1-8b-instant',
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def extract_vocabulary(self, text):
        """Extract new vocabulary from response"""
        if "NEW_WORD:" in text:
            lines = text.split('\n')
            for line in lines:
                if line.strip().startswith("NEW_WORD:"):
                    try:
                        content = line.split("NEW_WORD:")[1].strip()
                        if '|' in content:
                            word_part, example = content.split('|')
                            example = example.replace('Example:', '').strip()
                        else:
                            word_part = content
                            example = ""
                        
                        if '=' in word_part:
                            word, translation = word_part.split('=')
                            word = word.strip()
                            translation = translation.strip()
                            self.add_vocabulary(word, translation, example)
                            return word
                    except:
                        pass
        return None

def text_to_speech_base64(text, lang='ru'):
    """Convert text to speech and return base64 audio"""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_base64 = base64.b64encode(audio_buffer.read()).decode()
        return audio_base64
    except Exception as e:
        st.error(f"Audio error: {e}")
        return None

def play_audio_button(text, label="🔊 Listen", key=None):
    """Create a button that plays audio - FIXED VERSION"""
    if key is None:
        key = f"audio_{hash(text)}_{hash(label)}"
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button(label, key=key):
            audio_base64 = text_to_speech_base64(text)
            if audio_base64:
                # Use st.audio instead of HTML
                audio_bytes = base64.b64decode(audio_base64)
                st.audio(audio_bytes, format='audio/mp3', start_time=0)

def main():
    st.set_page_config(
        page_title="Russian Tutor - TORFL A1",
        page_icon="🇷🇺",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            color: #1E88E5;
            text-align: center;
            padding: 1rem;
        }
        .stat-box {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
        }
        .vocab-card {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #1E88E5;
            margin: 0.5rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🇷🇺 Russian Tutor - TORFL A1</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'tutor' not in st.session_state:
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            st.warning("⚠️ Please set your GROQ_API_KEY environment variable")
            api_key = st.text_input("Or enter your Groq API key:", type="password")
            if not api_key:
                st.stop()
        st.session_state.tutor = SpacedRepetitionTutor(api_key)
        st.session_state.messages = []
    
    tutor = st.session_state.tutor
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Your Progress")
        
        # Stats
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div class="stat-box">
                    <h3>{len(tutor.vocabulary)}</h3>
                    <p>Words Learned</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="stat-box">
                    <h3>{tutor.total_sessions}</h3>
                    <p>Sessions</p>
                </div>
            """, unsafe_allow_html=True)
        
        # Words to review
        review_words = tutor.get_words_to_review()
        if review_words:
            st.warning(f"📝 {len(review_words)} words need review today!")
        
        st.divider()
        
        # Mode selection
        mode = st.radio("Choose Mode:", ["💬 Chat", "📚 Vocabulary", "🎯 Quiz"])
        
        st.divider()
        
        if st.button("🔄 Reset Progress", type="secondary"):
            if st.checkbox("Are you sure?"):
                tutor.vocabulary = []
                tutor.total_sessions = 0
                tutor.save_data()
                st.success("Progress reset!")
                st.rerun()


    # Main content based on mode
    if mode == "💬 Chat":
        st.header("Chat with Your Tutor")
        
        # Chat messages
        chat_container = st.container()
        with chat_container:
            for idx, msg in enumerate(st.session_state.messages):
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    # Add audio button for Russian text
                    if msg["role"] == "assistant":
                        # Extract Russian words/sentences for audio
                        lines = msg["content"].split('\n')
                        audio_count = 0
                        for line_idx, line in enumerate(lines):
                            if any(ord(c) > 127 for c in line) and len(line.strip()) < 100 and line.strip():
                                play_audio_button(line.strip(), "🔊", key=f"chat_audio_{idx}_{line_idx}")
                                audio_count += 1
                                if audio_count >= 3:  # Limit audio buttons per message
                                    break
        
        # Chat input
        user_input = st.chat_input("Ask your tutor anything...")
        
        if user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get system prompt
            system_prompt = """You are a helpful Russian language tutor for TORFL A1 exam preparation.

When teaching new vocabulary, ALWAYS use this format:
NEW_WORD: [Russian] = [English] | Example: [sentence]

Be encouraging, patient, and keep it simple for beginners."""
            
            # Prepare messages for API
            api_messages = [{"role": "system", "content": system_prompt}]
            api_messages.extend(st.session_state.messages)
            
            # Get response
            response = tutor.get_chat_response(api_messages)
            
            # Extract vocabulary
            new_word = tutor.extract_vocabulary(response)
            if new_word:
                st.toast(f"✅ Saved: {new_word}", icon="📝")
            
            # Add assistant message
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.rerun()
    
    elif mode == "📚 Vocabulary":
        st.header("Your Vocabulary List")
        
        if not tutor.vocabulary:
            st.info("No words learned yet. Start chatting with your tutor!")
        else:
            # Search bar
            search = st.text_input("🔍 Search vocabulary:", "")
            
            # Filter by difficulty
            difficulty_filter = st.selectbox(
                "Filter by difficulty:",
                ["All", "New", "Easy", "Medium", "Hard"]
            )
            
            # Display vocabulary
            for i, word_data in enumerate(tutor.vocabulary):
                if search.lower() in word_data['word'].lower() or search.lower() in word_data['translation'].lower():
                    if difficulty_filter == "All" or \
                       (difficulty_filter == "New" and word_data['difficulty'] == 0) or \
                       (difficulty_filter == "Easy" and word_data['difficulty'] == 1) or \
                       (difficulty_filter == "Medium" and word_data['difficulty'] == 2) or \
                       (difficulty_filter == "Hard" and word_data['difficulty'] == 3):
                        
                        difficulty_labels = ["🆕 New", "✅ Easy", "⚡ Medium", "🔥 Hard"]
                        difficulty_label = difficulty_labels[word_data['difficulty']]
                        
                        st.markdown(f"""
                            <div class="vocab-card">
                                <h3>{word_data['word']} = {word_data['translation']}</h3>
                                <p><i>{word_data.get('example', '')}</i></p>
                                <small>
                                    {difficulty_label} | 
                                    Reviews: {word_data['total_reviews']} | 
                                    Correct: {word_data['correct_count']} | 
                                    Next review: {word_data.get('next_review', 'N/A')}
                                </small>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Audio button
                        play_audio_button(word_data['word'], "🔊 Pronounce", key=f"vocab_{i}")
                        
                        st.divider()
    
    elif mode == "🎯 Quiz":
        st.header("Vocabulary Quiz")
        
        review_words = tutor.get_words_to_review()
        
        if not review_words:
            st.success("🎉 No words to review today! Great job!")
            if len(tutor.vocabulary) > 0:
                st.info("Come back tomorrow for more practice.")
        else:
            st.write(f"📝 You have **{len(review_words)}** words to review today")
            
            if 'quiz_index' not in st.session_state:
                st.session_state.quiz_index = 0
                st.session_state.quiz_score = 0
            
            if st.session_state.quiz_index < len(review_words):
                current_word = review_words[st.session_state.quiz_index]
                
                st.subheader(f"Question {st.session_state.quiz_index + 1} of {len(review_words)}")
                
                # Play audio
                st.write("### Listen and translate:")
                play_audio_button(current_word['word'], "🔊 Play Audio", key=f"quiz_{st.session_state.quiz_index}")
                
                st.write(f"**{current_word['word']}**")
                
                # Answer input
                user_answer = st.text_input("Your answer:", key=f"answer_{st.session_state.quiz_index}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Submit", type="primary"):
                        is_correct = user_answer.lower().strip() == current_word['translation'].lower().strip()
                        
                        if is_correct:
                            st.success("✅ Correct!")
                            st.session_state.quiz_score += 1
                            tutor.update_word_difficulty(current_word['word'], True)
                        else:
                            st.error(f"❌ Incorrect. The answer is: {current_word['translation']}")
                            tutor.update_word_difficulty(current_word['word'], False)
                        
                        st.session_state.quiz_index += 1
                        st.rerun()
                
                with col2:
                    if st.button("⏭️ Skip"):
                        st.session_state.quiz_index += 1
                        st.rerun()
            else:
                # Quiz completed
                st.balloons()
                st.success(f"🎉 Quiz Complete! Score: {st.session_state.quiz_score}/{len(review_words)}")
                
                if st.button("🔄 Start New Quiz"):
                    st.session_state.quiz_index = 0
                    st.session_state.quiz_score = 0
                    st.rerun()

if __name__ == "__main__":
    main()