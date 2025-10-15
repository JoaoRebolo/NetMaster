# Code of Project

## Player Console

### Player Dashboard

#### Features

##### Interface Initialization and State Management

```pseudocode
Function __init__(root, player_color, saldo, other_players, player_name):
    self.player_color <- player_color
    self.player_name <- player_name
    self.saldo <- saldo
    self.other_players <- other_players

    // Initialize core data structures
    self.inventario <- initialize_inventory_dict()
    self.card_stats <- [{"To send": 0, "Rxd": 0, "Lost": 0} for i in 1..4]
    self.card_face_up_flags <- [False, False, False, False]

    // Initialize phase control flags
    self._next_phase_active <- False
    self._final_phase_active <- False
    self._final_phase_gestao_ativa <- False

    // Load card database and setup interface
    self.card_database <- IntegratedCardDatabase(".")
    self.cards <- initialize_back_card_paths()
```

###### Transition to Gameplay

```pseudocode
Function show_dice_roll_screen(player_name, saldo, other_players, screen_width, screen_height):
    // Create fullscreen interface
    self.configure(bg="black")
    self.geometry(f"{screen_width}x{screen_height}+0+0")
    
    // Create top bar with player info
    create_top_bar(player_name, saldo, other_players)
    
    // Create dice frame and image
    dice_frame <- tk.Frame(self, bg="black")
    dice_label <- tk.Label(dice_frame, bg="black")
    
    // Load initial dice image
    dice_img_path <- os.path.join(IMG_DIR, "dice_1.png")
    dice_img <- ImageTk.PhotoImage(Image.open(dice_img_path).resize((200, 200)))
    dice_label.configure(image=dice_img)
    
    // Create Go button
    go_btn <- tk.Button(dice_frame, text="Go!", 
                       command=lambda: roll_dice_and_animate())
```

```pseudocode
Function roll_dice_and_animate():
    // Disable Go button to prevent multiple clicks
    go_btn.configure(state="disabled")
    
    // Generate random dice result (1-6)
    dice_result <- random.randint(1, 6)
    
    // Animation parameters
    animation_steps <- 10
    animation_delay <- 100  // milliseconds between frames
    
    // Start dice animation sequence
    for step in range(animation_steps):
    // Show final dice result
    final_dice_path <- os.path.join(IMG_DIR, f"dice_{dice_result}.png")
    try:
        self.update()
    except Exception as e:
    
    // Calculate new player position
    old_position <- getattr(self, "player_pos", START_POSITIONS.get(player_color.lower(), 0))
    new_position <- (old_position + dice_result) % NUM_CASAS
    
    // Get house type and color from board
    house_type, house_color <- BOARD[new_position]
    
    // Update player position
    self.player_pos <- new_position
    
    // Update player position in dashboard if available
    if self.dashboard:
    
    // Wait before opening store
    time.sleep(0.5)
    
    // Open Store with house information
    self.open_store_for_house(house_type, house_color, new_position)

Function open_store_for_house(house_type, house_color, position):
    // Hide dice interface
    self.withdraw()
    
    // Determine if it's another player's house
    other_player_house <- (house_color != self.player_color and house_color != "neutral")
    
    // Create Store window with appropriate parameters
    store_window <- StoreWindow()
    
    // Show store window
    store_window.deiconify()
    store_window.lift()
    store_window.focus_force()
```

##### Main Interface Structure

```pseudocode
Function playerdashboard_interface(player_name, saldo, other_players, show_store_button=None):
    // Clear existing widgets and setup fullscreen
    for widget in self.winfo_children():
    
    screen_width <- self.winfo_screenwidth()
    screen_height <- self.winfo_screenheight()
    self.geometry(f"{screen_width}x{screen_height}+0+0")

    // Create top bar with TopBar image
    topbar_img_path <- os.path.join(IMG_DIR, f"TopBar_{self.player_color}.png")
    topbar_img <- ImageTk.PhotoImage(Image.open(topbar_img_path))
    topbar_label <- tk.Label(self, image=topbar_img)
    topbar_label.pack(side="top", fill="x")

    // Create action buttons frame
    action_frame <- tk.Frame(self, bg="black")
    action_frame.place(relx=0.5, rely=0.3, anchor="center")

    // Create carousel system
    cards_frame <- tk.Frame(self, bg="black")
    cards_frame.place(relx=0.5, rely=0.55, anchor="center")
    
    // Create progress bars
    progress_frame <- tk.Frame(self, bg="black")
    progress_frame.place(relx=0.5, rely=0.75, anchor="center")
```

###### Card Addition and Substitution Mechanism

```pseudocode
Function adicionar_carta_carrossel(carta_path, carta_tipo):
    // Find first empty position
    for i in range(4):
        if self.cards[i] is None or "back_card" in self.cards[i]:
            // Add card to carousel
            self.cards[i] <- carta_path
            self.card_face_up_flags[i] <- True
            
            // Initialize card stats from database
            message_size <- self._get_card_message_size(carta_path)
            self.card_stats[i] <- {
                "To send": message_size,
                "Rxd": 0, 
                "Lost": 0,
                "message_size": message_size
            }
            
            // Update visual representation and select card
            self.update_card_image()
            self._select_carousel_card(i, carta_path)
            
            // Add to inventory if not already present
            if carta_path not in self.inventario[carta_tipo]:
                self.inventario[carta_tipo].append(carta_path)
            
            return True
    
    // Carousel is full
    return False

Function processar_challenge_aceite(carta_challenge_path):
    // Find active Activities in carousel for substitution
    activities_ativas_indices <- []
    
    for i in range(len(self.cards)):
        carta_path <- self.cards[i]
        if carta_path and self._is_activity_card(carta_path):
            activities_ativas_indices.append(i)
    
    if len(activities_ativas_indices) == 0:
        // No Activities - add Challenge to inventory
        self.inventario["challenges"].append(carta_challenge_path)
    elif len(activities_ativas_indices) == 1:
        // Single Activity - substitute automatically
        self._executar_troca_challenge_activity(carta_challenge_path, activities_ativas_indices[0])
    else:
        // Multiple Activities - show selection interface
        self._mostrar_interface_escolha_activity(carta_challenge_path, activities_ativas_indices)
```

###### Card State Management and Visual Synchronization

```pseudocode
Function update_card_image():
    // Update visual representation of selected card
    if hasattr(self, 'selected_card_idx') and self.selected_card_idx is not None:
        card_idx <- self.selected_card_idx
        
        if card_idx < len(self.cards) and self.cards[card_idx]:
            carta_path <- self.cards[card_idx]
            
            // Check if card should be face-up or face-down
            if (card_idx < len(self.card_face_up_flags) and 
                self.card_face_up_flags[card_idx]):
                // Show actual card image
                carta_img <- ImageTk.PhotoImage(Image.open(carta_path).resize((85, 120)))
            else:
                // Show back card with player color
                back_card_path <- os.path.join(IMG_DIR, "cartas", f"back_card_{self.player_color}.png")
                carta_img <- ImageTk.PhotoImage(Image.open(back_card_path).resize((85, 120)))
            
            // Update card display widget
            if hasattr(self, 'carta_img_label'):
                self.carta_img_label.configure(image=carta_img)
                self.carta_img_label.image <- carta_img

Function _select_carousel_card(card_index, carta_path):
    // Update selection state
    self.selected_card_idx <- card_index
    self.selected_carousel_card <- carta_path
    
    // Update progress bars for selected card
    self.update_progress_bars_for_card(card_index)
    
    // Update visual highlighting
    self._update_carousel_selection_highlights()
```

###### Progress Tracking and Data Persistence

```pseudocode
Function update_progress_bars_for_card(card_idx):
    // Validate card index and get current stats
    if card_idx >= len(self.card_stats) or card_idx < 0:
        return
    
    current_stats <- self.card_stats[card_idx]
    
    // Update each progress bar type
    for stat_type in ["To send", "Rxd", "Lost"]:
        if stat_type in self.progress_bars:
            current_value <- current_stats.get(stat_type, 0)
            max_value <- current_stats.get("message_size", 100)
            
            // Update progress bar widget
            progress_bar <- self.progress_bars[stat_type]
            progress_bar.configure(value=current_value, maximum=max_value)
            
            // Update numerical label if exists
            if f"{stat_type}_label" in self.progress_bars:
                label <- self.progress_bars[f"{stat_type}_label"]
                label.configure(text=str(current_value))

Function _executar_troca_challenge_activity(challenge_path, activity_idx):
    // Get Activity to be replaced
    activity_path <- self.cards[activity_idx]
    
    // Replace Activity with Challenge in carousel - PROGRESS IS LOST
    self.cards[activity_idx] <- challenge_path
    
    // Reset card stats for new Challenge (no progress preservation)
    message_size <- self._get_card_message_size(challenge_path)
    self.card_stats[activity_idx] <- {
        "To send": message_size,
        "Rxd": 0,
        "Lost": 0,
        "message_size": message_size
    }
    
    // Move replaced Activity to inventory without progress
    if "activities" not in self.inventario:
        self.inventario["activities"] <- []
    self.inventario["activities"].append(activity_path)
    
    // Update interface
    self.update_card_image()
    self._select_carousel_card(activity_idx, challenge_path)
```

###### Selection and Highlighting System

```pseudocode
Function _update_carousel_selection_highlights():
    // Clear all existing highlights
    for i in range(4):
        if hasattr(self, f'carousel_card_{i}'):
            card_widget <- getattr(self, f'carousel_card_{i}')
            card_widget.configure(highlightthickness=0, relief="flat")
    
    // Apply highlight to selected card
    if (hasattr(self, 'selected_card_idx') and 
        self.selected_card_idx is not None and
        hasattr(self, f'carousel_card_{self.selected_card_idx}')):
        
        selected_widget <- getattr(self, f'carousel_card_{self.selected_card_idx}')
        
        // Determine highlight color based on game phase
        if hasattr(self, '_final_phase_gestao_ativa') and self._final_phase_gestao_ativa:
            highlight_color <- "#A020F0"  // Purple for management mode
        else:
            highlight_color <- self.player_color_hex  // Player color
        
        // Apply visual highlight
        selected_widget.configure(
            highlightbackground=highlight_color,
            highlightthickness=3,
            relief="solid"
        )

Function prev_card():
    // Navigate to previous card in carousel
    if self.selected_card_idx > 0:
        self.selected_card_idx -= 1
        self.selected_carousel_card <- self.cards[self.selected_card_idx]
        self.update_progress_bars_for_card(self.selected_card_idx)
        self.update_card_image()

Function next_card():
    // Navigate to next card in carousel
    if self.selected_card_idx < 3:
        self.selected_card_idx += 1
        self.selected_carousel_card <- self.cards[self.selected_card_idx]
        self.update_progress_bars_for_card(self.selected_card_idx)
        self.update_card_image()
```

###### Store Access Validation and Phase Management

```pseudocode
Function open_store():
    // Determine current board position
    current_position <- self.player_pos
    casa_tipo, casa_cor <- BOARD[current_position]
    
    // Check if it's another player's house
    other_player_house <- (casa_cor != self.player_color and casa_cor != "neutral")
    
    // Store current house information for Store interface
    self.current_casa_tipo <- casa_tipo
    self.current_casa_cor <- casa_cor
    self.current_other_player_house <- other_player_house
    
    // Validate store access based on current phase
    if self._next_phase_active or self._final_phase_active:
        // Show phase restriction message
        return
    
    // Create Store window with current context
    store_window <- StoreWindow(
        self.master, self.player_color, self.player_name,
        self.saldo, casa_tipo, casa_cor, self.inventario, 
        self, other_player_house
    )

Function disable_store_button():
    // Disable store access (used when Challenge is accepted)
    self._store_button_disabled <- True
    
    // Update store button visual state if it exists
    if hasattr(self, 'store_button') and self.store_button:
        self.store_button.configure(state="disabled", bg="#666666")

Function enable_store_button():
    // Re-enable store access
    self._store_button_disabled <- False
    
    // Update store button visual state if it exists
    if hasattr(self, 'store_button') and self.store_button:
        self.store_button.configure(state="normal", bg="#FF9800")
```

###### Direct Inventory Integration

```pseudocode
Function adicionar_carta_inventario(carta_path, carta_tipo):
    // Normalize card type for inventory storage
    if carta_tipo == "equipment":
        carta_tipo <- "equipments"
    elif carta_tipo == "action":
        carta_tipo <- "actions"
    elif carta_tipo == "event":
        carta_tipo <- "events"
    elif carta_tipo == "challenge":
        carta_tipo <- "challenges"
    elif carta_tipo == "activity":
        carta_tipo <- "activities"
    
    // Ensure inventory category exists
    if carta_tipo not in self.inventario:
        self.inventario[carta_tipo] <- []
    
    // Add card to inventory if not already present
    if carta_path not in self.inventario[carta_tipo]:
        self.inventario[carta_tipo].append(carta_path)
        
        // For certain card types, set up automatic activation
        if carta_tipo in ["actions", "events"]:
            self._activate_pending_cards()

Function show_inventory_page(carta_tipo):
    // Show inventory management interface for specific card type
    if self._next_phase_active and carta_tipo in ["equipments", "services", "users"]:
        // During Next Phase, disable sales for inventory cards
        self._disable_inventory_sales()
    
    // Navigate to inventory matrix display
    self.show_inventory_matrix([carta_tipo])
```

###### Challenge-Activity Substitution System

```pseudocode
Function aceitar_carta_challenge_activity(carta_path, carta_tipo):
    // Add to inventory first
    self.adicionar_carta_inventario(carta_path, carta_tipo)
    
    if carta_tipo in ["challenges", "challenge"]:
        // Process Challenge acceptance through Store system
        self.processar_challenge_aceite(carta_path)
    elif carta_tipo in ["activities", "activity"]:
        // Try to add Activity to carousel
        success <- self.adicionar_carta_carrossel(carta_path, carta_tipo)
        if not success:
            // Carousel is full - show restriction message
            self._mostrar_mensagem_restricao_activity()

Function _substituir_activity_por_challenge(idx_carrossel, carta_activity_path, carta_challenge_path):
    // Replace Activity with Challenge at specific carousel position
    
    // Move Activity to inventory (progress is permanently lost)
    if "activities" not in self.inventario:
        self.inventario["activities"] <- []
    self.inventario["activities"].append(carta_activity_path)
    
    // Place Challenge in carousel position
    self.cards[idx_carrossel] <- carta_challenge_path
    
    // Reset progress values for Challenge (no preservation)
    message_size <- self._get_card_message_size(carta_challenge_path)
    self.card_stats[idx_carrossel] <- {
        "To send": message_size,
        "Rxd": 0,
        "Lost": 0,
        "message_size": message_size
    }
    
    // Update interface
    self.update_card_image()
    self._select_carousel_card(idx_carrossel, carta_challenge_path)
```

##### Inventory System Implementation

```pseudocode
Function show_inventory_page(carta_tipo):
    // Check for Next Phase restrictions
    if self._next_phase_active and carta_tipo in ["equipments", "services", "users"]:
        self._disable_inventory_sales()
    
    // Navigate to inventory matrix display
    self.show_inventory_matrix([carta_tipo])

Function activate_card(card_type, card_path):
    // Add to appropriate active list
    if card_type == "users":
        if len(self.active_users) < self.max_users:
            self.active_users.append(card_path)
        else:
            return False
    elif card_type == "equipments":
        self.active_equipments.append(card_path)
    elif card_type == "services":
        self.active_services.append(card_path)
    
    // Update interface displays
    self.update_active_cards_display()
    return True

Function is_card_active(card_path, card_type):
    // Check appropriate active list
    if card_type == "users":
        return card_path in self.active_users
    elif card_type == "equipments":
        return card_path in self.active_equipments
    elif card_type == "services":
        return card_path in self.active_services
    return False
```

##### Multiplayer Communication System

