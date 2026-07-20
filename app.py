import streamlit as st
import streamlit.components.v1 as components
import os
import random
import time
from PIL import Image, ImageOps

# --- APP INITIALIZATION ---
# Must be the first Streamlit command
st.set_page_config(
    page_title="Guess that Pittsvillian", 
    page_icon="👥", 
    layout="centered"
)

# --- RESPONSIVE MOBILE CSS ---
# Forces Streamlit columns to remain as a 2-column grid on mobile instead of stacking to 1 column
st.markdown("""
    <style>
    @media (max-width: 768px) {
        /* Force the container to stay as a row and wrap its children */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: wrap !important;
        }
        /* Force each individual column to take up half the screen width, minus the gap */
        div[data-testid="column"] {
            width: calc(50% - 1rem) !important;
            flex: 1 1 calc(50% - 1rem) !important;
            min-width: calc(50% - 1rem) !important;
            padding-bottom: 1rem !important;
        }
    }
    </style>
""", unsafe_allow_html=True)


# --- HELPER FUNCTIONS ---
def format_name_blanks(name, mode):
    """Converts a name into spaced underscores based on user selection."""
    if mode == "First Names Only":
        name = name.split()[0]
    
    words = name.split()
    blank_words = [" ".join(["_"] * len(w)) for w in words]
    return " &nbsp; &nbsp; &nbsp; ".join(blank_words)

def get_standardized_image(image_path):
    """Opens an image and crops/resizes it to a uniform 3:4 portrait aspect ratio."""
    target_size = (300, 400)  # Standard portrait size
    try:
        img = Image.open(image_path)
        # Handle images with transparency to prevent black backgrounds on resize
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        # ImageOps.fit crops and centers the image perfectly to the target size
        resampling_method = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
        return ImageOps.fit(img, target_size, method=resampling_method)
    except Exception as e:
        # Fallback to the original path if processing fails
        return image_path

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
    st.session_state.no_idea = False   # Tracks if they clicked "I Have No Idea"
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
        st.session_state.seen_list.append({"name": correct_name, "status": "correct", "image_path": image_path, "year": correct_year})
        st.session_state.current_index += 1
        st.session_state.modal_state = None
        st.session_state.no_idea = False
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
            st.session_state.seen_list.append({"name": correct_name, "status": "incorrect", "image_path": image_path, "year": correct_year})
            st.session_state.current_index += 1
            st.session_state.modal_state = None
            st.session_state.gave_up = False
            st.session_state.no_idea = False
            st.rerun()
            
        # Only show the Give Me Credit button if they DID NOT click "I Have No Idea"
        if not st.session_state.get("no_idea", False):
            if st.button("Give Me Credit - Only My Spelling Was Off", use_container_width=True, type="primary"):
                st.session_state.score += 1
                # Add as "credited" so we can show the misspelled version at the end
                st.session_state.seen_list.append({
                    "name": correct_name, 
                    "status": "credited", 
                    "guess": last_guess, 
                    "image_path": image_path,
                    "year": correct_year
                })
                st.session_state.current_index += 1
                st.session_state.modal_state = None
                st.session_state.gave_up = False
                st.session_state.no_idea = False
                st.rerun()

# --- MAIN TABS NAVIGATION ---
tab_play, tab_browse = st.tabs(["🎮 Guess That Pittsvillian", "📚 Browse Pittsvillians"])

