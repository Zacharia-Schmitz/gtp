import streamlit as st
import streamlit.components.v1 as components
import os
import random
import time

# --- APP INITIALIZATION ---
# Must be the first Streamlit command
st.set_page_config(page_title="Guess that Pittsvillian", page_icon="👥", layout="centered")

# --- HELPER FUNCTIONS ---
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
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    base_dir = os.path.dirname(os.path.abspath(__file__))

    for year in selected_years:
        # Build a list of candidate directories to try so deploys find the images
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
    st.session_state.seen_list = []
    st.session_state.modal_state = None  # Controls which popup is open
    st.session_state.gave_up = False
    st.session_state.last_guess = ""
    st.session_state.game_active = True
    
    # Track the start time in Python for the final Game Over screen
    st.session_state.start_time = time.time()

# --- DIALOGS (POP-UPS) ---
@st.dialog("🎉 Correct!")
def show_correct_dialog(correct_name, correct_year, image_path):
    st.write(f"Spot on! That is **{correct_name}** (Class of {correct_year}).")
    if st.button("Next Picture", use_container_width=True, type="primary"):
        st.session_state.score += 1
        st.session_state.seen_list.append({"name": correct_name, "status": "correct", "image_path": image_path})
        st.session_state.current_index += 1
        st.session_state.modal_state = None
        st.rerun()

@st.dialog("❌ Incorrect")
def show_incorrect_dialog(last_guess, correct_name, correct_year, image_path):
    if not st.session_state.gave_up:
        st.write(f"Your guess **'{last_guess}'** wasn't quite right.")
        col1, col2 = st.columns(2)
        if col1.button("Try Again", use_container_width=True):
            st.session_state.modal_state = None
            st.rerun()
        if col2.button("Give Up", use_container_width=True, type="primary"):
            st.session_state.gave_up = True
            st.rerun()
    else:
        st.markdown(f"The correct answer was:<br><h3 style='text-align: center;'>{correct_name}</h3><h4 style='text-align: center;'>Class of {correct_year}</h4>", unsafe_allow_html=True)
        st.write("---")
        
        if st.button("Next Picture", use_container_width=True):
            st.session_state.seen_list.append({"name": correct_name, "status": "incorrect", "image_path": image_path})
            st.session_state.current_index += 1
            st.session_state.modal_state = None
            st.session_state.gave_up = False
            st.rerun()
            
        if st.button("Give Me Credit - Only My Spelling Was Off", use_container_width=True, type="primary"):
            st.session_state.score += 1
            # Add as "credited" so we can show the misspelled version at the end
            st.session_state.seen_list.append({
                "name": correct_name, 
                "status": "credited", 
                "guess": last_guess, 
                "image_path": image_path
            })
            st.session_state.current_index += 1
            st.session_state.modal_state = None
            st.session_state.gave_up = False
            st.rerun()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Guess That Pittsvillian", "Browse Classes"])