```pseudocode
Function on_pending_cards_received(data):
    // Extract card data from server message
    cards <- data.get('cards', [])
    
    // Process each received card
    for card in cards:
        card_path <- card.get('card_path')
        card_type <- card.get('card_type')
        from_player <- card.get('from_player')
        
        // Add to appropriate inventory
        self.adicionar_carta_inventario(card_path, card_type)

Function on_timer_sync(data):
    // Update local timer with server value
    time_remaining <- data.get('time_remaining', 0)
    self.session_time_remaining = time_remaining
    
    // Update timer display
    self.update_timer_display()
    
    // Handle session end
    if time_remaining <= 0:
        self._handle_game_time_ended()

Function on_multiplayer_turn_changed(data):
    // Extract turn change information
    current_player_id <- data.get('current_player_id')
    current_player_name <- data.get('current_player_name', 'Unknown')
    
    // Check if it's this player's turn
    my_player_id <- getattr(netmaster_client, 'player_id', None)
    is_my_turn <- (current_player_id == my_player_id)
    
    if is_my_turn:
        // Show player dashboard
        self.deiconify()
        self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
    else:
        // Show waiting screen
        self.show_waiting_for_turn_screen(current_player_name, current_player_color)
```

##### Service Expiration Management

```pseudocode
Function _verificar_services_expirados():
    // Find expired services
    services_expirados <- []
    
    for carta_path in self._service_start_turns:
        if self._is_service_expired(carta_path):
            services_expirados.append(carta_path)
    
    // Show expiration overlays sequentially
    if services_expirados:
        self._mostrar_overlays_services_expirados_sequencial(services_expirados, index=0)

Function _is_service_expired(carta_path):
    // Get service data from database
    service_data <- self._get_service_data_from_path(carta_path)
    if not service_data:
        return False
    
    // Check expiration based on type
    if service_data.get('duration_type') == 'turns':
        turns_elapsed <- self._current_turn_number - self._service_start_turns[carta_path]
        duration_turns <- service_data.get('duration_turns', 0)
        return turns_elapsed >= duration_turns
    
    return False

Function _processar_service_expirado_individual(carta_path):
    // Remove from active services
    if carta_path in self.active_services:
        self.active_services.remove(carta_path)
    
    // Remove from inventory
    if hasattr(self, 'inventario') and 'services' in self.inventario:
        if carta_path in self.inventario['services']:
            self.inventario['services'].remove(carta_path)
    
    // Cleanup tracking
    self._cleanup_expired_service_tracking(carta_path)
```

##### Game Phase Management System

```pseudocode
Function _criar_botao_next_phase():
    // Create Next Phase button
    self.next_phase_btn <- tk.Button(self, text="Next Phase",
                                    font=("Helvetica", 16, "bold"),
                                    bg="#A020F0", fg="white",
                                    command=self._iniciar_next_phase,
                                    width=12, height=2)
    self.next_phase_btn.place(relx=0.5, rely=0.95, anchor="s")

Function _iniciar_next_phase():
    // Set phase flags
    self._next_phase_active = True
    self._next_phase_manually_activated = True
    
    // Disable store button
    self.disable_store_button()
    
    // Create Final Phase button
    self._criar_botao_final_phase()

Function _iniciar_final_phase():
    // Validate bandwidth requirements
    if not self._has_active_bandwidth_services():
        self._show_bandwidth_required_message_overlay()
        return
    
    // Set final phase flags
    self._final_phase_active = True
    self._final_phase_gestao_ativa = True
    
    // Start packet management
    self._iniciar_gestao_pacotes()

Function end_turn():
    // Increment turn counter
    self._current_turn_number += 1
    
    // Check for expired services
    self._verificar_services_expirados()
    
    // Reset phase flags
    self._next_phase_active = False
    self._final_phase_active = False
    self._final_phase_gestao_ativa = False
    
    // Navigate to next turn
    self.show_dice_roll_screen(self.player_name, self.saldo, self.other_players)
```

###### Progress Tracking Implementation

```pseudocode
Function update_progress_bars_for_card(card_idx):
    // Validate card index and get current stats
    if card_idx >= len(self.card_stats) or card_idx < 0:
        return
    
    current_stats <- self.card_stats[card_idx]
    
    // Update each progress bar type
    for stat_type in ["To send", "Rxd", "Lost"]:
        if stat_type in self.progress_bars:
            current_value <- current_stats.get(stat_type, 0)
            max_value <- current_stats.get("message_size", 100)
            
            // Update progress bar widget
            progress_bar <- self.progress_bars[stat_type]
            progress_bar.configure(value=current_value, maximum=max_value)

Function _incrementar_valor(tipo, message_size):
    // Validate increment constraints
    if not self._validar_entrada(tipo, message_size):
        return False
    
    // Get selected card stats
    selected_idx <- self.selected_carousel_index
    if selected_idx is None:
        return False
    
    // Update progress values
    if tipo == "Rxd":
        self.card_stats[selected_idx]["Rxd"] += message_size
    elif tipo == "Lost":
        self.card_stats[selected_idx]["Lost"] += message_size
    
    // Update visual display
    self.update_progress_bars_for_card(selected_idx)
    
    // Check completion
    self._verificar_completion_activity()
    return True

Function _verificar_completion_activity():
    // Get current card information
    selected_idx <- self.selected_carousel_index
    if selected_idx is None:
        return
    
    carta_path <- self.cards[selected_idx]
    stats <- self.card_stats[selected_idx]
    
    // Check if card is completed
    to_send <- stats.get("To send", 0)
    if to_send <= 0:
        // Calculate reward and show completion overlay
        dados_carta <- self._obter_dados_carta(carta_path)
        reward <- self._calcular_reward_completion(carta_path, dados_carta, "activity", selected_idx)
        
        self._mostrar_overlay_completion(carta_path, dados_carta, False, selected_idx)
```

##### YOLO Detection Framework

```pseudocode
Function yolo_detect():
    // Parse command line arguments
    parser <- ArgumentParser()
    parser.add_argument('--model', help='Path to YOLO model file', required=True)
    parser.add_argument('--source', help='Image source (file, folder, video, usb0, picamera0)', required=True)
    parser.add_argument('--thresh', help='Minimum confidence threshold', default=0.5)
    parser.add_argument('--resolution', help='Resolution WxH', default=None)
    parser.add_argument('--record', help='Record results', action='store_true')
    parser.add_argument('--target_object', help='Target object name for auto-close', default=None)
    
    args <- parser.parse_args()
    
    // Extract arguments
    model_path <- args.model
    img_source <- args.source
    min_thresh <- args.thresh
    user_res <- args.resolution
    record <- args.record
    target_object <- args.target_object
    
    // Debug print target object
    if target_object:
        print f"Looking for target object: '{target_object}'"
    else:
        print "No target object specified - will close on any object with confidence > 0.8"
    
    // Validate model file exists
    if not os.path.exists(model_path):
        print 'ERROR: Model path is invalid or model was not found'
        sys.exit(0)
    
    // Load YOLO model
    model <- YOLO(model_path, task='detect')
    labels <- model.names
    
    // Determine source type (image, folder, video, usb, picamera)
    img_ext_list <- ['.jpg','.JPG','.jpeg','.JPEG','.png','.PNG','.bmp','.BMP']
    vid_ext_list <- ['.avi','.mov','.mp4','.mkv','.wmv']
    
    if os.path.isdir(img_source):
        source_type <- 'folder'
    elif os.path.isfile(img_source):
        _, ext <- os.path.splitext(img_source)
        if ext in img_ext_list:
            source_type <- 'image'
        elif ext in vid_ext_list:
            source_type <- 'video'
        else:
            print f'File extension {ext} is not supported'
            sys.exit(0)
    elif 'usb' in img_source:
        source_type <- 'usb'
        usb_idx <- int(img_source[3:])
    elif 'picamera' in img_source:
        source_type <- 'picamera'
        picam_idx <- int(img_source[8:])
    else:
        print f'Input {img_source} is invalid'
        sys.exit(0)
    
    // Parse display resolution if specified
    resize <- False
    if user_res:
        resize <- True
        resW, resH <- int(user_res.split('x')[0]), int(user_res.split('x')[1])
    
    // Setup recording if requested
    if record:
        if source_type not in ['video','usb']:
            print 'Recording only works for video and camera sources'
            sys.exit(0)
        if not user_res:
            print 'Please specify resolution to record video at'
            sys.exit(0)
        
        record_name <- 'demo1.avi'
        record_fps <- 30
        recorder <- cv2.VideoWriter(record_name, cv2.VideoWriter_fourcc(*'MJPG'), record_fps, (resW,resH))
    
    // Initialize image source based on type
    if source_type == 'image':
        imgs_list <- [img_source]
    elif source_type == 'folder':
        imgs_list <- []
        filelist <- glob.glob(img_source + '/*')
        for file in filelist:
            _, file_ext <- os.path.splitext(file)
            if file_ext in img_ext_list:
                imgs_list.append(file)
    elif source_type == 'video' or source_type == 'usb':
        if source_type == 'video': 
            cap_arg <- img_source
        elif source_type == 'usb': 
            cap_arg <- usb_idx
        cap <- cv2.VideoCapture(cap_arg)
        
        if user_res:
            ret <- cap.set(3, resW)
            ret <- cap.set(4, resH)
    elif source_type == 'picamera':
        from picamera2 import Picamera2
        cap <- Picamera2()
        cap.configure(cap.create_video_configuration(main={"format": 'XRGB8888', "size": (resW, resH)}))
        cap.start()
    
    // Set bounding box colors
    bbox_colors <- [(164,120,87), (68,148,228), (93,97,209), (178,182,133), (88,159,106), 
                   (96,202,231), (159,124,168), (169,162,241), (98,118,150), (172,176,184)]
    
    // Initialize variables
    avg_frame_rate <- 0
    frame_rate_buffer <- []
    fps_avg_len <- 200
    img_count <- 0
    
    // Main inference loop
    while True:
        t_start <- time.perf_counter()
        
        // Load frame based on source type
        if source_type == 'image' or source_type == 'folder':
            if img_count >= len(imgs_list):
                print 'All images have been processed. Exiting program.'
                sys.exit(0)
            img_filename <- imgs_list[img_count]
            frame <- cv2.imread(img_filename)
            img_count <- img_count + 1
        elif source_type == 'video':
            ret, frame <- cap.read()
            if not ret:
                print 'Reached end of the video file. Exiting program.'
                break
        elif source_type == 'usb':
            ret, frame <- cap.read()
            if (frame is None) or (not ret):
                print 'Unable to read frames from the camera. Exiting program.'
                break
        elif source_type == 'picamera':
            frame_bgra <- cap.capture_array()
            frame <- cv2.cvtColor(np.copy(frame_bgra), cv2.COLOR_BGRA2BGR)
            if (frame is None):
                print 'Unable to read frames from the Picamera. Exiting program.'
                break
        
        // Resize frame if needed
        if resize == True:
            frame <- cv2.resize(frame,(resW,resH))
        
        // Run YOLO inference
        results <- model(frame, verbose=False)
        detections <- results[0].boxes
        
        object_count <- 0
        target_detected <- False
        
        // Process each detection
        for i in range(len(detections)):
            // Get bounding box coordinates
            xyxy_tensor <- detections[i].xyxy.cpu()
            xyxy <- xyxy_tensor.numpy().squeeze()
            xmin, ymin, xmax, ymax <- xyxy.astype(int)
            
            // Get class ID and name
            classidx <- int(detections[i].cls.item())
            classname <- labels[classidx]
            
            // Get confidence
            conf <- detections[i].conf.item()
            
            // Debug print detection
            print f"Detected: '{classname}' with confidence {conf:.2f}"
            
            // Draw bounding box if confidence > 0.5
            if conf > 0.5:
                color <- bbox_colors[classidx % 10]
                cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), color, 2)
                label <- f'{classname}: {int(conf*100)}%'
                labelSize, baseLine <- cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                label_ymin <- max(ymin, labelSize[1] + 10)
                cv2.rectangle(frame, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), color, cv2.FILLED)
                cv2.putText(frame, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                object_count <- object_count + 1
            
            // Check for target detection with confidence > 0.8
            if conf > 0.8:
                print f"High confidence detection: '{classname}' with confidence {conf:.2f}"
                if target_object is None:
                    print "No specific target - will close on any high confidence detection"
                    target_detected <- True
                elif classname == target_object:
                    print f"Target object match! '{classname}' == '{target_object}'"
                    target_detected <- True
                else:
                    print f"Not target object: '{classname}' != '{target_object}'"
        
        // Draw framerate and scanning message
        if source_type == 'video' or source_type == 'usb' or source_type == 'picamera':
            cv2.putText(frame, f'FPS: {avg_frame_rate:0.2f}', (10,20), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,255,255), 2)
        
        cv2.putText(frame, f'Scanning object...', (10,40), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,255,255), 2)
        
        // Display fullscreen
        cv2.namedWindow("Object Detection", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Object Detection", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow('Object Detection',frame)
        if record: 
            recorder.write(frame)
        
        // Auto-close if target detected
        if target_detected:
            print "Object detected successfully!"
            print "Closing program automatically..."
            cv2.waitKey(1000)  // Wait 1 second to show detection
            if record: 
                recorder.release()
            if source_type == 'video' or source_type == 'usb':
                cap.release()
            elif source_type == 'picamera':
                cap.stop()
            cv2.destroyAllWindows()
            os._exit(0)  // Force program termination
        
        // Handle key presses
        if source_type == 'image' or source_type == 'folder':
            key <- cv2.waitKey()
        elif source_type == 'video' or source_type == 'usb' or source_type == 'picamera':
            key <- cv2.waitKey(5)
        
        if key == ord('q') or key == ord('Q'):  // Press 'q' to quit
            break
        elif key == ord('s') or key == ord('S'):  // Press 's' to pause
            cv2.waitKey()
        elif key == ord('p') or key == ord('P'):  // Press 'p' to save picture
            cv2.imwrite('capture.png',frame)
        
        // Calculate FPS
        t_stop <- time.perf_counter()
        frame_rate_calc <- float(1/(t_stop - t_start))
        
        // Update FPS buffer
        if len(frame_rate_buffer) >= fps_avg_len:
            temp <- frame_rate_buffer.pop(0)
            frame_rate_buffer.append(frame_rate_calc)
        else:
            frame_rate_buffer.append(frame_rate_calc)
        
        // Calculate average FPS
        avg_frame_rate <- np.mean(frame_rate_buffer)
    
    // Cleanup
    print f'Average pipeline FPS: {avg_frame_rate:.2f}'
    if source_type == 'video' or source_type == 'usb':
        cap.release()
    elif source_type == 'picamera':
        cap.stop()
    if record: 
        recorder.release()
    cv2.destroyAllWindows()
```

##### Equipment Activation and Validation Workflow Implementation

```pseudocode
Function execute_detection_script(object_name, parent_window=None):
    // Use universal utilities to detect environment and paths
    universal_paths <- get_universal_paths()
    
    if universal_paths['environment'] != 'raspberry_pi':
        print("Detection only works on Raspberry Pi")
        return False
    
    // Use automatically detected script path
    script_path <- universal_paths['detection_script']
    
    // Verify script exists
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        return False
    
    print(f"Executing: {script_path} {object_name}")
    
    // Make script executable
    subprocess.run(['chmod', '+x', script_path], check=True)
    
    // Create loading screen before executing script
    loading_window <- None
    if parent_window:
        loading_window <- create_yolo_loading_screen(parent_window, object_name)
    
    // Execute script in background
    process <- subprocess.Popen([script_path, object_name])
    
    print(f"Script started in background (PID: {process.pid})")
    
    // Monitor script with loading screen if available
    if parent_window and loading_window:
        monitor_detection_process_with_loading(process, loading_window, parent_window)
    
    return True

Function get_equipment_object_name(carta_path, card_database=None):
    // Initialize card database if not provided
    if not card_database:
        card_database <- IntegratedCardDatabase(".")
    
    // Extract filename from card path
    filename <- os.path.basename(carta_path)
    
    // Determine color from directory path
    color <- None
    if "/Blue/" in carta_path or "/blue/" in carta_path:
        color <- "azul"
    elif "/Red/" in carta_path or "/red/" in carta_path:
        color <- "vermelho"
    elif "/Green/" in carta_path or "/green/" in carta_path:
        color <- "verde"
    elif "/Yellow/" in carta_path or "/yellow/" in carta_path:
        color <- "amarelo"
    
    if not color:
        print(f"Could not determine color from path: {carta_path}")
        return None
    
    // Map filename to equipment type and ID
    match <- re.match(r'Equipment_(\d+)\.png', filename)
    if not match:
        print(f"Invalid equipment filename format: {filename}")
        return None
    
    equipment_num <- int(match.group(1))
    
    // Map equipment number to type and specific ID
    if 1 <= equipment_num <= 3:
        equipment_type <- "small_router"
        specific_id <- equipment_num
    elif 4 <= equipment_num <= 6:
        equipment_type <- "medium_router"
        specific_id <- equipment_num - 3
    elif 7 <= equipment_num <= 9:
        equipment_type <- "short_link"
        specific_id <- equipment_num - 6
    elif 10 <= equipment_num <= 12:
        equipment_type <- "long_link"
        specific_id <- equipment_num - 9
    else:
        print(f"Equipment number {equipment_num} out of valid range")
        return None
    
    // Construct equipment ID for database query
    equipment_id <- f"{equipment_type}_{specific_id}_{color}"
    
    // Query database for equipment data
    equipment_result <- card_database.get_equipment_with_file(equipment_id)
    
    if equipment_result:
        object_name <- equipment_result.get('object_name')
        print(f"Found object_name: {object_name}")
        return object_name
    else:
        print(f"Equipment not found in database: {equipment_id}")
        return None
```

