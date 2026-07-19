import streamlit as st
import os
import random

# Helper to safely rerun across Streamlit versions
def safe_rerun():
    try:
        st.experimental_rerun()
        return
    except Exception:
        # experimental_rerun not available or failed; fallback to stopping execution
        st.session_state["_needs_rerun"] = True
        # st.stop() will halt the script and allow the UI to update on next interaction
        st.stop()

# --- CONFIGURATION ---
# Replace this with the path to your images folder (e.g., "2011" or "photos")
IMAGE_DIR = r"C:\Users\schmi\Desktop\gtp\2011" 

# --- HELPER FUNCTIONS ---
@st.cache_data
def load_game_data(directory):
    """Reads the directory and creates a list of dicts mapping paths to cleaned names."""
    game_data = []
    if not os.path.exists(directory):
        return game_data
        
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    for filename in os.listdir(directory):
        if filename.lower().endswith(valid_extensions):
            # Convert "adam_reno.png" -> "Adam Reno"
            name_core = os.path.splitext(filename)[0]
            clean_name = name_core.replace('_', ' ').title()
            
            game_data.append({
                "image_path": os.path.join(directory, filename),
                "correct_name": clean_name
            })
    return game_data

# --- APP INITIALIZATION ---
st.set_page_config(page_title="Friend Guessing Game", page_icon="👥", layout="centered")
st.title("👥 Guess the Friend!")
st.write("Look at the picture and type the correct name.")

# Initialize Session State variables if they don't exist
if "all_items" not in st.session_state:
    st.session_state.all_items = load_game_data(IMAGE_DIR)
    # Shuffle the list so the order is random every game session
    random.shuffle(st.session_state.all_items)
    
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "feedback" not in st.session_state:
    st.session_state.feedback = None
if "seen_list" not in st.session_state:
    # Each entry: {"name": str, "status": "correct"|"incorrect"}
    st.session_state.seen_list = []
if "awaiting_next" not in st.session_state:
    # When True, user has skipped and must click Next to continue
    st.session_state.awaiting_next = False

# Safety check if directory is empty or wrong
if not st.session_state.all_items:
    st.error(f"No images found in the directory: `{IMAGE_DIR}`. Please verify your path configuration.")
    st.stop()

# --- GAME LOGIC CODE ---
current_idx = st.session_state.current_index
total_images = len(st.session_state.all_items)

if not st.session_state.game_over:
    # Get current item
    current_item = st.session_state.all_items[current_idx]
    correct_answer = current_item["correct_name"]
    
    # Display Score & Progress
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Score", f"{st.session_state.score} / {total_images}")
    with col2:
        st.write(f"**Progress:** Picture {current_idx + 1} of {total_images}")
        st.progress((current_idx + 1) / total_images)
        
    st.markdown("---")
    
    # Display Friend's Image
    st.image(current_item["image_path"], use_container_width=True)
    
    # Guess Form / Skip behavior
    if not st.session_state.awaiting_next:
        with st.form(key="guess_form", clear_on_submit=True):
            user_guess = st.text_input("Who is this?", placeholder="Type name here...").strip()
            col_submit, col_skip = st.columns([1,1])
            with col_submit:
                submit_button = st.form_submit_button(label="Submit Guess")
            with col_skip:
                skip_button = st.form_submit_button(label="Skip")

        if skip_button:
            # Reveal answer, mark as incorrect in seen list, wait for explicit Next
            st.session_state.seen_list.append({"name": correct_answer, "status": "incorrect"})
            st.session_state.feedback = ("skip", f"⏭️ Skipped. The correct name is **{correct_answer}**.")
            st.session_state.awaiting_next = True

        if submit_button:
            if user_guess:
                # Case-insensitive comparison
                if user_guess.lower() == correct_answer.lower():
                    st.session_state.score += 1
                    st.session_state.feedback = ("success", f"🎉 Correct! That is **{correct_answer}**.")
                    # Record correct name in seen list
                    st.session_state.seen_list.append({"name": correct_answer, "status": "correct"})
                else:
                    st.session_state.feedback = ("error", f"❌ Close, but that is **{correct_answer}**. You guessed '{user_guess}'.")

                # Advance game index or trigger Game Over
                if current_idx + 1 < total_images:
                    st.session_state.current_index += 1
                    # Rerun so the next picture is shown immediately
                    safe_rerun()
                else:
                    st.session_state.game_over = True
                    safe_rerun()
            else:
                st.warning("Please type a name before submitting!")
    else:
        # User skipped and must click Next to continue
        if st.session_state.feedback:
            fb_type, fb_msg = st.session_state.feedback
            if fb_type == "skip":
                st.info(fb_msg)
        if st.button("Next"):
            if current_idx + 1 < total_images:
                st.session_state.current_index += 1
                st.session_state.feedback = None
                st.session_state.awaiting_next = False
            else:
                st.session_state.game_over = True

    # Display feedback message persistent until next submission
    if st.session_state.feedback:
        fb_type, fb_msg = st.session_state.feedback
        if fb_type == "success":
            st.success(fb_msg)
        elif fb_type == "skip":
            st.info(fb_msg)
        else:
            st.error(fb_msg)

    # --- Seen Names List ---
    st.markdown("---")
    st.write("**Seen Names:**")
    if st.session_state.seen_list:
        for item in st.session_state.seen_list:
            name = item.get("name")
            status = item.get("status")
            if status == "correct":
                st.markdown(f"<span style='color:green'>✓ {name}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:red'>✗ {name}</span>", unsafe_allow_html=True)
    else:
        st.write("(No names seen yet)")

else:
    # --- GAME OVER SCREEN ---
    st.balloons()
    st.success("🎉 Game Completed!")
    final_score = st.session_state.score
    percentage = int((final_score / total_images) * 100)
    
    st.markdown(f"### Final Result: **{final_score} / {total_images}** ({percentage}%)")
    
    if percentage == 100:
        st.markdown("🥇 **Flawless Victory! You know everyone perfectly.**")
    elif percentage >= 70:
        st.markdown("🥈 **Great job! You have fantastic memory.**")
    else:
        st.markdown("🥉 **Not bad! Practice makes perfect.**")
        
    # Reset Button
    if st.button("🔄 Play Again"):
        random.shuffle(st.session_state.all_items)
        st.session_state.current_index = 0
        st.session_state.score = 0
        st.session_state.game_over = False
        st.session_state.feedback = None
        st.rerun()