# ==========================================
# TAB 1: MAIN GAME (GUESS THAT PITTSVILLIAN)
# ==========================================
with tab_play:
    # --- SETTINGS SCREEN ---
    if "game_active" not in st.session_state or not st.session_state.game_active:
        # Clear the JS timer if they are on the setup screen
        components.html("""<script>sessionStorage.removeItem("pittsvillian_startTime");</script>""", height=0)
        
        st.title("🎓 Guess that Pittsvillian - Setup")
        
        st.subheader("1. Select Years to Play")
        col1, col2, col3, col4 = st.columns(4)
        with col1: year_2011 = st.checkbox("Class of 2011", value=True)
        with col2: year_2012 = st.checkbox("Class of 2012")
        with col3: year_2013 = st.checkbox("Class of 2013")
        with col4: year_2014 = st.checkbox("Class of 2014")
        
        st.subheader("2. Name Format")
        name_mode = st.radio("How should the names be displayed/guessed?", ["First Names Only", "Full Name"])
        
        # Add a bit of space before the start button
        st.write("")
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

        st.title("👥 Guess That Pittsvillian")

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
            
            # Display Friend's Image - we keep original aspect ratio here for detail
            st.image(image_path, use_container_width=True)
            
            # Display the formatted blanks
            blanks = format_name_blanks(correct_name_full, st.session_state.name_mode)
            st.markdown(f"<h2 style='text-align: center; letter-spacing: 2px;'>{blanks}</h2>", unsafe_allow_html=True)
            
            # Guess Form
            with st.form(key="guess_form", clear_on_submit=True):
                user_guess = st.text_input("Who is this?", placeholder="Type name here...").strip()
                
                # Setup buttons side by side
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    submit_button = st.form_submit_button(label="Submit Guess", use_container_width=True)
                with btn_col2:
                    no_idea_button = st.form_submit_button(label="I Have No Idea", use_container_width=True)

            # Handle Submit Guess Button
            if submit_button:
                if user_guess:
                    # Case-insensitive comparison
                    name_correct = user_guess.lower() == correct_name_eval.lower()
                    
                    if name_correct:
                        st.session_state.modal_state = "correct"
                    else:
                        st.session_state.last_guess = user_guess
                        st.session_state.modal_state = "incorrect"
                        st.session_state.gave_up = False
                        st.session_state.no_idea = False
                    st.rerun()
                else:
                    st.warning("Please type a name before submitting!")
                    
            # Handle I Have No Idea Button
            if no_idea_button:
                st.session_state.last_guess = ""
                st.session_state.modal_state = "incorrect"
                st.session_state.gave_up = True   # Bypass the "Try Again" step
                st.session_state.no_idea = True   # Hide the "Credit" button
                st.rerun()

            # Trigger Dialogs outside of the form based on state
            if st.session_state.modal_state == "correct":
                show_correct_dialog(correct_name_full, correct_year, image_path)
            elif st.session_state.modal_state == "incorrect":
                show_incorrect_dialog(st.session_state.last_guess, correct_name_full, correct_year, image_path)

            # --- Restart Game Button ---
            st.markdown("---")
            # Inject Javascript to dynamically style the "Restart Game" button text red
            components.html(
                """
                <script>
                const elements = window.parent.document.querySelectorAll('button p');
                elements.forEach(p => {
                    if (p.innerText.includes('Restart Game')) {
                        p.style.color = '#ff4b4b'; // Streamlit's default red color
                        p.parentElement.style.borderColor = '#ff4b4b'; // Matches border
                    }
                });
                </script>
                """,
                height=0, width=0
            )
            
            if st.button("🔄 Restart Game (Change Settings)", use_container_width=True):
                st.session_state.game_active = False
                # Clear cache so we can return cleanly to setup menu
                for key in list(st.session_state.keys()):
                    if key != "game_active":
                        del st.session_state[key]
                st.rerun()

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
            
            # --- Calculate & Display Class Year Breakdown ---
            year_stats = {}
            for item in st.session_state.seen_list:
                y = item.get("year", "Unknown")
                if y not in year_stats:
                    year_stats[y] = {"correct": 0, "total": 0}
                year_stats[y]["total"] += 1
                if item.get("status") in ["correct", "credited"]:
                    year_stats[y]["correct"] += 1
            
            if year_stats:
                st.markdown("**Breakdown by Class:**")
                # Create exactly enough columns for the years played
                breakdown_cols = st.columns(len(year_stats))
                for idx, (y, stats) in enumerate(sorted(year_stats.items())):
                    with breakdown_cols[idx]:
                        st.metric(f"Class of {y}", f"{stats['correct']} / {stats['total']}")
            
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
                        # Pass through our standardization function so they line up cleanly
                        std_img = get_standardized_image(item["image_path"])
                        st.image(std_img, caption=item["name"], use_container_width=True)

            st.markdown("---")
            
            # --- End of Game Navigation Buttons ---
            btn_col1, btn_col2 = st.columns(2)
            
            with btn_col1:
                if st.button("🔁 Retry (Same Settings)", use_container_width=True):
                    # Shuffle and reset without modifying settings
                    random.shuffle(st.session_state.all_items)
                    st.session_state.current_index = 0
                    st.session_state.score = 0
                    st.session_state.game_over = False
                    st.session_state.seen_list = []
                    st.session_state.modal_state = None
                    st.session_state.gave_up = False
                    st.session_state.no_idea = False
                    st.session_state.last_guess = ""
                    st.session_state.start_time = time.time()
                    # Also need to reset JS timer for retry
                    components.html("""<script>sessionStorage.removeItem("pittsvillian_startTime");</script>""", height=0)
                    st.rerun()
                    
            with btn_col2:
                if st.button("⚙️ Change Settings", type="primary", use_container_width=True):
                    st.session_state.game_active = False
                    # Clear cache so we can return cleanly to setup menu
                    for key in list(st.session_state.keys()):
                        if key != "game_active":
                            del st.session_state[key]
                    st.rerun()

# ==========================================
# TAB 2: BROWSE PITTSVILLIANS
# ==========================================
with tab_browse:
    st.title("📚 Browse Pittsvillians")
    st.write("View the student directories below.")
    
    all_possible_years = ["2011", "2012", "2013", "2014"]
    
    # Filter columns setup
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        # Filter by class year
        selected_browse_year = st.selectbox("Select Class to Browse:", ["All Classes"] + all_possible_years)
    with filter_col2:
        # Wildcard search
        search_query = st.text_input("Search by Name:", placeholder="e.g., Smith, Sarah...")
    
    years_to_load = all_possible_years if selected_browse_year == "All Classes" else [selected_browse_year]
    
    with st.spinner("Loading directory..."):
        browse_data = load_game_data(years_to_load)
    
    if not browse_data:
        st.info(f"No images found for {selected_browse_year}. Please ensure your image folders are set up correctly.")
    else:
        # Apply the wildcard search filter
        if search_query:
            browse_data = [
                item for item in browse_data 
                if search_query.lower() in item["correct_name"].lower()
            ]

        if not browse_data:
            st.warning("No Pittsvillians found matching your search criteria.")
        else:
            # Sort alphabetically by first name
            browse_data = sorted(browse_data, key=lambda x: x["correct_name"])
            
            st.write(f"Showing **{len(browse_data)}** Pittsvillians.")
            st.markdown("---")
            
            # Display images in a grid
            cols = st.columns(4)
            for idx, item in enumerate(browse_data):
                with cols[idx % 4]:
                    # Standardize the image to a 3:4 aspect ratio to fix grid alignment
                    standard_img = get_standardized_image(item["image_path"])
                    
                    st.image(standard_img, use_container_width=True)
                    
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