##### Two-Phase Detection for Complex Operations

```pseudocode
Function execute_two_phase_detection_for_router_upgrade(old_object_name, new_object_name,loading_window, old_equipment_name, new_equipment_name):

    // Start Phase 1: Detect existing equipment
    universal_paths <- get_universal_paths()
    script_path <- universal_paths['detection_script']
    
    if not os.path.exists(script_path):
        print(f"Detection script not found: {script_path}")
        if loading_window:
            loading_window.destroy()
        return False
    
    print(f"Starting Phase 1 detection for: {old_object_name}")
    start_phase_1_detection(script_path, old_object_name, new_object_name, 
                           loading_window, old_equipment_name, new_equipment_name)
    
    return True

Function start_phase_1_detection(script_path, old_object_name, new_object_name, loading_window, old_equipment_name, new_equipment_name):

    // Update loading screen for Phase 1
    if loading_window and hasattr(loading_window, 'winfo_exists') and loading_window.winfo_exists():
        try:
            // Update loading text for Phase 1
            for widget in loading_window.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and "Initializing" in child.cget('text'):
                            child.configure(text=f"Phase 1: Remove {old_equipment_name}")
        except Exception as e:
            print(f"Error updating loading screen: {e}")
    
    // Execute Phase 1 detection
    subprocess.run(['chmod', '+x', script_path], check=True)
    process <- subprocess.Popen([script_path, old_object_name])
    
    print(f"Phase 1 detection started (PID: {process.pid})")
    
    // Monitor Phase 1 and transition to Phase 2
    monitor_phase_1_and_start_phase_2(process, script_path, new_object_name, new_equipment_name)

Function start_phase_2_detection(script_path, new_object_name, new_equipment_name):
    print(f"Starting Phase 2 detection for: {new_object_name}")
    
    // Create new loading screen for Phase 2
    loading_window_phase_2 <- create_yolo_loading_screen(self, new_object_name)
    
    if loading_window_phase_2:
        // Update loading text for Phase 2
        try:
            for widget in loading_window_phase_2.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and "Initializing" in child.cget('text'):
                            child.configure(text=f"Phase 2: Place {new_equipment_name}")
        except Exception as e:
            print(f"Error updating Phase 2 loading screen: {e}")
    
    // Execute Phase 2 detection
    subprocess.run(['chmod', '+x', script_path], check=True)
    process_phase_2 <- subprocess.Popen([script_path, new_object_name])
    
    print(f"Phase 2 detection started (PID: {process_phase_2.pid})")
    
    // Monitor Phase 2 completion
    monitor_phase_2_completion(process_phase_2, loading_window_phase_2)
```

##### Script Execution and Interface Management

```pseudocode
Script detection_fullscreen.sh:
    // Check if target object argument was provided
    if number_of_arguments == 0:
        print "Usage: $0 <object_name>"
        print "Example: $0 router_simples_vermelho"
        exit 1
    
    TARGET_OBJECT <- first_argument
    
    // Kill previous YOLO detection processes
    pkill -f yolo_detect.py
    
    // Wait 1 second
    sleep 1
    
    // Navigate to object detection directory
    cd "$HOME/netmaster_menu/object_detection"
    
    // Activate virtual environment
    source venv/bin/activate
    
    // Execute YOLO detection script with parameters
    python yolo_detect.py \
        --model="/home/joaorebolo2/netmaster_menu/object_detection/best_ncnn_model" \
        --source=picamera0 \
        --resolution=360x480 \
        --target_object="$TARGET_OBJECT"
    
    // Program terminates automatically after successful detection
    print "Detection script finished"
    
    // Deactivate virtual environment
    deactivate
```

### Store

#### Software Architecture and Implementation

##### Store Initialization and State Synchronization

```pseudocode
Function __init__(root, player_color, player_name, saldo, casa_tipo, casa_cor, inventario, dashboard, other_player_house):
    self.player_color <- player_color.lower()
    self.player_name <- player_name
    self.inventario <- inventario
    self.dashboard <- dashboard
    self.other_player_house <- other_player_house
    self.saldo <- saldo
    self.casa_tipo <- casa_tipo
    self.casa_cor <- casa_cor
    
    // Initialize synchronized card database
    self.card_database <- IntegratedCardDatabase(".")
    
    // Create synchronized local decks from global state
    self.cartas <- copy.deepcopy(baralhos)
    
    // Synchronize inventory and remove cards already owned
    if dashboard and hasattr(dashboard, 'inventario') and dashboard.inventario:
        total_removidas <- 0
        for tipo_carta, cartas_inventario in dashboard.inventario.items():
            if cartas_inventario:
                for carta_inventario in cartas_inventario:
                    nome_carta <- os.path.basename(carta_inventario)
                    for cor in self.cartas:
                        if tipo_carta in self.cartas[cor] and nome_carta in [os.path.basename(c) for c in self.cartas[cor][tipo_carta]]:
                            for carta_deck in list(self.cartas[cor][tipo_carta]):
                                if os.path.basename(carta_deck) == nome_carta:
                                    self.cartas[cor][tipo_carta].remove(carta_deck)
                                    total_removidas += 1
                                    break

    // Apply board position highlighting
    if casa_tipo and casa_cor:
        self.highlight_casa(casa_tipo, casa_cor)
    else:
        self.disable_all_buttons()
```

#### Features

##### Interface Architecture and Visual Design Implementation

```pseudocode
Function rebuild_store_interface():
    // Clear existing widgets and setup fullscreen
    for widget in self.winfo_children():
        widget.destroy()
    self.update()
    self.configure(bg="black")
    
    screen_width <- self.winfo_screenwidth()
    screen_height <- self.winfo_screenheight()
    
    // Create branded header with Store awning
    awning_img <- ImageTk.PhotoImage(Image.open(AWNING_IMG).resize((screen_width, 65)))
    awning_label <- tk.Label(self, image=awning_img, bg="black")
    awning_label.image <- awning_img
    awning_label.pack(pady=(0, 10), fill="x")
    
    // Create logo and store title positioning
    left_label <- tk.Label(self, text="....", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
    left_label.place(relx=0.46, y=10, anchor="center")
    
    logo_img <- ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "logo_netmaster_store.png")).resize((24, 24)))
    logo_lbl <- tk.Label(self, image=logo_img, bg="#DC8392")
    logo_lbl.image <- logo_img
    logo_lbl.place(relx=0.5, y=10, anchor="center")
    
    store_name_lbl <- tk.Label(self, text="Store", font=("Helvetica", 15, "bold"), bg="#DC8392", fg="black")
    store_name_lbl.place(relx=0.5, y=30, anchor="center")
    
    // Create matrix of category buttons
    main_frame <- tk.Frame(self, bg="black")
    main_frame.pack(anchor="center", pady=(0, 10))
    
    // First row: Actions, Events, Challenges (neutral cards)
    img_size <- (90, 90)
    actions_img <- ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Actions_button.png")).resize(img_size))
    events_img <- ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Events_button.png")).resize(img_size))
    challenges_img <- ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Challenges_button.png")).resize(img_size))
    
    self.btn_a <- tk.Button(main_frame, image=actions_img, bg="#000000", width=75, height=80)
    self.btn_e <- tk.Button(main_frame, image=events_img, bg="#000000", width=75, height=80)
    self.btn_d <- tk.Button(main_frame, image=challenges_img, bg="#000000", width=75, height=80)
    
    self.btn_a.grid(row=0, column=0, padx=10, pady=(5, 2))
    self.btn_e.grid(row=0, column=1, padx=10, pady=(5, 2))
    self.btn_d.grid(row=0, column=2, padx=10, pady=(5, 2))
    
    // Second row: Player-colored buttons for inventory categories
    players_frame <- tk.Frame(self, bg="black")
    players_frame.pack(pady=(0, 0))
    
    btn_users <- tk.Button(players_frame, text="Users", font=("Helvetica", 18, "bold"), bg=self.player_color_hex, fg="black")
    btn_equipments <- tk.Button(players_frame, text="Equipments", font=("Helvetica", 18, "bold"), bg=self.player_color_hex, fg="black")
    btn_activities <- tk.Button(players_frame, text="Activities", font=("Helvetica", 18, "bold"), bg=self.player_color_hex, fg="black")
    btn_services <- tk.Button(players_frame, text="Services", font=("Helvetica", 18, "bold"), bg=self.player_color_hex, fg="black")
    
    self.card_buttons <- {
        "users": btn_users,
        "equipments": btn_equipments,
        "activities": btn_activities,
        "services": btn_services
    }
```

##### Card Acquisition System Implementation

```pseudocode
Function show_buy_page():
    tipo_atual <- getattr(self, 'current_card_type', None)
    if not tipo_atual:
        messagebox.showinfo("Erro", "Tipo de carta nao definido!")
        return
    
    // Determine color for card search - always player's color
    cor_para_buscar <- self.player_color
    
    // Get available cards from local deck (player's color + sold cards)
    cartas_disp <- []
    
    if (hasattr(self, 'cartas') and cor_para_buscar in self.cartas and 
        tipo_atual in self.cartas[cor_para_buscar]):
        cartas_disp.extend(self.cartas[cor_para_buscar][tipo_atual].copy())
    
    // Add sold cards from other players
    if hasattr(self, 'cartas'):
        for cor_jogador in ["red", "blue", "green", "yellow"]:
            if (cor_jogador != cor_para_buscar and cor_jogador in self.cartas and 
                tipo_atual in self.cartas[cor_jogador]):
                for carta in self.cartas[cor_jogador][tipo_atual]:
                    cartas_disp.append(carta)
    
    // Filter cards already in player inventory
    if self.dashboard and hasattr(self.dashboard, 'inventario') and tipo_atual in self.dashboard.inventario:
        cartas_no_inventario <- self.dashboard.inventario[tipo_atual]
        nomes_no_inventario <- {os.path.basename(carta) for carta in cartas_no_inventario}
        cartas_disp <- [carta for carta in cartas_disp if os.path.basename(carta) not in nomes_no_inventario]
    
    // Apply pagination and create grid layout
    cards_per_page <- 4
    self._current_buy_page <- getattr(self, '_current_buy_page', 0)
    start_idx <- self._current_buy_page * cards_per_page
    end_idx <- start_idx + cards_per_page
    cartas_page <- cartas_disp[start_idx:end_idx]
    
    // Create 2x2 grid with fullscreen callbacks
    self.matriz_frame <- tk.Frame(self, bg="black")
    self.matriz_frame.place(relx=0.5, rely=0.55, anchor="center")
    
    for idx, carta_path in enumerate(cartas_page):
        row <- idx // 2
        col <- idx % 2
        global_idx <- start_idx + idx
        img <- ImageTk.PhotoImage(Image.open(carta_path).resize((85, 120)))
        carta_lbl <- tk.Label(self.matriz_frame, image=img, bg="black", cursor="hand2")
        carta_lbl.bind("<Button-1>", lambda e, p=carta_path, gi=global_idx: self._abrir_fullscreen_carta(gi))
```

##### Card Purchase Transaction Processing

```pseudocode
Function _comprar_carta():
    if self._selected_card_idx is None or self._selected_card_idx >= len(self._cartas_disponiveis):
        messagebox.showwarning("Nenhuma carta selecionada", "Por favor seleciona uma carta primeiro!")
        return
        
    carta_path <- self._cartas_disponiveis[self._selected_card_idx]
    valor <- self._extrair_valor_carta(carta_path)
    
    // Validate transaction feasibility
    player_saldo <- self.dashboard.saldo if self.dashboard else self.saldo
    
    if valor is not None and self.dashboard and self.dashboard.saldo >= valor:
        // Process financial transaction
        self.dashboard.saldo -= valor
        self.saldo += valor
        
        // Transfer card to player inventory
        tipo_inv <- self.current_card_type
        if tipo_inv == "equipment":
            tipo_inv <- "equipments"
        elif tipo_inv == "action":
            tipo_inv <- "actions"
        
        self.dashboard.adicionar_carta_inventario(carta_path, tipo_inv)
        
        // Remove card from store decks
        self._remover_carta_do_baralho_local(carta_path, tipo_inv)
        
        // Show success message and return
        messagebox.showinfo("Compra realizada", f"Carta comprada por {valor} PICoins!")
        self.show_buy_page()
    else:
        messagebox.showerror("Saldo insuficiente", f"Precisa de {valor} PICoins para comprar esta carta!")

Function _extrair_valor_carta(carta_path):
    if not self.card_database:
        // Fallback to filename pattern extraction
        nome <- os.path.basename(carta_path)
        match <- re.search(r'_(\d+)\.', nome)
        if match:
            return int(match.group(1))
        return None
    
    // Extract card information from database
    tipo_carta <- self._get_card_type_from_path(carta_path)
    card_id <- self._map_file_to_card_id(carta_path, tipo_carta)
    
    // Query database for card value
    if tipo_carta == "users":
        card <- self.card_database.get_user(card_id)
        return card.buy_cost if card else None
    elif tipo_carta == "equipments":
        card <- self.card_database.get_equipment(card_id)
        return card.buy_cost if card else None
    elif tipo_carta == "services":
        card <- self.card_database.get_service(card_id)
        return card.buy_cost if card else None
    elif tipo_carta == "activities":
        card <- self.card_database.get_activity(card_id)
        return card.application_fee if card else None
```

##### Randomized Deck Management Implementation

```pseudocode
Function tirar_carta_especifica(tipo, cor):
    // Check local deck availability
    if not hasattr(self, 'cartas') or not self.cartas:
        return None
    
    if cor not in self.cartas:
        return None
        
    if tipo not in self.cartas[cor]:
        return None
        
    if not self.cartas[cor][tipo]:
        return None
    
    // Select random card and remove from local deck
    carta_path <- random.choice(self.cartas[cor][tipo])
    self.cartas[cor][tipo].remove(carta_path)
    
    // Synchronize with global deck
    global baralhos
    if (baralhos and cor in baralhos and tipo in baralhos[cor] and 
        carta_path in baralhos[cor][tipo]):
        baralhos[cor][tipo].remove(carta_path)
    
    return carta_path

Function mostrar_carta(casa_cor, tipo):
    // Clear interface and show face-down card
    for widget in self.winfo_children():
        widget.destroy()
    self.configure(bg="black")
    
    center_frame <- tk.Frame(self, bg="black")
    center_frame.pack(expand=True)
    
    // Show back card initially
    verso_path <- os.path.join(IMG_DIR, "cartas", "back_card.png")
    if os.path.exists(verso_path):
        verso_img <- ImageTk.PhotoImage(Image.open(verso_path).resize((150, 210)))
        carta_lbl <- tk.Label(center_frame, image=verso_img, bg="black")
        carta_lbl.image <- verso_img
        carta_lbl.pack(pady=(0, 12))
    
    def revelar_carta():
        carta_lbl.destroy()
        go_btn.destroy()
        
        // Draw card from appropriate deck
        if tipo == "actions":
            carta_path <- tirar_carta("neutral", "actions")
        elif tipo == "events":
            carta_path <- tirar_carta("neutral", "events")
        elif tipo == "challenges":
            carta_path <- tirar_carta(casa_cor, "challenges")
        
        if carta_path and os.path.exists(carta_path):
            self.mostrar_carta_fullscreen(carta_path, tipo)
    
    go_btn <- tk.Button(center_frame, text="Go!", font=("Helvetica", 16, "bold"), 
                       bg="#005c75", fg="white", command=revelar_carta)
    go_btn.pack(pady=(5, 0))
```

##### Challenge Card Integration System Implementation

```pseudocode
Function processar_casa_challenges(casa_cor):
    // Draw Challenge card from deck
    carta_path <- self.tirar_carta_especifica("challenges", casa_cor)
    if not carta_path:
        messagebox.showwarning("Sem cartas", "Nao ha cartas de Challenges disponiveis!")
        return False
    
    // Show fullscreen Challenge with accept/reject options
    self.mostrar_carta_challenge_fullscreen(carta_path)
    return True

Function _processar_troca_challenge_activity(challenge_path):
    // Find active Activities in player carousel
    activities_ativas_indices <- []
    carrossel_cards <- getattr(self.dashboard, 'cards', [])
    
    for i, carta_path in enumerate(carrossel_cards):
        if carta_path and not os.path.basename(carta_path).startswith("back_card_"):
            if self.dashboard._is_activity_card(carta_path):
                activities_ativas_indices.append(i)
    
    // Determine substitution workflow based on active Activities
    if len(activities_ativas_indices) == 0:
        // No active Activities - Challenge goes to inventory
        self._enviar_challenge_para_inventario(challenge_path)
    elif len(activities_ativas_indices) == 1:
        // Single Activity - substitute automatically
        idx_substituir <- activities_ativas_indices[0]
        self._executar_troca_challenge_activity(challenge_path, idx_substituir)
    else:
        // Multiple Activities - show selection interface
        self._mostrar_interface_escolha_activity(challenge_path, activities_ativas_indices, 0)

Function _executar_troca_challenge_activity(challenge_path, idx_activity):
    carrossel_cards <- getattr(self.dashboard, 'cards', [])
    activity_substituida <- carrossel_cards[idx_activity]
    
    // Preserve Activity progress before substitution
    activity_original_stats <- None
    if (hasattr(self.dashboard, 'card_stats') and 
        idx_activity < len(self.dashboard.card_stats)):
        activity_original_stats <- {
            "To send": self.dashboard.card_stats[idx_activity]["To send"],
            "Rxd": self.dashboard.card_stats[idx_activity]["Rxd"], 
            "Lost": self.dashboard.card_stats[idx_activity]["Lost"]
        }
    
    // Move substituted Activity to inventory
    if hasattr(self.dashboard, 'inventario'):
        if 'activities' not in self.dashboard.inventario:
            self.dashboard.inventario['activities'] <- []
        self.dashboard.inventario['activities'].append(activity_substituida)
    
    // Place Challenge in carousel and reset progress
    self.dashboard.cards[idx_activity] <- challenge_path
    message_size <- self.dashboard._get_card_message_size(challenge_path)
    self.dashboard.card_stats[idx_activity] <- {
        "To send": message_size,
        "Rxd": 0,
        "Lost": 0,
        "message_size": message_size
    }
    
    // Preserve original Activity stats for future restoration
    if activity_original_stats and hasattr(self.dashboard, 'inventario'):
        if not hasattr(self.dashboard, '_activity_preserved_stats'):
            self.dashboard._activity_preserved_stats <- {}
        self.dashboard._activity_preserved_stats[activity_substituida] <- activity_original_stats.copy()
    
    // Disable Store button and return to dashboard
    self.dashboard.disable_store_button()
    self._voltar_para_playerdashboard_apos_troca()
```

##### Multiplayer Integration and Communication Implementation

```pseudocode
Function _enviar_carta_para_jogador(carta_path, casa_tipo, jogador_alvo):
    // Validate target player using server broadcast data
    cor_valida_no_broadcast <- self._verificar_cor_no_players_broadcast(jogador_alvo)
    
    if cor_valida_no_broadcast:
        // Process card delivery based on target
        if jogador_alvo == self.player_color:
            // Self-targeting: add directly to inventory
            tipo_inv <- casa_tipo
            if casa_tipo == "actions":
                tipo_inv <- "Actions"
            elif casa_tipo == "events":
                tipo_inv <- "Events"
            
            self.dashboard.adicionar_carta_inventario(carta_path, tipo_inv)
            self._mostrar_confirmacao_envio(carta_path, casa_tipo, jogador_alvo)
        else:
            // Other player: store on server for later retrieval
            self._armazenar_carta_no_servidor(carta_path, casa_tipo, jogador_alvo, None)
            self._mostrar_confirmacao_envio(carta_path, casa_tipo, jogador_alvo)
    else:
        // Player not found - show error message
        self._mostrar_confirmacao_devolucao(carta_path, casa_tipo, jogador_alvo)
    
    // Remove card from local deck
    self._remover_carta_do_baralho_local(carta_path, casa_tipo)
    self._voltar_ao_dashboard()

Function _armazenar_carta_no_servidor(carta_path, tipo_carta, jogador_alvo, target_player_id):
    netmaster_client <- __main__.netmaster_client
    
    // Prepare card data for server storage
    card_id <- os.path.splitext(os.path.basename(carta_path))[0]
    card_data <- {
        'id': card_id,
        'card_path': carta_path,
        'card_type': tipo_carta.lower(),
        'from_player': self.player_color
    }
    
    // Create server message
    message <- {
        'type': 'store_card_for_player',
        'sender_player_id': getattr(netmaster_client, 'player_id', 'unknown'),
        'sender_color': self.player_color,
        'target_player_color': jogador_alvo,
        'target_player_id': target_player_id,
        'card_data': card_data
    }
    
    // Send via async WebSocket in separate thread
    send_result <- [False]
    def send_message_in_thread():
        try:
            asyncio.run(netmaster_client.send_message(message))
            send_result[0] <- True
        except Exception as e:
            send_result[0] <- False
    
    thread <- threading.Thread(target=send_message_in_thread, daemon=True)
    thread.start()
    thread.join(timeout=5.0)
    
    return send_result[0]

Function _verificar_cor_no_players_broadcast(cor_alvo):
    // Check if target color exists in server broadcast data
    if not hasattr(self, 'dashboard') or not self.dashboard:
        return False
    
    if not hasattr(self.dashboard, 'session_players') or not self.dashboard.session_players:
        return False
    
    // Search for color in broadcast data
    for player_id, info in self.dashboard.session_players.items():
        player_color <- info.get('color', '').lower()
        is_active <- info.get('is_active', False)
        
        if player_color == cor_alvo.lower() and is_active:
            return True
    
    return False
```

##### Transaction and Balance Management Implementation

```pseudocode
Function confirmar_venda_carta(carta_path, carta_tipo, player_dashboard):
    // Extract card value using database or filename fallback
    valor <- None
    nome <- os.path.basename(carta_path)
    
    if carta_tipo == "activities":
        valor <- 0  // Activities always have zero sale value
    else:
        // Try to extract value from filename pattern
        match <- re.search(r'_(\d+)\.', nome)
        if match:
            valor <- int(match.group(1))
        else:
            valor <- 50  // Default value
    
    // Process sale transaction
    if valor is not None and valor > 0:
        // Update balances
        if player_dashboard:
            player_dashboard.saldo += valor
            self.saldo -= valor
        
        // Remove from player inventory
        if player_dashboard and hasattr(player_dashboard, 'inventario'):
            if carta_tipo in player_dashboard.inventario:
                if carta_path in player_dashboard.inventario[carta_tipo]:
                    player_dashboard.inventario[carta_tipo].remove(carta_path)
        
        // Add back to store decks for future purchases
        self.adicionar_carta_ao_baralho(carta_path, carta_tipo, self.player_color)

Function adicionar_carta_ao_baralho(carta_path, carta_tipo, carta_cor):
    // Add sold card back to store decks
    if carta_cor is None:
        carta_cor <- self.player_color
    
    // Ensure local deck structure exists
    if not hasattr(self, 'cartas'):
        self.cartas <- {}
    
    if carta_cor not in self.cartas:
        self.cartas[carta_cor] <- {}
    
    if carta_tipo not in self.cartas[carta_cor]:
        self.cartas[carta_cor][carta_tipo] <- []
    
    // Add to local deck if not already present
    if carta_path not in self.cartas[carta_cor][carta_tipo]:
        self.cartas[carta_cor][carta_tipo].append(carta_path)
    
    // Synchronize with global deck
    global baralhos
    if baralhos:
        if carta_cor not in baralhos:
            baralhos[carta_cor] <- {}
        if carta_tipo not in baralhos[carta_cor]:
            baralhos[carta_cor][carta_tipo] <- []
        if carta_path not in baralhos[carta_cor][carta_tipo]:
            baralhos[carta_cor][carta_tipo].append(carta_path)
```

### Cards Database

#### Software Architecture and Implementation

##### Database Initialization and Population

```pseudocode
Function __init__():
    // Initialize card storage dictionaries with type-specific containers
    self.users <- {}
    self.equipments <- {}
    self.services <- {}
    self.activities <- {}
    self.challenges <- {}
    self.actions <- {}
    self.events <- {}
    
    // Initialize metadata tracking structures
    self.card_counts <- {}
    self.validation_cache <- {}
    self.modification_timestamps <- {}
    
    // Populate database with card data using systematic approach
    self._initialize_database()

Function _initialize_database():
    // Create all card types systematically with dependency management
    print("Initializing NetMaster Cards Database...")
    
    // Phase 1: Create base card types (no dependencies)
    self._create_user_cards()
    self._create_equipment_cards()
    
    // Phase 2: Create service-dependent cards
    self._create_service_cards()
    
    // Phase 3: Create gameplay cards with dependencies
    self._create_activity_cards()
    self._create_challenge_cards()
    
    // Phase 4: Create dynamic interaction cards
    self._create_action_cards()
    self._create_event_cards()
    
    // Phase 5: Validate integrity and establish cross-references
    self._validate_database_integrity()
    self._build_cross_reference_indices()
    
    print(f"Database initialization complete: {self.get_total_card_count()} cards loaded")
```

#### Card Creation and Population System

##### User Cards Implementation

```pseudocode
Function _create_user_cards():
    // Residential user cards creation
    colors <- ["red", "green", "blue", "yellow"]
    
    // Card creation statistics tracking
    total_cards_created <- 0
    individual_cards_created <- 0
    
    for i in range(1, 7):  // User_1 to User_6 covering all card variations
        for color in colors:
            if i == 1:
                // User_1 represents a special residential user type
                user_id <- f"contract_{color}"
                users_count <- 4     // Supports up to 4 residential users
                applications <- 0    // No direct applications (managed separately)
                services <- 0        // No direct services (managed separately)
                buy_cost <- 0        // No acquisition cost
                sell_cost <- 0       // Cannot be resold
                
                // Network management attributes
                bandwidth_allocation <- "shared"
                quality_of_service <- "standard"
                
                individual_cards_created += 1
            else:
                // User_2 to User_6 correspond to individual User IDs 1 to 5
                actual_user_id <- i - 1  // Mapping: User_2=ID_1, User_3=ID_2, etc.
                user_id <- f"{actual_user_id}_{color}"
                
                // All individual User IDs have characteristics
                users_count <- 1     // Each card represents exactly 1 user
                applications <- 1    // Each user requires 1 application slot
                services <- 1        // Each user requires 1 service subscription
                buy_cost <- 2        // Acquisition cost: 2 picoins
                sell_cost <- 1       // Resale value: 1 picoin (50% depreciation)
                
                // Individual user attributes for resource management
                bandwidth_allocation <- "dedicated"
                quality_of_service <- "standard"
                
                individual_cards_created += 1
            
            // Create UserCard instance with attribute set
            user_card <- UserCard(
                user_id=user_id,
                user_type=UserType.RESIDENTIAL,
                color=color,
                users_count=users_count,
                applications=applications,
                services=services,
                buy_cost=buy_cost,
                sell_cost=sell_cost,
                created_timestamp=get_current_timestamp(),
                validation_status="valid"
            )
            
            // Store in database with indexing
            self.users[user_id] <- user_card
            total_cards_created += 1
            
            // Update category-specific indices for efficient querying
            self._update_user_indices(user_card)
    
    // Log creation statistics for database management
    print(f"User Cards Creation Complete:")
    print(f"  Total Cards: {total_cards_created}")
    print(f"  Individual User Cards: {individual_cards_created}")
    print(f"  Colors Supported: {len(colors)}")
```

##### Equipment Cards Implementation

```pseudocode
Function _create_equipment_cards():
    colors <- ["red", "green", "blue", "yellow"]
    
    // Cost and specification mapping for all equipment types
    equipment_costs <- {
        // Small Router specifications (Entry-level network equipment)
        "small_router_1": {"buy": 40, "sell": 20, "queue_size": 4, "throughput": 10, "power_consumption": 15},
        "small_router_2": {"buy": 40, "sell": 20, "queue_size": 4, "throughput": 10, "power_consumption": 15},
        "small_router_3": {"buy": 40, "sell": 20, "queue_size": 4, "throughput": 10, "power_consumption": 15},
        
        // Medium Router specifications (Enterprise-grade network equipment)
        "medium_router_1": {"buy": 80, "sell": 40, "queue_size": 8, "throughput": 25, "power_consumption": 35},
        "medium_router_2": {"buy": 80, "sell": 40, "queue_size": 8, "throughput": 25, "power_consumption": 35},
        "medium_router_3": {"buy": 80, "sell": 40, "queue_size": 8, "throughput": 25, "power_consumption": 35},
        
        // Short Link specifications (Local area network connections)
        "short_link_1": {"buy": 40, "sell": 20, "link_length": 4, "bandwidth": 100, "latency": 1},
        "short_link_2": {"buy": 40, "sell": 20, "link_length": 4, "bandwidth": 100, "latency": 1},
        "short_link_3": {"buy": 40, "sell": 20, "link_length": 4, "bandwidth": 100, "latency": 1},
        
        // Long Link specifications (Wide area network connections)
        "long_link_1": {"buy": 80, "sell": 40, "link_length": 8, "bandwidth": 50, "latency": 5},
        "long_link_2": {"buy": 80, "sell": 40, "link_length": 8, "bandwidth": 50, "latency": 5},
        "long_link_3": {"buy": 80, "sell": 40, "link_length": 8, "bandwidth": 50, "latency": 5}
    }
    
    // Object detection mapping for computer vision integration
    // Maps equipment type and color to specific object detection identifiers
    object_names <- {
        // Small Router detection patterns
        "small_router_red": "small_router_red",
        "small_router_green": "small_router_green", 
        "small_router_blue": "small_router_blue",
        "small_router_yellow": "small_router_yellow",
        
        // Medium Router detection patterns
        "medium_router_red": "medium_router_red",
        "medium_router_green": "medium_router_green",
        "medium_router_blue": "medium_router_blue", 
        "medium_router_yellow": "medium_router_yellow",
        
        // Short Link detection patterns
        "short_link_red": "short_link_red",
        "short_link_green": "short_link_green",
        "short_link_blue": "short_link_blue",
        "short_link_yellow": "short_link_yellow",
        
        // Long Link detection patterns
        "long_link_red": "long_link_red", 
        "long_link_green": "long_link_green",
        "long_link_blue": "long_link_blue",
        "long_link_yellow": "long_link_yellow"
    }
    
    // Small Router creation (Equipment_1 to Equipment_3)
    // Implements entry-level routing capabilities for residential networks
    for i in range(1, 4):
        for color in colors:
            equipment_id <- f"small_router_{i}_{color}"
            base_id <- f"small_router_{i}"
            
            // Retrieve specifications with fallback defaults
            costs <- equipment_costs.get(base_id, {
                "buy": 40, "sell": 20, "queue_size": 4, 
                "throughput": 10, "power_consumption": 15
            })
            
            // Map to object detection identifier
            object_name <- object_names.get(f"small_router_{color}")
            
            // Create equipment card with network specifications
            equipment_card <- EquipmentCard(
                equipment_id=equipment_id,
                equipment_type=EquipmentType.SMALL_ROUTER,
                color=color,
                category="Router",
                model="Small Router",
                specific_id=i,
                
                // Network performance specifications
                queue_size=costs["queue_size"],
                throughput_mbps=costs["throughput"],
                power_consumption_watts=costs["power_consumption"],
                
                // Link-specific attributes (None for routers)
                link_rate=None,
                link_length=None,
                
                // Economic attributes
                buy_cost=costs["buy"],
                sell_cost=costs["sell"],
                
                // Computer vision integration
                object_name=object_name,
                
                // Metadata for system management
                created_timestamp=get_current_timestamp(),
                validation_status="valid",
                compatibility_matrix=self._generate_router_compatibility_matrix("small")
            )
            
            // Store in database with indexing
            self.equipments[equipment_id] <- equipment_card
            
            // Update equipment-specific indices and cross-references
            self._update_equipment_indices(equipment_card)
    
    // Medium Router creation follows similar pattern with enhanced specifications
    // Long Link and Short Link creation with network topology considerations
    // [Additional equipment types follow similar creation patterns]
    
    // Generate equipment compatibility matrices for network design validation
    self._generate_equipment_compatibility_matrices()
    
    // Validate equipment specifications against network performance requirements
    self._validate_equipment_specifications()
```

