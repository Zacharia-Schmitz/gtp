import streamlit as st
import streamlit.components.v1 as components
import os
import random
import time

# --- HELPER FUNCTIONS ---
def safe_rerun():
    """Helper to safely rerun across Streamlit versions."""
    try:
        st.experimental_rerun()
        return
    except Exception:
        # experimental_rerun not available or failed; fallback to stopping execution
        st.session_state["_needs_rerun"] = True
        st.stop()

def format_name_blanks(name, mode):
    """Converts a name into spaced underscores based on user selection."""
    if mode == "First Names Only":
        name = name.split()[0]
    
    words = name.split()
    blank_words = [" ".join(["_"] * len(w)) for w in words]
    return " &nbsp; &nbsp; &nbsp; ".join(blank_words)

@st.cache_data
def load_game_data(selected_years):
    """Reads the selected directories and creates a list of dicts mapping paths to cleaned names."""
    game_data = []
    tried_paths = []
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')

    base_dir = os.path.dirname(os.path.abspath(__file__))

    for year in selected_years:
        candidates = [
            year,
            os.path.join(base_dir, year),
            os.path.join(os.getcwd(), year),
            os.path.join(base_dir, 'static', year),
            os.path.join(os.getcwd(), 'static', year)
        ]

        directory_found = None
        for cand in candidates:
            cand_abs = os.path.abspath(cand)
            tried_paths.append(cand_abs)
            if os.path.exists(cand_abs) and os.path.isdir(cand_abs):
                directory_found = cand_abs
                break

        if directory_found:
            for filename in os.listdir(directory_found):
                if filename.lower().endswith(valid_extensions):
                    # Convert "adam_reno.png" -> "Adam Reno"
                    name_core = os.path.splitext(filename)[0]
                    clean_name = name_core.replace('_', ' ').title()
                    
                    game_data.append({
                        "image_path": os.path.join(directory_found, filename),
                        "correct_name": clean_name,
                        "year": year
                    })

    # Attach tried paths for helpful debugging
    load_game_data._last_tried = tried_paths
    return game_data

def initialize_game():
    """Loads data, shuffles it, and initializes game session state."""
    st.session_state.all_items = load_game_data(st.session_state.selected_years)
    
    if not st.session_state.all_items:
        st.error("No images found for the selected years. Please check your folder structure.")
        st.stop()
        
    random.shuffle(st.session_state.all_items)
    
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.game_over = False
    st.session_state.feedback = None
    st.session_state.seen_list = []
    st.session_state.awaiting_next = False
    st.session_state.show_correct_modal = False
    st.session_state.show_wrong_modal = False
    st.session_state.last_guess = ""
    st.session_state.game_active = True

# --- APP INITIALIZATION ---
st.set_page_config(page_title="Guess that Pittsvillian", page_icon="👥", layout="centered")

# --- SETTINGS SCREEN ---
if "game_active" not in st.session_state or not st.session_state.game_active:
    st.title("🎓 Guess that Pittsvillian - Setup")
    
    st.subheader("1. Select Years to Play")
    col1, col2, col3, col4 = st.columns(4)
    with col1: year_2011 = st.checkbox("Class of 2011", value=True)
    with col2: year_2012 = st.checkbox("Class of 2012")
    with col3: year_2013 = st.checkbox("Class of 2013")
    with col4: year_2014 = st.checkbox("Class of 2014")
    
    st.subheader("2. Name Format")
    name_mode = st.radio("How should the names be displayed/guessed?", ["Full Name", "First Names Only"])
    
    st.subheader("3. Guess the Class?")
    guess_class = st.radio("Include class year guessing?", ["Yes", "No"])
    
    if st.button("Start Game", type="primary"):
        selected_years = []
        if year_2011: selected_years.append("2011")
        if year_2012: selected_years.append("2012")
        if year_2013: selected_years.append("2013")
        if year_2014: selected_years.append("2014")
        
        if not selected_years:
            st.error("Please select at least one class year to play!")
        else:
            st.session_state.selected_years = selected_years
            st.session_state.name_mode = name_mode
            st.session_state.guess_class = guess_class
            initialize_game()
            safe_rerun()

