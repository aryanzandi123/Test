document.addEventListener('DOMContentLoaded', () => {
    // --- Determine Page Context ---
    const isIndexPage = !!document.getElementById('status-display');

    // --- Early exit on viz page (inline script handles it) ---
    if (!isIndexPage) {
        return;
    }

    // --- Get all DOM elements (INDEX PAGE ONLY) ---
    const queryButton = document.getElementById('query-button');
    const proteinInput = document.getElementById('protein-input');

    // Track current protein for cancellation
    let currentProtein = null;
    let pollingIntervalId = null;

    // Config elements
    const interactorRoundsInput = document.getElementById('interactor-rounds');
    const functionRoundsInput = document.getElementById('function-rounds');
    const maxDepthSelect = document.getElementById('max-depth');

    // Interactor discovery round skips
    const skipRound1aCheckbox = document.getElementById('skip-round-1a');
    const skipRound1bCheckbox = document.getElementById('skip-round-1b');
    const skipRound1cCheckbox = document.getElementById('skip-round-1c');
    const skipRound1dCheckbox = document.getElementById('skip-round-1d');
    const skipRound1eCheckbox = document.getElementById('skip-round-1e');
    const skipRound1fCheckbox = document.getElementById('skip-round-1f');
    const skipRound1gCheckbox = document.getElementById('skip-round-1g');

    // Function discovery round skips
    const skipRound2aCheckbox = document.getElementById('skip-round-2a');
    const skipRound2a2Checkbox = document.getElementById('skip-round-2a2');
    const skipRound2a3Checkbox = document.getElementById('skip-round-2a3');
    const skipRound2a4Checkbox = document.getElementById('skip-round-2a4');
    const skipRound2a5Checkbox = document.getElementById('skip-round-2a5');
    const skipRound2bCheckbox = document.getElementById('skip-round-2b');
    const skipRound2b2Checkbox = document.getElementById('skip-round-2b2');
    const skipRound2b3Checkbox = document.getElementById('skip-round-2b3');

    // Post-processing skips
    const skipValidationCheckbox = document.getElementById('skip-validation');
    const skipDeduplicatorCheckbox = document.getElementById('skip-deduplicator');
    const skipArrowCheckbox = document.getElementById('skip-arrow-determination');
    const skipFactCheckingCheckbox = document.getElementById('skip-fact-checking');
    const skipPmidValidationCheckbox = document.getElementById('skip-pmid-validation');
    const skipMetadataGenerationCheckbox = document.getElementById('skip-metadata-generation');
    const skipSchemaValidationCheckbox = document.getElementById('skip-schema-validation');
    const skipFunctionCleaningCheckbox = document.getElementById('skip-function-cleaning');

    // Progress elements
    const progressWrapper = document.getElementById('progress-wrapper');
    const progressBarInner = document.getElementById('progress-bar-inner');
    const progressText = document.getElementById('progress-text');
    const progressPercent = document.getElementById('progress-percent');
    const statusMessage = document.getElementById('status-message');
    const cancelBtn = document.getElementById('cancel-btn');

    // --- updateStatus function ---
    const updateStatus = (progressData) => {
        const isProgressUpdate = typeof progressData === 'object' && progressData.current !== undefined;
        const messageText = isProgressUpdate ? `Step ${progressData.current}/${progressData.total}: ${progressData.text}` : (progressData.text || progressData);

        if (isProgressUpdate) {
            statusMessage.style.display = 'none';
            progressWrapper.style.display = 'block';
            if (cancelBtn) cancelBtn.style.display = 'block';
            const percentage = Math.round((progressData.current / progressData.total) * 100);
            progressBarInner.style.width = `${percentage}%`;
            progressText.textContent = `Step ${progressData.current}/${progressData.total}: ${progressData.text}`;
            progressPercent.textContent = `${percentage}%`;
        } else {
            progressWrapper.style.display = 'none';
            if (cancelBtn) cancelBtn.style.display = 'none';
            statusMessage.style.display = 'block';
            statusMessage.innerHTML = `<p>${messageText}</p>`;
        }
        console.log(`Status Update:`, progressData);
    };

    // --- Event Listeners ---
    if (proteinInput) {
        proteinInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                if (queryButton) queryButton.click();
            }
        });
    }

    if (queryButton) {
        queryButton.addEventListener('click', () => {
            const proteinName = proteinInput.value.trim();
            const validProteinRegex = /^[a-zA-Z0-9_-]+$/;

            if (!proteinName) {
                updateStatus("Please enter a protein name.");
                return;
            }

            if (!validProteinRegex.test(proteinName)) {
                updateStatus("Invalid format. Please use only letters, numbers, hyphens, and underscores.");
                return;
            }

            // NEW: Search first, then show query prompt if not found
            searchProtein(proteinName);
        });
    }

    // NEW: Search protein in database first
    const searchProtein = async (proteinName) => {
        updateStatus({ text: `Searching for ${proteinName}...` });

        try {
            const response = await fetch(`/api/search/${encodeURIComponent(proteinName)}`);

            if (!response.ok) {
                const errorData = await response.json();
                updateStatus({ text: errorData.error || 'Search failed' });
                return;
            }

            const data = await response.json();
            console.log('[DEBUG] Search result:', data);

            if (data.status === 'found') {
                // Protein exists in database - navigate immediately
                updateStatus({ text: `Found! Loading visualization for ${proteinName}...` });
                window.location.href = `/api/visualize/${encodeURIComponent(proteinName)}?t=${Date.now()}`;
            } else {
                // Protein not in database - show query prompt
                showQueryPrompt(proteinName);
            }
        } catch (error) {
            console.error('[ERROR] Search failed:', error);
            updateStatus({ text: 'Failed to search database.' });
        }
    };

    // Show "not found" message with "Start Query" button
    const showQueryPrompt = (proteinName) => {
        const message = `
            <div style="text-align: center; padding: 20px;">
                <p style="font-size: 16px; color: #6b7280; margin-bottom: 16px;">
                    Protein <strong>${proteinName}</strong> not found in database.
                </p>
                <button onclick="window.startQueryFromPrompt('${proteinName}')"
                        style="padding: 10px 20px; background: #3b82f6; color: white; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 14px;">
                    Start Research Query
                </button>
            </div>
        `;
        statusMessage.style.display = 'block';
        progressWrapper.style.display = 'none';
        statusMessage.innerHTML = message;
    };

    // Make startQuery available globally for the button onclick
    window.startQueryFromPrompt = (proteinName) => {
        startQuery(proteinName);
    };

    const startQuery = async (proteinName) => {
        // Stop any existing polling before starting a new query
        if (pollingIntervalId) {
            console.log('[DEBUG] Stopping existing polling interval');
            clearInterval(pollingIntervalId);
            pollingIntervalId = null;
        }

        // Track current protein for cancellation
        currentProtein = proteinName;

        // Get configuration values (fallback to localStorage if inputs don't exist)
        let interactorRounds = 3;
        let functionRounds = 3;
        let maxDepth = 3;

        // Interactor discovery round skips
        let skipRound1a = false, skipRound1b = false, skipRound1c = false;
        let skipRound1d = false, skipRound1e = false, skipRound1f = false, skipRound1g = false;

        // Function discovery round skips
        let skipRound2a = false, skipRound2a2 = false, skipRound2a3 = false;
        let skipRound2a4 = false, skipRound2a5 = false, skipRound2b = false;
        let skipRound2b2 = false, skipRound2b3 = false;

        // Post-processing skips
        let skipValidation = false, skipDeduplicator = false, skipArrowDetermination = false;
        let skipFactChecking = false, skipPmidValidation = false, skipMetadataGeneration = false;
        let skipSchemaValidation = false, skipFunctionCleaning = false;

        if (interactorRoundsInput && functionRoundsInput) {
            // On index page - read from inputs
            interactorRounds = parseInt(interactorRoundsInput.value) || 3;
            functionRounds = parseInt(functionRoundsInput.value) || 3;
            maxDepth = maxDepthSelect ? parseInt(maxDepthSelect.value) || 3 : 3;

            // Interactor discovery round skips
            skipRound1a = skipRound1aCheckbox ? skipRound1aCheckbox.checked : false;
            skipRound1b = skipRound1bCheckbox ? skipRound1bCheckbox.checked : false;
            skipRound1c = skipRound1cCheckbox ? skipRound1cCheckbox.checked : false;
            skipRound1d = skipRound1dCheckbox ? skipRound1dCheckbox.checked : false;
            skipRound1e = skipRound1eCheckbox ? skipRound1eCheckbox.checked : false;
            skipRound1f = skipRound1fCheckbox ? skipRound1fCheckbox.checked : false;
            skipRound1g = skipRound1gCheckbox ? skipRound1gCheckbox.checked : false;

            // Function discovery round skips
            skipRound2a = skipRound2aCheckbox ? skipRound2aCheckbox.checked : false;
            skipRound2a2 = skipRound2a2Checkbox ? skipRound2a2Checkbox.checked : false;
            skipRound2a3 = skipRound2a3Checkbox ? skipRound2a3Checkbox.checked : false;
            skipRound2a4 = skipRound2a4Checkbox ? skipRound2a4Checkbox.checked : false;
            skipRound2a5 = skipRound2a5Checkbox ? skipRound2a5Checkbox.checked : false;
            skipRound2b = skipRound2bCheckbox ? skipRound2bCheckbox.checked : false;
            skipRound2b2 = skipRound2b2Checkbox ? skipRound2b2Checkbox.checked : false;
            skipRound2b3 = skipRound2b3Checkbox ? skipRound2b3Checkbox.checked : false;

            // Post-processing skips
            skipValidation = skipValidationCheckbox ? skipValidationCheckbox.checked : false;
            skipDeduplicator = skipDeduplicatorCheckbox ? skipDeduplicatorCheckbox.checked : false;
            skipArrowDetermination = skipArrowCheckbox ? skipArrowCheckbox.checked : false;
            skipFactChecking = skipFactCheckingCheckbox ? skipFactCheckingCheckbox.checked : false;
            skipPmidValidation = skipPmidValidationCheckbox ? skipPmidValidationCheckbox.checked : false;
            skipMetadataGeneration = skipMetadataGenerationCheckbox ? skipMetadataGenerationCheckbox.checked : false;
            skipSchemaValidation = skipSchemaValidationCheckbox ? skipSchemaValidationCheckbox.checked : false;
            skipFunctionCleaning = skipFunctionCleaningCheckbox ? skipFunctionCleaningCheckbox.checked : false;
        } else {
            // On visualizer page - read from localStorage
            interactorRounds = parseInt(localStorage.getItem('interactor_rounds')) || 3;
            functionRounds = parseInt(localStorage.getItem('function_rounds')) || 3;
            maxDepth = parseInt(localStorage.getItem('max_depth')) || 3;

            // Interactor discovery round skips
            skipRound1a = localStorage.getItem('skip_round_1a') === 'true';
            skipRound1b = localStorage.getItem('skip_round_1b') === 'true';
            skipRound1c = localStorage.getItem('skip_round_1c') === 'true';
            skipRound1d = localStorage.getItem('skip_round_1d') === 'true';
            skipRound1e = localStorage.getItem('skip_round_1e') === 'true';
            skipRound1f = localStorage.getItem('skip_round_1f') === 'true';
            skipRound1g = localStorage.getItem('skip_round_1g') === 'true';

            // Function discovery round skips
            skipRound2a = localStorage.getItem('skip_round_2a') === 'true';
            skipRound2a2 = localStorage.getItem('skip_round_2a2') === 'true';
            skipRound2a3 = localStorage.getItem('skip_round_2a3') === 'true';
            skipRound2a4 = localStorage.getItem('skip_round_2a4') === 'true';
            skipRound2a5 = localStorage.getItem('skip_round_2a5') === 'true';
            skipRound2b = localStorage.getItem('skip_round_2b') === 'true';
            skipRound2b2 = localStorage.getItem('skip_round_2b2') === 'true';
            skipRound2b3 = localStorage.getItem('skip_round_2b3') === 'true';

            // Post-processing skips
            skipValidation = localStorage.getItem('skip_validation') === 'true';
            skipDeduplicator = localStorage.getItem('skip_deduplicator') === 'true';
            skipArrowDetermination = localStorage.getItem('skip_arrow_determination') === 'true';
            skipFactChecking = localStorage.getItem('skip_fact_checking') === 'true';
            skipPmidValidation = localStorage.getItem('skip_pmid_validation') === 'true';
            skipMetadataGeneration = localStorage.getItem('skip_metadata_generation') === 'true';
            skipSchemaValidation = localStorage.getItem('skip_schema_validation') === 'true';
            skipFunctionCleaning = localStorage.getItem('skip_function_cleaning') === 'true';
        }

        // Save to localStorage for next time
        localStorage.setItem('interactor_rounds', interactorRounds);
        localStorage.setItem('function_rounds', functionRounds);
        localStorage.setItem('max_depth', maxDepth);

        // Interactor discovery round skips
        localStorage.setItem('skip_round_1a', skipRound1a);
        localStorage.setItem('skip_round_1b', skipRound1b);
        localStorage.setItem('skip_round_1c', skipRound1c);
        localStorage.setItem('skip_round_1d', skipRound1d);
        localStorage.setItem('skip_round_1e', skipRound1e);
        localStorage.setItem('skip_round_1f', skipRound1f);
        localStorage.setItem('skip_round_1g', skipRound1g);

        // Function discovery round skips
        localStorage.setItem('skip_round_2a', skipRound2a);
        localStorage.setItem('skip_round_2a2', skipRound2a2);
        localStorage.setItem('skip_round_2a3', skipRound2a3);
        localStorage.setItem('skip_round_2a4', skipRound2a4);
        localStorage.setItem('skip_round_2a5', skipRound2a5);
        localStorage.setItem('skip_round_2b', skipRound2b);
        localStorage.setItem('skip_round_2b2', skipRound2b2);
        localStorage.setItem('skip_round_2b3', skipRound2b3);

        // Post-processing skips
        localStorage.setItem('skip_validation', skipValidation);
        localStorage.setItem('skip_deduplicator', skipDeduplicator);
        localStorage.setItem('skip_arrow_determination', skipArrowDetermination);
        localStorage.setItem('skip_fact_checking', skipFactChecking);
        localStorage.setItem('skip_pmid_validation', skipPmidValidation);
        localStorage.setItem('skip_metadata_generation', skipMetadataGeneration);
        localStorage.setItem('skip_schema_validation', skipSchemaValidation);
        localStorage.setItem('skip_function_cleaning', skipFunctionCleaning);

        updateStatus({ text: `Checking for ${proteinName}...` });
        try {
            console.log(`[DEBUG] Starting query for: ${proteinName}`);
            console.log(`[DEBUG] Config: interactor=${interactorRounds}, function=${functionRounds}, skip=${skipValidation}`);

            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    protein: proteinName,
                    interactor_rounds: interactorRounds,
                    function_rounds: functionRounds,
                    max_depth: maxDepth,
                    // Interactor discovery round skips
                    skip_round_1a: skipRound1a,
                    skip_round_1b: skipRound1b,
                    skip_round_1c: skipRound1c,
                    skip_round_1d: skipRound1d,
                    skip_round_1e: skipRound1e,
                    skip_round_1f: skipRound1f,
                    skip_round_1g: skipRound1g,
                    // Function discovery round skips
                    skip_round_2a: skipRound2a,
                    skip_round_2a2: skipRound2a2,
                    skip_round_2a3: skipRound2a3,
                    skip_round_2a4: skipRound2a4,
                    skip_round_2a5: skipRound2a5,
                    skip_round_2b: skipRound2b,
                    skip_round_2b2: skipRound2b2,
                    skip_round_2b3: skipRound2b3,
                    // Post-processing skips
                    skip_validation: skipValidation,
                    skip_deduplicator: skipDeduplicator,
                    skip_arrow_determination: skipArrowDetermination,
                    skip_fact_checking: skipFactChecking,
                    skip_pmid_validation: skipPmidValidation,
                    skip_metadata_generation: skipMetadataGeneration,
                    skip_schema_validation: skipSchemaValidation,
                    skip_function_cleaning: skipFunctionCleaning
                })
            });

            console.log(`[DEBUG] Response status: ${response.status}`);

            if (!response.ok) throw new Error(`Server error`);
            const data = await response.json();

            console.log(`[DEBUG] Response data:`, data);

            if (data.status === 'complete') {
                updateStatus({ text: `Cached result found! Loading visualization for ${proteinName}...` });
                // Add timestamp to force refresh even for cached results
                window.location.href = `/api/visualize/${proteinName}?t=${Date.now()}`;
            } else if (data.status === 'processing') {
                pollStatus(proteinName);
            } else {
                updateStatus({ text: `Error: ${data.message || 'Unknown error'}` });
            }
        } catch (error) {
            console.error("Failed to start query:", error);
            updateStatus({ text: `Failed to connect to the server.` });
        }
    };

    const pollStatus = (proteinName) => {
        updateStatus({ text: `Initializing...` });
        proteinInput.value = ''; // Clear input after a new job starts
        pollingIntervalId = setInterval(async () => {
            try {
                const response = await fetch(`/api/status/${proteinName}`);
                if (!response.ok) throw new Error(`Server error`);
                const data = await response.json();
                if (data.status === 'complete') {
                    clearInterval(pollingIntervalId);
                    pollingIntervalId = null;
                    currentProtein = null;
                    handleComplete(proteinName);
                } else if (data.status === 'cancelled' || data.status === 'cancelling') {
                    clearInterval(pollingIntervalId);
                    pollingIntervalId = null;
                    currentProtein = null;
                    updateStatus({ text: 'Job cancelled.' });
                } else if (data.status === 'error') {
                    clearInterval(pollingIntervalId);
                    pollingIntervalId = null;
                    currentProtein = null;
                    updateStatus(data.progress || "An unknown error occurred.");
                } else {
                    if (data.progress) {
                        updateStatus(data.progress);
                    }
                }
            } catch (error) {
                console.error("Polling failed:", error);
                clearInterval(pollingIntervalId);
                pollingIntervalId = null;
                currentProtein = null;
                updateStatus({ text: `Lost connection while checking ${proteinName}.` });
            }
        }, 5000);
    };

    const handleComplete = (proteinName) => {
        updateStatus({ text: `Pipeline complete! Loading visualization for ${proteinName}...` });
        window.location.href = `/api/visualize/${proteinName}?t=${Date.now()}`;
    };

    // --- Config Helper Functions ---
    // Restore saved settings from localStorage
    if (interactorRoundsInput && functionRoundsInput) {
        const savedInteractor = localStorage.getItem('interactor_rounds');
        const savedFunction = localStorage.getItem('function_rounds');

        if (savedInteractor) interactorRoundsInput.value = savedInteractor;
        if (savedFunction) functionRoundsInput.value = savedFunction;

        // Restore interactor discovery round skips
        if (skipRound1aCheckbox && localStorage.getItem('skip_round_1a') === 'true') skipRound1aCheckbox.checked = true;
        if (skipRound1bCheckbox && localStorage.getItem('skip_round_1b') === 'true') skipRound1bCheckbox.checked = true;
        if (skipRound1cCheckbox && localStorage.getItem('skip_round_1c') === 'true') skipRound1cCheckbox.checked = true;
        if (skipRound1dCheckbox && localStorage.getItem('skip_round_1d') === 'true') skipRound1dCheckbox.checked = true;
        if (skipRound1eCheckbox && localStorage.getItem('skip_round_1e') === 'true') skipRound1eCheckbox.checked = true;
        if (skipRound1fCheckbox && localStorage.getItem('skip_round_1f') === 'true') skipRound1fCheckbox.checked = true;
        if (skipRound1gCheckbox && localStorage.getItem('skip_round_1g') === 'true') skipRound1gCheckbox.checked = true;

        // Restore function discovery round skips
        if (skipRound2aCheckbox && localStorage.getItem('skip_round_2a') === 'true') skipRound2aCheckbox.checked = true;
        if (skipRound2a2Checkbox && localStorage.getItem('skip_round_2a2') === 'true') skipRound2a2Checkbox.checked = true;
        if (skipRound2a3Checkbox && localStorage.getItem('skip_round_2a3') === 'true') skipRound2a3Checkbox.checked = true;
        if (skipRound2a4Checkbox && localStorage.getItem('skip_round_2a4') === 'true') skipRound2a4Checkbox.checked = true;
        if (skipRound2a5Checkbox && localStorage.getItem('skip_round_2a5') === 'true') skipRound2a5Checkbox.checked = true;
        if (skipRound2bCheckbox && localStorage.getItem('skip_round_2b') === 'true') skipRound2bCheckbox.checked = true;
        if (skipRound2b2Checkbox && localStorage.getItem('skip_round_2b2') === 'true') skipRound2b2Checkbox.checked = true;
        if (skipRound2b3Checkbox && localStorage.getItem('skip_round_2b3') === 'true') skipRound2b3Checkbox.checked = true;

        // Restore post-processing skips
        if (skipValidationCheckbox && localStorage.getItem('skip_validation') === 'true') skipValidationCheckbox.checked = true;
        if (skipDeduplicatorCheckbox && localStorage.getItem('skip_deduplicator') === 'true') skipDeduplicatorCheckbox.checked = true;
        if (skipArrowCheckbox && localStorage.getItem('skip_arrow_determination') === 'true') skipArrowCheckbox.checked = true;
        if (skipFactCheckingCheckbox && localStorage.getItem('skip_fact_checking') === 'true') skipFactCheckingCheckbox.checked = true;
        if (skipPmidValidationCheckbox && localStorage.getItem('skip_pmid_validation') === 'true') skipPmidValidationCheckbox.checked = true;
        if (skipMetadataGenerationCheckbox && localStorage.getItem('skip_metadata_generation') === 'true') skipMetadataGenerationCheckbox.checked = true;
        if (skipSchemaValidationCheckbox && localStorage.getItem('skip_schema_validation') === 'true') skipSchemaValidationCheckbox.checked = true;
        if (skipFunctionCleaningCheckbox && localStorage.getItem('skip_function_cleaning') === 'true') skipFunctionCleaningCheckbox.checked = true;
    }

    // --- Cancel Job Function ---
    window.cancelJob = async function() {
        if (!currentProtein) {
            console.warn('No current job to cancel');
            return;
        }

        if (cancelBtn) cancelBtn.disabled = true;

        try {
            const response = await fetch(`/api/cancel/${encodeURIComponent(currentProtein)}`, {
                method: 'POST'
            });

            if (response.ok) {
                updateStatus({ text: 'Job cancelled.' });
                currentProtein = null;
            } else {
                const data = await response.json();
                updateStatus({ text: `Failed to cancel: ${data.error || 'Unknown error'}` });
            }
        } catch (error) {
            console.error('Cancel request failed:', error);
            updateStatus({ text: 'Failed to cancel job.' });
        } finally {
            if (cancelBtn) {
                cancelBtn.disabled = false;
                cancelBtn.style.display = 'none';
            }
        }
    };
});

// --- Global Helper Functions (for inline onclick handlers) ---
function setPreset(interactorRounds, functionRounds, maxDepth) {
    const interactorInput = document.getElementById('interactor-rounds');
    const functionInput = document.getElementById('function-rounds');
    const depthSelect = document.getElementById('max-depth');

    if (interactorInput) interactorInput.value = interactorRounds;
    if (functionInput) functionInput.value = functionRounds;
    if (depthSelect) depthSelect.value = maxDepth;
}