##### Service Cards Implementation

```pseudocode
Function _create_service_cards():
    colors <- ["red", "green", "blue", "yellow"]
    
    // Service specifications with economic modeling
    service_costs <- {
        // Bandwidth Service - Continuous network access model
        "bandwidth_1": {
            "service_type": ServiceType.BANDWIDTH,
            "service_packets_turn": 1,    // Guaranteed packets per turn
            "buy_price": 80,              // Premium pricing for guaranteed service
            "sell_price": 0,              // Non-transferable service subscription
            "renewal_cost": 40,           // Periodic renewal cost
            "quality_guarantee": "high"   // Service level agreement
        },
        
        // Data Volume Services - Consumption-based pricing models
        "data_volume_1": {
            "service_type": ServiceType.DATA_VOLUME,
            "service_packets": 5,         // Basic packet allocation
            "buy_price": 5,               // Entry-level pricing
            "sell_price": 0,              // Non-transferable
            "cost_per_packet": 1.0,       // Unit cost economics
            "overage_penalty": 1.5        // Penalty for exceeding allocation
        },
        "data_volume_2": {
            "service_type": ServiceType.DATA_VOLUME,
            "service_packets": 10,        // Standard packet allocation
            "buy_price": 8,               // Volume discount pricing
            "sell_price": 0,
            "cost_per_packet": 0.8,       // Improved unit economics
            "overage_penalty": 1.2
        },
        "data_volume_3": {
            "service_type": ServiceType.DATA_VOLUME,
            "service_packets": 20,        // Premium packet allocation
            "buy_price": 15,              // Best value proposition
            "sell_price": 0,
            "cost_per_packet": 0.75,      // Optimal unit economics
            "overage_penalty": 1.0        // Minimal penalties
        },
        
        // Temporary Services - Time-limited network capabilities
        "temporary_1": {
            "service_type": ServiceType.TEMPORARY,
            "service_turns": 4,           // Short-term service duration
            "buy_price": 4,               // Pay-per-use pricing
            "sell_price": 0,
            "turn_cost": 1.0,             // Cost per turn of service
            "auto_renewal": False         // Manual renewal required
        },
        "temporary_2": {
            "service_type": ServiceType.TEMPORARY,
            "service_turns": 8,           // Medium-term service duration
            "buy_price": 7,               // Volume discount for longer commitment
            "sell_price": 0,
            "turn_cost": 0.875,           // Improved turn economics
            "auto_renewal": True          // Automatic renewal option
        },
        "temporary_3": {
            "service_type": ServiceType.TEMPORARY,
            "service_turns": 16,          // Long-term service commitment
            "buy_price": 14,              // Maximum volume discount
            "sell_price": 0,
            "turn_cost": 0.875,           // Best turn economics
            "auto_renewal": True          // Automatic renewal included
        }
    }
    
    // Service template definitions with descriptions
    service_templates <- [
        {
            "type": ServiceType.BANDWIDTH,
            "base_key": "bandwidth_1",
            "title": "BANDWIDTH SERVICE",
            "description": "Subscribe to our premium Bandwidth Service and enjoy seamless network access with guaranteed packet delivery whenever you need it. Perfect for continuous applications requiring reliable connectivity.",
            "target_market": "residential_premium",
            "service_level": "guaranteed",
            "technical_specs": {
                "guaranteed_throughput": True,
                "priority_queuing": True,
                "quality_monitoring": True
            }
        },
        {
            "type": ServiceType.DATA_VOLUME,
            "base_key": "data_volume_1",
            "title": "DATA VOLUME - BASIC",
            "description": "Subscribe to our flexible Data Volume Service and pay only for the data you actually use. Ideal for light internet usage with predictable costs.",
            "target_market": "residential_basic",
            "service_level": "standard",
            "technical_specs": {
                "packet_tracking": True,
                "usage_analytics": True,
                "overage_protection": False
            }
        },
        {
            "type": ServiceType.DATA_VOLUME,
            "base_key": "data_volume_2",
            "title": "DATA VOLUME - STANDARD",
            "description": "Enhanced Data Volume Service with increased packet allocation and improved unit economics. Perfect for moderate internet usage with cost control.",
            "target_market": "residential_standard",
            "service_level": "enhanced",
            "technical_specs": {
                "packet_tracking": True,
                "usage_analytics": True,
                "overage_protection": True
            }
        },
        {
            "type": ServiceType.DATA_VOLUME,
            "base_key": "data_volume_3",
            "title": "DATA VOLUME - PREMIUM",
            "description": "Premium Data Volume Service offering maximum packet allocation with optimal pricing and minimal overage penalties. Best value for heavy internet users.",
            "target_market": "residential_premium",
            "service_level": "premium",
            "technical_specs": {
                "packet_tracking": True,
                "usage_analytics": True,
                "overage_protection": True,
                "priority_support": True
            }
        }
        // Additional service templates for temporary services and specialized offerings
        // [Temporary service templates with similar specifications]
    ]
    
    // Sequential ID assignment for service identification
    service_counter <- 1
    
    // Create service cards for each color with attribute mapping
    for color in colors:
        for template in service_templates:
            service_id <- f"Service_{service_counter}"
            base_key <- template["base_key"]
            
            service_counter += 1
            
            // Retrieve service specifications with defaults
            costs <- service_costs.get(base_key, {
                "buy_price": 80, "sell_price": 0, 
                "service_packets_turn": 1, "quality_guarantee": "standard"
            })
            
            // Create service card with full specifications
            service_card <- ServiceCard(
                service_id=service_id,
                service_type=template["type"],
                color=color,
                title=template["title"],
                description=template["description"],
                
                // Service specifications
                valid_for="1 Residential User",
                target_market=template["target_market"],
                service_level=template["service_level"],
                technical_specs=template["technical_specs"],
                
                // Economic attributes
                buy_cost=costs["buy_price"],
                sell_cost=costs["sell_price"],
                renewal_cost=costs.get("renewal_cost", 0),
                
                // Service-specific parameters
                service_packets_turn=costs.get("service_packets_turn"),
                service_packets=costs.get("service_packets"),
                service_turns=costs.get("service_turns"),
                
                // Quality and performance guarantees
                quality_guarantee=costs.get("quality_guarantee", "standard"),
                auto_renewal=costs.get("auto_renewal", False),
                
                // Metadata for system management
                created_timestamp=get_current_timestamp(),
                validation_status="valid"
            )
            
            // Store in database with indexing
            self.services[service_id] <- service_card
            
            // Update service-specific indices and compatibility matrices
            self._update_service_indices(service_card)
    
    // Generate service compatibility matrices and pricing optimization
    self._generate_service_compatibility_matrices()
    self._optimize_service_pricing_models()
    
    // Validate service specifications against market requirements
    self._validate_service_market_positioning()
```

##### Activity and Challenge Cards Implementation

```pseudocode
Function _create_activity_cards():
    colors <- ["red", "green", "blue", "yellow"]
    
    // Activity templates based on real-world network applications
    activity_templates <- [
        // HOME SURVEILLANCE - Multiple variations with different reward structures
        {
            "type": ActivityType.HOME_SURVEILLANCE,
            "title": "HOME SURVEILLANCE SYSTEM",
            "description": "Deploy and manage a home surveillance application that monitors residential premises from remote locations. Requires consistent packet delivery with minimal latency for real-time monitoring capabilities.",
            "network_requirements": {
                "message_size": 20,           // Total message packets required
                "rate": [1],                  // Single rate option for consistent delivery
                "latency_tolerance": "low",   // Real-time requirements
                "packet_priority": "high",    // High priority network traffic
                "compression_ratio": 0.8      // Video compression efficiency
            },
            "quality_parameters": {
                "drops_allowed": True,        // Some packet loss acceptable
                "error_correction": False,    // No built-in error correction
                "redundancy_level": "low"     // Minimal redundancy requirements
            },
            "reward_structure": {
                "reward_per_packet": 4,       // Base reward per successfully delivered packet
                "penalty_per_packet": 0,      // No penalty for packet loss (drops allowed)
                "completion_bonus": 20,       // Bonus for full message completion
                "quality_bonus": 10           // Bonus for maintaining quality metrics
            },
            "economic_parameters": {
                "application_fee": 40,        // Initial deployment cost
                "maintenance_cost": 2,        // Per-turn maintenance cost
                "upgrade_cost": 15            // Cost for performance upgrades
            },
            "completion_criteria": {
                "bonus_condition": None,      // No special bonus conditions
                "penalty_condition": None,    // No penalty conditions
                "time_limit": None            // No time constraints
            }
        },
        {
            "type": ActivityType.HOME_SURVEILLANCE,
            "title": "PREMIUM HOME SURVEILLANCE",
            "description": "Home surveillance application with enhanced features including motion detection, facial recognition and cloud storage integration. Requires optimized packet delivery with quality bonuses for sustained performance.",
            "network_requirements": {
                "message_size": 20,
                "rate": [1],
                "latency_tolerance": "very_low",
                "packet_priority": "critical",
                "compression_ratio": 0.9
            },
            "quality_parameters": {
                "drops_allowed": True,
                "error_correction": True,
                "redundancy_level": "medium"
            },
            "reward_structure": {
                "reward_per_packet": 3,       // Lower base reward
                "packet_bonus": 4,            // Additional bonus per packet after threshold
                "penalty_per_packet": 0,
                "completion_bonus": 25,
                "quality_bonus": 15
            },
            "economic_parameters": {
                "application_fee": 40,
                "maintenance_cost": 3,
                "upgrade_cost": 20
            },
            "completion_criteria": {
                "bonus_condition": 10,        // Bonus triggered after 10 packets received
                "penalty_condition": None,
                "time_limit": None,
                "quality_threshold": 0.95     // 95% delivery rate required for bonuses
            }
        },
        // REAL-TIME COMMUNICATION - Interactive applications with strict timing requirements
        {
            "type": ActivityType.REAL_TIME_COMMUNICATION,
            "title": "VIDEO CONFERENCING SERVICE",
            "description": "Implement a video conferencing service supporting multiple participants with real-time audio and video transmission. Critical timing requirements with penalties for packet loss.",
            "network_requirements": {
                "message_size": 30,
                "rate": [2, 3],              // Multiple rate options for adaptive quality
                "latency_tolerance": "critical",
                "packet_priority": "real_time",
                "compression_ratio": 0.7
            },
            "quality_parameters": {
                "drops_allowed": False,       // No packet loss acceptable
                "error_correction": True,
                "redundancy_level": "high"
            },
            "reward_structure": {
                "reward_per_packet": 5,
                "penalty_per_packet": 3,      // Penalty for packet loss
                "completion_bonus": 40,
                "quality_bonus": 25
            },
            "economic_parameters": {
                "application_fee": 60,
                "maintenance_cost": 5,
                "upgrade_cost": 30
            },
            "completion_criteria": {
                "bonus_condition": None,
                "penalty_condition": 15,      // Penalty triggered after 15 lost packets
                "time_limit": 8,              // Must complete within 8 turns
                "quality_threshold": 0.98
            }
        }
        // Additional activity types covering various network application scenarios
        // [File Transfer, Online Gaming, IoT Sensor Networks, etc.]
    ]
    
    // Create activity cards for each color with attribute mapping
    for color in colors:
        for idx, template in enumerate(activity_templates):
            activity_id <- f"activity_{idx+1}_{color}"
            
            // Create activity card with full specifications
            activity_card <- ActivityCard(
                activity_id=activity_id,
                activity_type=template["type"],
                color=color,
                title=template["title"],
                description=template["description"],
                
                // Network requirements and specifications
                message_size=template["network_requirements"]["message_size"],
                rate=template["network_requirements"]["rate"],
                latency_tolerance=template["network_requirements"]["latency_tolerance"],
                packet_priority=template["network_requirements"]["packet_priority"],
                compression_ratio=template["network_requirements"]["compression_ratio"],
                
                // Quality parameters and service level agreements
                destination="Central Network Node",
                drops_allowed=template["quality_parameters"]["drops_allowed"],
                error_correction=template["quality_parameters"]["error_correction"],
                redundancy_level=template["quality_parameters"]["redundancy_level"],
                
                // Reward and penalty structure
                reward_per_packet=template["reward_structure"]["reward_per_packet"],
                packet_bonus=template["reward_structure"].get("packet_bonus", 0),
                penalty_per_packet=template["reward_structure"]["penalty_per_packet"],
                completion_bonus=template["reward_structure"]["completion_bonus"],
                quality_bonus=template["reward_structure"]["quality_bonus"],
                
                // Economic parameters
                application_fee=template["economic_parameters"]["application_fee"],
                maintenance_cost=template["economic_parameters"]["maintenance_cost"],
                upgrade_cost=template["economic_parameters"]["upgrade_cost"],
                
                // Completion criteria and performance metrics
                bonus_condition=template["completion_criteria"]["bonus_condition"],
                penalty_condition=template["completion_criteria"]["penalty_condition"],
                time_limit=template["completion_criteria"]["time_limit"],
                quality_threshold=template["completion_criteria"].get("quality_threshold", 0.9),
                
                // Metadata and system management
                sell_cost=0,                  // Activities cannot be sold once deployed
                created_timestamp=get_current_timestamp(),
                validation_status="valid",
                performance_metrics=self._initialize_activity_metrics(),
                network_compatibility=self._generate_activity_compatibility_matrix(template["type"])
            )
            
            // Store in database with indexing
            self.activities[activity_id] <- activity_card
            
            // Update activity-specific indices and performance tracking
            self._update_activity_indices(activity_card)
            self._initialize_activity_performance_tracking(activity_card)
    
    // Generate activity compatibility matrices and performance benchmarks
    self._generate_activity_compatibility_matrices()
    self._establish_activity_performance_benchmarks()
    
    // Validate activity specifications against network capacity requirements
    self._validate_activity_network_requirements()
```

##### Action and Event Cards Implementation

```pseudocode
Function _create_event_cards():
    // Event templates covering realistic network scenarios
    event_templates <- [
        // TRANSMISSION DELAY events with various configurations and targeting
        {
            "event_type": EventType.TRANSMISSION_DELAY,
            "severity": "minor",
            "duration_turns": 1,
            "router_id": 1,
            "target_player": None,      // Affects own player by default
            "player_choice": False,     // No player choice in targeting
            "network_impact": {
                "throughput_reduction": 0.5,    // 50% throughput reduction
                "latency_increase": 2.0,        // 2x latency increase
                "packet_loss_rate": 0.1         // 10% packet loss
            },
            "description_template": "Network congestion is causing transmission delays on {target_description}. Packet processing is slowed.",
            "mitigation_options": ["traffic_shaping", "alternative_routing"],
            "recovery_time": "automatic"
        },
        {
            "event_type": EventType.TRANSMISSION_DELAY,
            "severity": "moderate",
            "duration_turns": 1,
            "router_id": 2,
            "target_player": None,
            "player_choice": False,
            "network_impact": {
                "throughput_reduction": 0.3,
                "latency_increase": 1.5,
                "packet_loss_rate": 0.05
            },
            "description_template": "Moderate network congestion detected on {target_description}. Performance degradation expected.",
            "mitigation_options": ["load_balancing", "queue_management"],
            "recovery_time": "automatic"
        },
        {
            "event_type": EventType.TRANSMISSION_DELAY,
            "severity": "targeted",
            "duration_turns": 1,
            "router_id": 1,
            "target_player": "yellow",  // Specific targeted player attack
            "player_choice": False,
            "network_impact": {
                "throughput_reduction": 0.7,
                "latency_increase": 3.0,
                "packet_loss_rate": 0.15
            },
            "description_template": "Targeted network interference affecting {target_description}. Malicious traffic detected.",
            "mitigation_options": ["firewall_rules", "traffic_filtering"],
            "recovery_time": "manual_intervention"
        },
        {
            "event_type": EventType.TRANSMISSION_DELAY,
            "severity": "strategic",
            "duration_turns": 1,
            "router_id": 1,
            "target_player": None,      // Player choice in targeting
            "player_choice": True,      // Strategic targeting decision
            "network_impact": {
                "throughput_reduction": 0.6,
                "latency_increase": 2.5,
                "packet_loss_rate": 0.12
            },
            "description_template": "Network attack capabilities available. Choose target for maximum strategic impact.",
            "mitigation_options": ["defensive_measures", "counter_attack"],
            "recovery_time": "strategic"
        },
        {
            "event_type": EventType.TRANSMISSION_DELAY,
            "severity": "variable",
            "duration_turns": "variable", // Variable duration determined by dice roll
            "router_id": 1,
            "target_player": None,
            "player_choice": False,
            "network_impact": {
                "throughput_reduction": 0.4,
                "latency_increase": "variable",    // Impact scales with duration
                "packet_loss_rate": 0.08
            },
            "description_template": "Unpredictable network instability on {target_description}. Duration and impact uncertain.",
            "mitigation_options": ["monitoring", "adaptive_routing"],
            "recovery_time": "uncertain"
        },
        
        // LINK FAILURE events with network impacts
        {
            "event_type": EventType.LINK_FAILURE,
            "severity": "critical",
            "duration_turns": 2,
            "router_id": 1,
            "target_player": None,
            "player_choice": False,
            "network_impact": {
                "throughput_reduction": 1.0,       // Complete link failure
                "connectivity_loss": True,         // Total connectivity loss
                "packet_loss_rate": 1.0            // All packets lost
            },
            "description_template": "Link failure on {target_description}. All network connectivity lost.",
            "mitigation_options": ["backup_links", "rerouting", "emergency_repair"],
            "recovery_time": "extended"
        },
        
        // TRAFFIC BURST events with dynamic capacity challenges
        {
            "event_type": EventType.TRAFFIC_BURST,
            "severity": "high_demand",
            "duration_turns": 3,
            "router_id": 2,
            "target_player": None,
            "player_choice": False,
            "network_impact": {
                "additional_traffic": 2,           // 2 extra packets per turn
                "queue_pressure": "high",          // High queue utilization
                "overflow_risk": True              // Risk of buffer overflow
            },
            "description_template": "Traffic burst detected on {target_description}. Network capacity under pressure.",
            "mitigation_options": ["traffic_shaping", "capacity_expansion"],
            "recovery_time": "gradual"
        }
        // Additional event types covering network scenarios
        // [Equipment failures, security incidents, performance optimizations, etc.]
    ]
    
    // Create event cards with attribute mapping and targeting logic
    for idx, template in enumerate(event_templates):
        event_id <- f"event_{idx+1}"
        router_id <- template["router_id"]
        player_choice <- template["player_choice"]
        
        // Determine event type with default handling
        event_type <- template.get("event_type", EventType.TRANSMISSION_DELAY)
        
        // Generate dynamic title and description based on event type and severity
        title, description, effect_text <- self._generate_event_content(
            event_type, 
            template["severity"], 
            template["description_template"]
        )
        
        // Determine target allocation based on event number and type
        event_number <- idx + 1
        target_link, target_queue <- self._calculate_event_targets(
            event_number, 
            router_id, 
            event_type
        )
        
        // Calculate dynamic duration based on template specifications
        duration_turns <- self._process_event_duration(template["duration_turns"])
        
        // Create event card with full network modeling
        event_card <- EventCard(
            event_id=event_id,
            event_type=event_type,
            severity=template["severity"],
            title=title,
            description=description,
            effect_description=effect_text,
            
            // Temporal parameters
            duration_turns=duration_turns,
            recovery_time=template["recovery_time"],
            
            // Targeting specifications
            target_link=target_link,
            target_queue=target_queue,
            router_id=router_id,
            target_player=template["target_player"],
            player_choice=player_choice,
            
            // Network impact specifications
            network_impact=template["network_impact"],
            mitigation_options=template["mitigation_options"],
            
            // Strategic parameters
            strategic_value=self._calculate_strategic_value(template),
            countermeasure_effectiveness=self._calculate_countermeasure_effectiveness(template),
            
            // Metadata and system management
            created_timestamp=get_current_timestamp(),
            validation_status="valid",
            activation_requirements=self._determine_activation_requirements(event_type),
            network_prerequisites=self._generate_network_prerequisites(template)
        )
        
        // Store in database with indexing
        self.events[event_id] <- event_card
        
        // Update event-specific indices and strategic analysis
        self._update_event_indices(event_card)
        self._analyze_event_strategic_impact(event_card)
    
    // Generate event interaction matrices and strategic combinations
    self._generate_event_interaction_matrices()
    self._analyze_event_strategic_combinations()
    
    // Validate event specifications against network simulation requirements
    self._validate_event_network_modeling()
```

##### File System Integration Implementation

```pseudocode
Function _build_card_mappings():
    // Utilize universal environment detection utilities for cross-platform compatibility
    self.universal_paths <- get_universal_paths()
    self.environment <- self.universal_paths['environment']
    self.base_dir <- self.universal_paths['base_dir']
    
    // Log environment detection for system diagnostics
    print(f"Environment detected: {self.environment}")
    print(f"Base directory resolved: {self.base_dir}")
    print(f"Platform: {self.universal_paths['platform']}")
    
    // Initialize mapping structure for all card types
    mappings <- {
        "users": {},
        "equipments": {},
        "services": {},
        "actions": {},
        "events": {},
        "challenges": {},
        "activities": {},
        "contracts": {},
        
        // Additional metadata tracking
        "metadata": {
            "scan_timestamp": get_current_timestamp(),
            "environment": self.environment,
            "total_files_scanned": 0,
            "validation_errors": [],
            "missing_files": []
        }
    }
    
    // Color mapping for all card categories
    colors <- ["Blue", "Red", "Green", "Yellow"]
    total_files_processed <- 0
    
    // Process User cards with file validation
    for color in colors:
        color_lower <- color.lower()
        users_dir <- self._get_users_path(color)
        
        print(f"Scanning {color_lower} user cards in directory: {users_dir}")
        
        if os.path.exists(users_dir):
            try:
                files_found <- os.listdir(users_dir)
                print(f"Files discovered for {color_lower}: {len(files_found)} items")
                
                for filename in files_found:
                    if self._is_valid_user_card_file(filename):
                        try:
                            // Extract card metadata with validation
                            card_metadata <- self._extract_card_metadata(filename, users_dir)
                            
                            if card_metadata:
                                // Create file mapping entry
                                card_id <- f"{card_metadata['number']}_{color_lower}"
                                full_path <- os.path.join(users_dir, filename)
                                
                                // Validate file accessibility and format
                                if self._validate_card_file(full_path):
                                    mappings["users"][card_id] <- {
                                        "path": full_path,
                                        "color": color_lower,
                                        "number": card_metadata['number'],
                                        "filename": filename,
                                        "file_size": os.path.getsize(full_path),
                                        "last_modified": os.path.getmtime(full_path),
                                        "format_validated": True,
                                        "accessibility_confirmed": True
                                    }
                                    
                                    total_files_processed += 1
                                    print(f"Successfully mapped: User ID {card_id} -> {filename}")
                                else:
                                    mappings["metadata"]["validation_errors"].append({
                                        "file": full_path,
                                        "error": "File validation failed"
                                    })
                            
                        except ValueError as e:
                            print(f"Metadata extraction failed for {filename}: {e}")
                            mappings["metadata"]["validation_errors"].append({
                                "file": filename,
                                "error": f"Metadata extraction error: {e}"
                            })
                            continue
                            
            except PermissionError as e:
                print(f"Permission denied accessing directory {users_dir}: {e}")
                mappings["metadata"]["validation_errors"].append({
                    "directory": users_dir,
                    "error": f"Permission denied: {e}"
                })
        else:
            print(f"Directory not found: {users_dir}")
            mappings["metadata"]["missing_files"].append(users_dir)
    
    // Process Equipment cards with object detection integration validation
    equipment_types <- ["small_router", "medium_router", "short_link", "long_link"]
    
    for equipment_type in equipment_types:
        for color in colors:
            color_lower <- color.lower()
            equipment_dir <- self._get_equipment_path(equipment_type, color)
            
            if os.path.exists(equipment_dir):
                equipment_files <- self._scan_equipment_files(equipment_dir, equipment_type)
                
                for file_info in equipment_files:
                    // Validate object detection integration
                    object_name <- self._validate_object_detection_name(equipment_type, color_lower)
                    
                    if object_name:
                        equipment_id <- f"{equipment_type}_{file_info['specific_id']}_{color_lower}"
                        
                        mappings["equipments"][equipment_id] <- {
                            "path": file_info["path"],
                            "color": color_lower,
                            "equipment_type": equipment_type,
                            "specific_id": file_info["specific_id"],
                            "object_name": object_name,
                            "detection_validated": True,
                            "file_size": file_info["file_size"],
                            "last_modified": file_info["last_modified"]
                        }
                        
                        total_files_processed += 1
    
    // Process Service, Activity, Challenge, Action and Event cards
    // [Similar processing for each card type]
    
    // Update metadata with scan results
    mappings["metadata"]["total_files_scanned"] = total_files_processed
    mappings["metadata"]["scan_completion_time"] = get_current_timestamp()
    
    // Generate validation report
    self._generate_file_mapping_validation_report(mappings)
    
    return mappings

Function _get_users_path(color):
    // Environment-aware path resolution with fallback strategies
    if self.environment == "raspberry_pi":
        // Production Raspberry Pi deployment paths
        primary_path <- os.path.join(self.base_dir, "img", "cartas", "users", "Residential-level", color)
        
        // Fallback paths for alternative deployment structures
        fallback_paths <- [
            os.path.join(self.base_dir, "cartas", "users", "Residential-level", color),
            os.path.join("/home/joaorebolo2/netmaster_menu/img/cartas/users/Residential-level", color)
        ]
        
        // Return first existing path
        for path in [primary_path] + fallback_paths:
            if os.path.exists(path):
                return path
                
        return primary_path  // Return primary path even if not found for error reporting
        
    else:
        // Development environment paths
        return os.path.join(self.base_dir, "Users", "Residential-level", color)

Function _validate_card_file(file_path):
    // File validation including format, accessibility and content verification
    try:
        // Check file accessibility
        if not os.access(file_path, os.R_OK):
            return False
            
        // Validate file format (PNG for card images)
        if not file_path.lower().endswith('.png'):
            return False
            
        // Check file size (reasonable bounds for card images)
        file_size <- os.path.getsize(file_path)
        if file_size < 1024 or file_size > 10 * 1024 * 1024:  # 1KB to 10MB range
            return False
            
        # Validate image format integrity
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                img.verify()  // Verify image integrity
                return True
        except Exception:
            return False
            
    except Exception as e:
        print(f"File validation error for {file_path}: {e}")
        return False
```

## NetMaster Server

### Software Architecture and Implementation

##### Server Initialization and Connection Management

```pseudocode
Function __init__():
    // Initialize core data structures for session and connection management
    self.sessions <- {}
    self.connected_clients <- {}  // websocket connections mapped by client ID
    self.player_to_session <- {}  // player_id -> session_id mapping for quick lookup
    self.running <- False
    self.session_timers <- {}     // session_id -> timer_info for server-controlled timing

Function start_server():
    // Configure server parameters and initialize logging system
    print("Starting NetMaster Server on " + SERVER_HOST + ":" + SERVER_PORT)
    print("Configuration:")
    print("   - Maximum " + MAX_PLAYERS_PER_SESSION + " players per session")
    print("   - Session duration: " + SESSION_DURATION_MINUTES + " minutes")
    print("   - Waiting timeout: " + WAITING_TIMEOUT_MINUTES + " minute(s)")
    print("   - Heartbeat interval: " + HEARTBEAT_INTERVAL + " seconds")
    
    self.running <- True
    
    // Initialize background maintenance tasks for system health
    create_task(self.cleanup_expired_sessions())
    create_task(self.heartbeat_monitor())
    
    // Start WebSocket server with connection handler
    serve(self.handle_client, SERVER_HOST, SERVER_PORT)
    print("NetMaster Server active at ws://" + SERVER_HOST + ":" + SERVER_PORT)
    print("Public access: ws://netmaster.vps.tecnico.ulisboa.pt:8000")

Function handle_client(websocket):
    // Generate unique client identifier for connection tracking
    client_id <- str(uuid.uuid4())
    self.connected_clients[client_id] <- websocket
    
    try:
        print("Client connected: " + client_id + " from " + websocket.remote_address)
        
        // Send welcome message with server information
        welcome_message <- {
            "type": "welcome",
            "client_id": client_id,
            "server_info": {
                "name": "NetMaster Server",
                "version": "1.0.0",
                "max_players_per_session": MAX_PLAYERS_PER_SESSION,
                "session_duration_minutes": SESSION_DURATION_MINUTES
            }
        }
        await self.send_message(websocket, welcome_message)
        
        // Process incoming messages with error handling
        async for message in websocket:
            try:
                data <- json.loads(message)
                await self.process_message(client_id, websocket, data)
            except json.JSONDecodeError:
                print("Invalid JSON message from " + client_id + ": " + message)
                await self.send_error(websocket, "Invalid message format")
            except Exception as e:
                print("Error processing message from " + client_id + ": " + e)
                await self.send_error(websocket, "Internal error: " + str(e))
                
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected: " + client_id)
    except Exception as e:
        print("Error in connection " + client_id + ": " + e)
    finally:
        await self.cleanup_client(client_id)
```

### Features

##### Concurrent Session Management Implementation

```pseudocode
Function handle_create_session(client_id, websocket, data):
    try:
        // Extract and validate session parameters
        player_name <- data.get("player_name", "Player")
        player_color <- data.get("color", "red")
        duration_minutes <- data.get("duration_minutes", SESSION_DURATION_MINUTES)
        
        // Validate duration within acceptable bounds (15-120 minutes)
        if not isinstance(duration_minutes, int) or duration_minutes < 15 or duration_minutes > 120:
            await self.send_error(websocket, "Invalid duration: " + duration_minutes + ". Must be between 15 and 120 minutes.")
            return
        
        // Validate player color selection
        try:
            color_enum <- PlayerColor(player_color.lower())
        except ValueError:
            await self.send_error(websocket, "Invalid color: " + player_color)
            return
        
        // Generate unique identifiers for session and host player
        session_id <- str(uuid.uuid4())[:8]  // Short ID for easy sharing
        player_id <- str(uuid.uuid4())
        
        // Create host player with attributes
        host_player <- Player(
            id=player_id,
            name=player_name,
            color=color_enum,
            websocket=websocket,
            connected=True,
            last_heartbeat=time.time()
        )
        
        // Create new game session with configuration
        session <- GameSession(
            id=session_id,
            host_player_id=player_id,
            players={player_id: host_player},
            state=GameState.WAITING,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=duration_minutes),
            waiting_expires_at=datetime.now() + timedelta(minutes=WAITING_TIMEOUT_MINUTES),
            duration_minutes=duration_minutes
        )
        
        // Add host to turn order and broadcast system
        session.add_player_to_order(player_id)
        session.add_player_info(player_id, player_color, player_name, websocket)
        
        // Register session and player mappings in server data structures
        self.sessions[session_id] <- session
        self.player_to_session[player_id] <- session_id
        
        print("New session created: " + session_id + " by " + player_name + " (" + player_color + ") - Duration: " + duration_minutes + "min")
        
        // Send response to session creator
        session_dict <- session.to_dict()
        player_dict <- host_player.to_dict()
        
        await self.send_message(websocket, {
            "type": "session_created",
            "session": session_dict,
            "player_id": player_id,
            "player_info": player_dict
        })
        
        // Broadcast updated session list to all clients
        await self.broadcast_session_list_update()
        
    except Exception as e:
        print("Error creating session: " + e)
        await self.send_error(websocket, "Error creating session: " + str(e))

Function handle_join_session(client_id, websocket, data):
    try:
        // Extract joining player parameters
        session_id <- data.get("session_id")
        player_name <- data.get("player_name", "Player")
        player_color <- data.get("color")
        
        // Validate session existence and availability
        session <- self.sessions.get(session_id)
        if not session:
            await self.send_error(websocket, "Session not found")
            return
        
        if session.is_expired():
            await self.send_error(websocket, "Session expired")
            return
        
        if session.is_full():
            await self.send_error(websocket, "Session full")
            return
        
        // Handle color selection and availability
        if player_color:
            try:
                color_enum <- PlayerColor(player_color.lower())
                if color_enum not in session.get_available_colors():
                    await self.send_error(websocket, "Color " + player_color + " not available")
                    return
            except ValueError:
                await self.send_error(websocket, "Invalid color: " + player_color)
                return
        else:
            // Assign first available color automatically
            available_colors <- session.get_available_colors()
            if not available_colors:
                await self.send_error(websocket, "No colors available")
                return
            color_enum <- available_colors[0]
        
        // Create new player instance with data
        player_id <- str(uuid.uuid4())
        new_player <- Player(
            id=player_id,
            name=player_name,
            color=color_enum,
            websocket=websocket,
            connected=True,
            last_heartbeat=time.time()
        )
        
        // Add player to session with integration
        session.players[player_id] <- new_player
        self.player_to_session[player_id] <- session_id
        
        // Clear empty session markers if present
        if hasattr(session, "empty_since") and session.empty_since:
            session.empty_since <- None
            print("Session " + session_id + " no longer empty - canceling automatic removal")
        
        // Integrate player into turn system and broadcast network
        session.add_player_to_order(player_id)
        session.add_player_info(player_id, color_enum.value, player_name, websocket)
        
        // Extend waiting time when second player joins
        if len(session.players) == 2 and session.state == GameState.WAITING:
            session.waiting_expires_at <- datetime.now() + timedelta(minutes=1)
            print("Second player joined session " + session_id + ". Waiting time extended by 1 minute.")
        
        print(player_name + " (" + color_enum.value + ") joined session " + session_id)
        
        // Send join confirmation to new player
        await self.send_message(websocket, {
            "type": "session_joined",
            "session": session.to_dict(),
            "player_id": player_id,
            "player_info": new_player.to_dict()
        })
        
        // Notify existing players about new participant
        await self.broadcast_to_session(session_id, {
            "type": "player_joined",
            "player": new_player.to_dict(),
            "session": session.to_dict()
        }, exclude_player=player_id)
        
        // Update global session list
        await self.broadcast_session_list_update()
        
    except Exception as e:
        print("Error joining session: " + e)
        await self.send_error(websocket, "Error joining session: " + str(e))
```

##### Real-Time Communication Framework Implementation

```pseudocode
Function process_message(client_id, websocket, data):
    // Extract message type for routing
    message_type <- data.get("type")
    print("Message from " + client_id + ": " + message_type)
    
    // Define handler mapping for all message types
    handlers <- {
        "create_session": self.handle_create_session,
        "join_session": self.handle_join_session,
        "leave_session": self.handle_leave_session,
        "list_sessions": self.handle_list_sessions,
        "start_game": self.handle_start_game,
        "game_action": self.handle_game_action,
        "heartbeat": self.handle_heartbeat,
        "get_session_info": self.handle_get_session_info,
        "end_turn": self.handle_end_turn,
        "timer_sync": self.handle_timer_sync,
        "store_card_for_player": self.handle_store_card_for_player,
        "get_pending_cards": self.handle_get_pending_cards,
        "update_player_score": self.handle_update_player_score
    }
    
    // Route message to appropriate handler
    handler <- handlers.get(message_type)
    if handler:
        await handler(client_id, websocket, data)
    else:
        print("Unknown message type: " + message_type)
        await self.send_error(websocket, "Unsupported message type: " + message_type)

Function send_message(websocket, message):
    try:
        message_type <- message.get("type", "UNKNOWN")
        
        // Special handling for critical message types
        if message_type == "session_joined":
            print("*** SEND_MESSAGE: Sending SESSION_JOINED ***")
            print("*** WEBSOCKET: " + str(websocket) + " ***")
            print("*** WEBSOCKET CLOSED: " + str(self.is_websocket_closed(websocket)) + " ***")
        
        // Validate WebSocket connection status
        if self.is_websocket_closed(websocket):
            print("SEND_MESSAGE: WebSocket is closed - cannot send")
            raise websockets.exceptions.ConnectionClosed(None, None)
        
        // Test JSON serialization before sending
        json_message <- json.dumps(message)
        
        if message_type == "session_joined":
            print("*** JSON_MESSAGE: " + json_message[:200] + "... ***")
        
        // Send message with timeout protection
        print("*** STARTING WEBSOCKET.SEND() FOR " + message_type + " ***")
        await asyncio.wait_for(websocket.send(json_message), timeout=5.0)
        print("*** WEBSOCKET.SEND() COMPLETED FOR " + message_type + " ***")
        
        if message_type == "session_joined":
            print("*** SESSION_JOINED SENT SUCCESSFULLY! ***")
            print("*** POST-SEND: WEBSOCKET CLOSED: " + str(self.is_websocket_closed(websocket)) + " ***")
        
    except asyncio.TimeoutError:
        print("SEND_MESSAGE: Timeout sending message type " + message.get("type", "UNKNOWN"))
        raise Exception("Timeout sending message")
    except websockets.exceptions.ConnectionClosed:
        print("SEND_MESSAGE: WebSocket connection closed for message type " + message.get("type", "UNKNOWN"))
        raise Exception("WebSocket connection closed")
    except TypeError as json_error:
        print("SEND_MESSAGE: JSON serialization error: " + str(json_error))
        print("SEND_MESSAGE: Problematic message: " + str(message))
        raise json_error
    except Exception as e:
        print("SEND_MESSAGE: General error sending message: " + str(e))
        raise e

Function broadcast_to_session(session_id, message, exclude_player=None):
    // Retrieve session for broadcasting
    session <- self.sessions.get(session_id)
    if not session:
        print("BROADCAST_ERROR: Session " + session_id + " not found")
        return
    
    print("BROADCAST_TO_SESSION: Sending " + message.get("type") + " to session " + session_id)
    print("BROADCAST_TO_SESSION: Players in session: " + str(list(session.players.keys())))
    print("BROADCAST_TO_SESSION: Exclude player: " + str(exclude_player))
    
    // Iterate through all session players
    for player_id, player in session.players.items():
        if exclude_player and player_id == exclude_player:
            print("BROADCAST_TO_SESSION: Skipping excluded player: " + player_id)
            continue
        
        print("BROADCAST_TO_SESSION: Attempting to send to " + player.name + " (ID: " + player_id + ")")
        print("BROADCAST_TO_SESSION: - WebSocket exists: " + str(player.websocket is not None))
        print("BROADCAST_TO_SESSION: - Player connected: " + str(player.connected))
        
        if player.websocket and player.connected:
            try:
                await self.send_message(player.websocket, message)
                print("BROADCAST_TO_SESSION: Message sent to " + player.name)
            except Exception as send_error:
                print("BROADCAST_TO_SESSION: X Error sending to " + player.name + ": " + str(send_error))
                // Mark player as disconnected on communication failure
                player.connected <- False
        else:
            print("BROADCAST_TO_SESSION: Player " + player.name + " without websocket or disconnected")

Function is_websocket_closed(websocket):
    // Check WebSocket status with version compatibility
    try:
        // New websockets version
        return websocket.close_code is not None
    except AttributeError:
        try:
            // Old websockets version
            return websocket.closed
        except AttributeError:
            // Fallback: assume connection is open
            return False
```

##### Game State Synchronization Implementation

```pseudocode
Function handle_end_turn(client_id, websocket, data):
    try:
        // Extract turn management parameters
        session_id <- data.get("session_id")
        player_id <- data.get("player_id")
        
        // Validate required parameters
        if not session_id or not player_id:
            await self.send_error(websocket, "session_id and player_id are required")
            return
        
        // Retrieve and validate session
        session <- self.sessions.get(session_id)
        if not session:
            await self.send_error(websocket, "Session not found")
            return
        
        if session.state != GameState.PLAYING:
            await self.send_error(websocket, "Session not in playing state")
            return
        
        // Verify turn ownership
        current_player_id <- session.get_current_player_id()
        if player_id != current_player_id:
            await self.send_error(websocket, "Not your turn")
            return
        
        print("End turn for player " + player_id + " in session " + session_id)
        
        // Advance to next player in turn order
        session.next_turn()
        
        // Get new current player information
        new_current_player_id <- session.get_current_player_id()
        new_current_player <- session.players.get(new_current_player_id)
        
        // Prepare turn change notification
        turn_changed_message <- {
            "type": "turn_changed",
            "current_player_id": new_current_player_id,
            "current_player_name": new_current_player.name,
            "current_player_color": new_current_player.color.value if hasattr(new_current_player.color, "value") else str(new_current_player.color),
            "player_order": session.player_order,
            "current_turn_index": session.current_turn_index,
            "session_id": session_id
        }
        
        print("Sending turn_changed: new player " + new_current_player.name + " (" + new_current_player_id + ")")
        await self.broadcast_to_session(session_id, turn_changed_message)
        
        // Send confirmation to turn-ending player
        await self.send_message(websocket, {
            "type": "end_turn_ack",
            "success": True,
            "next_player_id": new_current_player_id,
            "next_player_name": new_current_player.name
        })
        
    except Exception as e:
        print("Error processing end turn: " + str(e))
        await self.send_error(websocket, "Error processing end turn: " + str(e))

Function process_game_action(session, player_id, action_type, action_data, session_id=None):
    // Retrieve player instance from session
    player <- session.players.get(player_id)
    if not player:
        raise ValueError("Player not found in session")
    
    // If session_id not provided, attempt to find it
    if session_id is None:
        session_id <- self.player_to_session.get(player_id)
    
    // Process specific action types with logic
    if action_type == "move":
        // Handle player movement on game board
        new_position <- action_data.get("position", player.position)
        player.position <- new_position
        return {"new_position": new_position}
    
    else if action_type == "buy_card":
        // Handle card purchase transactions
        card_id <- action_data.get("card_id")
        cost <- action_data.get("cost", 0)
        
        if player.score >= cost:
            player.score <- player.score - cost
            return {"card_purchased": card_id, "new_score": player.score}
        else:
            raise ValueError("Insufficient funds")
    
    else if action_type == "end_turn":
        // Handle turn ending with multi-player support
        print("Processing end_turn for player " + player_id + " in session " + session_id)
        print("Players in session: " + str(len(session.players)))
        print("Current player order: " + str(session.player_order))
        print("Current turn index: " + str(session.current_turn_index))
        
        if len(session.players) > 1:
            // Verify turn ownership before advancing
            current_player_id <- session.get_current_player_id()
            if current_player_id != player_id:
                print("Player " + player_id + " tried to end turn, but it's " + current_player_id + "'s turn")
                raise ValueError("Not your turn. It's player " + current_player_id + "'s turn")
            
            next_player_id <- session.next_turn()
            next_player <- session.get_current_player()
            
            print("Next player: " + next_player_id + " (" + (next_player.name if next_player else "Unknown") + ")")
            print("New turn index: " + str(session.current_turn_index))
            
            // Broadcast turn change to all players
            turn_changed_message <- {
                "type": "turn_changed",
                "current_player_id": next_player_id,
                "current_player_name": next_player.name if next_player else "Unknown",
                "current_player_color": next_player.color.value if next_player and hasattr(next_player.color, "value") else str(next_player.color) if next_player else "unknown",
                "player_order": session.player_order,
                "current_turn_index": session.current_turn_index
            }
            
            print("Sending turn_changed: " + str(turn_changed_message))
            await self.broadcast_to_session(session_id, turn_changed_message)
            
            return {
                "message": "Turn ended",
                "next_player_id": next_player_id,
                "next_player_name": next_player.name if next_player else "Unknown"
            }
        else:
            print("Session with single player - solo mode")
            return {"message": "Turn ended (solo mode)"}
    
    else:
        return {"message": "Action " + action_type + " processed"}
```

##### Server-Controlled Timer System Implementation

```pseudocode
Function start_session_timer(session_id, duration_minutes):
    try:
        // Calculate total session duration in seconds
        total_seconds <- duration_minutes * 60
        timer_info <- {
            "task": None,
            "start_time": time.time(),
            "duration_seconds": total_seconds,
            "remaining_seconds": total_seconds
        }
        
        // Cancel existing timer if present to prevent conflicts
        if session_id in self.session_timers:
            old_timer <- self.session_timers[session_id]
            if old_timer.get("task") and not old_timer["task"].done():
                old_timer["task"].cancel()
        
        // Create and start new timer task
        timer_task <- create_task(self.run_session_timer(session_id, total_seconds))
        timer_info["task"] <- timer_task
        self.session_timers[session_id] <- timer_info
        
        print("[SERVER_TIMER] Timer started for session " + session_id + ": " + str(duration_minutes) + "min (" + str(total_seconds) + "s)")
        
    except Exception as e:
        print("Error starting session timer " + session_id + ": " + str(e))

Function run_session_timer(session_id, total_seconds):
    try:
        remaining <- total_seconds
        
        // Main timer loop with second-by-second updates
        while remaining > 0 and session_id in self.sessions:
            session <- self.sessions.get(session_id)
            if not session or session.state != GameState.PLAYING:
                print("[SERVER_TIMER] Session " + session_id + " no longer playing - stopping timer")
                break
            
            // Update timer information in server data structures
            if session_id in self.session_timers:
                self.session_timers[session_id]["remaining_seconds"] <- remaining
            
            // Broadcast timer update to all session participants
            timer_message <- {
                "type": "timer_sync",
                "time_remaining": remaining,
                "source": "server"
            }
            
            await self.broadcast_to_session(session_id, timer_message)
            print("[SERVER_TIMER] Sent timer_sync to session " + session_id + ": " + str(remaining) + "s remaining")
            
            // Wait one second before next update
            await asyncio.sleep(1)
            remaining <- remaining - 1
        
        // Handle timer expiration
        if remaining <= 0:
            print("[SERVER_TIMER] Timer expired for session " + session_id)
            await self.handle_session_timeout(session_id)
        
    except asyncio.CancelledError:
        print("[SERVER_TIMER] Timer canceled for session " + session_id)
    except Exception as e:
        print("[SERVER_TIMER] Error in session timer " + session_id + ": " + str(e))
    finally:
        // Clean up timer resources
        if session_id in self.session_timers:
            del self.session_timers[session_id]

Function handle_session_timeout(session_id):
    try:
        session <- self.sessions.get(session_id)
        if not session:
            return
        
        print("[SERVER_TIMER] Session " + session_id + " expired by timeout")
        
        // Mark as processed by timer to prevent duplicate processing
        session.timer_finished <- True
        print("[SERVER_TIMER] Session " + session_id + " marked as timer_finished")
        
        // Update session state
        session.state <- GameState.EXPIRED
        
        // Calculate final game results and determine winner
        if len(session.players) > 0:
            game_result <- self.calculate_game_winner(session)
            
            if game_result:
                print("Final result for session " + session_id + " (timer expired):")
                print("  Winner: " + game_result["winner"]["player_name"] + " (" + str(game_result["winner"]["score"]) + " points)")
                
                // Notify players about final results
                game_finished_message <- {
                    "type": "game_finished",
                    "message": "Game finished! Winner determined by highest score.",
                    "timeout_reason": "timer_expired",
                    "game_result": game_result
                }
                
                await self.broadcast_to_session(session_id, game_finished_message)
                print("[SERVER_TIMER] ✓ Sent game_finished to session " + session_id)
                
                // Allow time for message delivery
                await asyncio.sleep(2)
            else:
                // Fallback message when winner calculation fails
                fallback_message <- {
                    "type": "game_finished",
                    "message": "Game finished! Time expired.",
                    "timeout_reason": "timer_expired"
                }
                
                await self.broadcast_to_session(session_id, fallback_message)
                print("[SERVER_TIMER] ✓ Sent game_finished (fallback) to session " + session_id)
        
        // Schedule session cleanup after message delivery
        await asyncio.sleep(3)
        await self.cleanup_session(session_id)
        
    except Exception as e:
        print("Error handling session timeout " + session_id + ": " + str(e))

Function cleanup_session(session_id):
    try:
        if session_id in self.sessions:
            session <- self.sessions[session_id]
            
            // Remove players from mapping structures
            for player_id in list(session.players.keys()):
                if player_id in self.player_to_session:
                    del self.player_to_session[player_id]
            
            // Remove session from server
            del self.sessions[session_id]
            
            // Cancel and clean up timer resources
            if session_id in self.session_timers:
                timer_info <- self.session_timers[session_id]
                if timer_info.get("task") and not timer_info["task"].done():
                    timer_info["task"].cancel()
                del self.session_timers[session_id]
            
            print("[SERVER_TIMER] Session " + session_id + " completely removed")
            
            // Update global session list
            await self.broadcast_session_list_update()
            
    except Exception as e:
        print("Error cleaning up session " + session_id + ": " + str(e))

Function handle_timer_sync(client_id, websocket, data):
    try:
        // Timer is now server-controlled, ignore client attempts
        print("[SERVER_TIMER] Client " + client_id + " attempted timer_sync - ignored (server-controlled timer)")
        
        // Send informative response
        await self.send_message(websocket, {
            "type": "timer_sync_response",
            "message": "Timer is server-controlled",
            "server_controlled": True
        })
        
    except Exception as e:
        print("Error processing timer_sync message: " + str(e))
```

##### Card Distribution and Storage System Implementation

```pseudocode
Function handle_store_card_for_player(client_id, websocket, data):
    try:
        // Extract card transfer parameters
        sender_player_id <- data.get("sender_player_id")
        sender_color <- data.get("sender_color")
        target_player_color <- data.get("target_player_color")
        target_player_id <- data.get("target_player_id")
        card_data <- data.get("card_data", {})
        
        print("[CARD_STORAGE] Storing card from " + sender_color + " to " + target_player_color)
        print("[CARD_STORAGE] Card: " + card_data.get("card_path", "Unknown"))
        
        // Validate required parameters
        if not all([sender_player_id, sender_color, target_player_color, card_data]):
            print("[CARD_STORAGE] Incomplete data")
            await self.send_error(websocket, "Incomplete data for card storage")
            return
        
        // Find sender's session
        session_id <- self.player_to_session.get(sender_player_id)
        if not session_id or session_id not in self.sessions:
            print("[CARD_STORAGE] Session not found for player " + sender_color)
            await self.send_error(websocket, "Session not found")
            return
        
        session <- self.sessions[session_id]
        
        // Verify target player exists in same session
        target_player_found <- False
        for player in session.players.values():
            if player.color.value == target_player_color:
                target_player_found <- True
                break
        
        if not target_player_found:
            print("[CARD_STORAGE] Target player " + target_player_color + " not found in session")
            print("[CARD_STORAGE] SOLUTION: Returning card to store deck")
            
            // Return card to appropriate store deck instead of losing it
            success <- self.return_card_to_store(card_data, session_id)
            
            if success:
                print("[CARD_STORAGE] SUCCESS: Card returned to store successfully")
                await self.send_message(websocket, {
                    "type": "card_returned_to_store",
                    "reason": "target_player_not_in_session",
                    "message": "Player " + target_player_color + " not in session. Card returned to store.",
                    "card_path": card_data.get("card_path", ""),
                    "card_type": card_data.get("card_type", ""),
                    "status": "returned_to_store"
                })
            else:
                print("[CARD_STORAGE] ERROR: Failed to return card to store")
                await self.send_error(websocket, "Failed to return card to store")
            
            return
        
        // Store card in session for target player
        session.store_card_for_player(target_player_color, card_data)
        
        // Send confirmation to sender
        await self.send_message(websocket, {
            "type": "card_stored_confirmation",
            "target_player_color": target_player_color,
            "card_type": card_data.get("card_type", "Unknown"),
            "status": "stored",
            "message": "Card stored for " + target_player_color
        })
        
    except Exception as e:
        print("[CARD_STORAGE] Error storing card: " + str(e))
        await self.send_error(websocket, "Error storing card: " + str(e))

Function handle_get_pending_cards(client_id, websocket, data):
    try:
        // Extract pending card request parameters
        player_id <- data.get("player_id")
        player_color <- data.get("player_color")
        
        print("[CARD_DELIVERY] Pending cards request from " + player_color)
        
        // Validate required parameters
        if not all([player_id, player_color]):
            print("[CARD_DELIVERY] Incomplete data")
            await self.send_error(websocket, "Incomplete data for card retrieval")
            return
        
        // Find player's session
        session_id <- self.player_to_session.get(player_id)
        if not session_id or session_id not in self.sessions:
            print("[CARD_DELIVERY] Session not found for player " + player_color)
            await self.send_error(websocket, "Session not found")
            return
        
        session <- self.sessions[session_id]
        
        // Retrieve and clear pending cards
        pending_cards <- session.get_pending_cards(player_color)
        
        // Send pending cards to requesting player
        await self.send_message(websocket, {
            "type": "pending_cards",
            "cards": pending_cards
        })
        
    except Exception as e:
        print("[CARD_DELIVERY] Error retrieving pending cards: " + str(e))
        await self.send_error(websocket, "Error retrieving pending cards: " + str(e))

Function return_card_to_store(card_data, session_id):
    try:
        card_path <- card_data.get("card_path", "")
        card_type <- card_data.get("card_type", "")
        
        print("[RETURN_TO_STORE] Returning card to store:")
        print("[RETURN_TO_STORE]   Card: " + card_path)
        print("[RETURN_TO_STORE]   Type: " + card_type)
        print("[RETURN_TO_STORE]   Session: " + session_id)
        
        // Get session instance
        if session_id not in self.sessions:
            print("[RETURN_TO_STORE] Session " + session_id + " not found")
            return False
            
        session <- self.sessions[session_id]
        
        // Return card to appropriate store deck based on type
        if card_type == "actions":
            // Actions return to Actions deck in store
            if not hasattr(session, "store_actions_deck"):
                session.store_actions_deck <- []
            session.store_actions_deck.append(card_path)
            print("[RETURN_TO_STORE] Action returned to store Actions deck")
            
        else if card_type == "events":
            // Events return to Events deck in store  
            if not hasattr(session, "store_events_deck"):
                session.store_events_deck <- []
            session.store_events_deck.append(card_path)
            print("[RETURN_TO_STORE] Event returned to store Events deck")
            
        else:
            print("[RETURN_TO_STORE] Unknown card type: " + card_type)
            return False
        
        print("[RETURN_TO_STORE] SUCCESS: Card returned successfully")
        return True
        
    except Exception as e:
        print("[RETURN_TO_STORE] ERROR: " + str(e))
        return False
```

##### Session Discovery and Matching System Implementation

```pseudocode
Function handle_list_sessions(client_id, websocket, data):
    try:
        print("*** HANDLE_LIST_SESSIONS called by " + client_id + " ***")
        print("Total sessions on server: " + str(len(self.sessions)))
        
        // Filter available sessions with criteria
        available_sessions <- []
        for session_id, session in self.sessions.items():
            print("Checking session " + session_id + ":")
            print("  - State: " + str(session.state))
            print("  - Expired: " + str(session.is_expired()) + " (expires_at: " + str(session.expires_at) + ")")
            print("  - Full: " + str(session.is_full()) + " (players: " + str(len(session.players)) + "/" + str(session.max_players) + ")")
            print("  - Waiting expired: " + str(session.is_waiting_expired()) + " (waiting_expires_at: " + str(session.waiting_expires_at) + ")")
            print("  - Current time: " + str(datetime.now()))
            
            if (session.state in [GameState.WAITING, GameState.STARTING] and 
                not session.is_expired() and 
                not session.is_full()):
                print("  Session " + session_id + " INCLUDED in list")
                available_sessions.append(session.to_dict())
            else:
                print("  X Session " + session_id + " EXCLUDED from list")
        
        print("*** RESULT: " + str(len(available_sessions)) + " available sessions of " + str(len(self.sessions)) + " total ***")

        await self.send_message(websocket, {
            "type": "sessions_list",
            "sessions": available_sessions,
            "total_sessions": len(self.sessions),
            "available_sessions": len(available_sessions)
        })
        
    except Exception as e:
        print("Error listing sessions: " + str(e))
        await self.send_error(websocket, "Error listing sessions: " + str(e))

Function broadcast_session_list_update():
    try:
        // Generate current list of available sessions
        available_sessions <- []
        for session in self.sessions.values():
            if (session.state in [GameState.WAITING, GameState.STARTING] and 
                not session.is_expired() and 
                not session.is_full()):
                try:
                    session_dict <- session.to_dict()
                    available_sessions.append(session_dict)
                except Exception as session_error:
                    print("Error serializing session " + session.id + ": " + str(session_error))
                    continue
        
        message <- {
            "type": "sessions_list_update",
            "sessions": available_sessions
        }
        
        print("Broadcasting session list: " + str(len(available_sessions)) + " available sessions")
        
        // Send to all connected clients
        for client_id, websocket in list(self.connected_clients.items()):
            try:
                await self.send_message(websocket, message)
            except Exception as send_error:
                print("Error sending to client " + client_id + ": " + str(send_error))
                // Remove problematic client connection
                self.connected_clients.pop(client_id, None)
                
    except Exception as e:
        print("General error in broadcast_session_list_update: " + str(e))

Function filter_available_sessions():
    // Apply filtering criteria
    available_sessions <- []

    for session in self.sessions.values():
        if session.state in [GameState.WAITING, GameState.STARTING] and not session.is_expired() and not session.is_full():
            try:
                session_dict <- session.to_dict()
                available_sessions.append(session_dict)
            except Exception:
                continue

    return available_sessions
```

##### Resource Management and Background Tasks Implementation

```pseudocode
Function cleanup_expired_sessions():
    // Main cleanup loop with session lifecycle management
    while self.running:
        try:
            expired_sessions <- []
            waiting_timeout_sessions <- []
            
            // Categorize sessions requiring different cleanup approaches
            for session_id, session in self.sessions.items():
                if session.is_expired():
                    expired_sessions.append(session_id)
                else if session.is_waiting_expired():
                    waiting_timeout_sessions.append(session_id)
            
            // Process sessions with waiting timeout
            for session_id in waiting_timeout_sessions:
                session <- self.sessions[session_id]
                print("Session " + session_id + " expired by waiting timeout (1 minute)")
                
                if len(session.players) == 1:
                    // Convert single-player session to solo game
                    session.state <- GameState.PLAYING
                    
                    await self.broadcast_to_session(session_id, {
                        "type": "waiting_timeout",
                        "message": "Waiting timeout reached. You can start a solo game.",
                        "timeout_reason": "waiting_expired",
                        "allow_solo": True
                    })
                    
                    print("Session " + session_id + " converted to solo game")
                else:
                    // Handle multi-player waiting timeout
                    await self.broadcast_to_session(session_id, {
                        "type": "waiting_timeout",
                        "message": "Waiting timeout reached.",
                        "timeout_reason": "waiting_expired"
                    })
                    
                    // Remove players from multi-player sessions
                    for player_id in list(session.players.keys()):
                        await self.remove_player_from_session(player_id)
            
            // Process fully expired sessions
            for session_id in expired_sessions:
                session <- self.sessions[session_id]
                
                // Check if session already processed by timer system
                if getattr(session, "timer_finished", False):
                    print("Session " + session_id + " already processed by timer, skipping cleanup")
                    continue
                    
                print("Session " + session_id + " expired by total game time (cleanup)")
                
                // Calculate final results and determine winner
                if len(session.players) > 0:
                    game_result <- self.calculate_game_winner(session)
                    
                    if game_result:
                        print("Final result for session " + session_id + ":")
                        print("  Winner: " + game_result["winner"]["player_name"] + " (" + str(game_result["winner"]["score"]) + " points)")
                        
                        // Notify players about final results
                        await self.broadcast_to_session(session_id, {
                            "type": "game_finished",
                            "message": "Game finished! Winner determined by highest score.",
                            "timeout_reason": "session_expired",
                            "game_result": game_result
                        })
                        
                        // Allow message delivery time
                        await asyncio.sleep(2)
                    else:
                        // Fallback for winner calculation failure
                        await self.broadcast_to_session(session_id, {
                            "type": "session_expired",
                            "message": "Session expired",
                            "timeout_reason": "session_expired"
                        })
                else:
                    // Empty session handling
                    await self.broadcast_to_session(session_id, {
                        "type": "session_expired",
                        "message": "Session expired",
                        "timeout_reason": "session_expired"
                    })
                
                // Remove players after showing results
                for player_id in list(session.players.keys()):
                    await self.remove_player_from_session(player_id)
            
            // Update global session list if changes occurred
            if expired_sessions or waiting_timeout_sessions:
                await self.broadcast_session_list_update()
                
        except Exception as e:
            print("Error in session cleanup: " + str(e))
        
        // Check every 30 seconds for responsive cleanup
        await asyncio.sleep(30)

Function heartbeat_monitor():
    // Continuous connection health monitoring
    while self.running:
        try:
            current_time <- time.time()
            disconnected_players <- []
            
            // Check all players across all sessions
            for session_id, session in self.sessions.items():
                for player_id, player in session.players.items():
                    time_since_heartbeat <- current_time - player.last_heartbeat
                    if time_since_heartbeat > HEARTBEAT_INTERVAL * 2:
                        disconnected_players.append(player_id)
                        print(player.name + " no heartbeat for " + str(time_since_heartbeat) + "s")
            
            // Remove disconnected players
            for player_id in disconnected_players:
                await self.remove_player_from_session(player_id)
                
        except Exception as e:
            print("Error in heartbeat monitor: " + str(e))
        
        await asyncio.sleep(HEARTBEAT_INTERVAL)

Function calculate_game_winner(session):
    // Winner calculation based on final scores
    if not session.players:
        return None
    
    // Sort players by score (highest to lowest)
    players_by_score <- sorted(
        session.players.values(), 
        key=lambda p: p.score, 
        reverse=True
    )
    
    winner <- players_by_score[0]
    print("Winner of session " + session.id + ": " + winner.name + " with " + str(winner.score) + " points")
    
    // Create ranking
    ranking <- []
    for i, player in enumerate(players_by_score):
        ranking.append({
            "position": i + 1,
            "player_id": player.id,
            "player_name": player.name,
            "player_color": player.color.value if isinstance(player.color, PlayerColor) else player.color,
            "score": player.score,
            "is_winner": i == 0
        })
    
    return {
        "winner": {
            "player_id": winner.id,
            "player_name": winner.name,
            "player_color": winner.color.value if isinstance(winner.color, PlayerColor) else winner.color,
            "score": winner.score
        },
        "ranking": ranking,
        "total_players": len(session.players)
    }

Function handle_update_player_score(client_id, websocket, data):
    // Handle player score synchronization across clients
    try:
        player_id <- data.get("player_id")
        new_score <- data.get("score")
        session_id <- data.get("session_id")
        
        print("[SCORE_SYNC] Score update: player " + player_id + ", new score: " + str(new_score))
        
        if not player_id or new_score is None:
            await self.send_error(websocket, "player_id and score are required")
            return
        
        // Find session if not provided
        if not session_id:
            session_id <- self.player_to_session.get(player_id)
        
        if not session_id or session_id not in self.sessions:
            print("[SCORE_SYNC] Session not found for player " + player_id)
            await self.send_error(websocket, "Session not found")
            return
        
        session <- self.sessions[session_id]
        player <- session.players.get(player_id)
        
        if not player:
            print("[SCORE_SYNC] Player " + player_id + " not found in session " + session_id)
            await self.send_error(websocket, "Player not found in session")
            return
        
        // Update player score on server
        old_score <- player.score
        player.score <- new_score
        
        print("[SCORE_SYNC] ✓ Score updated: " + player.name + " (" + player_id + "): " + str(old_score) + " → " + str(new_score))
        
        // Send confirmation
        await self.send_message(websocket, {
            "type": "score_updated",
            "player_id": player_id,
            "old_score": old_score,
            "new_score": new_score,
            "success": True
        })
        
    except Exception as e:
        print("[SCORE_SYNC] Error updating player score: " + str(e))
        await self.send_error(websocket, "Error updating score: " + str(e))
```