# --- GAME LOGIC CODE ---
if st.session_state.get("game_active"):
    
    # Inject custom HTML/JS for a live ticking timer
    timer_html = """
    <div style="position: fixed; top: 40px; right: 40px; font-size: 24px; font-weight: bold; background-color: #f0f2f6; padding: 10px 20px; border-radius: 10px; border: 2px solid #ccc; z-index: 9999; color: black;">
        ⏱️ <span id="time-display">00:00</span>
    </div>
    <script>
        if (!sessionStorage.getItem("pittsvillian_startTime")) {
            sessionStorage.setItem("pittsvillian_startTime", Date.now());
        }
        var startTime = sessionStorage.getItem("pittsvillian_startTime");
        
        setInterval(function() {
            var delta = Date.now() - startTime;
            var seconds = Math.floor((delta / 1000) % 60);
            var minutes = Math.floor((delta / 1000) / 60);
            document.getElementById("time-display").innerText = 
                (minutes < 10 ? "0" + minutes : minutes) + ":" + 
                (seconds < 10 ? "0" + seconds : seconds);
        }, 1000);
    </script>
    """
    components.html(timer_html, height=0)

    st.title("👥 Guess the Pittsvillian")

    current_idx = st.session_state.current_index
    total_images = len(st.session_state.all_items)

    if not st.session_state.game_over:
        # Get current item
        current_item = st.session_state.all_items[current_idx]
        
        # Adjust correct answer based on game mode
        correct_name_full = current_item["correct_name"]
        correct_name_eval = correct_name_full.split()[0] if st.session_state.name_mode == "First Names Only" else correct_name_full
        correct_year = current_item["year"]
        
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
        
        # Display the formatted blanks
        blanks = format_name_blanks(correct_name_full, st.session_state.name_mode)
        st.markdown(f"<h2 style='text-align: center; letter-spacing: 2px;'>{blanks}</h2>", unsafe_allow_html=True)
        
        # Guess Form / Skip behavior
        if not st.session_state.awaiting_next:
            with st.form(key="guess_form", clear_on_submit=True):
                user_guess = st.text_input("Who is this?", placeholder="Type name here...").strip()
                
                # Dynamic radio buttons for class year guessing
                class_guess = None
                if st.session_state.guess_class == "Yes":
                    class_guess = st.radio("Guess their class:", st.session_state.selected_years, horizontal=True)

                col_submit, col_skip = st.columns([1,1])
                with col_submit:
                    submit_button = st.form_submit_button(label="Submit Guess")
                with col_skip:
                    skip_button = st.form_submit_button(label="Skip")

            if skip_button:
                # Reveal answer, mark as incorrect in seen list, wait for explicit Next
                st.session_state.seen_list.append({"name": correct_name_full, "status": "incorrect"})
                
                skip_msg = f"⏭️ Skipped. The correct name is **{correct_name_full}**"
                if st.session_state.guess_class == "Yes":
                    skip_msg += f" (Class of {correct_year})."
                else:
                    skip_msg += "."
                    
                st.session_state.feedback = ("skip", skip_msg)
                st.session_state.awaiting_next = True
                safe_rerun()

            if submit_button:
                if user_guess:
                    # Case-insensitive comparison
                    name_correct = user_guess.lower() == correct_name_eval.lower()
                    class_correct = (class_guess == correct_year) if st.session_state.guess_class == "Yes" else True
                    
                    if name_correct and class_correct:
                        # Record correct answer but do NOT advance yet; show modal
                        st.session_state.score += 1
                        st.session_state.seen_list.append({"name": correct_name_full, "status": "correct"})
                        st.session_state.show_correct_modal = True
                        st.session_state.feedback = None
                        safe_rerun()
                    else:
                        # Wrong answer
                        st.session_state.last_guess = user_guess
                        st.session_state.show_wrong_modal = True
                        st.session_state.feedback = None
                        safe_rerun()
                else:
                    st.warning("Please type a name before submitting!")
        else:
            # User skipped and must click Next to continue
            if st.session_state.feedback:
                fb_type, fb_msg = st.session_state.feedback
                if fb_type == "skip":
                    st.info(fb_msg)
            if st.button("Next Image"):
                if current_idx + 1 < total_images:
                    st.session_state.current_index += 1
                    st.session_state.feedback = None
                    st.session_state.awaiting_next = False
                else:
                    st.session_state.game_over = True
                safe_rerun()

        # --- Modals for correct / wrong answers ---
        if st.session_state.show_correct_modal:
            try:
                with st.modal("Correct!", clear_on_close=True):
                    success_msg = f"🎉 Correct! That is **{correct_name_full}**"
                    if st.session_state.guess_class == "Yes":
                        success_msg += f" (Class of {correct_year})."
                    else:
                        success_msg += "."
                        
                    st.success(success_msg)
                    col_ok, col_next = st.columns([1,1])
                    if col_ok.button("OK", key=f"ok_{current_idx}"):
                        st.session_state.show_correct_modal = False
                        safe_rerun()
                    if col_next.button("Next", key=f"next_{current_idx}"):
                        if current_idx + 1 < total_images:
                            st.session_state.current_index += 1
                        else:
                            st.session_state.game_over = True
                        st.session_state.show_correct_modal = False
                        safe_rerun()
            except Exception:
                # Fallback if st.modal not available
                st.success(f"🎉 Correct! That is **{correct_name_full}**.")
                if st.button("Next Image", key=f"next_fallback_{current_idx}"):
                    if current_idx + 1 < total_images:
                        st.session_state.current_index += 1
                    else:
                        st.session_state.game_over = True
                    st.session_state.show_correct_modal = False
                    safe_rerun()

        if st.session_state.show_wrong_modal:
            try:
                with st.modal("Incorrect", clear_on_close=True):
                    st.error(f"❌ '{st.session_state.last_guess}' (or the selected year) is not entirely correct.")
                    st.write("What would you like to do?")
                    col_try, col_give = st.columns([1,1])
                    if col_try.button("Try Again", key=f"try_{current_idx}"):
                        st.session_state.show_wrong_modal = False
                        safe_rerun()
                    if col_give.button("Give Up", key=f"give_{current_idx}"):
                        st.session_state.seen_list.append({"name": correct_name_full, "status": "incorrect"})
                        
                        give_up_msg = f"⏭️ Given up. The correct name is **{correct_name_full}**"
                        if st.session_state.guess_class == "Yes":
                            give_up_msg += f" (Class of {correct_year})."
                        else:
                            give_up_msg += "."
                            
                        st.session_state.feedback = ("skip", give_up_msg)
                        st.session_state.awaiting_next = True
                        st.session_state.show_wrong_modal = False
                        safe_rerun()
            except Exception:
                # Fallback inline if modal not available
                st.error(f"❌ '{st.session_state.last_guess}' is not correct.")
                col_try, col_give = st.columns([1,1])
                if col_try.button("Try Again", key=f"try_fb_{current_idx}"):
                    st.session_state.show_wrong_modal = False
                    safe_rerun()
                if col_give.button("Give Up", key=f"give_fb_{current_idx}"):
                    st.session_state.seen_list.append({"name": correct_name_full, "status": "incorrect"})
                    st.session_state.feedback = ("skip", f"⏭️ Given up. The correct name is **{correct_name_full}**.")
                    st.session_state.awaiting_next = True
                    st.session_state.show_wrong_modal = False
                    safe_rerun()

        # Display feedback message persistent until next submission
        if st.session_state.feedback and not st.session_state.awaiting_next:
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
        
        # Stop JS timer
        components.html("""<script>sessionStorage.removeItem("pittsvillian_startTime");</script>""", height=0)
        
        final_score = st.session_state.score
        percentage = int((final_score / total_images) * 100) if total_images > 0 else 0
        
        st.markdown(f"### Final Result: **{final_score} / {total_images}** ({percentage}%)")
        
        if percentage == 100:
            st.markdown("🥇 **Flawless Victory! You know everyone perfectly.**")
        elif percentage >= 70:
            st.markdown("🥈 **Great job! You have fantastic memory.**")
        else:
            st.markdown("🥉 **Not bad! Practice makes perfect.**")
            
        # Reset Button returns to settings
        if st.button("🔄 Play Again / Change Settings"):
            st.session_state.game_active = False
            # Clear cache so we can select new folders
            for key in list(st.session_state.keys()):
                if key != "game_active":
                    del st.session_state[key]
            safe_rerun()