# ==========================================
# PAGE 1: MAIN GAME (GUESS THAT PITTSVILLIAN)
# ==========================================
if page == "Guess That Pittsvillian":
    # --- SETTINGS SCREEN ---
    if "game_active" not in st.session_state or not st.session_state.game_active:
        st.title("🎓 Guess that Pittsvillian - Setup")
        
        st.subheader("1. Select Years to Play")
        col1, col2, col3, col4 = st.columns(4)
        with col1: year_2011 = st.checkbox("Class of 2011", value=True)
        with col2: year_2012 = st.checkbox("Class of 2012", value=True)
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
                st.rerun()

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

        # Check for game over condition
        if current_idx >= total_images and total_images > 0:
            st.session_state.game_over = True

        if not st.session_state.game_over:
            # Get current item
            current_item = st.session_state.all_items[current_idx]
            
            correct_name_full = current_item["correct_name"]
            correct_name_eval = correct_name_full.split()[0] if st.session_state.name_mode == "First Names Only" else correct_name_full
            correct_year = current_item["year"]
            image_path = current_item["image_path"]
            
            # Display Score & Progress
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Score", f"{st.session_state.score} / {total_images}")
            with col2:
                st.write(f"**Progress:** Picture {current_idx + 1} of {total_images}")
                st.progress((current_idx + 1) / total_images)
                
            st.markdown("---")
            
            # Display Friend's Image
            st.image(image_path, use_container_width=True)
            
            # Display the formatted blanks
            blanks = format_name_blanks(correct_name_full, st.session_state.name_mode)
            st.markdown(f"<h2 style='text-align: center; letter-spacing: 2px;'>{blanks}</h2>", unsafe_allow_html=True)
            
            # Guess Form
            with st.form(key="guess_form", clear_on_submit=True):
                user_guess = st.text_input("Who is this?", placeholder="Type name here...").strip()
                
                # Dynamic radio buttons for class year guessing
                class_guess = None
                if st.session_state.guess_class == "Yes":
                    class_guess = st.radio("Guess their class:", st.session_state.selected_years, horizontal=True)

                submit_button = st.form_submit_button(label="Submit Guess", use_container_width=True)

            if submit_button:
                if user_guess:
                    # Case-insensitive comparison
                    name_correct = user_guess.lower() == correct_name_eval.lower()
                    class_correct = (class_guess == correct_year) if st.session_state.guess_class == "Yes" else True
                    
                    if name_correct and class_correct:
                        st.session_state.modal_state = "correct"
                    else:
                        st.session_state.last_guess = user_guess
                        st.session_state.modal_state = "incorrect"
                        st.session_state.gave_up = False
                    st.rerun()
                else:
                    st.warning("Please type a name before submitting!")

            # Trigger Dialogs outside of the form based on state
            if st.session_state.modal_state == "correct":
                show_correct_dialog(correct_name_full, correct_year, image_path)
            elif st.session_state.modal_state == "incorrect":
                show_incorrect_dialog(st.session_state.last_guess, correct_name_full, correct_year, image_path)

            # --- Seen Names List ---
            st.markdown("---")
            st.write("**Seen Names:**")
            if st.session_state.seen_list:
                for item in st.session_state.seen_list:
                    name = item.get("name")
                    status = item.get("status")
                    if status == "correct" or status == "credited":
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
            
            # Calculate Final Time
            total_time_seconds = int(time.time() - st.session_state.start_time)
            mins, secs = divmod(total_time_seconds, 60)
            time_formatted = f"{mins:02d}:{secs:02d}"

            final_score = st.session_state.score
            percentage = int((final_score / total_images) * 100) if total_images > 0 else 0
            
            st.markdown(f"### Final Result: **{final_score} / {total_images}** ({percentage}%)")
            st.markdown(f"### ⏱️ Total Time: **{time_formatted}**")
            
            if percentage == 100:
                st.markdown("🥇 **Flawless Victory! You know everyone perfectly.**")
            elif percentage >= 70:
                st.markdown("🥈 **Great job! You have fantastic memory.**")
            else:
                st.markdown("🥉 **Not bad! Practice makes perfect.**")
                
            st.markdown("---")
            
            # --- End Game Stats ---
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### ⚙️ Game Settings")
                st.write(f"- **Classes Included:** {', '.join(st.session_state.selected_years)}")
                st.write(f"- **Name Mode:** {st.session_state.name_mode}")
                st.write(f"- **Class Guessing:** {st.session_state.guess_class}")

            with col2:
                credited_items = [item for item in st.session_state.seen_list if item.get("status") == "credited"]
                if credited_items:
                    st.markdown("### 📝 Spelled Incorrectly (Given Credit)")
                    for item in credited_items:
                        st.write(f"- Guessed **'{item['guess']}'** for **{item['name']}**")
                else:
                    st.write("") # Spacer

            # --- Display Incorrect Faces ---
            incorrect_items = [item for item in st.session_state.seen_list if item.get("status") == "incorrect"]
            if incorrect_items:
                st.markdown("---")
                st.markdown("### ❌ People You Missed")
                cols = st.columns(4) # Adjust number of columns based on preference
                for idx, item in enumerate(incorrect_items):
                    with cols[idx % 4]:
                        st.image(item["image_path"], caption=item["name"], use_container_width=True)

            st.markdown("---")
            # Reset Button returns to settings
            if st.button("🔄 Play Again / Change Settings", type="primary", use_container_width=True):
                st.session_state.game_active = False
                # Clear cache so we can select new folders
                for key in list(st.session_state.keys()):
                    if key != "game_active":
                        del st.session_state[key]
                st.rerun()


# ==========================================
# PAGE 2: BROWSE CLASSES
# ==========================================
elif page == "Browse Classes":
    st.title("📚 Browse Classes")
    st.write("View the student directories below.")
    
    all_possible_years = ["2011", "2012", "2013", "2014"]
    
    # Filter by class year
    selected_browse_year = st.selectbox("Select Class to Browse:", ["All Classes"] + all_possible_years)
    
    years_to_load = all_possible_years if selected_browse_year == "All Classes" else [selected_browse_year]
    
    with st.spinner("Loading directory..."):
        browse_data = load_game_data(years_to_load)
    
    if not browse_data:
        st.info(f"No images found for {selected_browse_year}. Please ensure your image folders are set up correctly.")
    else:
        # Sort alphabetically by first name
        browse_data = sorted(browse_data, key=lambda x: x["correct_name"])
        
        st.write(f"Showing **{len(browse_data)}** Pittsvillians.")
        st.markdown("---")
        
        # Display images in a grid
        cols = st.columns(4)
        for idx, item in enumerate(browse_data):
            with cols[idx % 4]:
                st.image(item["image_path"], use_container_width=True)
                
                # HTML markdown to display name and class beautifully centered underneath
                st.markdown(
                    f"""
                    <div style='text-align: center; margin-top: -10px; margin-bottom: 25px;'>
                        <strong>{item['correct_name']}</strong><br>
                        <span style='font-size: 0.8em; color: gray;'>Class of {item['year']}</span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )